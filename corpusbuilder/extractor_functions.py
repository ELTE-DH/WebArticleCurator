#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from html import unescape as html_unescape
from datetime import datetime

strptime = datetime.strptime

"""Here comes the stuff to extract data from a specific downloaded webpage (archive or article)"""


# TODO: This is also used when extracting all article URL from an article (extract cross-linking between articles)
def extract_article_urls_from_page(archive_page_raw_html, settings):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    """
    urls = set()
    article_url_format_re = settings['ARTICLE_URL_FORMAT_RE']
    for code_line in article_url_format_re.findall(archive_page_raw_html):
        code_line = settings['BEFORE_ARTICLE_URL_RE'].sub(settings['before_article_url_repl'], code_line)
        code_line = settings['AFTER_ARTICLE_URL_RE'].sub(settings['after_article_url_repl'], code_line)
        code_line = html_unescape(code_line)
        urls.add(code_line)
    return urls


def extract_article_date(article_raw_html, settings, scheme):
    """
        extracts and returns next page URL from an HTML code if there is one...
    """
    article_date_format_re = settings['ARTICLE_DATE_FORMAT_RE']
    code_line = article_date_format_re.search(article_raw_html)
    if code_line is not None:
        code_line = code_line.group(0)
        code_line = settings['BEFORE_ARTICLE_DATE_RE'].sub(settings['before_article_date_repl'], code_line)
        code_line = settings['AFTER_ARTICLE_DATE_RE'].sub(settings['after_article_date_repl'], code_line)
        try:
            code_line = strptime(code_line, settings['article_date_formatting']).date()
        except (UnicodeError, ValueError, KeyError):  # In case of any error log outside of this function...
            code_line = None
    return code_line


# TODO: This is a type of find_next_page_url
def extract_next_page_url(archive_page_raw_html, settings):
    """
        extracts and returns next page URL from an HTML code if there is one...
    """
    # WARNING: We can not tell if the RE is bad, or we are on the last page!
    next_page_url_format_re = settings['NEXT_PAGE_URL_FORMAT_RE']
    code_line = next_page_url_format_re.search(archive_page_raw_html)
    if code_line is not None:
        code_line = code_line.group(0)
        code_line = settings['BEFORE_NEXT_PAGE_URL_RE'].sub(settings['before_next_page_url_repl'], code_line)
        code_line = settings['AFTER_NEXT_PAGE_URL_RE'].sub(settings['after_next_page_url_repl'], code_line)
        code_line = html_unescape(code_line)
    return code_line


# TODO: This stays here or goes to NewsArchiveCrawler as it can be perfectly parametrized? Or bettersuits
#  the config level?
def find_next_page_url(raw_html, settings, archive_page_url_base, article_urls, page_num, known_article_urls):
    """
        The next URL can be determined by various conditions (no matter how the pages are grouped):
            1) If there is a "next page" link, find it with REs and use that
            2) If there is "infinite scrolling" use pagenum from base to specified maximum or to infinity
            3) If there is no pagination return None
    """
    max_pagenum = settings['max_pagenum']
    next_page_url = None  # Method #1: No pagination

    if settings['next_url_by_regex']:  # Method #2: Use regex to follow the link to the next page
        next_page_url = extract_next_page_url(raw_html, settings)
    elif settings['next_url_by_pagenum']:
        if settings['infinite_scrolling'] and len(article_urls) > 0:  # Method #3: No link, but infinite scrolling!
            next_page_url = archive_page_url_base.replace('#pagenum', str(page_num))  # must generate URL
        elif max_pagenum is not None or page_num < max_pagenum:  # Method #4: Has predefined max_pagenum!
            next_page_url = archive_page_url_base.replace('#pagenum', str(page_num))  # must generate URL
        # Method #5: Global pages, active archive -> We allow intersecting elements as the archive may have been moved
        # Method #6: Inactive archive, no max_pagenum, no infinite_scrolling, no next_url_by_regex -> threshold == 0
        elif settings['new_article_url_threshold'] is not None and \
                (len(known_article_urls) == 0 or len(article_urls.minus(known_article_urls)) >
                 settings['new_article_url_threshold']):
            next_page_url = archive_page_url_base.replace('#pagenum', str(page_num))  # must generate URL

    return next_page_url


def identify_site_scheme(logger_, settings, url):
    for site_re, tag_key_readable in settings['TAGS_KEYS'].items():
        if site_re.search(url):
            return tag_key_readable

    logger_.log('ERROR', '\t'.join((url, str([regexp.pattern for regexp in settings['TAGS_KEYS'].keys()]),
                                    'NO MATCHING TAG_KEYS PATTERN! IGNORING ARTICLE!')))
    return None
