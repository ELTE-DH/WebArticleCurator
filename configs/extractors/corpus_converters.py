#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
import sys
from argparse import Namespace
from datetime import datetime

import yaml

"""Here comes the stuff to extract data from a specific downloaded webpage (article)"""


class CorpusConverterNewspaper:  # Mimic CorpusConverter
    def __init__(self, settings):
        from newspaper import Article
        self._article = Article

        self._logger = Namespace(log=print)  # Hack to be able to monkeypatch logger

        # Set output_file handle
        self._file_out = open(settings['output_corpus'], 'a+', encoding='UTF-8')

        # This is useful to ingnore unwanted URLs by regex
        known_columns = yaml.safe_load(open('known_columns.yaml', encoding='UTF-8'))

        # Read tag_keys
        self._known_columns = {re.compile(column_def): val for column_def, val in known_columns.items()}

    def identify_site_scheme(self, url, article_raw_html):
        _ = article_raw_html  # Silence IDE
        for column_re, column_name in self._known_columns.items():
            if column_re.search(url):
                return column_name

        self._logger.log('ERROR', url, {regexp.pattern for regexp in self._known_columns.keys()},
                         'NO MATCHING COLUMN_RE PATTERN! IGNORING ARTICLE!', sep='\t', file=sys.stderr)
        return None

    def extract_article_date(self, url, article_raw_html, scheme):
        """
            extracts and returns next page URL from an HTML code if there is one...
        """
        _ = url, scheme  # Silence dummy IDE
        article = self._article(url, memoize_articles=False, language='hu')
        article.download(input_html=article_raw_html)
        article.parse()
        article.nlp()

        return article.publish_date.date()

    def article_to_corpus(self, url, article_raw_html, scheme):
        _ = scheme  # Silence dummy IDE
        article = self._article(url, memoize_articles=False, language='hu')
        article.download(input_html=article_raw_html)
        article.parse()
        article.nlp()

        html_date = '<html-date> {0} </html-date>'.format(article.publish_date.date())
        html_description_lead = '<html-lead>\n </html-lead>'
        html_charset = '<html-charset> utf-8 </html-charset>'
        html_url = '<html-url> {0} </html-url>'.format(url)
        html_keywords = '<html-keywords> {0} </html-keywords>'.format(', '.join(article.keywords))
        html_title = '<html-title> {0} </html-title>'.format(article.title)
        html_body = '<html-body>\n{0} </html-body>\n'.format(article.text)

        print('<html_article>', html_date, html_description_lead, html_charset, html_url, html_keywords, html_title,
              html_body, '</html_article>', sep='\n', end='', file=self._file_out)
        self._logger.log('INFO', url, 'Article extraction OK', sep='\t', file=sys.stderr)

    @staticmethod
    def follow_links_on_page(url, article_raw_html, scheme):
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        return set()

    def __del__(self):
        if hasattr(self, '_file_out') and self._file_out is not None:
            self._file_out.close()


class MultiPageArticleConverter:  # No output corpus
    """
        An example converter to showcase API and to suppress any article processing at crawling time (for new portals)
    """

    def __init__(self, settings):
        self._logger = Namespace(log=print)  # Hack to be able to monkeypatch logger
        # Override this if needed!
        if settings['FILTER_ARTICLES_BY_DATE'] and not settings['archive_page_urls_by_date']:
            raise ValueError(f'Date filtering is not possible with {type(self).__name__} on a non-date-based archive!')
        settings['FILTER_ARTICLES_BY_DATE'] = False  # Use the archive dates for filtering...
        # Init stuff
        if settings['NEXT_PAGE_OF_ARTICLE_FUN'] is None:
            raise ValueError('next_page_of_article_fun is not supplied!')
        self._next_page_of_article_fun = settings['NEXT_PAGE_OF_ARTICLE_FUN']

    @staticmethod
    def identify_site_scheme(url, article_raw_html):
        _ = url, article_raw_html  # Silence IDE

    @staticmethod
    def extract_article_date(url, article_raw_html, scheme):
        """ extracts and returns next page URL from an HTML code if there is one... """
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        return datetime.today().date()

    @staticmethod
    def article_to_corpus(url, article_raw_html, scheme):
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        # pass

    def follow_links_on_page(self, url, article_raw_html, scheme):
        _ = url, scheme  # Silence dummy IDE
        ret = self._next_page_of_article_fun(article_raw_html)
        if ret is not None:
            return {ret}
        return set()
