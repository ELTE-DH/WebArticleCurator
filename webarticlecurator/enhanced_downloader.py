#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# Good for downloading archive index and also the actual articles in two separate row

import os
import sys
from io import BytesIO
from collections import Counter

from warcio.warcwriter import WARCWriter
from warcio.archiveiterator import ArchiveIterator
from warcio.statusandheaders import StatusAndHeaders
from warcio.exceptions import ArchiveLoadFailed

from requests import Session
from urllib.parse import urlparse, quote, urlunparse
from requests.exceptions import RequestException
from urllib3.exceptions import ProtocolError, InsecureRequestWarning, LocationParseError
from urllib3 import disable_warnings
from chardet import detect
from ratelimit import limits, sleep_and_retry

respv_str = {10: '1.0', 11: '1.1'}


class WarcCachingDownloader:
    """
        This class optionally applies the supplied existing warc archive to retrive the downloaded pages from cache
         in case of hit and writes the retrived page to the newly created archive file.
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

    def download_url(self, url, ignore_cache=False):
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
            # 3a) ...copy it! (from the last source WARC where the URL is found in)
            cache, reqv, resp = self.get_records(url)
            self._new_downloads.write_record(reqv, url)
            self._new_downloads.write_record(resp, url)
            # 3b) Get content even if the URL is a duplicate, because ignore_cache knows better what to do with it
            cached_content = cache.download_url(url)
        else:
            cached_content = None

        # 4) If we have the URL cached...
        if cached_content is not None:
            if not ignore_cache:
                # 4a) and we do not expliticly ignore the cache, return the cached content!
                return cached_content
            else:
                # 4b) Log that we ignored the cached_content and do noting!
                self._logger.log('INFO', 'Ignoring cached_content for URL:', url)

        # 5) Really download the URL! (url not in cached_content or cached_content is ignored)
        return self._new_downloads.download_url(url)  # Still check if the URL is already downloaded!

    def get_records(self, url):
        for cache in reversed(self._cached_downloads):
            if url in cache.url_index:
                reqv, resp = cache.get_record(url)
                break
        else:
            raise ValueError('INTERNAL ERROR: {0} not found in any supplied source WARC file,'
                             ' but is in the URL index!'.format(url))
        return cache, reqv, resp

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
    def download_url(_):
        return None

    @staticmethod
    def write_record(*_):
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
        self._error_threshold = err_threshold  # Set the error threshold which cause aborting to prevent deinal

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
                peer_name = 'None'  # Socket closed and could not derermine peername...
        return peer_name

    def _dummy_download_url(self, _):
        raise NotImplementedError

    def _download_url(self, url):
        if url in self.bad_urls:
            self._logger.log('DEBUG', 'Not downloading known bad URL:', url)
            return None

        if url in self.good_urls:  # This should not happen!
            self._logger.log('ERROR', 'Not downloading URL, because it is already downloaded in this session:', url)
            return None

        scheme, netloc, path, params, query, fragment = urlparse(url)
        # For safety urlencode the generated URL... (The URL might by modified in this step.)
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

        enc = resp.encoding  # Get or detect encoding to decode the bytes of the text to str
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
        # Everything is OK, write the two WARC records
        self.write_record(reqv_record, url)
        self.write_record(resp_record, url)

        return text

    def write_record(self, record, url):
        self.good_urls.add(url)
        self._writer.write_record(record)


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
        self._logger.log('INFO', 'Index succesuflly created.')

    def get_record(self, url):
        reqv_resp_pair = self._internal_url_index.get(url)
        if reqv_resp_pair is not None:
            self._stream.seek(reqv_resp_pair[0][0])
            reqv = next(iter(ArchiveIterator(self._stream, check_digests=self._check_digest)))
            self._stream.seek(reqv_resp_pair[1][0])
            resp = next(iter(ArchiveIterator(self._stream, check_digests=self._check_digest)))
            return reqv, resp
        else:
            raise KeyError('The request or response is missing from the archive for URL: {0}'.format(url))

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


def sample_warc_by_urls(source_warcfiles, new_urls, sampler_logger, target_warcfile=None, out_dir=None, offline=True,
                        just_cache=False):
    """ Create new warc file for the supplied list of URLs from an existing warc file """
    is_out_dir_mode = out_dir is not None
    if is_out_dir_mode:
        os.makedirs(out_dir, exist_ok=True)
        if len(os.listdir(out_dir)) != 0:
            print('Supplied output directory ({0}) is not empty!'.format(out_dir), file=sys.stderr)
            exit(1)

    w = WarcCachingDownloader(source_warcfiles, target_warcfile, sampler_logger, just_cache=just_cache,
                              download_params={'stay_offline': offline})
    for url in new_urls:
        url = url.strip()
        sampler_logger.log('INFO', 'Adding url', url)
        cont = w.download_url(url)
        if is_out_dir_mode and cont is not None:
            safe_url = ''.join(char if char.isalnum() else '_' for char in url).rstrip('_')[:200]
            i, fname = 0, os.path.join(out_dir, '{0}{1}.html'.format(safe_url, 0))
            while os.path.exists(fname):
                i += 1
                fname = os.path.join(out_dir, '{0}{1}.html'.format(safe_url, i))
            sampler_logger.log('INFO', 'Creating file', fname)
            with open(fname, 'w', encoding='UTF-8') as fh:
                fh.write(cont)


def validate_warc_file(source_warcfiles, validator_logger):
    reader = WarcCachingDownloader(source_warcfiles, None, validator_logger, True,
                                   download_params={'stay_offline': True, 'strict_mode': True, 'check_digest': True})
    validator_logger.log('INFO', 'OK!', len(reader.url_index), 'records read!')
    return reader.url_index


def online_test(url='https://index.hu/belfold/2018/08/27/fidesz_media_helyreigazitas/', filename='example.warc.gz',
                test_logger=None):
    w = WarcCachingDownloader(None, filename, test_logger)
    t = w.download_url(url)
    test_logger.log('INFO', t)
