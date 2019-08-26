#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import re
import sys
import yaml
import logging
from datetime import date, timedelta

from .corpus_converter import corpus_converter_class
import corpusbuilder.site_specific_extractor_functions as site_spec_extractor_functions


def wrap_input_consants(current_task_config_filename, args):
    """
        Helper to store and process input data so that main function does not contain so many
         codelines of variable initialization
        Fields should be handled as constants after initialization
         CAPITALIZED KEYS are transformed runtime (e.g. Regular Expressions),
         lowercase keys are present in the config and will be used as is
    """
    # Instructions to the current task
    with open(current_task_config_filename, encoding='UTF-8') as fh:
        settings = yaml.load(fh)

    # The directory name of the configs
    dir_name = os.path.dirname(os.path.abspath(current_task_config_filename))

    # Technical data about the website to crawl
    with open(os.path.join(dir_name, settings['site_schemas']), encoding='UTF-8') as fh:
        current_site_schema = yaml.load(fh)[settings['site_name']]

    # TODO: How to avoid key errors?
    # if len(settings.keys() & current_site_schema.keys()) > 0:
    #    raise KeyError('Config file key collision!')
    current_site_schema.update(settings)
    settings = current_site_schema  # Settings have higher priority over current_site_schema!

    settings['TAGS_KEYS'] = {re.compile(tag_key): val for tag_key, val in settings['tags_keys'].items()}

    # TODO: Curretnly disabled!
    # If the program is to create a corpus, then it will load the required tags and compile the REs
    if settings.get('create_corpus', False):
        with open(os.path.join(dir_name, settings['tags']), encoding='UTF-8') as fh:
            all_tags = yaml.load(fh)
            common_tags = all_tags['common']

        cleaning_rules = {}
        general_cleaning_rules = common_tags.pop('general_cleaning_rules', {})  # Also remove general rules from common!
        for rule, regex in ((rule, regex) for rule, regex in general_cleaning_rules.items()
                            if not rule.endswith('_repl')):
            r = re.compile(regex)
            cleaning_rules[rule] = lambda x: r.sub(general_cleaning_rules['{0}_repl'.format(rule)], x)

        site_tags = {}
        for tag_key_readable in settings['TAGS_KEYS'].values():
            site_tags[tag_key_readable] = {}
            if tag_key_readable is not None:  # None == Explicitly ignored
                for tag_name, tag_desc in all_tags[tag_key_readable].items():
                    site_tags[tag_key_readable][tag_name] = {}
                    site_tags[tag_key_readable][tag_name]['open-inside-close'] = re.compile('{0}{1}{2}'.
                                                                                            format(tag_desc['open'],
                                                                                                   tag_desc['inside'],
                                                                                                   tag_desc['close']))
                    site_tags[tag_key_readable][tag_name]['open'] = re.compile(tag_desc['open'])
                    site_tags[tag_key_readable][tag_name]['close'] = re.compile(tag_desc['close'])

    else:
        site_tags = {}
        common_tags = {'article_begin_mark': '', 'article_end_mark': ''}
        cleaning_rules = {}
    settings['SITE_TAGS'] = site_tags
    settings['COMMON_SITE_TAGS'] = common_tags
    settings['GENERAL_CLEANING_RULES'] = cleaning_rules

    # TODO: Under rearrangement!
    """
    site_schemas:

    "article_date_format": ""
    "before_article_date": ""
    "before_article_date_repl": ""
    "after_article_date": ""
    "after_article_date_repl": ""
    "article_date_formatting": "%Y.%m.%d."

    settings['BEFORE_ARTICLE_DATE_RE'] = re.compile(current_site_schema['before_article_date'])
    settings['AFTER_ARTICLE_DATE_RE'] = re.compile(current_site_schema['after_article_date'])
    settings['ARTICLE_DATE_FORMAT_RE'] = re.compile('{0}{1}{2}'.format(current_site_schema['before_article_date'],
                                                                       current_site_schema['article_date_format'],
                                                                       current_site_schema['after_article_date']))
    """

    # Date filtering ON in any other cases OFF
    settings['FILTER_ARTICLES_BY_DATE'] = 'date_from' in settings and 'date_until' in settings

    # We use the supplied dates (None != date_first_article <= date_from <= date_until < today (or raise exception))
    # to generate all URLs from the first day to the last one-by-one
    if 'date_from' in settings:
        settings['DATE_FROM'] = settings['date_from']
    elif 'date_first_article' in settings:
        settings['DATE_FROM'] = current_site_schema['date_first_article']

    if 'date_until' in settings:
        settings['DATE_UNTIL'] = settings['date_until']
    elif'date_last_article' in settings:
        settings['DATE_UNTIL'] = current_site_schema['date_last_article']
    else:
        settings['DATE_UNTIL'] = date.today() - timedelta(1)  # yesterday

    # Checks go here
    if 'date_from' in settings and not isinstance(settings['date_from'], date):
        raise ValueError('DateError: date_from not datetime ({0})!'.format(settings['date_from']))
    if 'date_first_article' in settings and not isinstance(current_site_schema['date_first_article'], date):
        raise ValueError('DateError: date_first_article not datetime ({0})!'.
                         format(current_site_schema['date_first_article']))

    if 'date_until' in settings and not isinstance(settings['date_until'], date):
        raise ValueError('DateError: date_until not datetime ({0})!'.format(settings['date_until']))
    if 'date_last_article' in settings and not isinstance(current_site_schema['date_last_article'], date):
        raise ValueError('DateError: date_last_article not datetime ({0})!'.
                         format(current_site_schema['date_last_article']))

    if settings['FILTER_ARTICLES_BY_DATE'] or settings['archive_page_urls_by_date']:
        if 'DATE_FROM' not in settings:
            raise ValueError('DateError: date_first_article and date_from is not set please set at least one of them!'.
                             format(current_site_schema['date_first_article']))
        if not (settings['DATE_FROM'] <= settings['DATE_UNTIL'] < date.today()):
            raise ValueError('DateError: DATE_FROM ({0}) <= DATE UNTIL ({1}) < date.doday() ({2}) is not satisfiable!'
                             ' Please check date_from ({3}), date_until ({4}), date_first_article ({5})'
                             ' and date_last_article ({6})!'.format(settings['DATE_FROM'], settings['DATE_UNTIL'],
                                                                    date.today(), settings['date_from'],
                                                                    settings['date_until'],
                                                                    settings['date_first_article'],
                                                                    settings['date_last_article']))

    # New problematic article URLs to be checked manually (dropped by default)
    new_problematic_urls = settings.get('new_problematic_urls')
    if new_problematic_urls is not None:
        settings['NEW_PROBLEMATIC_URLS_FH'] = open(new_problematic_urls, 'a+', encoding='UTF-8')
    else:
        settings['NEW_PROBLEMATIC_URLS_FH'] = None

    # New good artilce URLs downloaded and in the archive (dropped by default)
    new_good_urls = settings.get('new_good_urls')
    if new_good_urls is not None:
        settings['NEW_GOOD_URLS_FH'] = open(new_good_urls, 'a+', encoding='UTF-8')
    else:
        settings['NEW_PROBLEMATIC_URLS_FH'] = None

    # New problematic archive URLs to be checked manually (dropped by default)
    new_problematic_archive_urls = settings.get('new_problematic_archive_urls')
    if new_problematic_archive_urls is not None:
        settings['NEW_PROBLEMATIC_ARCHIVE_URLS_FH'] = open(new_problematic_archive_urls, 'w', encoding='UTF-8')
    else:
        settings['NEW_PROBLEMATIC_ARCHIVE_URLS_FH'] = None

    # New good archive URLs downloaded and in the archive (dropped by default)
    new_good_archive_urls = settings.get('new_good_archive_urls')
    if new_good_archive_urls is not None:
        settings['NEW_GOOD_ARCHIVE_URLS_FH'] = open(new_good_archive_urls, 'w', encoding='UTF-8')
    else:
        settings['NEW_GOOD_ARCHIVE_URLS_FH'] = None

    output_corpus = settings.get('output_corpus')
    if output_corpus is not None:
        settings['OUTPUT_CORPUS_FH'] = open(output_corpus, 'a+', encoding='UTF-8')
    elif not args.corpus:
        settings['OUTPUT_CORPUS_FH'] = None
    else:
        raise ValueError('output_corpus must be set for --corpus!')

    settings['CORPUS_CONVERTER'] = corpus_converter_class[settings['corpus_converter']]

    extract_next_page_url = settings['extract_next_page_url_fun']
    if extract_next_page_url is not None:
        extract_next_page_url_fun = getattr(site_spec_extractor_functions, settings['extract_next_page_url_fun'], None)
        if extract_next_page_url_fun is not None:
            settings['EXTRACT_NEXT_PAGE_URL_FUN'] = extract_next_page_url_fun
        else:
            raise ValueError('extract_next_page_url_fun is unset!')
    else:
        settings['EXTRACT_NEXT_PAGE_URL_FUN'] = None

    extract_article_urls_from_page_fun = getattr(site_spec_extractor_functions,
                                                 settings['extract_article_urls_from_page_fun'], None)
    if extract_article_urls_from_page_fun is not None:
        settings['EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN'] = extract_article_urls_from_page_fun
    else:
        raise ValueError('extract_article_urls_from_page_fun is unset!')

    new_article_url_threshold = settings.get('new_article_url_threshold')
    if new_article_url_threshold is not None:
        if not isinstance(new_article_url_threshold, int) or new_article_url_threshold < 0:
            raise ValueError('new_article_url_threshold should be int >= 0!')
    settings['NEW_ARTICLE_URL_THRESHOLD'] = new_article_url_threshold

    initial_pagenum = settings.get('initial_pagenum', '')
    if initial_pagenum != '':
        if not isinstance(initial_pagenum, int) or initial_pagenum < 0:
            raise ValueError('initial_pagenum should be int >= 0!')
        initial_pagenum = str(initial_pagenum)
    settings['INITIAL_PAGENUM'] = initial_pagenum

    max_pagenum = settings.get('max_pagenum')
    if max_pagenum is not None:
        if not isinstance(max_pagenum, int) or max_pagenum < 0:
            raise ValueError('max_pagenum should be int >= 0!')
    settings['MAX_PAGENUM'] = max_pagenum

    return settings


class Logger:
    """
        Handle logging with Python's built-in logging facilities simplified
    """
    def __init__(self, log_filename=None, console_level='INFO', console_stream=sys.stderr,
                 logfile_level='INFO', logfile_mode='a', logfile_encoding='UTF-8'):
        # logging.basicConfig(level=logging.INFO)
        log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR,
                      'CRITICAL': logging.CRITICAL}

        if console_level not in log_levels:
            raise KeyError('Console loglevel is not valid ({0}): {1}'.format(', '.join(log_levels.keys()),
                                                                             console_level))
        if logfile_level not in log_levels:
            raise KeyError('Logfile loglevel is not valid ({0}): {1}'.format(', '.join(log_levels.keys()),
                                                                             logfile_level))

        # Create logger
        self._logger = logging.getLogger(log_filename)  # Logger is named after the logfile
        self._logger.propagate = False

        # Create handler one for console output and one for logfile and set their properties accordingly
        c_handler = logging.StreamHandler(stream=console_stream)
        c_handler.setLevel(console_level)

        # Create formatters and add them to handlers
        c_format = logging.Formatter('{asctime} {levelname}: {message}', style='{')
        c_handler.setFormatter(c_format)

        # Add handlers to the logger
        self._logger.addHandler(c_handler)

        if log_filename is not None:
            f_handler = logging.FileHandler(log_filename, mode=logfile_mode, encoding=logfile_encoding)
            f_handler.setLevel(logfile_level)
            f_format = logging.Formatter('{asctime} {levelname}: {message}', style='{')
            f_handler.setFormatter(f_format)
            self._logger.addHandler(f_handler)

        if console_level < logfile_level:
            self._logger.setLevel(console_level)
        else:
            self._logger.setLevel(logfile_level)

        self._leveled_logger = {'DEBUG': self._logger.debug, 'INFO': self._logger.info, 'WARNING': self._logger.warning,
                                'ERROR': self._logger.error, 'CRITICAL': self._logger.critical}

        self.log('INFO', 'Logging started')

    def log(self, level, msg):
        if level in self._leveled_logger:
            self._leveled_logger[level](msg)
        else:
            self._leveled_logger['CRITICAL']('UNKNOWN LOGGING LEVEL SPECIFIED FOR THE NEXT ENTRY: {0}'.format(level))
            self._leveled_logger['CRITICAL'](msg)

    def __del__(self):
        handlers = list(self._logger.handlers)
        for h in handlers:
            self._logger.removeHandler(h)
            h.flush()
            if isinstance(h, logging.FileHandler):
                h.close()
