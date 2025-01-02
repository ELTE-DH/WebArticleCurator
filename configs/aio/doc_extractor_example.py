from glob import glob

from mplogger import Logger
from webarticlecurator import WarcCachingDownloader

logger = Logger('extractor.log', logfile_level='DEBUG', console_level='DEBUG')
for file in glob('new/*.warc.gz'):
    wac = WarcCachingDownloader(file, None, logger, just_cache=True, download_params={'allow_empty_warc': True})
    for url in wac.url_index:
        doc_content = wac.download_url(url, decode=False)  # TODO Set true for only HTML, XML and such files
        # TODO save or handle the document as needed
