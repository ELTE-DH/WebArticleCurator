#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import re
import json


class CorpusConverter:
    def __init__(self, settings, file_out, logger_):
        # can be a raw filename or a JSON data structure which was already read by the calling program
        site_schemas = settings['site_schemas']
        tags_filename = settings['tags']
        self._settings = settings
        self._file_out = file_out
        self._logger_ = logger_

        if isinstance(site_schemas, str):  # if it is a filename, open that file
            self.site_schemas = json.load(open(os.path.join(settings['dir_name'], site_schemas), encoding='UTF-8'))
        elif isinstance(site_schemas, dict):
            self.site_schemas = site_schemas
        else:
            print('CorpusConverter constructor got wrong input type. Valid input types are:\n'
                  ' - str (name of JSON file to open)\n'
                  ' - dict (containing the read-in JSON)')

        self.tags_filename = tags_filename
        self.tags = json.load(open(os.path.join(settings['dir_name'], tags_filename), encoding='UTF-8'))
        for k, v in self.tags.items():  # Site, tag
            self.site_schemas[k][v]['open-inside-close'] = re.compile('{0}{1}{2}'.
                                                                      format(self.site_schemas[k][v]['open'],
                                                                             self.site_schemas[k][v]['inside'],
                                                                             self.site_schemas[k][v]['close']))
        self.url_pattern = re.compile('(https?://)?(www.)?([^/]+\.)(\w+/|$)(.*)')
        self.script_pattern = re.compile(r'<script[\s\S]+?/script>')
        self.img_pattern = re.compile(r'<img.*?/>')
        self.multi_ws_pattern = re.compile(' {2,}')
        self.endl_ws_pattern = re.compile('\n ')
        self.multi_endl_pattern = re.compile('\n{2,}')

    def article_to_corpus(self, json_key_src, doc_in):
        """
        converts the raw HTML code of an article to corpus format and saves it to the output file
        :param doc_in: the document to convert
        :param json_key_src: a URL from which the key of setting set to use can be mined, or that key itself
            tries to map the given json_key_src string to a site-spcific setting set int the JSON file by checking
            if it equals or matches to one of the keys of setting sets
        :return:
        """
        # url_match = settings['URL_PATTERN'].match(url)
        # url_path = url_match.group(5)
        # print(url_path)

        # check if json_key_src is the same as one of the JSON keys
        if json_key_src in self.site_schemas:
            json_key = json_key_src
        else:
            # check if json_key_src matches to the URL of a site;
            # if it does then the the key belonging to that site will be used
            match = self.url_pattern.match(json_key_src)
            if match:
                # possible_json_key = match.group(3) + match.group(4)
                # domain of website
                possible_json_key = match.group(3)[:-1]
                possible_json_key = possible_json_key.split('.')[-1]
                if possible_json_key in self.site_schemas:
                    json_key = possible_json_key
                else:
                    self._logger_.log(json_key_src, 'Configuration type key {0} can not be found in JSON file!'.
                                      format(possible_json_key))
                    return
            else:
                self._logger_.log(json_key_src, 'Configuration type key {0} can not be found in JSON file!'.
                                  format(json_key_src))
                return
        # if json_key was/contained a valid key then call the converter function
        article_corpus_format = self.__convert_doc(doc_in, self.tags[self.site_schemas[json_key]['tags_key']])

        print(self._settings['article_begin_flag'], article_corpus_format, self._settings['article_end_flag'],
              sep='', end='', file=self._file_out)
        self._logger_.log(json_key_src, 'download OK')
        return

    def __convert_doc(self, doc_in, json_tags_key):
        """
            reads from the JSON file what parts of original files should be replaced by what tags and
            executes replacement
        """
        doc_out = ''.join(self.__check_regex(json_tags_key_vals['open'],
                                             json_tags_key_vals['close'],
                                             json_tags_key_vals['open-inside-close'], t, doc_in)
                          for t, json_tags_key_vals in json_tags_key.items())
        doc_out = self.script_pattern.sub('', doc_out)
        doc_out = self.img_pattern.sub('', doc_out)
        doc_out = self.multi_ws_pattern.sub(' ', doc_out)
        doc_out = self.endl_ws_pattern.sub('\n', doc_out)
        doc_out = self.multi_endl_pattern.sub('\n', doc_out)
        # TODO: drop useless div and span tags
        return doc_out

    @staticmethod
    def __check_regex(old_tag_open, old_tag_close, old_tag, new_tag, doc_in):
        """
            keeps parts of input file that match patterns specified in JSON and
            then changes their HTML/CSS tags to our corpus markup tags
        """
        match = old_tag.search(doc_in)
        matched_part = ''
        if match is not None:
            matched_part = match.group(0)
            matched_part = re.sub(old_tag_open, '<'+new_tag+'> ', matched_part)
            matched_part = re.sub(old_tag_close, ' </'+new_tag+'>\n', matched_part)
        return matched_part
