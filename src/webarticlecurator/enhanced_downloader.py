#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# Good for downloading archive index and also the actual articles in two separate row

import os
import sys
from io import BytesIO
from collections import Counter
from urllib.parse import urlparse, quote, urlunparse

from warcio.warcwriter import WARCWriter
from warcio.exceptions import ArchiveLoadFailed
from warcio.archiveiterator import ArchiveIterator
from warcio.statusandheaders import StatusAndHeaders

from requests import Session
from requests.exceptions import RequestException

from urllib3 import disable_warnings
from urllib3.exceptions import ProtocolError, InsecureRequestWarning, LocationParseError

from chardet import detect
from ratelimit import limits, sleep_and_retry

respv_str = {10: '1.0', 11: '1.1'}

# Patch get_encoding_from_headers in requests


def _parse_content_type_header(header):
    """Returns content type and parameters from given header

    :param header: string
    :return: tuple containing content type and dictionary of
         parameters
    """

    tokens = header.split(';')
    content_type, params = tokens[0].strip(), tokens[1:]
    params_dict = {}
    items_to_strip = "\"' "

    for param in params:
        param = param.strip()
        if param:
            key, value = param, True
            index_of_equals = param.find("=")
            if index_of_equals != -1:
                key = param[:index_of_equals].strip(items_to_strip)
                value = param[index_of_equals + 1:].strip(items_to_strip)
            params_dict[key.lower()] = value
    return content_type, params_dict


def patched_get_encoding_from_headers(headers):
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    :rtype: str
    """

    content_type = headers.get('content-type')

    if not content_type:
        return None

    content_type, params = _parse_content_type_header(content_type)

    if 'charset' in params:
        return params['charset'].strip("'\"")

    if 'text' in content_type:
        # PATCH: Do not fallback to Latin1! Detect encoding instead!
        # Further info: https://github.com/psf/requests/issues/480#issuecomment-7901023
        return None

    if 'application/json' in content_type:
        # Assume UTF-8 based on RFC 4627: https://www.ietf.org/rfc/rfc4627.txt since the charset was unset
        return 'utf-8'


class WarcCachingDownloader:
    """
        This class optionally applies the supplied existing warc archive to retrieve the downloaded pages from cache
         in case of hit and writes the retrieved page to the newly created archive file.
         When the requested page is not present in the archive, it downloads the page and saves it into the new archive.

        It basically wraps WarcReader and WarcDownloader classes which do the hard work.

        All parameters are wired out to the CLI and are documented there.
    """
    def __init__(self, existing_warc_filenames, new_warc_filename, _logger, just_cache=False, download_params=None):
        self._logger = _logger
        if download_params is not None:
            strict_mode = download_params.pop('strict_mode', False)
            check_digest = download_params.pop('check_digest', False)
        else:
            strict_mode = False
            check_digest = False
            download_params = {}

        self.url_index = set()
        info_record_data = None
        if existing_warc_filenames is not None:  # Setup the supplied existing warc archive file as cache
            if isinstance(existing_warc_filenames, str):  # Transform it to list
                existing_warc_filenames = [existing_warc_filenames]
            self._cached_downloads = []
            for ex_warc_filename in existing_warc_filenames:
                cached_downloads = WarcReader(ex_warc_filename, _logger, strict_mode, check_digest)
                self._cached_downloads.append(cached_downloads)
                self.url_index |= cached_downloads.url_index
                info_record_data = cached_downloads.info_record_data

        if just_cache:
            self._new_downloads = WarcDummyDownloader()
        else:
            self._new_downloads = WarcDownloader(new_warc_filename, _logger, info_record_data, **download_params)

    def download_url(self, url, ignore_cache=False, return_warc_records_wo_writing=False):
        # 1) Check if the URL is explicitly marked as bad...
        if url in self._new_downloads.bad_urls:
            self._logger.log('WARNING', url, 'Skipping URL explicitly marked as bad!', sep='\t')
            return None
        # 2) If the URL is present in the newly created WARC file warn and skip the URL!
        elif url in self._new_downloads.good_urls:
            # 3) throw error and return None!
            self._logger.log('ERROR', 'Not processing URL, because it is already present in the WARC archive:', url)
            return None
        # 3) Check if the URL presents in the cached_content...
        elif url in self.url_index:
            # 3a) ...retrieve it! (from the last source WARC where the URL is found in)
            cache, reqv, resp = self.get_records_offset(url)
            # 3b) Get content even if the URL is a duplicate, because ignore_cache knows better what to do with it
            cached_content = cache.download_url(url)
            # 3c) Decide to return the records with the content XOR write the records and return the content only
            if return_warc_records_wo_writing:
                cached_content = ((cache, reqv, resp), cached_content)
            else:
                self._new_downloads.write_records_for_url(url, (cache, reqv, resp))
        else:
            cached_content = None

        # 4) If we have the URL cached...
        if cached_content is not None:
            if not ignore_cache:
                # 4a) and we do not explicitly ignore the cache, return the cached content!
                return cached_content
            else:
                # 4b) Log that we ignored the cached_content and do noting!
                self._logger.log('INFO', 'Ignoring cached_content for URL:', url)

        # 5) Really download the URL! (url not in cached_content or cached_content is ignored)
        #    Still check if the URL is already downloaded!
        return self._new_downloads.download_url(url, return_warc_records_wo_writing)

    def write_records_for_url(self, url, rec):
        self._new_downloads.write_records_for_url(url, rec)

    def get_records_offset(self, url):
        for cache in reversed(self._cached_downloads):
            if url in cache.url_index:
                reqv, resp = cache.get_record_data(url)
                break
        else:
            raise ValueError('INTERNAL ERROR: {0} not found in any supplied source WARC file,'
                             ' but is in the URL index!'.format(url))
        return cache, reqv, resp

    def get_records(self, url):
        cache, reqv, resp = self.get_records_offset(url)
        reqv_rec = cache.get_record(reqv[0])
        resp_rec = cache.get_record(resp[0])
        return cache, reqv_rec, resp_rec

    @property
    def bad_urls(self):  # Ready-only property for shortcut
        return self._new_downloads.bad_urls

    @property
    def good_urls(self):  # Ready-only property for shortcut
        return self._new_downloads.good_urls


class WarcDummyDownloader:
    """
        I.e. When want to use only the cache...
    """
    def __init__(self, *_, **__):
        self.bad_urls = set()
        self.good_urls = set()

    @staticmethod
    def download_url(*_, **__):
        return None

    @staticmethod
    def write_records_for_url(*_, **__):
        return None

    @staticmethod
    def write_record(*_, **__):
        return None


class WarcDownloader:
    """
        Download URL with HTTP GET, save to a WARC file and return the decoded text
    """
    def __init__(self, expected_filename, _logger, warcinfo_record_data=None, program_name='WebArticleCurator',
                 user_agent=None, overwrite_warc=True, err_threshold=10, known_bad_urls=None,
                 max_no_of_calls_in_period=2, limit_period=1, proxy_url=None, allow_cookies=False, verify_request=True,
                 stay_offline=False):
        # Store variables
        self._logger = _logger
        self._req_headers = {'Accept-Encoding': 'identity', 'User-agent': user_agent}
        self._error_count = 0
        self._error_threshold = err_threshold  # Set the error threshold which cause aborting to prevent denial

        # Setup download function
        if not stay_offline:
            self.download_url = self._download_url
        else:
            self.download_url = self._dummy_download_url

        if known_bad_urls is not None:  # Setup the list of cached bad URLs to prevent trying to download them again
            with open(known_bad_urls, encoding='UTF-8') as fh:
                self.bad_urls = {line.strip() for line in fh}
        else:
            self.bad_urls = set()

        self.good_urls = set()

        # Setup target file handle
        filename = self._set_target_filename(expected_filename, overwrite_warc)
        self._logger.log('INFO', 'Creating archivefile:', filename)
        self._output_file = open(filename, 'wb')

        self._session = Session()  # Setup session for speeding up downloads
        if proxy_url is not None:  # Set socks proxy if provided
            self._session.proxies['http'] = proxy_url
            self._session.proxies['https'] = proxy_url

        self._allow_cookies = allow_cookies
        self._verify_request = verify_request
        if not self._verify_request:
            disable_warnings(InsecureRequestWarning)

        # Setup rate limiting to prevent hammering the server
        self._requests_get = sleep_and_retry(limits(calls=max_no_of_calls_in_period,
                                                    period=limit_period)(self._http_get_w_cookie_handling))

        self._writer = WARCWriter(self._output_file, gzip=True, warc_version='WARC/1.1')
        if warcinfo_record_data is None:  # Or use the parsed else custom headers will not be copied
            # INFO RECORD
            # Some custom information about the warc writer program and its settings
            warcinfo_record_data = {'software': program_name, 'arguments': ' '.join(sys.argv[1:]),
                                    'format': 'WARC File Format 1.1',
                                    'conformsTo': 'http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1-1_latestdraft.pdf'}
        info_record = self._writer.create_warcinfo_record(filename, warcinfo_record_data)
        self._writer.write_record(info_record)

    @staticmethod
    def _set_target_filename(filename, overwrite_warc):
        if not overwrite_warc:  # Find out next nonexisting warc filename
            num = 0
            while os.path.exists(filename):
                filename2, ext = os.path.splitext(filename)  # Should be filename.warc.gz
                if ext == '.gz' and filename2.endswith('.warc'):
                    filename2, ext2 = os.path.splitext(filename2)  # Should be filename.warc
                    ext = ext2 + ext  # Should be .warc.gz

                filename = '{0}-{1:05d}{2}'.format(filename2, num, ext)
                num += 1
        return filename

    def __del__(self):
        if hasattr(self, '_output_file'):  # If the program opened a file, then it should gracefully close it on exit!
            self._output_file.close()

    def _http_get_w_cookie_handling(self, *args, **kwargs):
        """
            Extend requests.get with optional cookie purging
        """
        if not self._allow_cookies:
            self._session.cookies.clear()
        return self._session.get(*args, **kwargs)

    def _handle_request_exception(self, url, msg):
        self._logger.log('WARNING', url, msg, sep='\t')

        self._error_count += 1
        if self._error_count >= self._error_threshold:
            raise NameError('Too many error happened! Threshold exceeded! See log for details!')

    @staticmethod
    def _get_peer_name(resp):
        # Must get peer_name before the content is read
        # It has no official API for that:
        # https://github.com/kennethreitz/requests/issues/2158
        # https://github.com/urllib3/urllib3/issues/1071
        # So workaround to be compatible with windows:
        # https://stackoverflow.com/questions/22492484/how-do-i-get-the-ip-address-from-a-http-request-using-the-\
        # requests-library/22513161#22513161
        try:
            peer_name = resp.raw._connection.sock.getpeername()[0]  # Must get peer_name before the content is read
        except AttributeError:  # On Windows there is no getpeername() Attribute of the class...
            try:
                peer_name = resp.raw._connection.sock.socket.getpeername()[0]
            except AttributeError:
                peer_name = 'None'  # Socket closed and could not determine peername...
        return peer_name

    def _dummy_download_url(self, *_, **__):
        raise NotImplementedError

    def _download_url(self, url, return_warc_records_wo_writing=False):
        if url in self.bad_urls:
            self._logger.log('DEBUG', 'Not downloading known bad URL:', url)
            return None

        if url in self.good_urls:  # This should not happen!
            self._logger.log('ERROR', 'Not downloading URL, because it is already downloaded in this session:', url)
            return None

        scheme, netloc, path, params, query, fragment = urlparse(url)
        # For safety urlencode the generated URL... (The URL might be modified in this step.)
        path = quote(path, safe='/%')
        url_reparsed = urlunparse((scheme, netloc, path, params, query, fragment))

        try:  # The actual request (on the reparsed URL, everything else is made on the original URL)
            resp = self._requests_get(url_reparsed, headers=self._req_headers, stream=True, verify=self._verify_request)
        # UnicodeError is originated from idna codec error, LocationParseError is originated from URLlib3 error
        except (UnicodeError, RequestException, LocationParseError) as err:
            self._handle_request_exception(url, 'RequestException happened during downloading: {0} \n\n'
                                                ' The program ignores it and jumps to the next one.'.format(err))
            return None

        if resp.status_code != 200:  # Not HTTP 200 OK
            self._handle_request_exception(url, 'Downloading failed with status code: {0} {1}'.format(resp.status_code,
                                                                                                      resp.reason))
            return None

        # REQUEST (build headers for warc)
        reqv_headers = resp.request.headers
        reqv_headers['Host'] = netloc

        proto = 'HTTP/{0}'.format(respv_str[resp.raw.version])  # Friendly protocol name
        reqv_http_headers = StatusAndHeaders('GET {0} {1}'.format(urlunparse(('', '', path, params, query, fragment)),
                                                                  proto), reqv_headers.items(), is_http_request=True)
        reqv_record = self._writer.create_warc_record(url, 'request', http_headers=reqv_http_headers)

        # RESPONSE
        # resp_status need to be stripped else warcio strips the spaces and digest verification will fail!
        resp_status = '{0} {1}'.format(resp.status_code, resp.reason).strip()
        resp_headers_list = resp.raw.headers.items()  # get raw headers from urllib3
        # Must get peer_name before the content is read
        peer_name = self._get_peer_name(resp)

        try:
            data = resp.raw.read()  # To be able to return decoded and also write warc
        except ProtocolError as err:
            self._handle_request_exception(url, 'RequestException happened during downloading: {0} \n\n'
                                                ' The program ignores it and jumps to the next one.'.format(err))
            return None

        if len(data) == 0:
            err = 'Response data has zero length!'
            self._handle_request_exception(url, 'RequestException happened during downloading: {0} \n\n'
                                                ' The program ignores it and jumps to the next one.'.format(err))
            return None

        # warcio hack as \r\n is the record separator and trailing ones will be split and digest will eventually fail!
        if data.endswith(b'\r\n'):  # TODO: Warcio bugreport!
            data = data.rstrip()

        # Get or detect encoding to decode the bytes of the text to str
        enc = patched_get_encoding_from_headers(resp.headers)
        if enc is None:
            enc = detect(data)['encoding']
        try:
            text = data.decode(enc)  # Normal decode process
        except UnicodeDecodeError:
            self._logger.log('WARNING', 'DECODE ERROR RETRYING IN \'IGNORE\' MODE:', url, enc, sep='\t')
            text = data.decode(enc, 'ignore')
        data_stream = BytesIO(data)  # Need the original byte stream to write the payload to the warc file

        resp_http_headers = StatusAndHeaders(resp_status, resp_headers_list, protocol=proto)
        # Add extra headers like encoding because it is not stored any other way...
        resp_record = self._writer.create_warc_record(url, 'response', payload=data_stream,
                                                      http_headers=resp_http_headers,
                                                      warc_headers_dict={'WARC-IP-Address': peer_name,
                                                                         'WARC-X-Detected-Encoding': enc})
        # Everything is OK
        if return_warc_records_wo_writing:
            # Return the WARC records and the text content
            return (None, reqv_record, resp_record), text
        else:
            # Write the two WARC records and return the text content only
            self.write_records_for_url(url, (None, reqv_record, resp_record))

            return text

    def write_records_for_url(self, url, rec):
        self.good_urls.add(url)
        if rec[0] is not None:
            cache, (reqv_offset, _), (resp_offset, _) = rec
            reqv_record = cache.get_record(reqv_offset)  # Seek to the appropriate pos in the WARC to retrive the record
            self._writer.write_record(reqv_record)       # else random zlib errors happen when the payload is removed
            resp_record = cache.get_record(resp_offset)  # from the cache
            self._writer.write_record(resp_record)
        else:
            _, reqv_record, resp_record = rec
            self._writer.write_record(reqv_record)
            self._writer.write_record(resp_record)


class WarcReader:
    def __init__(self, filename, _logger, strict_mode=False, check_digest=False):
        self.filename = filename
        self._stream = open(filename, 'rb')
        self._internal_url_index = {}
        self._logger = _logger
        self.info_record_data = None
        self._strict_mode = strict_mode
        if check_digest:
            check_digest = 'raise'
        self._check_digest = check_digest
        try:
            self._create_index()
        except KeyError as e:
            if self._strict_mode:
                raise e
            self._logger.log('ERROR', 'Ignoring exception:', e)

    def __del__(self):
        if hasattr(self, '_stream'):  # If the program opened a file, then it should gracefully close it on exit!
            self._stream.close()

    @property
    def url_index(self):  # Ready-only property for shortcut
        return self._internal_url_index.keys()

    def _create_index(self):
        self._logger.log('INFO', 'Creating index for {0}...'.format(self.filename))
        archive_it = ArchiveIterator(self._stream, check_digests=self._check_digest)
        info_rec = next(archive_it)
        # First record should be an info record, then it should be followed by the request-response pairs
        assert info_rec.rec_type == 'warcinfo'
        try:
            # Read out custom headers for later use
            custom_headers_raw = info_rec.content_stream().read()  # Parse custom headers
            if len(custom_headers_raw) == 0:
                raise ValueError('WARCINFO record payload length is 0!')
            # Read and parse the warcinfo record for writing it back unchanged into a warc file
            # else due to warcio problems it will not be copied properly!
            # See: https://github.com/webrecorder/warcio/issues/90
            # and https://github.com/webrecorder/warcio/issues/91
            self.info_record_data = dict(r.split(': ', maxsplit=1) for r in custom_headers_raw.decode('UTF-8')
                                         .strip().split('\r\n') if len(r) > 0)
        except ValueError as e:
            if self._strict_mode:
                raise e
            self._logger.log('WARNING', 'WARCINFO record in', self._stream.name,
                             'is corrupt! Continuing with a fresh one!')
            self.info_record_data = None

        archive_load_failed = False
        count = 0
        double_urls = Counter()
        reqv_data = (None, (None, None))  # To be able to handle the request-response pairs together
        for i, record in enumerate(archive_it):
            if record.rec_type == 'request':
                assert i % 2 == 0
                try:
                    reqv_data = (record.rec_headers.get_header('WARC-Target-URI'),
                                 (archive_it.get_record_offset(), archive_it.get_record_length()))
                except ArchiveLoadFailed as e:
                    self._logger.log('ERROR', 'REQUEST:', e.msg, 'for', reqv_data[0])
                    archive_load_failed = True
            if record.rec_type == 'response':
                assert i % 2 == 1
                resp_url = record.rec_headers.get_header('WARC-Target-URI')
                assert resp_url == reqv_data[0]
                double_urls[resp_url] += 1
                try:
                    self._internal_url_index[resp_url] = (reqv_data[1],  # Request-response pair
                                                          (archive_it.get_record_offset(),
                                                           archive_it.get_record_length()))
                except ArchiveLoadFailed as e:
                    self._logger.log('ERROR', 'RESPONSE:', e.msg, 'for', resp_url)
                    archive_load_failed = True
                count += 1
        if count != len(self._internal_url_index):
            double_urls_str = '\n'.join('{0}\t{1}'.format(url, freq) for url, freq in double_urls.most_common()
                                        if freq > 1)
            raise KeyError('The following double URLs detected in the WARC file:{0}'.format(double_urls_str))
        if count == 0:
            raise IndexError('No index created or no response records in the WARC file!')
        if archive_load_failed and self._strict_mode:
            raise ArchiveLoadFailed('Archive loading failed! See logs for details!')
        self._stream.seek(0)
        self._logger.log('INFO', 'Index successfully created.')

    def get_record_data(self, url):
        reqv_resp_pair = self._internal_url_index.get(url)
        if reqv_resp_pair is not None:
            return reqv_resp_pair  # ((offset, length), (offset, length))
        else:
            raise KeyError('The request or response is missing from the archive for URL: {0}'.format(url))

    def get_record(self, offset):
        self._stream.seek(offset)
        rec = next(iter(ArchiveIterator(self._stream, check_digests=self._check_digest)))
        return rec

    def download_url(self, url):
        text = None
        reqv_resp_pair = self._internal_url_index.get(url)
        if reqv_resp_pair is not None:
            offset = reqv_resp_pair[1][0]  # Only need the offset of the response part
            self._stream.seek(offset)  # Can not be cached as we also want to write it out to the new archive!
            record = next(iter(ArchiveIterator(self._stream, check_digests=self._check_digest)))
            data = record.content_stream().read()
            assert len(data) > 0
            enc = record.rec_headers.get_header('WARC-X-Detected-Encoding', 'UTF-8')
            text = data.decode(enc, 'ignore')
        else:
            self._logger.log('CRITICAL', url, 'URL not found in WARC!', sep='\t')

        return text
