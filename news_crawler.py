#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# import external libs
import sys
from datetime import timedelta

# import own modules
from logger import Logger
from corpus_converter import CorpusConverter
from input_constants_wrapper import wrap_input_consants
from enhanced_downloader import WarcDownloader, WarcReader
from extractor import extract_article_urls_from_page, articles_to_corpus


class NewsCrawler:
    def __init__(self):
        """
        get the command line argument
        it is the configuration file's name
        """
        try:
            current_task_config_filename = sys.argv[1]
        except IndexError:
            raise IndexError('Not enough or too many input arguments!\n'
                             'The program should be called like:\n'
                             'python web_crawler.py current_task_config.json')

        # read input data from the given files, initialize variables
        self._settings = wrap_input_consants(current_task_config_filename)
        self._file_out = open(self._settings['output_file'], 'a+', encoding=self._settings['encoding'])
        self._logger_ = Logger(self._settings['log_file'])
        self._converter = CorpusConverter(self._settings['site_schemas'], self._settings['tags'])
        self._max_pagenum = -1
        self._good_urls = set()
        self._problematic_urls = set()
        self._urls_to_download = set()
        filename = 'example.warc.gz'
        download == True
        if download == True:
            self._downloader = WarcDownloader('example.warc.gz', logger_)
        else:
            self._downloader = WarcReader('example.warc.gz', logger_)

    def __del__(self):
        self._file_out.close()

    def url_iterator(self):

        # generate URLs of lists of articles
        # extract URLs of articles from these lists
        # download article pages
        # convert these articles from raw HTML to corpus format

        # if URLs of current website's archive pages are generated based on an ID,
        # which is a positive integer growing one by one
        article_list_urls = []

        if self._settings['ARTICLE_LIST_URLS_BY_DATE']:  # e.g. index.hu, origo.hu
            self._max_pagenum = 0  # No pages (may be overwritten e.g. origo.hu)
            date_from = self._settings['DATE_FROM']
            url_format = self._settings['article_list_url_format']
            article_list_urls = [self._gen_article_list_url_from_date(date_from, timedelta(days=curr_day), url_format)
                                 for curr_day in range(self._settings['INTERVAL'].days + 1)]

        if self._settings['ARTICLE_LIST_URLS_BY_ID']:
            self._max_pagenum = -1  # Infinty
            # not URL_BY_DATE and URLS_BY_ID
            if len(article_list_urls) == 0:  # e.g. 444.hu
                article_list_urls.append(self._settings['article_list_url_format'])

        if len(article_list_urls) == 0:
            print('There is no existing case where settings[\'ARTICLE_LIST_URLS_BY_DATE\'] and'
                  ' settings[\'ARTICLE_LIST_URLS_BY_ID\'] are both False')  # try/excepttel csinálni?
            return

        for article_list_url in article_list_urls:
            self._gen_corpus_from_id_url_list_w_subpages(article_list_url)  # TODO: yield from...

    @staticmethod
    def _gen_article_list_url_from_date(date_from, delta_day, url_format):
        """
            generates and returns the URLs of a page the contains URLs of articles published that day
        """
        curr_year, curr_month, curr_day = '{0}{1}'.format(date_from,  delta_day).split('-', maxsplit=2)
        art_list_url = url_format.replace('#year', curr_year).replace('#month', curr_month).replace('#day', curr_day)
        return art_list_url

    def _gen_corpus_from_id_url_list_w_subpages(self, article_list_url_base):
        """
            generates corpus from a URL regarding to a sub-pages that contains article URLs
        """
        # Download the first page
        is_last_page = self._gen_corpus_from_id_url_list(article_list_url_base)
        page_num = 0
        max_pagenum = self._max_pagenum
        # if the last article list page does not contain any links to articles, go to next date
        while is_last_page and page_num < max_pagenum:  # TODO: convert to for in range + break?
            page_num += 1
            article_list_url = '{0}{1}'.format(article_list_url_base, page_num)
            is_last_page = self._gen_corpus_from_id_url_list(article_list_url)

    def _gen_corpus_from_id_url_list(self, article_list_url):
            article_list_only_urls = []
            article_list_raw_html = self._downloader.download_url(article_list_url)
            if article_list_raw_html is not None:
                self._good_urls.add(article_list_url)
                article_list_only_urls = extract_article_urls_from_page(article_list_raw_html, self._settings)
                self._urls_to_download |= article_list_only_urls  # TODO: This or iterator...
                # articles_to_corpus(article_list_only_urls, self._converter, self._file_out, self._settings,
                #                    self._downloader, self._logger_)
             else:
                self._problematic_urls.add(article_list_url)
            return article_list_raw_html is not None and len(article_list_only_urls) > 0  # is last


# run the whole thing
if __name__ == '__main__':
    m = NewsCrawler()
    m.url_iterator()
