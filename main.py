#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
from argparse import ArgumentParser

from corpusbuilder.utils import wrap_input_consants
from corpusbuilder.news_crawler import NewsArchiveCrawler, NewsArticleCrawler


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('config', type=str, help='Portal configfile (see configs folder for examples!)')
    parser.add_argument('--old-archive-warc', type=str, help='Existing WARC archive of the portal\'s archive '
                                                             '(Use as it cache)', default=None)
    parser.add_argument('--archive-warc', type=str, help='New WARC archive of the portal\'s archive '
                                                         '(Copy all cached pages if --old-archive-warc is specified)')
    parser.add_argument('--old-articles-warc', type=str, help='Existing WARC archive of the portal\'s archive '
                                                              '(Use as it cache)', default=None)
    parser.add_argument('--articles-warc', type=str, help='New WARC archive of the portal\'s archive '
                                                          '(Copy all cached pages if --old-archive-warc is specified)')
    # Mutually exclusive group...
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--archive', help='Crawl only the portal\'s archive', action='store_true')
    group.add_argument('--articles', help='Crawl articles (and optionally use cached WARC for the portal\'s archive),'
                                          ' DEFAULT behaviour', action='store_true')
    args = parser.parse_args()
    args.articles = not args.archive  # If archive is True -> articles is False, if archive is False -> articles is True
    if args.archive and not args.archive_warc:
        print('Must specify at least --archive-warc as destination!', file=sys.stderr)
        exit(1)
    if args.articles and (not args.archive_warc or not args.articles_warc):
        print('Must specify at least --archive-warc and --articles-warc as destination!', file=sys.stderr)
        exit(1)

    return args


if __name__ == '__main__':
    # Parse CLI args
    args = parse_args()

    # read input data from the given files, initialize variables
    portal_settings = wrap_input_consants(args.config)
    if args.archive:
        # For the article links only...
        archive_crawler = NewsArchiveCrawler(portal_settings, args.old_archive_warc, args.archive_warc)
        for url in archive_crawler.url_iterator():  # Get the list of urls in the archive...
            print(url, flush=True)
    else:
        articles_crawler = NewsArticleCrawler(portal_settings, args.old_articles_warc, args.articles_warc,
                                              args.old_archive_warc, args.archive_warc)
        articles_crawler.download_and_extract_all_articles()
