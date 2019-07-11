#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from newspaper import Article


"""Here comes the stuff to extract data from a specific downloaded webpage (article)"""


class CorpusConverter:
    """
        Extract text and metadata from the downloaded raw html by using site specific REs from the config
    """
    def __init__(self, settings, file_out, logger_):
        self._settings = settings
        self._article_begin_mark = settings['COMMON_SITE_TAGS']['article_begin_mark']
        self._article_end_mark = settings['COMMON_SITE_TAGS']['article_end_mark']
        self._file_out = file_out
        self._logger_ = logger_

    def article_to_corpus(self, url, doc_in, site_tag_scheme):
        """
        converts the raw HTML code of an article to corpus format and saves it to the output file
        :param doc_in: the document to convert
        :param url: the URL. Not used here, just for logging
        :param site_tag_scheme: the identified scheme of the article to load the appropriate tags

        :return:
        """
        if site_tag_scheme is not None:
            site_tags = self._settings['SITE_TAGS'][site_tag_scheme]

            # Build the article in corpus format by sequentially adding elements described by open-close REs
            doc_out = ''.join(self._check_regex(json_tags_key_vals['open'],
                                                json_tags_key_vals['close'],
                                                json_tags_key_vals['open-inside-close'], t, doc_in)
                              for t, json_tags_key_vals in site_tags.items())

            # Apply general cleaning rules to remove unneeded parts
            for rule_name, rule in self._settings['GENERAL_CLEANING_RULES'].items():
                doc_out = rule(doc_out)

            # Write the result into the output file
            print(self._article_begin_mark, doc_out, self._article_end_mark, sep='', end='', file=self._file_out)
            self._logger_.log('INFO', '\t'.join((url, site_tag_scheme, 'Article extraction OK')))
        return

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


class CorpusConverterNewspaper:  # Mimic CorpusConverter
    def __init__(self, settings, file_out, logger_):
        self._file_out = file_out
        self._logger_ = logger_
        self._settings = settings

    def article_to_corpus(self, url, page_str, _):
        article = Article(url, memoize_articles=False, language='hu')
        article.download(input_html=page_str)
        article.parse()
        article.nlp()

        html_date = '<html-date> {0} </html-date>'.format(article.publish_date.date())
        html_description_lead = '<html-lead>\n </html-lead>'
        html_charset = '<html-charset> utf-8 </html-charset>'
        html_url = '<html-url> {0} </html-url>'.format(url)
        html_keywords = '<html-keywords> {0} </html-keywords>'.format(', '.join(article.keywords))
        html_title = '<html-title> {0} </html-title>'.format(article.title)
        html_body = '<html-body>\n{0} </html-body>\n'.format(article.text)

        print(self._settings['article_begin_flag'], '\n'.join((html_date,
                                                               html_description_lead,
                                                               html_charset,
                                                               html_url,
                                                               html_keywords,
                                                               html_title,
                                                               html_body)),
              self._settings['article_end_flag'], sep='', end='', file=self._file_out)
        self._logger_.log('INFO', '\t'.join((url, 'Article extraction OK')))
