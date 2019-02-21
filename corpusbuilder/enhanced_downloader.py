#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# Good for downloading archive index and also the actual articles in two separate row

import os
import sys
from io import BytesIO

from warcio.warcwriter import WARCWriter
from warcio.archiveiterator import ArchiveIterator
from warcio.statusandheaders import StatusAndHeaders

from requests import Session
from requests.utils import urlparse, quote, urlunparse
from requests.exceptions import RequestException
from requests.packages.urllib3.exceptions import ProtocolError

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
    def __init__(self, existing_warc_filename, new_warc_filename, logger_, program_name='corpusbuilder 1.0',
                 user_agent=None, overwrite_warc=True, err_threshold=10, known_bad_urls=None,
                 max_no_of_calls_in_period=2, limit_period=1, proxy_url=None, allow_cookies=False):
        if existing_warc_filename is not None:  # Setup the supplied existing warc archive file as cache
            self._cached_downloads = WarcReader(existing_warc_filename, logger_)
            self.url_index = self._cached_downloads.url_index
            info_record_data = self._cached_downloads.info_record_data
        else:
            self.url_index = {}
            info_record_data = None
        self._new_downloads = WarcDownloader(new_warc_filename, logger_, program_name, user_agent, overwrite_warc,
                                             err_threshold, info_record_data, known_bad_urls,
                                             max_no_of_calls_in_period, limit_period, proxy_url, allow_cookies)

    def download_url(self, url):
        if url in self.url_index:
            reqv, resp = self._cached_downloads.get_record(url)
            self._new_downloads.write_record(reqv)
            self._new_downloads.write_record(resp)
            return self._cached_downloads.download_url(url)
        else:
            return self._new_downloads.download_url(url)

    @property
    def bad_urls(self):
        return self._new_downloads.bad_urls

    @bad_urls.setter
    def bad_urls(self, value):
        self._new_downloads.bad_urls = value


class WarcDownloader:
    """
        Download URL with HTTP GET, save to a WARC file and return the decoded text
    """
    def __init__(self, filename, logger_, program_name='corpusbuilder 1.0', user_agent=None, overwrite_warc=True,
                 err_threshold=10, warcinfo_record_data=None, known_bad_urls=None, max_no_of_calls_in_period=2,
                 limit_period=1, proxy_url=None, allow_cookies=False):
        if known_bad_urls is not None:  # Setup the list of cached bad URLs to prevent trying to download them again
            with open(known_bad_urls, encoding='UTF-8') as fh:
                self.bad_urls = {line.strip() for line in fh}
        else:
            self.bad_urls = set()

        if not overwrite_warc:  # Find out next nonexisting warc filename
            num = 0
            while os.path.exists(filename):
                filename2, ext = os.path.splitext(filename)  # Should be filename.warc.gz
                if ext == '.gz' and filename2.endswith('.warc'):
                    filename2, ext2 = os.path.splitext(filename2)  # Should be filename.warc
                    ext = ext2 + ext  # Should be .warc.gz

                filename = '{0}-{1:05d}{2}'.format(filename2, num, ext)
                num += 1

        logger_.log('INFO', 'Creating archivefile: {0}'.format(filename))

        self._output_file = open(filename, 'wb')
        self._logger_ = logger_
        self._req_headers = {'Accept-Encoding': 'identity', 'User-agent': user_agent}

        self._session = Session()  # Setup session for speeding up downloads

        if proxy_url is not None:  # Set socks proxy if provided
            self._session.proxies['http'] = proxy_url
            self._session.proxies['https'] = proxy_url

        self._allow_cookies = allow_cookies

        # Setup rate limiting to prevent hammering the server
        self._requests_get = sleep_and_retry(limits(calls=max_no_of_calls_in_period,
                                                    period=limit_period)(self._http_get_w_cookie_handling))
        self._error_count = 0
        self._error_threshold = err_threshold  # Set the error threshold which cause aborting to prevent deinal

        self._writer = WARCWriter(self._output_file, gzip=True)
        if warcinfo_record_data is None:
            # INFO RECORD
            # Some custom information about the warc writer program and its settings
            info_headers = {'software': program_name, 'arguments': ' '.join(sys.argv[1:]),
                            'format': 'WARC File Format 1.0',
                            'conformsTo': 'http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf'}
            info_record = self._writer.create_warcinfo_record(filename, info_headers)
        else:  # Must recreate custom headers else they will not be copied
            custom_headers = ''.join('{0}: {1}\r\n'.format(k, v) for k, v in warcinfo_record_data[1].items()).\
                             encode('UTF-8')
            info_record = self._writer.create_warc_record('', 'warcinfo', warc_headers=warcinfo_record_data[0],
                                                          payload=BytesIO(custom_headers),
                                                          length=len(custom_headers))
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
        self._logger_.log('WARNING', '\t'.join((url, msg)))

        self._error_count += 1
        if self._error_count >= self._error_threshold:
            raise NameError('Too many error happened! Threshold exceeded! See log for details!')

    def download_url(self, url):
        scheme, netloc, path, params, query, fragment = urlparse(url)
        path = quote(path)  # For safety urlencode the generated URL...
        url = urlunparse((scheme, netloc, path, params, query, fragment))

        if url in self.bad_urls:
            self._logger_.log('INFO', 'Not downloading known bad URL: {0}'.format(url))
            return None

        try:  # The actual request
            resp = self._requests_get(url, headers=self._req_headers, stream=True)
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
        self._writer.write_record(reqv_record)

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

        enc = resp.encoding  # Get or detect encoding to decode the bytes of the text to str
        if enc is None:
            enc = detect(data)['encoding']
        try:
            text = data.decode(enc)  # Normal decode process
        except UnicodeDecodeError:
            self._logger_.log('WARNING', '\t'.join(('DECODE ERROR RETRYING IN \'IGNORE\' MODE:', url, enc)))
            text = data.decode(enc, 'ignore')
        data_stream = BytesIO(data)  # Need the original byte stream to write the payload to the warc file

        resp_http_headers = StatusAndHeaders(resp_status, resp_headers_list, protocol=proto)
        # Add extra headers like encoding because it is not stored any other way...
        resp_record = self._writer.create_warc_record(url, 'response', payload=data_stream,
                                                      http_headers=resp_http_headers,
                                                      warc_headers_dict={'WARC-IP-Address': peer_name,
                                                                         'WARC-X-Detected-Encoding': enc})
        self._writer.write_record(resp_record)

        return text

    def write_record(self, record):
        self._writer.write_record(record)


class WarcReader:
    def __init__(self, filename, logger_):
        self._stream = open(filename, 'rb')
        self.url_index = {}
        self._count = 0
        self._logger_ = logger_
        self.info_record_data = None
        try:
            self.create_index()
        except KeyError as e:
            self._logger_.log('ERROR', 'Ignoring exception: {0}'.format(e))

    def __del__(self):
        if hasattr(self, '_stream'):  # If the program opened a file, then it should gracefully close it on exit!
            self._stream.close()

    def create_index(self):
        self._logger_.log('INFO', 'Creating index...')
        archive_it = ArchiveIterator(self._stream)
        info_rec = next(archive_it)
        # First record should be an info record, then it should be followed by the reqvuest-response pairs
        assert info_rec.rec_type == 'warcinfo'
        custom_headers_raw = info_rec.content_stream().read()  # Parse custom headers
        info_rec_payload = dict(r.split(': ', maxsplit=1) for r in custom_headers_raw.decode('UTF-8')
                                .strip().split('\r\n'))
        self.info_record_data = (info_rec.rec_headers, info_rec_payload)  # Info headers in parsed form

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
                self.url_index[resp_url] = (reqv_data[1],  # Request-response pair
                                            (archive_it.get_record_offset(), archive_it.get_record_length()))
                self._count += 1
        if self._count != len(self.url_index):
            raise KeyError('Double URL detected in WARC file!')
        if self._count == 0:
            raise IndexError('No index created or no response records in the WARC file!')
        self._stream.seek(0)
        self._logger_.log('INFO', 'Index succesuflly created.')

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
            record = next(iter(ArchiveIterator(self._stream)))
            data = record.content_stream().read()
            assert len(data) > 0
            enc = record.rec_headers.get_header('WARC-X-Detected-Encoding', 'UTF-8')
            text = data.decode(enc, 'ignore')
        else:
            self._logger_.log('CRITICAL', '\t'.join((url, 'URL not found in WARC!')))

        return text


def main():  # Test
    filename = 'example.warc.gz'
    url = 'https://index.hu/belfold/2018/08/27/fidesz_media_helyreigazitas/'
    from corpusbuilder.utils import Logger
    w = WarcCachingDownloader(None, filename, Logger('WarcCachingDownloader-test.log'))
    t = w.download_url(url)
    print(t)


if __name__ == '__main__':
    main()
