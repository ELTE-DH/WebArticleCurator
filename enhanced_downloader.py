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

from chardet import detect

respv_str = {10: '1.0', 11: '1.1'}


class WarcDownloader:
    """
        Download URL with HTTP GET, save to a WARC file and return the decoded text
    """
    def __init__(self, filename, logger, program_name='corpusbuilder 1.0', user_agent=None, overwrite_warc=True,
                 err_threshold=10):
        if not overwrite_warc:
            num = 0
            while os.path.exists(filename):
                filename, ext = os.path.splitext(filename)
                if ext == 'gz' and filename.endswith('.warc'):
                    filename, ext2 = os.path.splitext(filename)
                    ext = ext2 + ext

                filename = '-{0:05d}{1}'.format(num, ext)
                num += 1

        logger.log('', 'Creating archivefile: {0}'.format(filename))

        self._output_file = open(filename, 'wb')
        self._logger = logger
        self._req_headers = {'Accept-Encoding': 'identity', 'User-agent': user_agent}
        self._requests_get = Session().get
        self._error_count = 0
        self._error_threshold = err_threshold

        self._writer = WARCWriter(self._output_file, gzip=True)
        # INFO RECORD
        # Some custom information about the warc writer program and its settings
        info_headers = {'software': program_name, 'arguments': ' '.join(sys.argv[1:]), 'format': 'WARC File Format 1.0',
                        'conformsTo': 'http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf'}
        info_record = self._writer.create_warcinfo_record(filename, info_headers)

        self._writer.write_record(info_record)

    def __del__(self):
        self._output_file.close()

    def download_url(self, url):
        scheme, netloc, path, params, query, fragment = urlparse(url)
        path = quote(path)
        url = urlunparse((scheme, netloc, path, params, query, fragment))

        # The actual request
        try:
            resp = self._requests_get(url, headers=self._req_headers, stream=True)
        except RequestException as err:
            self._logger.log(url, 'RequestException happened during downloading: {0} \n\n'
                                  ' The program ignores it and jumps to the next one.'.format(err))
            self._error_count += 1
            if self._error_count >= self._error_threshold:
                raise NameError('Too many error happened! Threshold exceeded! See log for details!')
            return None

        if resp.status_code != 200:
            self._logger.log(url, 'Downloading failed with status code: {0} {1}'.format(resp.status_code, resp.reason))
            self._error_count += 1
            if self._error_count >= self._error_threshold:
                raise NameError('Too many error happened! Threshold exceeded! See log for details!')
            return None

        # REQUEST
        reqv_headers = resp.request.headers
        reqv_headers['Host'] = netloc

        proto = 'HTTP/{0}'.format(respv_str[resp.raw.version])
        reqv_http_headers = StatusAndHeaders('GET {0} {1}'.format(path, proto), reqv_headers.items(),
                                             is_http_request=True)
        reqv_record = self._writer.create_warc_record(url, 'request', http_headers=reqv_http_headers)
        self._writer.write_record(reqv_record)

        # RESPONSE
        resp_status = '{0} {1}'.format(resp.status_code, resp.reason)
        resp_headers_list = resp.raw.headers.items()  # get raw headers from urllib3
        peer_name = resp.raw._fp.fp.raw._sock.getpeername()[0]  # Must get peer_name before the content is read

        data = resp.raw.read()  # To be able to return decoded and also write warc
        enc = resp.encoding
        if enc is None:
            enc = detect(data)['encoding']
        text = data.decode(enc, 'ignore')
        data_stream = BytesIO(data)

        resp_http_headers = StatusAndHeaders(resp_status, resp_headers_list, protocol=proto)

        # TODO: This is the best solution? http_headers.get_header('content-encoding')
        resp_record = self._writer.create_warc_record(url, 'response', payload=data_stream,
                                                      http_headers=resp_http_headers,
                                                      warc_headers_dict={'WARC-IP-Address': peer_name,
                                                                         'WARC-X-Detected-Encoding': enc})
        self._writer.write_record(resp_record)

        return text


class WarcReader:
    def __init__(self, filename, logger, *_, **__):
        self._stream = open(filename, 'rb')  # TODO: error handling
        self._url_index = {}
        self._count = 0
        self._logger = logger
        self.create_index()

    def __del__(self):
        self._stream.close()

    def create_index(self):
        archive_it = ArchiveIterator(self._stream)
        for record in archive_it:
            if record.rec_type == 'response':
                self._url_index[record.rec_headers.get_header('WARC-Target-URI')] = (archive_it.get_record_offset(),
                                                                                     archive_it.get_record_length())
                self._count += 1
        if self._count != len(self._url_index):
            raise KeyError('Double URL detected in WARC file!')
        if self._count == 0:
            raise IndexError('No index created or no response records in the WARC file!')
        self._stream.seek(0)

    def download_url(self, url):
        text = None
        d = self._url_index.get(url)
        if d is not None:
            offset, length = d
            self._stream.seek(offset)
            record = next(iter(ArchiveIterator(self._stream)))
            data = record.content_stream().read()
            enc = record.rec_headers.get_header('WARC-X-Detected-Encoding', 'UTF-8')
            text = data.decode(enc, 'ignore')
        else:
            self._logger.log(url, 'URL not found in WARC!')

        return text


def main():
    filename = 'example.warc.gz'
    url = 'https://index.hu/belfold/2018/08/27/fidesz_media_helyreigazitas/'
    from logger import Logger
    w = WarcDownloader(filename, Logger('WarcDownloader-test.log'))
    t = w.download_url(url)
    print(t)
    r = WarcReader(filename, Logger('WarcReader-test.log'))
    t2 = r.download_url(url)
    print(t2)
    print(t == t2)


if __name__ == '__main__':
    main()
