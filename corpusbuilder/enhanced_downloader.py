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

from requests import Session
from requests.utils import urlparse, quote, urlunparse
from requests.exceptions import RequestException
from urllib3.exceptions import ProtocolError, InsecureRequestWarning
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
    def __init__(self, existing_warc_filename, new_warc_filename, _logger, just_cache=False, **download_params):
        self._logger = _logger
        if existing_warc_filename is not None:  # Setup the supplied existing warc archive file as cache
            self._cached_downloads = WarcReader(existing_warc_filename, _logger)
            self.url_index = self._cached_downloads.url_index
            info_record_data = self._cached_downloads.info_record_data
        else:
            self.url_index = {}
            info_record_data = None

        if just_cache:
            self._new_downloads = WarcDummyDownloader()
        else:
            self._new_downloads = WarcDownloader(new_warc_filename, _logger, info_record_data, **download_params)

    def download_url(self, url, ignore_cache=False):
        # 1) Check if the URL presents in the cache...
        if url in self.url_index:
            # 2) If the URL does not present in the newly created WARC file...
            if url not in self._new_downloads.good_urls:
                # 2a) ...copy it!
                reqv, resp = self._cached_downloads.get_record(url)
                self._new_downloads.write_record(reqv, url)
                self._new_downloads.write_record(resp, url)
            else:
                # 2b) ...or throw error and return None!
                self._logger.log('ERROR', 'Not processing URL because it is already present in the WARC archive:'
                                          ' {0}'.format(url))
                return None
            cache = self._cached_downloads.download_url(url)
        else:
            cache = None

        # 3) If we have the URL cached...
        if cache is not None:
            if not ignore_cache:
                return cache  # 3a) and we do not expliticly ignore cache, return the content!

            else:
                # 3b) Log that we ignored the cache and do noting!
                self._logger.log('INFO', 'Ignoring cache for URL: {0}'.format(url))

        # 4) Really download the URL! (url not in cache or cache is ignored)
        return self._new_downloads.download_url(url)  # Still check if the URL is already downloaded!

    @property
    def bad_urls(self):
        return self._new_downloads.bad_urls

    @bad_urls.setter
    def bad_urls(self, value):
        self._new_downloads.bad_urls = value

    @property
    def good_urls(self):
        return self._new_downloads.good_urls

    @good_urls.setter
    def good_urls(self, value):
        self._new_downloads.good_urls = value

    @property
    def cached_urls(self):
        return self._cached_downloads.url_index


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
    def __init__(self, filename, _logger, warcinfo_record_data=None, program_name='corpusbuilder 1.0', user_agent=None,
                 overwrite_warc=True, err_threshold=10, known_bad_urls=None, max_no_of_calls_in_period=2,
                 limit_period=1, proxy_url=None, allow_cookies=False, verify=True):
        if known_bad_urls is not None:  # Setup the list of cached bad URLs to prevent trying to download them again
            with open(known_bad_urls, encoding='UTF-8') as fh:
                self.bad_urls = {line.strip() for line in fh}
        else:
            self.bad_urls = set()

        self.good_urls = set()

        if not overwrite_warc:  # Find out next nonexisting warc filename
            num = 0
            while os.path.exists(filename):
                filename2, ext = os.path.splitext(filename)  # Should be filename.warc.gz
                if ext == '.gz' and filename2.endswith('.warc'):
                    filename2, ext2 = os.path.splitext(filename2)  # Should be filename.warc
                    ext = ext2 + ext  # Should be .warc.gz

                filename = '{0}-{1:05d}{2}'.format(filename2, num, ext)
                num += 1

        _logger.log('INFO', 'Creating archivefile: {0}'.format(filename))

        self._output_file = open(filename, 'wb')
        self._logger = _logger
        self._req_headers = {'Accept-Encoding': 'identity', 'User-agent': user_agent}

        self._session = Session()  # Setup session for speeding up downloads

        if proxy_url is not None:  # Set socks proxy if provided
            self._session.proxies['http'] = proxy_url
            self._session.proxies['https'] = proxy_url

        self._allow_cookies = allow_cookies
        self._verify = verify
        if not verify:
            disable_warnings(InsecureRequestWarning)

        # Setup rate limiting to prevent hammering the server
        self._requests_get = sleep_and_retry(limits(calls=max_no_of_calls_in_period,
                                                    period=limit_period)(self._http_get_w_cookie_handling))
        self._error_count = 0
        self._error_threshold = err_threshold  # Set the error threshold which cause aborting to prevent deinal

        self._writer = WARCWriter(self._output_file, gzip=True, warc_version='WARC/1.1')
        if warcinfo_record_data is None:  # Or use the parsed else custom headers will not be copied
            # INFO RECORD
            # Some custom information about the warc writer program and its settings
            warcinfo_record_data = {'software': program_name, 'arguments': ' '.join(sys.argv[1:]),
                                    'format': 'WARC File Format 1.1',
                                    'conformsTo': 'http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1-1_latestdraft.pdf'}
        info_record = self._writer.create_warcinfo_record(filename, warcinfo_record_data)
        self._writer.write_record(info_record)

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
        self._logger.log('WARNING', '\t'.join((url, msg)))

        self._error_count += 1
        if self._error_count >= self._error_threshold:
            raise NameError('Too many error happened! Threshold exceeded! See log for details!')

    def download_url(self, url):
        if url in self.bad_urls:
            self._logger.log('DEBUG', 'Not downloading known bad URL: {0}'.format(url))
            return None

        if url in self.good_urls:  # This should not happen!
            self._logger.log('ERROR', 'Not downloading URL because it is already downloaded in this session:'
                                      ' {0}'.format(url))
            return None

        scheme, netloc, path, params, query, fragment = urlparse(url)
        path = quote(path)  # For safety urlencode the generated URL...
        url = urlunparse((scheme, netloc, path, params, query, fragment))

        try:  # The actual request
            resp = self._requests_get(url, headers=self._req_headers, stream=True, verify=self._verify)
        except RequestException as err:
            self._handle_request_exception(url, 'RequestException happened during downloading: {0} \n\n'
                                                ' The program ignores it and jumps to the next one.'.format(err))
            return None

        if resp.status_code != 200:  # Not HTTP 200 OK
            self._handle_request_exception(url, 'Downloading failed with status code: {0} {1}'.format(resp.status_code,
                                                                                                      resp.reason))
            return None

        # REQUEST
        reqv_headers = resp.request.headers
        reqv_headers['Host'] = netloc

        proto = 'HTTP/{0}'.format(respv_str[resp.raw.version])  # Friendly protocol name
        reqv_http_headers = StatusAndHeaders('GET {0} {1}'.format(urlunparse(('', '', path, params, query, fragment)),
                                                                  proto), reqv_headers.items(), is_http_request=True)
        reqv_record = self._writer.create_warc_record(url, 'request', http_headers=reqv_http_headers)

        # RESPONSE
        resp_status = '{0} {1}'.format(resp.status_code, resp.reason)
        resp_headers_list = resp.raw.headers.items()  # get raw headers from urllib3
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

        enc = resp.encoding  # Get or detect encoding to decode the bytes of the text to str
        if enc is None:
            enc = detect(data)['encoding']
        try:
            text = data.decode(enc)  # Normal decode process
        except UnicodeDecodeError:
            self._logger.log('WARNING', '\t'.join(('DECODE ERROR RETRYING IN \'IGNORE\' MODE:', url, enc)))
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
    def __init__(self, filename, _logger, strict_mode=False):  # TODO: Wire-out strict_mode!
        self._stream = open(filename, 'rb')
        self.url_index = {}
        self._logger = _logger
        self.info_record_data = None
        self._strict_mode = strict_mode
        try:
            self.create_index()
        except KeyError as e:
            if self._strict_mode:
                raise e
            self._logger.log('ERROR', 'Ignoring exception: {0}'.format(e))

    def __del__(self):
        if hasattr(self, '_stream'):  # If the program opened a file, then it should gracefully close it on exit!
            self._stream.close()

    def create_index(self):
        self._logger.log('INFO', 'Creating index...')
        archive_it = ArchiveIterator(self._stream)
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
        except (UnicodeDecodeError, ValueError) as e:
            if self._strict_mode:
                raise e
            self._logger.log('WARNING', 'WARCINFO record in {0} is corrupt! Continuing with a fresh one!'.
                             format(self._stream.name))
            self.info_record_data = None

        count = 0
        double_urls = Counter()
        reqv_data = (None, (None, None))  # To be able to handle the request-response pairs together
        for i, record in enumerate(archive_it):
            if record.rec_type == 'request':
                assert i % 2 == 0
                reqv_data = (record.rec_headers.get_header('WARC-Target-URI'),
                             (archive_it.get_record_offset(), archive_it.get_record_length()))
            if record.rec_type == 'response':
                assert i % 2 == 1
                resp_url = record.rec_headers.get_header('WARC-Target-URI')
                assert resp_url == reqv_data[0]
                double_urls[resp_url] += 1
                self.url_index[resp_url] = (reqv_data[1],  # Request-response pair
                                            (archive_it.get_record_offset(), archive_it.get_record_length()))
                count += 1
        if count != len(self.url_index):
            double_urls_str = '\n'.join('{0}\t{1}'.format(url, freq) for url, freq in double_urls.most_common()
                                        if freq > 1)
            raise KeyError('The following double URLs detected in the WARC file:{0}'.format(double_urls_str))
        if count == 0:
            raise IndexError('No index created or no response records in the WARC file!')
        self._stream.seek(0)
        self._logger.log('INFO', 'Index succesuflly created.')

    def get_record(self, url):
        reqv_resp_pair = self.url_index.get(url)
        if reqv_resp_pair is not None:
            self._stream.seek(reqv_resp_pair[0][0])
            reqv = next(iter(ArchiveIterator(self._stream)))
            self._stream.seek(reqv_resp_pair[1][0])
            resp = next(iter(ArchiveIterator(self._stream)))
            return reqv, resp
        else:
            raise KeyError('The request or response is missing from the archive for URL: {0}'.format(url))

    def download_url(self, url):
        text = None
        d = self.url_index.get(url)
        if d is not None:
            offset = d[1][0]  # Only need the offset of the response part
            self._stream.seek(offset)  # Can not be cached as we also want to write it out to the new archive!
            record = next(iter(ArchiveIterator(self._stream, check_digests='raise')))
            data = record.content_stream().read()
            assert len(data) > 0
            enc = record.rec_headers.get_header('WARC-X-Detected-Encoding', 'UTF-8')
            text = data.decode(enc, 'ignore')
        else:
            self._logger.log('CRITICAL', '\t'.join((url, 'URL not found in WARC!')))

        return text


def main():  # Test
    filename = 'example.warc.gz'
    url = 'https://index.hu/belfold/2018/08/27/fidesz_media_helyreigazitas/'
    from corpusbuilder.utils import Logger
    w = WarcCachingDownloader(None, filename, Logger('WarcCachingDownloader-test.log'))
    t = w.download_url(url)
    print(t)


def validate_warc_file(filename):
    import sys
    from os.path import dirname, join as os_path_join, abspath

    # To be able to run it standalone from anywhere!
    project_dir = abspath(os_path_join(dirname(__file__), '..'))
    sys.path.append(project_dir)

    from corpusbuilder.utils import Logger
    reader = WarcReader(filename, Logger(), strict_mode=True)
    print('OK! {0} records read!'.format(len(reader.url_index)))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        main()
    else:
        validate_warc_file(sys.argv[1])
