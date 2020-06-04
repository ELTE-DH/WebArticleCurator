#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import re
import sys
from datetime import datetime
from collections import defaultdict
from argparse import Namespace

import yaml
from newspaper import Article

"""Here comes the stuff to extract data from a specific downloaded webpage (article)"""


class DummyConverter:  # No output corpus
    def __init__(self, settings):
        self._logger = Namespace(log=print)  # Hack to be able to monkeypatch logger
        # Init stuff
        _ = settings  # Silence IDE

    @staticmethod
    def identify_site_scheme(url, article_raw_html):
        _ = url, article_raw_html  # Silence IDE

    @staticmethod
    def extract_article_date(url, article_raw_html, scheme):
        """
            extracts and returns next page URL from an HTML code if there is one...
        """
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        return datetime.today()

    @staticmethod
    def article_to_corpus(url, article_raw_html, scheme):
        _ = url, article_raw_html, scheme  # Silence dummy IDE
        pass

    def __del__(self):
        pass


class CorpusConverter:
    """
        Extract text and metadata from the downloaded raw html by using site specific REs from the config
    """
    def __init__(self, settings):
        self._logger = Namespace(log=print)  # Hack to be able to monkeypatch logger

        # Read tag_keys
        self._tags_keys = {re.compile(tag_key): val for tag_key, val in settings['tags_keys'].items()}

        # Set output_file handle
        self._file_out = open(settings['output_corpus'], 'a+', encoding='UTF-8')

        # Load the required tags and compile the REs
        with open(os.path.join(settings['DIR_NAME'], settings['tags']), encoding='UTF-8') as fh:
            all_tags = yaml.load(fh)

        common_tags = all_tags['common']
        self._article_begin_mark = common_tags['article_begin_mark']
        self._article_end_mark = common_tags['article_end_mark']

        self._cleaning_rules = {}
        # Also remove general rules from common!
        general_cleaning_rules = common_tags.pop('general_cleaning_rules', {})
        for rule, regex in ((rule, regex) for rule, regex in general_cleaning_rules.items()
                            if not rule.endswith('_repl')):
            r = re.compile(regex)
            self._cleaning_rules[rule] = lambda x: r.sub(general_cleaning_rules['{0}_repl'.format(rule)], x)

        self._site_tags = defaultdict(dict)
        for tag_key_readable in self._tags_keys.values():
            if tag_key_readable is not None:  # None == Explicitly ignored
                for tag_name, tag_desc in all_tags[tag_key_readable].items():
                    self._site_tags[tag_key_readable][tag_name] = {}
                    self._site_tags[tag_key_readable][tag_name]['open-inside-close'] = \
                        re.compile('{0}{1}{2}'.format(tag_desc['open'],
                                                      tag_desc['inside'],
                                                      tag_desc['close']))
                    self._site_tags[tag_key_readable][tag_name]['open'] = re.compile(tag_desc['open'])
                    self._site_tags[tag_key_readable][tag_name]['close'] = re.compile(tag_desc['close'])

        """
        site_schemas:

        "article_date_format": ""
        "before_article_date": ""
        "before_article_date_repl": ""
        "after_article_date": ""
        "after_article_date_repl": ""
        "article_date_formatting": "%Y.%m.%d."
        """
        self._date_settings = {'article_date_format': settings['article_date_format'],
                               'before_article_date': settings['before_article_date'],
                               'before_article_date_repl': settings['before_article_date_repl'],
                               'after_article_date': settings['after_article_date'],
                               'after_article_date_repl': settings['after_article_date_repl'],
                               'article_date_formatting': settings['article_date_formatting'],  # "%Y.%m.%d."
                               'BEFORE_ARTICLE_DATE_RE': re.compile(settings['before_article_date']),
                               'AFTER_ARTICLE_DATE_RE': re.compile(settings['after_article_date']),
                               'ARTICLE_DATE_FORMAT_RE': re.compile('{0}{1}{2}'.
                                                                    format(settings['before_article_date'],
                                                                           settings['article_date_format'],
                                                                           settings['after_article_date']))
                               }

    def identify_site_scheme(self, url, article_raw_html):
        _ = article_raw_html  # Silence IDE
        for site_re, tag_key_readable in self._tags_keys.items():
            if site_re.search(url):
                return tag_key_readable

        self._logger.log('ERROR', url, {regexp.pattern for regexp in self._tags_keys.keys()},
                         'NO MATCHING TAG_KEYS PATTERN! IGNORING ARTICLE!', sep='\t', file=sys.stderr)
        return None

    def extract_article_date(self, url, article_raw_html, scheme):
        """
            extracts and returns next page URL from an HTML code if there is one...
        """
        _ = url, scheme  # Silence dummy IDE
        code_line = self._date_settings['ARTICLE_DATE_FORMAT_RE'].search(article_raw_html)
        if code_line is not None:
            code_line = code_line.group(0)
            code_line = self._date_settings['BEFORE_ARTICLE_DATE_RE']. \
                sub(self._date_settings['before_article_date_repl'], code_line)
            code_line = self._date_settings['AFTER_ARTICLE_DATE_RE']. \
                sub(self._date_settings['after_article_date_repl'], code_line)
            try:
                code_line = datetime.strptime(code_line, self._date_settings['article_date_formatting']).date()
            except (UnicodeError, ValueError, KeyError):  # In case of any error log outside of this function...
                code_line = None
        return code_line

    def article_to_corpus(self, url, article_raw_html, scheme):
        """
        converts the raw HTML code of an article to corpus format and saves it to the output file
        :param article_raw_html: the document to convert
        :param url: the URL. Not used here, just for logging
        :param scheme: the identified scheme of the article to load the appropriate tags

        :return:
        """
        if scheme is not None and scheme in self._site_tags:
            site_tags = self._site_tags[scheme]

            # Build the article in corpus format by sequentially adding elements described by open-close REs
            doc_out = ''.join(self._check_regex(json_tags_key_vals['open'],
                                                json_tags_key_vals['close'],
                                                json_tags_key_vals['open-inside-close'], t, article_raw_html)
                              for t, json_tags_key_vals in site_tags.items())

            # Apply general cleaning rules to remove unneeded parts
            for rule_name, rule in self._cleaning_rules.items():
                doc_out = rule(doc_out)

            # Write the result into the output file
            print(self._article_begin_mark, doc_out, self._article_end_mark, sep='', end='', file=self._file_out)
            self._logger.log('INFO', url, scheme, 'Article extraction OK', sep='\t', file=sys.stderr)
        else:
            self._logger.log('ERROR', url, scheme, 'Scheme could not be identified!', sep='\t', file=sys.stderr)

    @staticmethod
    def _check_regex(old_tag_open, old_tag_close, old_tag, new_tag, doc_in):
        """
            keeps parts of input file that match patterns specified in JSON and
            then changes their HTML/CSS tags to our corpus markup tags
        """
        match = old_tag.search(doc_in)
        matched_part = ''
        if match is not None:
            matched_part = match.group(0)
            matched_part = old_tag_open.sub('<'+new_tag+'>\n', matched_part)
            matched_part = old_tag_close.sub(' </'+new_tag+'>\n', matched_part)
        return matched_part

    def __del__(self):
        if hasattr(self, '_file_out') and self._file_out is not None:
            self._file_out.close()


class CorpusConverterNewspaper:  # Mimic CorpusConverter
    def __init__(self, settings):
        self._logger = Namespace(log=print)  # Hack to be able to monkeypatch logger

        # Read tag_keys
        self._tags_keys = {re.compile(tag_key): val for tag_key, val in settings['tags_keys'].items()}

        # Set output_file handle
        self._file_out = open(settings['output_corpus'], 'a+', encoding='UTF-8')

        self._article_begin_mark = settings['article_begin_mark']
        self._article_end_mark = settings['article_end_mark']

    def identify_site_scheme(self, url, article_raw_html):
        _ = article_raw_html  # Silence IDE
        for site_re, tag_key_readable in self._tags_keys.items():
            if site_re.search(url):
                return tag_key_readable

        self._logger.log('ERROR', url, {regexp.pattern for regexp in self._tags_keys.keys()},
                         'NO MATCHING TAG_KEYS PATTERN! IGNORING ARTICLE!', sep='\t', file=sys.stderr)
        return None

    @staticmethod
    def extract_article_date(url, article_raw_html, scheme):
        """
            extracts and returns next page URL from an HTML code if there is one...
        """
        _ = url, scheme  # Silence dummy IDE
        article = Article(url, memoize_articles=False, language='hu')
        article.download(input_html=article_raw_html)
        article.parse()
        article.nlp()

        return article.publish_date.date()

    def article_to_corpus(self, url, article_raw_html, scheme):
        _ = scheme  # Silence dummy IDE
        article = Article(url, memoize_articles=False, language='hu')
        article.download(input_html=article_raw_html)
        article.parse()
        article.nlp()

        html_date = '<html-date> {0} </html-date>'.format(article.publish_date.date())
        html_description_lead = '<html-lead>\n </html-lead>'
        html_charset = '<html-charset> utf-8 </html-charset>'
        html_url = '<html-url> {0} </html-url>'.format(url)
        html_keywords = '<html-keywords> {0} </html-keywords>'.format(', '.join(article.keywords))
        html_title = '<html-title> {0} </html-title>'.format(article.title)
        html_body = '<html-body>\n{0} </html-body>\n'.format(article.text)

        print(self._article_begin_mark, '\n'.join((html_date, html_description_lead, html_charset, html_url,
                                                   html_keywords, html_title, html_body)),
              self._article_end_mark, sep='', end='', file=self._file_out)
        self._logger.log('INFO', url, 'Article extraction OK', sep='\t', file=sys.stderr)

    def __del__(self):
        if hasattr(self, '_file_out') and self._file_out is not None:
            self._file_out.close()
