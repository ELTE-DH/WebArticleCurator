#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

# TODO Logger is defined here for legacy reasons to be dropped on 2.0.0
from mplogger import Logger
from .utils import wrap_input_constants, DummyConverter, create_or_check_clean_dir, \
    write_content_to_url_named_file
from .enhanced_downloader import WarcCachingDownloader
from .other_modes import validate_warc_file, online_test, sample_warc_by_urls, \
    archive_page_contains_article_url
from .news_crawler import NewsArchiveCrawler, NewsArticleCrawler
from .strategies import gen_article_urls_and_subpages, date_range, infinite_scrolling, until_maxpagenum, \
    intersecting_pages, stop_on_empty_or_taboo
from .version import __version__

__all__ = ['NewsArchiveCrawler', 'NewsArticleCrawler', 'DummyConverter', 'WarcCachingDownloader', 'Logger',
           'wrap_input_constants', 'gen_article_urls_and_subpages', 'date_range', 'infinite_scrolling',
           'until_maxpagenum', 'intersecting_pages', 'stop_on_empty_or_taboo', __version__]
