#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
from argparse import ArgumentParser, ArgumentTypeError

from corpusbuilder import wrap_input_consants, NewsArchiveCrawler, NewsArticleCrawler, sample_warc_by_urls,\
    validate_warc_file, online_test, Logger


def str2bool(v):
    """
    Original code from:
     https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse/43357954#43357954
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')


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
    parser.add_argument('--archive-just-cache', type=str2bool, nargs='?', const=True, default=False,
                        help='Use only cached pages:--old-archive-warc must be specified!')
    parser.add_argument('--articles-just-cache', type=str2bool, nargs='?', const=True, default=False,
                        help='Use only cached pages:--old-articles-warc must be specified!')
    parser.add_argument('--debug-news-archive', type=str2bool, nargs='?', const=True, default=False,
                        help='Set DEBUG logging on NewsArchiveCrawler and print the number of extracted URLs per page')
    parser.add_argument('--strict', type=str2bool, nargs='?', const=True, default=False,
                        help='Set strict-mode in WARCReader')
    parser.add_argument('--crawler-name', type=str, help='The name of the crawler for the WARC info record',
                        default='corpusbuilder 1.0')
    parser.add_argument('--user-agent', type=str, help='The User-Agent string to use in headers while downloading')
    parser.add_argument('--no-overwrite-warc', help='Do not overwrite --{archive,articles}-warc if needed',
                        action='store_false')
    parser.add_argument('--comulative-error-threshold', type=int, help='Sum of download errors before giving up',
                        default=15)
    parser.add_argument('--known-bad-urls', type=str, help='Known bad URLs to be excluded from download (filename, '
                                                           'one URL per line)', default=None)
    parser.add_argument('--known-article-urls', type=str, help='Known article URLs to mark the desired end of '
                                                               'the archive (filename, one URL per line)', default=None)
    parser.add_argument('--max-no-of-calls-in-period', type=int, help='Limit number of HTTP request per period',
                        default=2)
    parser.add_argument('--limit-period', type=int, help='Limit (seconds) the period the number of HTTP request'
                                                         'see \'also max-no-of-calls-in-period\'',
                        default=1)
    parser.add_argument('--proxy-url', type=str, help='SOCKS Proxy URL to use eg. socks5h://localhost:9050',
                        default=None)
    parser.add_argument('--allow-cookies', type=str2bool, nargs='?', help='Allow session cookies', const=True,
                        default=False)
    parser.add_argument('--stay-offline', type=str2bool, nargs='?', help='Do not download, but write output WARC'
                                                                         ' (see --just-cache)', const=True,
                        default=False)

    # Mutually exclusive group...
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--archive', help='Crawl only the portal\'s archive', action='store_true')
    group.add_argument('--articles', help='Crawl articles (and optionally use cached WARC for the portal\'s archive),'
                                          ' DEFAULT behaviour', action='store_true')
    group.add_argument('--corpus', help='Use --old-articles-warc to create corpus (no crawling, equals to'
                                        ' --archive-just-cache and --articles-just-cache)', action='store_true')
    cli_args = parser.parse_args()
    # If archive is True -> articles is False, if archive is False -> articles is True
    cli_args.articles = not cli_args.archive
    if cli_args.corpus:
        cli_args.archive_just_cache = True
        cli_args.articles_just_cache = True
    if cli_args.archive and (not cli_args.archive_warc and not cli_args.archive_just_cache):
        print('Must specify at least --archive-warc as destination!', file=sys.stderr)
        exit(1)
    if cli_args.articles and ((not cli_args.archive_warc and not cli_args.archive_just_cache) or
                              (not cli_args.articles_warc and not cli_args.articles_just_cache)):
        print('Must specify at least --archive-warc and --articles-warc as destination!', file=sys.stderr)
        exit(1)
    if cli_args.corpus and not cli_args.old_articles_warc:
        print('Must specify at least --old-articles-warc as source!', file=sys.stderr)
        exit(1)

    if cli_args.debug_news_archive:
        cli_args.debug_params = {'console_level': 'DEBUG', 'logfile_level': 'DEBUG'}
    else:
        cli_args.debug_params = {}
    return cli_args


def enhanced_downloader():  # TODO place it properly Create an ArgParser for it...
    """
        Modes:
            - validate [warcfile to validate] WarcReader(..., strict_mode=True, check_digest=True)
            - sample [warcfile to sample] [urls list] [new warcfile to sample]
    """
    main_logger = Logger()
    if len(sys.argv) == 1:
        online_test(main_logger)
    elif sys.argv[1] == 'validate':
        validate_warc_file(sys.argv[2], main_logger)
    elif sys.argv[1] == 'sample':
        urls = sys.argv[3]
        if not urls.startswith('http'):
            with open(urls, encoding='UTF-8') as fhandle:
                urls = {url.strip() for url in fhandle}
        if len(sys.argv) == 5:
            new_warc_file = sys.argv[4]
        else:
            new_warc_file = None
        sample_warc_by_urls(sys.argv[2], urls, main_logger, new_warc_fineame=new_warc_file)


def main():
    # Parse CLI args
    args = parse_args()
    # read input data from the given files, initialize variables
    portal_settings = wrap_input_consants(args.config)
    # These parameters go down directly to the downloader
    download_params = {'program_name': args.crawler_name, 'user_agent': args.user_agent,
                       'overwrite_warc': args.no_overwrite_warc, 'err_threshold': args.comulative_error_threshold,
                       'known_bad_urls': args.known_bad_urls, 'strict_mode': args.strict,
                       'max_no_of_calls_in_period': args.max_no_of_calls_in_period, 'limit_period': args.limit_period,
                       'proxy_url': args.proxy_url, 'allow_cookies': args.allow_cookies,
                       'stay_offline': args.stay_offline, 'verify_request': portal_settings['verify_request']}
    if args.archive:
        # For the article links only...
        archive_crawler = NewsArchiveCrawler(portal_settings, args.old_archive_warc, args.archive_warc,
                                             args.archive_just_cache, args.known_article_urls, args.debug_params,
                                             download_params)
        for url in archive_crawler.url_iterator():  # Get the list of urls in the archive...
            print(url, flush=True)
    else:
        articles_crawler = NewsArticleCrawler(portal_settings, args.old_articles_warc, args.articles_warc,
                                              args.old_archive_warc, args.archive_warc,
                                              args.articles_just_cache, args.archive_just_cache,
                                              args.known_article_urls, args.debug_params,
                                              download_params)
        articles_crawler.download_and_extract_all_articles()


if __name__ == '__main__':
    main()
