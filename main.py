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
                                                             '(Use it as cache)', default=None)
    parser.add_argument('--archive-warc', type=str, help='New WARC archive of the portal\'s archive '
                                                         '(Copy all cached pages if --old-archive-warc is specified)')
    parser.add_argument('--old-articles-warc', type=str, help='Existing WARC archive of the portal\'s archive '
                                                              '(Use it as cache)', default=None)
    parser.add_argument('--articles-warc', type=str, help='New WARC archive of the portal\'s archive '
                                                          '(Copy all cached pages if --old-archive-warc is specified)')
    parser.add_argument('--crawler-name', type=str, help='The name of the crawler for the WARC info record',
                        default='corpusbuilder 1.0')
    parser.add_argument('--user-agent', type=str, help='The User-Agent string to use in headers while downloading')
    parser.add_argument('--no-overwrite-warc', help='Do not overwrite --{archive,articles}-warc if needed',
                        action='store_false')
    parser.add_argument('--comulative-error-threshold', type=int, help='Sum of download errors before giving up',
                        default=15)
    parser.add_argument('--corpus-converter', type=str, help='The type of html->corpus class', default='rule-based',
                        choices=['rule-based', 'newspaper'])

    # Mutually exclusive group...
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--archive', help='Crawl only the portal\'s archive', action='store_true')
    group.add_argument('--articles', help='Crawl articles (and optionally use cached WARC for the portal\'s archive),'
                                          ' DEFAULT behaviour', action='store_true')
    cli_args = parser.parse_args()
    # If archive is True -> articles is False, if archive is False -> articles is True
    cli_args.articles = not cli_args.archive
    if cli_args.archive and not cli_args.archive_warc:
        print('Must specify at least --archive-warc as destination!', file=sys.stderr)
        exit(1)
    if cli_args.articles and (not cli_args.archive_warc or not cli_args.articles_warc):
        print('Must specify at least --archive-warc and --articles-warc as destination!', file=sys.stderr)
        exit(1)

    return cli_args


if __name__ == '__main__':
    # Parse CLI args
    args = parse_args()

    # read input data from the given files, initialize variables
    portal_settings = wrap_input_consants(args.config)
    if args.archive:
        # For the article links only...
        archive_crawler = NewsArchiveCrawler(portal_settings, args.old_archive_warc, args.archive_warc,
                                             program_name=args.crawler_name,
                                             user_agent=args.user_agent,
                                             overwrite_warc=args.no_overwrite_warc,
                                             err_threshold=args.comulative_error_threshold)
        for url in archive_crawler.url_iterator():  # Get the list of urls in the archive...
            print(url, flush=True)
    else:
        articles_crawler = NewsArticleCrawler(portal_settings, args.old_articles_warc, args.articles_warc,
                                              args.old_archive_warc, args.archive_warc,
                                              program_name=args.crawler_name,
                                              user_agent=args.user_agent,
                                              overwrite_warc=args.no_overwrite_warc,
                                              err_threshold=args.comulative_error_threshold,
                                              corpus_converter=args.corpus_converter)
        articles_crawler.download_and_extract_all_articles()
