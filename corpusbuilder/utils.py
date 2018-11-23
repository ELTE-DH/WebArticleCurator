#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-
import datetime
import os
import re
import json
import sys
from datetime import date, timedelta, datetime


def wrap_input_consants(current_task_config_filename):
    """
        Helper to store and process input data so that main function does not contain so many
         codelines of variable initialization
        Its fields should be handled as constants after initialization
        CAPITALIZED KEYS are transformed (eg. to Date(), Bool(), etc.) or created runtime,
         lowercase keys are present in the config and will be used as is
    """
    # Instructions to the current task
    settings = json.load(open(current_task_config_filename, encoding='UTF-8'))

    # Technical data about the website to crawl
    dir_name = os.path.dirname(current_task_config_filename)
    site_schemas_filename = os.path.join(dir_name, settings['site_schemas'])
    settings['dir_name'] = dir_name
    current_site_schema = json.load(open(site_schemas_filename, encoding='UTF-8'))[settings['site']]
    if len(settings.keys() & current_site_schema.keys()) > 0:
        raise KeyError('Config file key collision!')
    settings.update(current_site_schema)

    settings['BEFORE_ARTICLE_URL_RE'] = re.compile(current_site_schema['before_article_url'])
    settings['AFTER_ARTICLE_URL_RE'] = re.compile(current_site_schema['after_article_url'])
    settings['ARTICLE_LINK_FORMAT_RE'] = re.compile('{0}{1}{2}'.format(current_site_schema['before_article_url'],
                                                                       current_site_schema['article_url_format'],
                                                                       current_site_schema['after_article_url']))

    settings['BEFORE_NEXT_PAGE_URL_RE'] = re.compile(current_site_schema['before_next_page_url'])
    settings['AFTER_NEXT_PAGE_URL_RE'] = re.compile(current_site_schema['after_next_page_url'])
    settings['ARCHIVE_NEXT_PAGE_FORMAT_RE'] = re.compile('{0}{1}{2}'.format(current_site_schema['before_next_page_url'],
                                                                            current_site_schema['archive_next_page_'
                                                                                                'format'],
                                                                            current_site_schema['after_next_page_url']))

    settings['ARTICLE_LIST_URLS_BY_DATE'] = bool(current_site_schema['bool_article_list_urls_by_date'])
    settings['ARTICLE_LIST_URLS_BY_ID'] = bool(current_site_schema['bool_article_list_urls_by_id'])
    settings['DATE_INTERVAL_USED'] = bool(settings['bool_date_interval_used'])
    settings['NEXT_URL_BY_REGEX'] = bool(settings['bool_next_url_by_regex'])
    settings['GO_REVERSE_IN_ARCHIVE'] = bool(settings['bool_go_reverse_in_archive'])
    settings['CREATE_CORPUS'] = bool(settings['bool_create_corpus'])

    if settings['DATE_INTERVAL_USED']:
        # We generate all URLs FROM the past UNTIL the "not so past"
        # Raises ValueError if there is something wrong
        settings['DATE_FROM'] = datetime.strptime(settings['date_from'], '%Y-%m-%d').date()
        settings['DATE_UNTIL'] = datetime.strptime(settings['date_until'], '%Y-%m-%d').date()

        if settings['DATE_FROM'] > settings['DATE_UNTIL']:
            raise ValueError('DateError: DATE_FROM is later than DATE UNTIL!')
        settings['INTERVAL'] = settings['DATE_UNTIL'] - settings['DATE_FROM']

    # if there is no time filtering then we use dates only if they are needed to generate URLs
    elif settings['ARTICLE_LIST_URLS_BY_DATE']:
        # We generate all URLs from the first day of the website until yesterday
        settings['DATE_FROM'] = datetime.strptime(settings['date_first_article'], '%Y-%m-%d').date()
        settings['DATE_UNTIL'] = date.today() - timedelta(1)  # yesterday

        if settings['DATE_FROM'] > settings['DATE_UNTIL']:
            raise ValueError('DateError: DATE_FROM is later than DATE UNTIL!')
        settings['INTERVAL'] = settings['DATE_UNTIL'] - settings['DATE_FROM']

    # settings['URL_PATTERN'] = re.compile('(https?://)?(www.)?([^/]+\.)(\w+/|$)(.*)')
    return settings


class Logger:
    """
        handles log file
        writes out log messages
        checks in log file if the current article is processed already
    """
    def __init__(self, log_filename):
        self.file_log = open(log_filename, 'w+', encoding='UTF-8')

        if os.stat(log_filename).st_size == 0:
            print('TIME;URL;LOG MESSAGE', file=self.file_log, flush=True)
        self.log('', 'Logging started')

    def log(self, url, msg):
        if len(url) == 0:
            print(msg, file=sys.stderr, flush=True)
        else:
            print(url, msg, sep=';', file=sys.stderr, flush=True)
        print(datetime.now(), url, msg, sep=';', file=self.file_log, flush=True)

    def __del__(self):
        if hasattr(self, 'file_log'):
            self.log('', 'Logging finished')
            self.file_log.close()
