#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import timedelta

from corpusbuilder.enhanced_downloader import WarcCachingDownloader
from corpusbuilder.extractor import extract_article_urls_from_page
from corpusbuilder.logger import Logger


class NewsArchiveCrawler:
    """
        1) Generate URLs of lists of articles
        2) Extract URLs of articles from these lists
    """
    def __init__(self, settings, existing_archive_filename, new_archive_filename):
        self._settings = settings
        self._logger_ = Logger(self._settings['log_file_archive'])

        # For external use
        self.good_urls = set()
        self.problematic_urls = set()

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(existing_archive_filename, new_archive_filename, self._logger_)

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
            article_list_urls = [self._gen_article_list_url_from_date(date_from + timedelta(days=curr_day), url_format)
                                 for curr_day in range(self._settings['INTERVAL'].days + 1)]

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
        # Download the first page
        article_urls, is_last_page = self._gen_corpus_from_id_url_list(article_list_url_base)
        yield from article_urls
        page_num = self._settings['min_pagenum']
        max_pagenum = self._settings['max_pagenum']
        # TODO: Better way: Search for the "next page" link, if there is no such link, than it is the last page!
        # if the last article list page does not contain any links to articles, go to next date
        while not is_last_page and (max_pagenum < 0 or page_num < max_pagenum):
            page_num += 1
            article_list_url = '{0}{1}'.format(article_list_url_base, page_num)
            article_urls, is_last_page = self._gen_corpus_from_id_url_list(article_list_url)
            yield from article_urls

    def _gen_corpus_from_id_url_list(self, article_list_url):
            article_list_only_urls = []
            article_list_raw_html = self._downloader.download_url(article_list_url)
            if article_list_raw_html is not None:
                self.good_urls.add(article_list_url)
                article_list_only_urls = extract_article_urls_from_page(article_list_raw_html, self._settings)
            else:
                self.problematic_urls.add(article_list_url)
            # None should only occur when the pattern is not OK  # is last page
            return article_list_only_urls, article_list_raw_html is None or len(article_list_only_urls) == 0
