#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import re
import json
from datetime import date, timedelta

# TODO: More simplifications: regex keys should be suffixed with _RE and compiled automatically, bools with _BOOL,
#  etc. with dates to make this config wrapper more general


def wrap_input_consants(current_task_config_filename):
    """
        Helper to store and process input data so that main function does not contain so many
         codelines of variable initialization
        Its fields should be handled as constants after initialization
    """
    # # instructions to the current task
    current_task_config = json.load(open(current_task_config_filename, encoding='UTF-8'))

    settings = current_task_config

    # # technical data about the website to crawl
    dir_name = os.path.dirname(current_task_config_filename)
    site_schemas_filename = os.path.join(dir_name, settings['site_schemas'])
    current_site_schema = json.load(open(site_schemas_filename, encoding='UTF-8'))[settings['site']]
    if len(settings.keys() & current_site_schema.keys()) > 0:
        raise Exception('Config file key collision!')
    settings.update(current_site_schema)

    settings['BEFORE_ARTICLE_URL_RE'] = re.compile(current_site_schema['before_article_url'])
    settings['AFTER_ARTICLE_URL_RE'] = re.compile(current_site_schema['after_article_url'])
    settings['ARTICLE_LINK_FORMAT_RE'] = re.compile('{0}{1}{2}'.format(current_site_schema['before_article_url'],
                                                                       current_site_schema['article_url_format'],
                                                                       current_site_schema['after_article_url']))

    settings['ARTICLE_LIST_URLS_BY_DATE'] = bool(current_site_schema['article_list_urls_by_date'])#############################!!!!!!!!!!!!!!!!!!!!!!!!!
    settings['ARTICLE_LIST_URLS_BY_ID'] = bool(current_site_schema['article_list_urls_by_id'])

    try:
        settings['DATE_INTERVAL_USED'] = True
        settings['DATE_FROM'] = date(current_task_config['year_from'], current_task_config['month_from'],
                                     current_task_config['day_from'])
        settings['DATE_UNTIL'] = date(current_task_config['year_until'], current_task_config['month_until'],
                                      current_task_config['day_until'])
        settings['INTERVAL'] = settings['DATE_UNTIL'] - settings['DATE_FROM']
        if settings['DATE_FROM'] > settings['DATE_UNTIL']:
            raise Exception('DateError: DATE_FROM is later than DATE UNTIL!')
    except ValueError:
        # if there is no time filtering
        settings['DATE_INTERVAL_USED'] = False
        # then we use dates only if they are needed to generate URLs
        if settings['ARTICLE_LIST_URLS_BY_DATE']:
            # we generate all URLs from the first day of website until yesterday
            # date of the first article
            settings['DATE_FROM'] = date(current_site_schema['first_article_year'],
                                         current_site_schema['first_article_month'],
                                         current_site_schema['first_article_day'])
            # yesterday
            settings['DATE_UNTIL'] = date.today() - timedelta(1)
            settings['INTERVAL'] = settings['DATE_UNTIL'] - settings['DATE_FROM']

    settings['URL_PATTERN'] = re.compile('(https?://)?(www.)?([^/]+\.)(\w+/|$)(.*)')
    return settings
