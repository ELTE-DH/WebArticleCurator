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


def article_to_corpus(url, article_raw_html, converter, file_out, settings, logger_):
    """
        converts the raw HTML code of an article to corpus format and saves it to the output file
    """
    # url_match = settings['URL_PATTERN'].match(url)
    # url_path = url_match.group(5)
    # print(url_path)
    try:
        article_corpus_format = converter.convert_doc_by_json(article_raw_html, url)
    except ValueError as e:
        logger_.log(url, e)
        return
    print(settings['article_begin_flag'], article_corpus_format, settings['article_end_flag'], sep='', end='',
          file=file_out)
    logger_.log(url, 'download OK')


# TODO: something like this...
def articles_to_corpus_newspaper(url, page_str, file_out, downloader, logger_):
    article = Article(url, memoize_articles=False)
    article.download(input_html=page_str)
    article.parse()
    print(article.title)
    print(article.publish_date)
    print(article.authors)
    print(article.text)
