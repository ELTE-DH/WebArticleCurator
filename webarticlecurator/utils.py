#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import sys
import importlib.util
from argparse import Namespace
from datetime import datetime, date, timedelta

import yamale

site_schema = yamale.make_schema(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site_schema.yaml'))
crawl_schema = yamale.make_schema(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawl_schema.yaml'))


def load_and_validate(schema, fname):
    data = yamale.make_data(fname)
    try:
        yamale.validate(schema, data, strict=True)
    except yamale.YamaleError as e:
        for result in e.results:
            print('Error validating data {0} with {1}:'.format(result.data, result.schema), file=sys.stderr)
            for error in result.errors:
                print('', error, sep='\t', file=sys.stderr)
        exit(1)
    return data[0][0]


def import_python_file(module_name, file_path):
    # Import module from file: https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def wrap_input_constants(current_task_config_filename):
    """
        Helper to store and process input data so that main function does not contain so many
         codelines of variable initialization
        Fields should be handled as constants after initialization
         CAPITALIZED KEYS are transformed runtime (e.g. Regular Expressions),
         lowercase keys are present in the config and will be used as is
    """
    # Instructions to the current task
    settings = load_and_validate(crawl_schema, current_task_config_filename)

    # The directory name of the configs
    settings['DIR_NAME'] = os.path.dirname(os.path.abspath(current_task_config_filename))

    # Technical data about the website to crawl
    site_schema_fname = os.path.join(settings['DIR_NAME'], settings['schema'])
    settings['SITE_SCHEMA_DIR_NAME'] = os.path.dirname(os.path.abspath(site_schema_fname))
    current_site_schema = load_and_validate(site_schema, site_schema_fname)
    settings.update(current_site_schema)

    # Date filtering ON in any other cases OFF
    settings['FILTER_ARTICLES_BY_DATE'] = 'date_from' in settings and 'date_until' in settings

    for column in settings['columns'].keys():
        column_settings = settings['columns'][column]
        # We use the supplied dates (None != date_first_article <= date_from <= date_until < today (or raise exception))
        # to generate all URLs from the first day to the last one-by-one
        if 'date_from' in settings:
            column_settings['DATE_FROM'] = settings['date_from']
        elif 'date_first_article' in column_settings:
            column_settings['DATE_FROM'] = column_settings['date_first_article']

        if 'date_until' in settings:
            column_settings['DATE_UNTIL'] = settings['date_until']
        elif'date_last_article' in column_settings:
            column_settings['DATE_UNTIL'] = column_settings['date_last_article']
        else:
            column_settings['DATE_UNTIL'] = date.today() - timedelta(1)  # yesterday

        if settings['FILTER_ARTICLES_BY_DATE'] or settings['archive_page_urls_by_date']:
            if 'DATE_FROM' not in column_settings:
                raise ValueError('DateError: date_first_article and date_from is not set please'
                                 ' set at least one of them!')
            if not (column_settings['DATE_FROM'] <= column_settings['DATE_UNTIL'] < date.today()):
                raise ValueError('DateError: DATE_FROM ({0}) <= DATE UNTIL ({1}) < date.doday() ({2}) is not'
                                 ' satisfiable! Please check date_from ({3}), date_until ({4}),'
                                 ' date_first_article ({5}) and date_last_article ({6})!'.
                                 format(column_settings['DATE_FROM'], column_settings['DATE_UNTIL'], date.today(),
                                        settings['date_from'], settings['date_until'],
                                        column_settings['date_first_article'], column_settings['date_last_article']))

        min_pagenum = column_settings.get('min_pagenum', -1)  # Can not normally be -1!
        initial_pagenum = column_settings.get('initial_pagenum', '')
        max_pagenum = column_settings.get('max_pagenum')

        if settings['next_url_by_pagenum']:
            # If column consists of only one page, min_pagenum and max_pagenum must be omited
            # while initial_pagenum must be set
            if 'min_pagenum' not in column_settings:
                if 'max_pagenum' in column_settings or 'initial_pagenum' not in column_settings:
                    raise ValueError('min_pagenum can be omited iff max_pagenum is not present'
                                     ' and initial_pagenum is set, when next_url_by_pagenum is true!')
                else:  # min_pagenum and max_pagenum are not set, but initial_pagenum is. -> One page column!
                    min_pagenum = 2  # so max < min and exit immediately
                    max_pagenum = 1
            else:
                # If initial_pagenum is explicitly set as int and min_pagenum is set,
                #  initial_pagenum + 1 == min_pagenum <= max_pagenum must be satisfied!
                if ((isinstance(initial_pagenum, int) and min_pagenum != initial_pagenum + 1) or
                   (isinstance(max_pagenum, int) and min_pagenum > max_pagenum)):
                    raise ValueError('If two or more from initial_pagenum, min_pagenum and max_pagenum are set,'
                                     ' initial_pagenum + 1 == min_pagenum <= max_pagenum must be satisfied!')

        # If initial_pagenum is implicit, then it will be substituted with empty string. e.g. in &page=
        column_settings['INITIAL_PAGENUM'] = str(initial_pagenum)
        column_settings['min_pagenum'] = min_pagenum
        column_settings['max_pagenum'] = max_pagenum

    settings['new_article_url_threshold'] = settings.get('new_article_url_threshold')

    # Portal specific functions
    file_path = settings['portal_specific_exctractor_functions_file']
    module = import_python_file('portal_specific_exctractor_functions',
                                os.path.join(settings['SITE_SCHEMA_DIR_NAME'], file_path))
    for attr_name, attr_name_dest, mandatory in \
            (('extract_next_page_url_fun', 'EXTRACT_NEXT_PAGE_URL_FUN', False),
             ('extract_article_urls_from_page_fun', 'EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN', True),
             ('next_page_of_article_fun', 'NEXT_PAGE_OF_ARTICLE_FUN', False)):
        settings[attr_name_dest] = getattr(module, settings.get(attr_name, ''), None)
        if mandatory and settings[attr_name_dest] is None:
            raise ValueError('{0} is unset!'.format(attr_name))

    if settings['infinite_scrolling']:
        if not settings['next_url_by_pagenum']:
            raise ValueError('If infinite_scrolling is true, next_url_by_pagenum must be also true!')
        if settings['EXTRACT_NEXT_PAGE_URL_FUN'] is not None:
            raise ValueError('If infinite_scrolling is true, extract_next_page_url_fun must be None!')

    # Set and init converter class which is dummy-converter by default
    corp_conv = settings.get('corpus_converter', 'dummy-converter')
    if corp_conv == 'dummy-converter':
        if settings['NEXT_PAGE_OF_ARTICLE_FUN'] is not None:
            raise ValueError('If next_page_of_article_fun is supplied corpus_converter cannot be dummy-converter!')
        corpus_converter_class = DummyConverter
        if settings['FILTER_ARTICLES_BY_DATE'] and not settings['archive_page_urls_by_date']:
            raise ValueError('Date filtering is not possible with DummyConverter with a non-date-based archive!')
        settings['FILTER_ARTICLES_BY_DATE'] = False  # Use the archive dates for filtering...
    else:
        file_path = settings['corpus_converter_file']
        if file_path is None:
            raise ValueError('corpus_converter is {0}, but {1} is unset!'.format(corp_conv, file_path))
        module = import_python_file('corpus_converter', os.path.join(settings['SITE_SCHEMA_DIR_NAME'], file_path))
        corpus_converter_class = getattr(module, corp_conv)
    settings['CORPUS_CONVERTER'] = corpus_converter_class(settings)

    return settings


class DummyConverter:  # No output corpus
    """
        An example converter to showcase API and to suppress any article processing at crawling time (for new portals)
    """

    def __init__(self, settings):
        self._logger = Namespace(log=print)  # Hack to be able to monkeypatch logger
        # Override this if needed!
        if settings['FILTER_ARTICLES_BY_DATE'] and not settings['archive_page_urls_by_date']:
            raise ValueError(f'Date filtering is not possible with {type(self).__name__} on a non-date-based archive!')
        settings['FILTER_ARTICLES_BY_DATE'] = False  # Use the archive dates for filtering...
        # Init stuff
        _ = settings  # Silence IDE

    @staticmethod
    def identify_site_scheme(url, article_raw_html):
        _ = url, article_raw_html  # Silence IDE

    @staticmethod
    def extract_article_date(url, article_raw_html, scheme):
        """ extracts and returns next page URL from an HTML code if there is one... """
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        return datetime.today().date()

    @staticmethod
    def article_to_corpus(url, article_raw_html, scheme):
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        pass

    @staticmethod
    def follow_links_on_page(url, article_raw_html, scheme):
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        return set()

    def __del__(self):
        pass


if __name__ == '__main__':
    if len(sys.argv) == 2:
        wrap_input_constants(sys.argv[1])
        print(f'Config {sys.argv[1]} OK!')
