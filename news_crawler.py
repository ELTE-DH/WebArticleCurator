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
from extractor import extract_article_urls_from_page, article_to_corpus


class NewsArchiveCrawler:
    """
        1) Generate URLs of lists of articles
        2) Extract URLs of articles from these lists
    """
    def __init__(self, settings, download, filename):
        self._settings = settings
        self._logger_ = Logger(self._settings['log_file_articles'])  # TODO: Separate Logger for the Archive from settings

        self._min_pagenum = 0  # TODO: MINIMAL PAGENUM FROM SETTINGS!
        self._max_pagenum = -1

        # For external use
        self.good_urls = set()
        self.problematic_urls = set()

        # Create new archive while downloading, or simulate download and read the archive
        if download == True:
            self._downloader = WarcDownloader(filename, logger_)
        else:
            self._downloader = WarcReader(filename, logger_)

    def url_iterator(self):
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
            yield from self._gen_corpus_from_id_url_list_w_subpages(article_list_url)

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
        article_urls, is_last_page = self._gen_corpus_from_id_url_list(article_list_url_base)
        yield article_urls
        page_num = self._min_pagenum
        max_pagenum = self._max_pagenum
        # TODO: Better way: Search for the "next page" link, if there is no such link, than it is the last page!
        # if the last article list page does not contain any links to articles, go to next date
        while not is_last_page and page_num < max_pagenum:
            page_num += 1
            article_list_url = '{0}{1}'.format(article_list_url_base, page_num)
            article_urls, is_last_page = self._gen_corpus_from_id_url_list(article_list_url)
            yield article_urls

    def _gen_corpus_from_id_url_list(self, article_list_url):
            article_list_only_urls = []
            article_list_raw_html = self._downloader.download_url(article_list_url)
            if article_list_raw_html is not None:
                self.good_urls.add(article_list_url)
                article_list_only_urls = extract_article_urls_from_page(article_list_raw_html, self._settings)
             else:
                self.problematic_urls.add(article_list_url)
            # None should only occur when the pattern is not OK
            return article_list_only_urls, article_list_raw_html is None or len(article_list_only_urls) == 0  # is last page

class NewsArticleCrawler:
    """
        1) Get the list of articles (NewsArchiveCrawler)
        2) Download article pages
        3) Extract the text of articles from raw HTML
        4) save them in corpus format
    """
    def __init__(self, atricles_filename, archive_filename, download):
        # get the command line argument it is the configuration file's name
        try:
            current_task_config_filename = sys.argv[1]
        except IndexError:
            raise IndexError('Not enough or too many input arguments!\n'
                             'The program should be called like:\n'
                             'python web_crawler.py current_task_config.json')

        # read input data from the given files, initialize variables
        self._settings = wrap_input_consants(current_task_config_filename)
        self._logger_ = Logger(self._settings['log_file_articles'])

        self._file_out = open(self._settings['output_file'], 'a+', encoding=self._settings['encoding'])
        self._converter = CorpusConverter(self._settings['site_schemas'], self._settings['tags'])

        # Create new archive while downloading, or simulate download and read the archive
        if download == True:
            self._downloader = WarcDownloader(atricles_filename, logger_)
        else:
            self._downloader = WarcReader(atricles_filename, logger_)

        self._archive_downloader = NewsArchiveCrawler(self._settings, download, archive_filename)

    def _get_archive_urls(self):
        return self._archive_downloader.url_iterator()

    def _process_urls(self, it):
        for url in it:
            # "Download" article, extract text
            # Extract links to other articles...
            # Check for already extracted urls!
            
            # Handling of time filtering when archive page URLs are not generated by date
            if settings['ARTICLE_LIST_URLS_BY_ID'] and not settings['ARTICLE_LIST_URLS_BY_DATE']:
                date_before_interval = False
                date_after_interval = False
                if settings['DATE_INTERVAL_USED']:
                    article_date = extractArticlePublishedDate(url)
                    date_before_interval = settings['DATE_FROM'] > article_date.date()
                    date_after_interval = article_date.date() > settings['DATE_UNTIL']

                if not (date_before_interval or date_after_interval):
                    article_raw_html = downloader.download_url(url)  # TODO: Either way we end up download_page(...)

                elif date_before_interval:
                    print(date_before_interval)
                    # return None # does not work LOL WTF
                    sys.exit()
                else:
                    continue
            else:
                article_raw_html = downloader.download_url(url)
            articles_to_corpus(url, article_raw_html, self._converter, self._file_out, self._settings, self._logger_)

    def download_and_extract_all_articles(self):
        self._process_urls(self._get_archive_urls())

    def __del__(self):
        self._file_out.close()

# run the whole thing
if __name__ == '__main__':
    m = NewsArchiveCrawler()
    m.url_iterator()  # Get the list of urls in the archive...
