#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
from argparse import ArgumentParser, ArgumentTypeError, FileType

from webarticlecurator import wrap_input_constants, NewsArchiveCrawler, NewsArticleCrawler, sample_warc_by_urls, \
    validate_warc_file, online_test, Logger, __version__


def str2bool(v):
    """
    Original code from:
     https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse/43357954#43357954
    """
    if v.lower() in ('yes', 'Yes', 'YES', 'true', 'True', 'TRUE', 't', 'T', 'y', 'Y', '1'):
        return True
    elif v.lower() in ('no', 'No', 'NO', 'false', 'False', 'FALSE', 'f', 'F', 'n', 'N', '0'):
        return False
    else:
        raise ArgumentTypeError('Boolean value expected.')


def parse_args_crawl(parser):
    parser.add_argument(dest='command', choices={'crawl'}, metavar='crawl',
                        help='Crawl a portal with the supplied configuation and arguments')
    parser.add_argument('config', type=str, help='Portal configfile (see configs folder for examples!)')
    parser.add_argument('--old-archive-warc', type=str, help='Existing WARC archives of the portal\'s archive '
                                                             '(Use them as cache)', nargs='+', default=None)
    parser.add_argument('--archive-warc', type=str, help='New WARC archive of the portal\'s archive '
                                                         '(Copy all cached pages if --old-archive-warc is specified)')
    parser.add_argument('--old-articles-warc', type=str, help='Existing WARC archives of the portal\'s archive '
                                                              '(Use them as cache)', nargs='+', default=None)
    parser.add_argument('--articles-warc', type=str, help='New WARC archive of the portal\'s archive '
                                                          '(Copy all cached pages if --old-archive-warc is specified)')
    parser.add_argument('--archive-just-cache', type=str2bool, nargs='?', const=True, default=False,
                        metavar='True/False', help='Use only cached pages (no output warcfile):'
                                                   ' --old-archive-warc must be specified!')
    parser.add_argument('--articles-just-cache', type=str2bool, nargs='?', const=True, default=False,
                        metavar='True/False', help='Use only cached pages (no output warcfile):'
                                                   ' --old-articles-warc must be specified!')
    parser.add_argument('--debug-news-archive', type=str2bool, nargs='?', const=True, default=False,
                        metavar='True/False', help='Set DEBUG logging on NewsArchiveCrawler'
                                                   ' and print the number of extracted URLs per page')
    parser.add_argument('--strict', type=str2bool, nargs='?', const=True, default=False, metavar='True/False',
                        help='Set strict-mode in WARCReader to enable validation')
    parser.add_argument('--crawler-name', type=str, help='The name of the crawler for the WARC info record',
                        default='WebArticleCurator {0}'.format(__version__))
    parser.add_argument('--user-agent', type=str, help='The User-Agent string to use in headers while downloading')
    parser.add_argument('--no-overwrite-warc', help='Do not overwrite --{archive,articles}-warc if needed',
                        action='store_false')
    parser.add_argument('--cumulative-error-threshold', type=int, help='Sum of download errors before giving up',
                        default=15)
    parser.add_argument('--known-bad-urls', type=str, help='Known bad URLs to be excluded from download (filename, '
                                                           'one URL per line)', default=None)
    parser.add_argument('--known-article-urls', type=str, help='Known article URLs to mark the desired end of '
                                                               'the archive (filename, one URL per line)', default=None)
    parser.add_argument('--max-no-of-calls-in-period', type=int, help='Limit number of HTTP request per period',
                        default=2)
    parser.add_argument('--limit-period', type=int, help='Limit (seconds) the period the number of HTTP request'
                                                         ' see also --max-no-of-calls-in-period',
                        default=1)
    parser.add_argument('--proxy-url', type=str, help='SOCKS Proxy URL to use eg. socks5h://localhost:9050',
                        default=None)
    parser.add_argument('--allow-cookies', type=str2bool, nargs='?', const=True, default=False, metavar='True/False',
                        help='Allow session cookies')
    parser.add_argument('--stay-offline', type=str2bool, nargs='?', const=True, default=False, metavar='True/False',
                        help='Do not download, but write output WARC (see --just-cache when no output warcfile'
                             ' is needed)')

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


def parse_args_validate_and_list(parser):
    parser.add_argument('command', choices={'validate', 'listurls'}, metavar='validate|listurls',
                        help='Validate a warc file (created by this program) or list the urls in it')
    parser.add_argument('-s', '--source-warcfile', type=str, metavar='SOURCE WARCFILE', nargs='+',
                        help='A warc file (created by this program) to work from')
    args = parser.parse_args()
    if (args.source_warcfile is None or len(args.source_warcfile) == 0) and args.offline:
        print('Must specify at least one SOURCE_WARC !', file=sys.stderr)
        exit(1)
    return args


def parse_args_sample(parser):
    parser.add_argument(dest='command', choices={'sample'}, metavar='sample',
                        help='Copy the supplied list of URLs to the output warc file from the internet '
                             'or from the supplied warc file (created by this program)')
    parser.add_argument('-s', '--source-warcfile', type=str, default=None, nargs='*', metavar='SOURCE WARCFILE',
                        help='A warc file (created by this program) to work from '
                             '(not mandatory when --offline is True)')
    parser.add_argument('-i', '--input-urls', dest='url_input_stream', type=FileType(), default=sys.stdin,
                        help='Use input file instead of STDIN (one URL per line)', metavar='FILE', required=False)
    parser.add_argument('target_warcfile', type=str, metavar='TARGET_WARFCILE', help='The name of the target warc file')
    parser.add_argument('--offline', type=str2bool, nargs='?', const=True, default=True, metavar='True/False',
                        help='Download URLs which are not present in the source archive (default True)')
    args = parser.parse_args()
    if (args.source_warcfile is None or len(args.source_warcfile) == 0) and args.offline:
        print('Must specify at least one SOURCE_WARC if --offline is False!', file=sys.stderr)
        exit(1)
    return args


def parse_args_cat(parser):
    parser.add_argument(dest='command', choices={'cat'}, metavar='cat',
                        help='Print the list of URLs from the supplied warc file (created by this program)')
    parser.add_argument('-s', '--source-warcfile', type=str, metavar='SOURCE WARCFILE', nargs='+',
                        help='A warc file (created by this program) to work from')
    parser.add_argument('-i', '--input-urls', dest='url_input_stream', type=FileType(), default=sys.stdin,
                        help='Use input file instead of STDIN (one URL per line)', metavar='FILE')
    parser.add_argument('out_dir', type=str)
    args = parser.parse_args()
    if (args.source_warcfile is None or len(args.source_warcfile) == 0) and args.offline:
        print('Must specify at least one SOURCE_WARC !', file=sys.stderr)
        exit(1)
    return args


def parse_args_donwload(parser):
    parser.add_argument(dest='command', choices={'download'}, metavar='downlaod',
                        help='Download a single URL to a warc file')
    parser.add_argument('source_url', type=str, metavar='URL', help='The URL to download')
    parser.add_argument('target_warcfile', type=str, metavar='TARGET_WARFCILE', help='The name of the target warc file')
    return parser.parse_args()


def main_crawl(args):
    """ read input data from the given files, initialize variables """
    portal_settings = wrap_input_constants(args.config)
    # These parameters go down directly to the downloader
    download_params = {'program_name': args.crawler_name, 'user_agent': args.user_agent,
                       'overwrite_warc': args.no_overwrite_warc, 'err_threshold': args.cumulative_error_threshold,
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
                                              args.old_archive_warc, args.archive_warc, args.articles_just_cache,
                                              args.archive_just_cache, args.known_article_urls, args.debug_params,
                                              download_params)
        articles_crawler.download_and_extract_all_articles()


def main_validate_and_list(args):
    """ __file__ validate [source warcfiles]     # WarcReader(..., strict_mode=True, check_digest=True) """
    level = 'INFO'
    url_index = validate_warc_file(args.source_warcfile, Logger(console_level=level, logfile_level=level))
    if args.command == 'listurls':
        for url in url_index:
            print(url)


def main_cat_and_sample(args):
    """ __file__ sample [source warcfiles or None] [urls list file or stdin] [target warcfile] [Online or Offline] """
    main_logger = Logger()
    out_dir = getattr(args, 'out_dir', None)
    target_warcfile = getattr(args, 'target_warcfile', None)
    target = out_dir if out_dir is not None else target_warcfile
    main_logger.log('INFO', 'Adding URLs to', target, ':')
    offline = getattr(args, 'offline', True)  # Sample can be online or offline, but we write warc only when sampling!
    sample_warc_by_urls(args.source_warcfile, args.url_input_stream, main_logger, target_warcfile=target_warcfile,
                        offline=offline, out_dir=out_dir, just_cache=args.command == 'cat')
    main_logger.log('INFO', 'Done!')


def main_download(args):
    """ __file__ download [URL] [target warfile] """
    main_logger = Logger()
    main_logger.log('INFO', 'Adding URL to', args.target_warcfile, ':')
    online_test(args.source_url, args.target_warcfile, main_logger)
    main_logger.log('INFO', 'Done!')


def main():
    # Parse command arg from CLI and pass to the selected main function
    commands = {'validate': (parse_args_validate_and_list, main_validate_and_list),
                'listurls': (parse_args_validate_and_list, main_validate_and_list),
                'sample': (parse_args_sample, main_cat_and_sample), 'download': (parse_args_donwload, main_download),
                'cat': (parse_args_cat, main_cat_and_sample), 'crawl': (parse_args_crawl, main_crawl)}
    parser = ArgumentParser()
    parser.add_argument('command', choices=commands.keys(), metavar='COMMAND',
                        help='Please choose from the available commands ({0}) to set mode and see deatiled help!'.
                        format(set(commands.keys())))

    command = parser.parse_args(sys.argv[1:2]).command  # Route ArgumentParser before reparsing the whole CLI
    argparse_fun, main_fun = commands[command]
    sub_args = argparse_fun(ArgumentParser())
    main_fun(sub_args)


if __name__ == '__main__':
    main()
