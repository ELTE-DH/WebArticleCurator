#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

"""Here comes the stuff to extract more URL or the text from a specific downloaded webpage"""

from newspaper import Article


def extract_article_urls_from_page(article_list_raw_html, settings):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    """
    urls = set()
    for code_line in settings['ARTICLE_LINK_FORMAT_RE'].findall(article_list_raw_html):
        code_line = settings['BEFORE_ARTICLE_URL_RE'].sub('', code_line)
        code_line = settings['AFTER_ARTICLE_URL_RE'].sub('', code_line)
        urls.add(code_line)
    return urls


class CorpusConverterNewspaper:
    def __init__(self, settings, file_out, logger_):
        self._file_out = file_out
        self._logger_ = logger_
        self._settings = settings

    def article_to_corpus(self, url, page_str):
        article = Article(url, memoize_articles=False)
        article.download(input_html=page_str)
        article.parse()
        # article.title
        # article.publish_date
        # article.authors
        # article.text
        print(self._settings['article_begin_flag'], '\n'.join((article.title, article.text)),
              self._settings['article_end_flag'], sep='', end='', file=self._file_out)
        self._logger_.log(url, 'download OK')
