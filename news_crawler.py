#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# import external libs
import sys
from datetime import timedelta

# import own modules
from logger import Logger
from corpus_converter import CorpusConverter
from input_constants_wrapper import wrap_input_consants
from enhanced_downloader import WarcDownloader
from extractor import extract_article_urls_from_page, articles_to_corpus


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
    settings = wrap_input_consants(current_task_config_filename)
    file_out = open(settings['output_file'], 'a+', encoding=settings['encoding'])
    logger_ = Logger(settings['log_file'])
    converter = CorpusConverter(settings['site_schemas'], settings['tags'])
    downloader = WarcDownloader('example.warc.gz', logger_)

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
        gen_corpus_from_id_url_list_w_subpages(article_list_url, converter, file_out, downloader, logger_, settings,
                                               max_pagenum)

    file_out.close()


def gen_article_list_url_from_date(date_from, delta_day, settings):
    """
        generates and returns the URLs of a page the contains URLs of articles published that day
    """
    current_year, current_month, current_day = '{0}{1}'.format(date_from,  delta_day).split('-', maxsplit=2)
    article_list_url = settings['article_list_url_format'].replace('#year', current_year).\
        replace('#month', current_month).replace('#day', current_day)
    return article_list_url


def gen_corpus_from_id_url_list_w_subpages(article_list_url, converter, file_out, downloader, logger_, settings,
                                           max_pagenum):
    """
        generates corpus from a URL regarding to a sub-pages that contains article URLs
    """
    # Download the first page
    article_list_raw_html, article_list_only_urls = \
        gen_corpus_from_id_url_list(article_list_url, converter, file_out, downloader, logger_, settings)
    page_num = 0
    # if the last article list page does not contain any links to articles, go to next date
    while article_list_raw_html is not None and len(article_list_only_urls) > 0 and page_num < max_pagenum:
        page_num += 1
        article_list_url = '{0}{1}'.format(article_list_url, page_num)
        article_list_raw_html, article_list_only_urls = \
            gen_corpus_from_id_url_list(article_list_url, converter, file_out, downloader, logger_, settings)


def gen_corpus_from_id_url_list(article_list_url, converter, file_out, downloader, logger_, settings):
        article_list_only_urls = []
        article_list_raw_html = downloader.download_url(article_list_url)
        if article_list_raw_html is not None:
            article_list_only_urls = extract_article_urls_from_page(article_list_raw_html, settings)
            articles_to_corpus(article_list_only_urls, converter, file_out, settings, downloader, logger_)
        return article_list_raw_html, article_list_only_urls


# run the whole thing
if __name__ == '__main__':
    main()
