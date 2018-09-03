#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# import external libs
import sys

# import own modules
from corpusbuilder.input_constants_wrapper import wrap_input_consants
from corpusbuilder.news_archive_crawler import NewsArchiveCrawler
from corpusbuilder.news_article_crawler import NewsArticleCrawler

# run the whole thing
if __name__ == '__main__':
    # get the command line argument it is the configuration file's name
    try:
        current_task_config_filename = sys.argv[1]
    except IndexError:
        raise IndexError('Not enough or too many input arguments!\n'
                         'The program should be called like:\n'
                         'python web_crawler.py current_task_config.json')

    # read input data from the given files, initialize variables
    portal_settings = wrap_input_consants(current_task_config_filename)
    # For the article links only...
    archive_crawler = NewsArchiveCrawler(portal_settings, True, 'example-archive.warc.gz')
    archive_crawler.url_iterator()  # Get the list of urls in the archive...

    articles_crawler = NewsArticleCrawler('example-article.warc.gz', 'example-archive.warc.gz', True,
                                          portal_settings)
    articles_crawler.download_and_extract_all_articles()
