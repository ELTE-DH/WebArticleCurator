#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
import sys
from argparse import Namespace

import yaml
from newspaper import Article

"""Here comes the stuff to extract data from a specific downloaded webpage (article)"""


class CorpusConverterNewspaper:  # Mimic CorpusConverter
    def __init__(self, settings):
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

    @staticmethod
    def extract_article_date(url, article_raw_html, scheme):
        """
            extracts and returns next page URL from an HTML code if there is one...
        """
        _ = url, scheme  # Silence dummy IDE
        article = Article(url, memoize_articles=False, language='hu')
        article.download(input_html=article_raw_html)
        article.parse()
        article.nlp()

        return article.publish_date.date()

    def article_to_corpus(self, url, article_raw_html, scheme):
        _ = scheme  # Silence dummy IDE
        article = Article(url, memoize_articles=False, language='hu')
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

    def __del__(self):
        if hasattr(self, '_file_out') and self._file_out is not None:
            self._file_out.close()
