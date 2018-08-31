#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# >>> HunNewsCorpusBuilder                            <<<
# >>>                                                 <<<
# >>> Prerequests:                                    <<<
# >>>    Python 3.x                                   <<<
# >>>    pip install articleDateExtractor             <<<


# import external libs
import sys
from datetime import timedelta
import urllib.request
import urllib.error
from urllib import parse

import articleDateExtractor

# import own modules
import logger
import corpus_converter
import input_constants_wrapper


def main():
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
    settings = input_constants_wrapper.wrap_input_consants(current_task_config_filename)
    file_out = open(settings['output_file'], 'a+', encoding=settings['encoding'])
    logger_ = logger.Logger(settings['log_file'])
    converter = corpus_converter.CorpusConverter(settings['site_schemas'], settings['tags'])

    # generate URLs of lists of articles
    # extract URLs of articles from these lists
    # download article pages
    # convert these articles from raw HTML to corpus format

    # if URLs of current website's archive pages are generated based on an ID,
    # which is a positive integer growing one by one
    article_list_urls = []
    max_pagenum = -1
    if settings['ARTICLE_LIST_URLS_BY_DATE']:  # e.g. index.hu, origo.hu
        max_pagenum = 0  # No pages (may be overwritten e.g. origo.hu)
        article_list_urls = [gen_article_list_url_from_date(settings['DATE_FROM'], timedelta(days=curr_day), settings)
                             for curr_day in range(settings['INTERVAL'].days + 1)]

    if settings['ARTICLE_LIST_URLS_BY_ID']:
        max_pagenum = -1  # Infinty
        # not URL_BY_DATE and URLS_BY_ID
        if len(article_list_urls) == 0:  # e.g. 444.hu
            article_list_urls.append(settings['article_list_url_format'])

    if len(article_list_urls) == 0:
        print('There is no existing case where settings[\'ARTICLE_LIST_URLS_BY_DATE\'] and'
              ' settings[\'ARTICLE_LIST_URLS_BY_ID\'] are both False')  # try/excepttel csinálni?
        return

    for article_list_url in article_list_urls:
        gen_corpus_from_id_url_list_w_subpages(article_list_url, converter, file_out, logger_, settings, max_pagenum)

    file_out.close()


def gen_article_list_url_from_date(date_from, delta_day, settings):
    """
        generates and returns the URLs of a page the contains URLs of articles published that day
    """
    current_year, current_month, current_day = '{0}{1}'.format(date_from,  delta_day).split('-', maxsplit=2)
    article_list_url = settings['article_list_url_format'].replace('#year', current_year).\
        replace('#month', current_month).replace('#day', current_day)
    return article_list_url


def gen_corpus_from_id_url_list_w_subpages(article_list_url, converter, file_out, logger_, settings, max_pagenum):
    """
        generates corpus from a URL regarding to a sub-pages that contains article URLs
    """
    # Download the first page
    article_list_raw_html, article_list_only_urls = \
        gen_corpus_from_id_url_list(article_list_url, converter, file_out, logger_, settings)
    page_num = 0
    # if the last article list page does not contain any links to articles, go to next date
    while article_list_raw_html is not None and len(article_list_only_urls) > 0 and page_num < max_pagenum:
        page_num += 1
        article_list_url = '{0}{1}'.format(article_list_url, page_num)
        article_list_raw_html, article_list_only_urls = \
            gen_corpus_from_id_url_list(article_list_url, converter, file_out, logger_, settings)


def gen_corpus_from_id_url_list(article_list_url, converter, file_out, logger_, settings):
        article_list_only_urls = []
        article_list_raw_html = download_page(article_list_url, logger_)
        if article_list_raw_html is not None:
            article_list_only_urls = extract_article_urls_from_page(article_list_raw_html, settings)
            articles_to_corpus(article_list_only_urls, converter, file_out, settings, logger_)
        return article_list_raw_html, article_list_only_urls


def extract_article_urls_from_page(article_list_raw_html, settings):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    """
    urls = []
    for code_line in settings['ARTICLE_LINK_FORMAT_RE'].findall(article_list_raw_html):
        code_line = settings['BEFORE_ARTICLE_URL_RE'].sub('', code_line)
        code_line = settings['AFTER_ARTICLE_URL_RE'].sub('', code_line)
        urls.append(code_line)
    return urls


# TODO: This is about downloading we want to support downloading to and reading WARC archives
def download_page(url, logger_):
    """
        downloads and returns the raw HTML code from a given URL with given encoding
    """
    try:
        scheme, netloc, path, query, fragment = parse.urlsplit(url)
        path = parse.quote(path)
        url = parse.urlunsplit((scheme, netloc, path, query, fragment))
        connection = urllib.request.urlopen(url)
        page_bytes = connection.read()
        page_str = page_bytes.decode(connection.headers.get_content_charset(), 'ignore')
        connection.close()
    except urllib.error.URLError:
        logger_.log('', 'urllib.error.URLError happened during downloading this article list,'
                        ' the program ignores it and jumps to the next one')
        page_str = None
    return page_str


# TODO: This is article extraction
def articles_to_corpus(article_list_only_urls, converter, file_out, settings, logger_):
    """
        converts the raw HTML code of an article to corpus format and saves it to the output file
    """
    for url in article_list_only_urls:
        # url_match = settings['URL_PATTERN'].match(url)
        # url_path = url_match.group(5)
        # print(url_path)
        if logger_.is_url_processed(url):
            print(url + ' has already been processed')
            continue
        # handling of time filtering when archive page URLs are not generated by date
        if settings['ARTICLE_LIST_URLS_BY_ID'] and not settings['ARTICLE_LIST_URLS_BY_DATE']:
            date_before_interval = False
            date_after_interval = False
            if settings['DATE_INTERVAL_USED']:
                article_date = articleDateExtractor.extractArticlePublishedDate(url)
                date_before_interval = settings['DATE_FROM'] > article_date.date()
                date_after_interval = article_date.date() > settings['DATE_UNTIL']

            if not (date_before_interval or date_after_interval):
                article_raw_html = download_page(url, logger_)  # TODO: Either way we end up download_page(...)

            elif date_before_interval:
                print(date_before_interval)
                # return None # does not work LOL WTF
                sys.exit()
            else:
                continue
        else:
            article_raw_html = download_page(url, logger_)

        try:
            corpus_formatted_article = converter.convert_doc_by_json(article_raw_html, url)
        except ValueError as e:
            logger_.log(url, e)
            continue
        print(settings['article_begin_flag'], corpus_formatted_article, settings['article_end_flag'], sep='', end='',
              file=file_out)
        logger_.log(url, 'download OK')


# run the whole thing
if __name__ == '__main__':
    main()
