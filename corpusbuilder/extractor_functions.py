#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from html import unescape as html_unescape
from datetime import datetime

strptime = datetime.strptime

"""Here comes the stuff to extract data from a specific downloaded webpage (archive or article)
    These functions are separated to allow easy debuging!"""


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


def extract_article_date(settings, url, article_raw_html, scheme):
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


def identify_site_scheme(logger_, settings, url):
    for site_re, tag_key_readable in settings['TAGS_KEYS'].items():
        if site_re.search(url):
            return tag_key_readable

    logger_.log('ERROR', '\t'.join((url, str([regexp.pattern for regexp in settings['TAGS_KEYS'].keys()]),
                                    'NO MATCHING TAG_KEYS PATTERN! IGNORING ARTICLE!')))
    return None
