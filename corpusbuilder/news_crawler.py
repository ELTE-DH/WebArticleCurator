#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import timedelta

from articleDateExtractor import extractArticlePublishedDate

from corpusbuilder.corpus_converter import CorpusConverter, CorpusConverterNewspaper, extract_article_urls_from_page,\
    extract_next_page_url
from corpusbuilder.enhanced_downloader import WarcCachingDownloader
from corpusbuilder.utils import Logger

corpus_converter_class = {'rule-based': CorpusConverter, 'newspaper': CorpusConverterNewspaper}


class NewsArchiveCrawler:
    """
        1) Generate URLs of lists of articles
        2) Extract URLs of articles from these lists
    """
    def __init__(self, settings, existing_archive_filename, new_archive_filename, program_name='corpusbuilder 1.0',
                 user_agent=None, overwrite_warc=True, err_threshold=10, known_bad_urls=None,
                 max_no_of_calls_in_period=2, limit_period=1, proxy_url=None, allow_cookies=False):
        self._settings = settings
        self._logger_ = Logger(self._settings['log_file_archive'])

        # For external use
        self.good_urls = set()
        self.problematic_urls = set()

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(existing_archive_filename, new_archive_filename, self._logger_,
                                                 program_name, user_agent, overwrite_warc, err_threshold,
                                                 known_bad_urls, max_no_of_calls_in_period, limit_period, proxy_url,
                                                 allow_cookies)

    def __del__(self):
        for url in self.good_urls:
            self._logger_.log(url, 'GOOD ARCHIVE URL')
        for url in self.problematic_urls:
            self._logger_.log(url, 'PROBLEMATIC ARCHIVE URL')

    def url_iterator(self):
        # if URLs of current website's archive pages are generated based on an ID,
        # which is a positive integer growing one by one
        article_list_urls = []

        if self._settings['ARTICLE_LIST_URLS_BY_DATE']:  # e.g. index.hu, origo.hu
            date_from = self._settings['DATE_FROM']
            url_format = self._settings['article_list_url_format']
            article_list_urls = list(sorted(set(self._gen_article_list_url_from_date(date_from +
                                                                                     timedelta(days=curr_day),
                                                                                     url_format)
                                                for curr_day in range(self._settings['INTERVAL'].days + 1)),
                                            reverse=self._settings['GO_REVERSE_IN_ARCHIVE']))

        if self._settings['ARTICLE_LIST_URLS_BY_ID']:
            # not URL_BY_DATE and URLS_BY_ID
            if len(article_list_urls) == 0:  # e.g. 444.hu
                article_list_urls.append(self._settings['article_list_url_format'])

        if len(article_list_urls) == 0:
            print('There is no existing case where settings[\'ARTICLE_LIST_URLS_BY_DATE\'] and'
                  ' settings[\'ARTICLE_LIST_URLS_BY_ID\'] are both False')  # try/excepttel csinálni?
            return

        for article_list_url in article_list_urls:
            yield from self._gen_corpus_from_id_url_list_w_subpages(article_list_url)

    @staticmethod
    def _gen_article_list_url_from_date(curr_date, url_format):
        """
            generates and returns the URLs of a page the contains URLs of articles published that day
        """
        art_list_url = url_format.replace('#year', '{0:04d}'.format(curr_date.year)).\
            replace('#month', '{0:02d}'.format(curr_date.month)).\
            replace('#day', '{0:02d}'.format(curr_date.day))
        return art_list_url

    def _gen_corpus_from_id_url_list_w_subpages(self, article_list_url_base):
        """
            generates corpus from a URL regarding to a sub-pages that contains article URLs
        """
        page_num = self._settings['min_pagenum']
        max_pagenum = self._settings['max_pagenum']
        # Download the first page
        article_urls, article_list_next_page_url = self._gen_corpus_from_id_url_list(article_list_url_base,
                                                                                     article_list_url_base, page_num,
                                                                                     max_pagenum)
        yield from article_urls

        while article_list_next_page_url is not None:
            page_num += 1
            article_urls, article_list_next_page_url = self._gen_corpus_from_id_url_list(article_list_next_page_url,
                                                                                         article_list_url_base,
                                                                                         page_num, max_pagenum)
            yield from article_urls

    def _gen_corpus_from_id_url_list(self, article_list_url, article_list_url_base, page_num, max_pagenum):
            article_list_only_urls = []
            article_list_raw_html = self._downloader.download_url(article_list_url)
            next_page_url = None
            if article_list_raw_html is not None:
                self.good_urls.add(article_list_url)
                article_list_only_urls = extract_article_urls_from_page(article_list_raw_html, self._settings)
                if self._settings['NEXT_URL_BY_REGEX']:
                    next_page_url = extract_next_page_url(article_list_raw_html, self._settings)
                elif len(article_list_only_urls) > 0 and (max_pagenum < 0 or page_num < max_pagenum):
                    # ...must generate URL
                    next_page_url = '{0}{1}'.format(article_list_url_base, page_num)
            else:
                self.problematic_urls.add(article_list_url)
            return article_list_only_urls, next_page_url


class NewsArticleCrawler:
    """
        1) Get the list of articles (eg. NewsArchiveCrawler)
        2) Download article pages
        3) Extract the text of articles from raw HTML
        4) save them in corpus format
    """
    def __init__(self, settings, articles_existing_warc_filename, articles_new_warc_filename,
                 archive_existing_warc_filename, archive_new_warc_filename, program_name='corpusbuilder 1.0',
                 user_agent=None, overwrite_warc=True, err_threshold=10, corpus_converter='rule-based',
                 known_bad_urls=None, max_no_of_calls_in_period=2, limit_period=1, proxy_url=None, allow_cookies=False):
        self._settings = settings
        self._logger_ = Logger(self._settings['log_file_articles'])

        self._file_out = open(self._settings['output_file'], 'a+', encoding='UTF-8')

        # Create new corpus converter class from the available methods...
        converter = corpus_converter_class[corpus_converter]
        self._converter = converter(self._settings,  self._file_out, self._logger_)

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(articles_existing_warc_filename, articles_new_warc_filename,
                                                 self._logger_,  program_name, user_agent, overwrite_warc,
                                                 err_threshold, known_bad_urls,
                                                 max_no_of_calls_in_period, limit_period, proxy_url, allow_cookies)

        self._archive_downloader = NewsArchiveCrawler(self._settings, archive_existing_warc_filename,
                                                      archive_new_warc_filename, program_name, user_agent,
                                                      overwrite_warc, err_threshold, known_bad_urls,
                                                      max_no_of_calls_in_period, limit_period, proxy_url, allow_cookies)

        self.good_article_urls = set()
        self.problematic_article_urls = set()
        self._new_urls = set()

    def __del__(self):
        self._file_out.close()
        for url in self._new_urls:
            self._logger_.log(url, 'NEW URL')

    def process_urls(self, it):
        create_corpus = self._settings['CREATE_CORPUS']
        for url in it:
            # Check if it is a duplicate
            if url in self.good_article_urls or \
               url in self.problematic_article_urls:
                self._logger_.log(url, 'Not downloading article, because it is already downloaded!')
                continue

            # "Download" article
            article_raw_html = self._downloader.download_url(url)
            if article_raw_html is None:
                self._logger_.log(url, 'Article were not processed because download failed!')
                self.problematic_article_urls.add(url)
                continue

            # Note downloaded url
            self.good_article_urls.add(url)

            # Filter: time filtering when archive page URLs are not generated by date
            is_ok = self._filter_urls_by_date(url, article_raw_html)

            # Extract text to corpus
            if is_ok and create_corpus:
                self._converter.article_to_corpus(url, article_raw_html)

            # Extract links to other articles...
            extracted_article_urls = extract_article_urls_from_page(article_raw_html, self._settings)

            # Check for already extracted urls!
            for extracted_url in extracted_article_urls:
                if extracted_url not in self.good_article_urls and \
                   extracted_url not in self.problematic_article_urls and \
                   extracted_url not in self._archive_downloader.good_urls and \
                   extracted_url not in self._archive_downloader.problematic_urls:
                    self._new_urls.add(extracted_url)

    def _filter_urls_by_date(self, url, raw_html):
        ret = True
        if self._settings['ARTICLE_LIST_URLS_BY_ID'] and not self._settings['ARTICLE_LIST_URLS_BY_DATE'] and \
                self._settings['DATE_INTERVAL_USED']:
            article_date = extractArticlePublishedDate(url, html=raw_html)
            date_before_interval = self._settings['DATE_FROM'] > article_date.date()
            date_after_interval = article_date.date() > self._settings['DATE_UNTIL']

            if date_before_interval or date_after_interval:
                ret = False  # Not OK
                self._logger_.log(url, 'Date ({0}) not in the specified interval: {1}-{2} didn\'t use it in the corpus'.
                                  format(article_date, self._settings['DATE_FROM'], self._settings['DATE_UNTIL']))
        return ret

    def download_and_extract_all_articles(self):
        self.process_urls(self._archive_downloader.url_iterator())
        self.download_gathered_new_urls()

    def download_gathered_new_urls(self):
        # Recheck new urls
        self._new_urls = {url for url in self._new_urls
                          if url not in self.good_article_urls and
                          url not in self.problematic_article_urls and
                          url not in self._archive_downloader.good_urls and
                          url not in self._archive_downloader.problematic_urls}
        while len(self._new_urls) > 0:  # Article URL-s not in the archive... Shouldn't be any!
            for url in self._new_urls:
                self._logger_.log(url, 'TRUE NEW URL')
            new_urls = self._new_urls
            self._new_urls = set()
            self.process_urls(new_urls)
