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


class WarcCachingDownloader:
    def __init__(self, existing_warc_filename, new_warc_filename, logger_, program_name='corpusbuilder 1.0',
                 user_agent=None, overwrite_warc=True, err_threshold=10):
        if existing_warc_filename is not None:
            self._cached_downloads = WarcReader(existing_warc_filename, logger_)
            self._url_index = self._cached_downloads.url_index
            warcinfo = self._cached_downloads.info_record
        else:
            self._url_index = {}
            warcinfo = None
        self._new_donwloads = WarcDownloader(new_warc_filename, logger_, program_name, user_agent, overwrite_warc,
                                             err_threshold, warcinfo)

    def download_url(self, url):
        if url in self._url_index:
            reqv, resp = self._cached_downloads.get_record(url)
            self._new_donwloads.write_record(reqv)
            self._new_donwloads.write_record(resp)
            return self._cached_downloads.download_url(url)
        else:
            return self._new_donwloads.download_url(url)


class WarcDownloader:
    """
        Download URL with HTTP GET, save to a WARC file and return the decoded text
    """
    def __init__(self, filename, logger_, program_name='corpusbuilder 1.0', user_agent=None, overwrite_warc=True,
                 err_threshold=10, warcinfo=None):
        if not overwrite_warc:
            num = 0
            while os.path.exists(filename):
                filename, ext = os.path.splitext(filename)
                if ext == 'gz' and filename.endswith('.warc'):
                    filename, ext2 = os.path.splitext(filename)
                    ext = ext2 + ext

                filename = '-{0:05d}{1}'.format(num, ext)
                num += 1

        logger_.log('', 'Creating archivefile: {0}'.format(filename))

        self._output_file = open(filename, 'wb')
        self._logger_ = logger_
        self._req_headers = {'Accept-Encoding': 'identity', 'User-agent': user_agent}
        self._requests_get = Session().get
        self._error_count = 0
        self._error_threshold = err_threshold

        self._writer = WARCWriter(self._output_file, gzip=True)
        if warcinfo is None:
            # INFO RECORD
            # Some custom information about the warc writer program and its settings
            info_headers = {'software': program_name, 'arguments': ' '.join(sys.argv[1:]),
                            'format': 'WARC File Format 1.0',
                            'conformsTo': 'http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf'}
            info_record = self._writer.create_warcinfo_record(filename, info_headers)
        else:
            info_record = warcinfo
        self._writer.write_record(info_record)

    def __del__(self):
        if hasattr(self, '_output_file'):
            self._output_file.close()

    def download_url(self, url):
        scheme, netloc, path, params, query, fragment = urlparse(url)
        path = quote(path)
        url = urlunparse((scheme, netloc, path, params, query, fragment))

        # The actual request
        try:
            resp = self._requests_get(url, headers=self._req_headers, stream=True)
        except RequestException as err:
            self._logger_.log(url, 'RequestException happened during downloading: {0} \n\n'
                                   ' The program ignores it and jumps to the next one.'.format(err))
            self._error_count += 1
            if self._error_count >= self._error_threshold:
                raise NameError('Too many error happened! Threshold exceeded! See log for details!')
            return None

        if resp.status_code != 200:
            self._logger_.log(url, 'Downloading failed with status code: {0} {1}'.format(resp.status_code, resp.reason))
            self._error_count += 1
            if self._error_count >= self._error_threshold:
                raise NameError('Too many error happened! Threshold exceeded! See log for details!')
            return None

        # REQUEST
        reqv_headers = resp.request.headers
        reqv_headers['Host'] = netloc

        proto = 'HTTP/{0}'.format(respv_str[resp.raw.version])
        reqv_http_headers = StatusAndHeaders('GET {0} {1}'.format(urlunparse(('', '', path, params, query, fragment)),
                                                                  proto), reqv_headers.items(), is_http_request=True)
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
        self._url_index_req = {}
        self._count = 0
        self._logger_ = logger_
        self.info_record = None
        self.create_index()

    def __del__(self):
        if hasattr(self, '_stream'):
            self._stream.close()

    def create_index(self):
        self._logger_.log('', 'Creating index...')
        archive_it = ArchiveIterator(self._stream)
        info_rec = next(archive_it)
        assert info_rec.rec_type == 'warcinfo'
        self.info_record = info_rec
        for record in archive_it:
            if record.rec_type == 'request':
                self._url_index_req[record.rec_headers.get_header('WARC-Target-URI')] = (archive_it.get_record_offset(),
                                                                                         archive_it.get_record_length())
            if record.rec_type == 'response':
                self.url_index[record.rec_headers.get_header('WARC-Target-URI')] = (archive_it.get_record_offset(),
                                                                                    archive_it.get_record_length())
                self._count += 1
        if self._count != len(self.url_index):
            raise KeyError('Double URL detected in WARC file!')
        if self._count == 0:
            raise IndexError('No index created or no response records in the WARC file!')
        self._stream.seek(0)
        self._logger_.log('', 'Index succesuflly created.')

    def get_record(self, url):
        reqv_offset = self._url_index_req.get(url)
        resp_offset = self.url_index.get(url)
        if reqv_offset is not None and resp_offset is not None:
            self._stream.seek(reqv_offset[0])
            reqv = next(iter(ArchiveIterator(self._stream)))
            self._stream.seek(resp_offset[0])
            resp = next(iter(ArchiveIterator(self._stream)))
            return reqv, resp
        else:
            raise KeyError('The request or response is missing from the archive for URL: {0}'.format(url))

    def download_url(self, url):
        text = None
        d = self.url_index.get(url)
        if d is not None:
            offset, length = d
            self._stream.seek(offset)  # Can not be cached as we also want to write it out to the new archive!
            record = next(iter(ArchiveIterator(self._stream)))
            data = record.content_stream().read()
            assert len(data) > 0
            enc = record.rec_headers.get_header('WARC-X-Detected-Encoding', 'UTF-8')
            text = data.decode(enc, 'ignore')
        else:
            self._logger_.log(url, 'URL not found in WARC!')

        return text


def main():
    filename = 'example.warc.gz'
    url = 'https://index.hu/belfold/2018/08/27/fidesz_media_helyreigazitas/'
    from corpusbuilder.utils import Logger
    w = WarcCachingDownloader(None, filename, Logger('WarcCachingDownloader-test.log'))
    t = w.download_url(url)
    print(t)


if __name__ == '__main__':
    main()
