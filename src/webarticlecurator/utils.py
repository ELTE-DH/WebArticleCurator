#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import sys
import importlib.util
from pathlib import Path
from argparse import Namespace
from contextlib import contextmanager
from datetime import datetime, date, timedelta

import yamale

site_schema = yamale.make_schema(Path(__file__).absolute().parent / 'site_schema.yaml')
crawl_schema = yamale.make_schema(Path(__file__).absolute().parent / 'crawl_schema.yaml')


def load_and_validate(schema, fname):
    data = yamale.make_data(fname)
    try:
        yamale.validate(schema, data)  # strict=True
    except yamale.YamaleError as e:
        for result in e.results:
            print(f'Error validating data {result.data} with {result.schema}:', file=sys.stderr)
            for error in result.errors:
                print('', error, sep='\t', file=sys.stderr)
        exit(1)
    return data[0][0]


def import_python_file(file_path, package=None):
    """Import module from file:
       https://stackoverflow.com/questions/2349991/how-to-import-other-python-files/55892361#55892361"""
    abs_file_path = Path(file_path).absolute()
    pathname, filename = abs_file_path.parent, abs_file_path.name
    sys.path.append(str(pathname))
    modname = Path(filename).stem
    module = importlib.import_module(modname, package)
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
    settings['DIR_NAME'] = Path(current_task_config_filename).absolute().parent

    # Technical data about the website to crawl
    site_schema_fname = Path(settings['DIR_NAME']) / settings['schema']
    settings['SITE_SCHEMA_DIR_NAME'] = Path(site_schema_fname).absolute().parent
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
                raise ValueError(f'DateError: DATE_FROM ({column_settings["DATE_FROM"]}) <='
                                 f' DATE UNTIL ({column_settings["DATE_UNTIL"]}) < date.today() ({date.today()}) is not'
                                 f' satisfiable! Please check date_from ({settings["date_from"]}),'
                                 f' date_until ({settings["date_until"]}),'
                                 f' date_first_article ({column_settings["date_first_article"]})'
                                 f' and date_last_article ({column_settings["date_last_article"]})!')

        min_pagenum = column_settings.get('min_pagenum', -1)  # Can not normally be -1!
        initial_pagenum = column_settings.get('initial_pagenum', '')
        max_pagenum = column_settings.get('max_pagenum')

        if settings['next_url_by_pagenum']:
            if 'min_pagenum' not in column_settings and 'max_pagenum' not in column_settings and \
                    'initial_pagenum' in column_settings:
                # One page column: min_pagenum and max_pagenum are not set, but initial_pagenum is
                # so max < min and exit immediately
                min_pagenum = 2
                max_pagenum = 1
            elif 'min_pagenum' in column_settings and 'max_pagenum' not in column_settings and \
                    (not isinstance(initial_pagenum, int) or min_pagenum == initial_pagenum + 1):
                # Go from  min_pagenum (with initial_pagenum) until there are articles extracted:
                # if initial_pagenum is integer and min pagenum == initial_pagenum + 1 and no max_pagenum is set
                pass
            elif 'min_pagenum' in column_settings and 'max_pagenum' in column_settings and \
                    (not isinstance(initial_pagenum, int) or min_pagenum == initial_pagenum + 1) and \
                    (isinstance(max_pagenum, int) and min_pagenum <= max_pagenum):
                # Go from min_pagenum (with initial_pagenum) to max_pagenum:
                # If initial_pagenum and max_pagenum are integers,
                # initial_pagenum + 1 == min_pagenum <= max_pagenum must be satisfied!
                pass
            else:
                raise ValueError('PagenumError: if next_url_by_pagenum is set one of the following must be satisfied:'
                                 ' a) One page column: initial_pagenum is set, min and max pagenum are omitted.'
                                 ' b) No defined max_pagenum for column: min_pagenum is set and max_pagenum is omitted.'
                                 ' c) Pagenum interval for column: min_pagenum and max_pagenum is defined.'
                                 ' initial_pagenum can be any string and for (b) and (c) is optional.'
                                 ' For integer values: initial_pagenum + 1 == min_pagenum <= max_pagenum must hold!')

        # If initial_pagenum is implicit, then it will be substituted with empty string. e.g. in &page=
        column_settings['INITIAL_PAGENUM'] = str(initial_pagenum)
        column_settings['min_pagenum'] = min_pagenum
        column_settings['max_pagenum'] = max_pagenum

    settings['new_article_url_threshold'] = settings.get('new_article_url_threshold')

    # Portal specific functions
    file_path = settings['portal_specific_exctractor_functions_file']
    module = import_python_file(Path(settings['SITE_SCHEMA_DIR_NAME']) / file_path, 'webarticlecurator')
    for attr_name, attr_name_dest, mandatory in \
            (('extract_next_page_url_fun', 'EXTRACT_NEXT_PAGE_URL_FUN', False),
             ('extract_article_urls_from_page_fun', 'EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN', True),
             ('extract_article_urls_from_page_plus_fun', 'EXTRACT_ARTICLE_URLS_FROM_PAGE_PLUS_FUN', False),
             ('next_page_of_article_fun', 'NEXT_PAGE_OF_ARTICLE_FUN', False)):
        settings[attr_name_dest] = getattr(module, settings.get(attr_name, ''), None)
        if mandatory and settings[attr_name_dest] is None:
            raise ValueError(f'{attr_name} is unset!')
        elif settings.get(attr_name, None) is not None and settings[attr_name_dest] is None:
            raise ValueError(f'Cannot find python function for {attr_name}'
                             f' with value \'{settings.get(attr_name, None)}\' !')

    settings.setdefault('stop_on_empty_archive_page', False)
    if settings.setdefault('stop_on_taboo_set', False):
        taboo_urls = set()
        if isinstance(settings.get('taboo_article_urls', []), list):
            for url in settings.get('taboo_article_urls', []):
                taboo_urls.add(url)
        if len(taboo_urls) > 0:
            settings['TABOO_ARTICLE_URLS'] = taboo_urls
        else:
            raise ValueError('If stop_on_taboo_set is true, taboo_article_urls must be list of URLs!')
    else:
        settings['TABOO_ARTICLE_URLS'] = set()

    if settings['infinite_scrolling']:
        if not settings['next_url_by_pagenum']:
            raise ValueError('If infinite_scrolling is true, next_url_by_pagenum must be also true!')
        if settings['EXTRACT_NEXT_PAGE_URL_FUN'] is not None:
            raise ValueError('If infinite_scrolling is true, extract_next_page_url_fun must be None!')
        if settings['stop_on_empty_archive_page']:
            raise ValueError('If infinite_scrolling is true, stop_on_empty_archive_page must not be true!')

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
            raise ValueError(f'corpus_converter is {corp_conv}, but {file_path} is unset!')
        module = import_python_file(Path(settings['SITE_SCHEMA_DIR_NAME']) / file_path, 'webarticlecurator')
        corpus_converter_class = getattr(module, corp_conv)
    settings['CORPUS_CONVERTER'] = corpus_converter_class(settings)

    return settings


def write_content_to_url_named_file(url, cont, out_dir):
    out_dir = Path(out_dir)
    safe_url = ''.join(char if char.isalnum() else '_' for char in url).rstrip('_')[:200]
    i, fname = 0, out_dir / f'{safe_url}_0.html'
    while fname.exists():
        i += 1
        fname = out_dir / f'{safe_url}_{i}.html'
    with open(fname, 'w', encoding='UTF-8') as fh:
        fh.write(cont)

    return fname


def create_or_check_clean_dir(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if next(out_dir.iterdir(), None) is not None:
        print(f'Supplied output directory ({out_dir}) is not empty!', file=sys.stderr)
        exit(1)


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


@contextmanager
def write_set_contents_to_file(set_instance, fname=None):
    fh = None
    if fname is not None:
        fh = open(fname, 'w', encoding='UTF-8')  # To store FH (for closing it)

    def _add_fun(elem: str):
        set_instance.add(elem)
        print(elem, file=fh, flush=True)

    try:
        yield _add_fun
    finally:
        if fh is not None:
            fh.close()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        wrap_input_constants(sys.argv[1])
        print(f'Config {sys.argv[1]} OK!')
