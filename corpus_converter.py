#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
import json


class CorpusConverter:
    def __init__(self, site_schemas, tags_filename):
        """
        :param site_schemas: can be a raw filename or
         a JSON data structure which was already read by the calling program
        :param tags_filename:
        """
        if isinstance(site_schemas, str):  # if it is a filename, open that file
            self.site_schemas = json.load(open(site_schemas, encoding='UTF-8'))
        elif isinstance(site_schemas, dict):
            self.site_schemas = site_schemas
        else:
            print('CorpusConverter constructor got wrong input type. Valid input types are:\n'
                  ' - str (name of JSON file to open)\n'
                  ' - dict (containing the read-in JSON)')

        self.tags_filename = tags_filename
        self.tags = json.load(open(tags_filename, encoding='UTF-8'))
        self.url_pattern = re.compile('(https?://)?(www.)?([^/]+\.)(\w+/|$)(.*)')
        self.script_pattern = re.compile(r'<script[\s\S]+?/script>')
        self.img_pattern = re.compile(r'<img.*?/>')
        self.multi_ws_pattern = re.compile(' {2,}')
        self.endl_ws_pattern = re.compile('\n ')
        self.multi_endl_pattern = re.compile('\n{2,}')

    def convert_doc_by_json(self, doc_in, json_key_src):
        """

        :param doc_in: the document to convert
        :param json_key_src: a URL from which the key of setting set to use can be mined, or that key itself
            tries to map the given json_key_src string to a site-spcific setting set int the JSON file by checking
            if it equals or matches to one of the keys of setting sets
        :return:
        """
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
                    # TODO: függvénybe
                    raise ValueError('Configuration type key ' + possible_json_key + ' can not be found in JSON file!')
            else:
                # TODO: függvénybe
                raise ValueError('Configuration type key ' + json_key_src + ' can not be found in JSON file!')
        # if json_key was/contained a valid key then call the converter function
        return self.__convert_doc(doc_in, self.tags[self.site_schemas[json_key]['tags_key']])

    def __convert_doc(self, doc_in, json_tags_key):
        """
            reads from the JSON file what parts of original files should be replaced by what tags and
            executes replacement
        """
        doc_out = ''.join(self.__check_regex(json_tags_key_vals['open'],
                                             json_tags_key_vals['inside'],
                                             json_tags_key_vals['close'], t, doc_in)
                          for t, json_tags_key_vals in json_tags_key.items())
        doc_out = self.script_pattern.sub('', doc_out)
        doc_out = self.img_pattern.sub('', doc_out)
        doc_out = self.multi_ws_pattern.sub(' ', doc_out)
        doc_out = self.endl_ws_pattern.sub('\n', doc_out)
        doc_out = self.multi_endl_pattern.sub('\n', doc_out)
        # TODO: drop useless div and span tags
        return doc_out

    @staticmethod
    def __check_regex(old_tag_open, old_tag_inside, old_tag_close, new_tag, doc_in):
        """
            keeps parts of input file that match patterns specified in JSON and
            then changes their HTML/CSS tags to our corpus markup tags
        """
        regex = re.compile(old_tag_open + old_tag_inside + old_tag_close)  # TODO: Pull out to config reading!
        match = regex.search(doc_in)
        matched_part = ''
        if match is not None:
            matched_part = match.group(0)
            matched_part = re.sub(old_tag_open, '<'+new_tag+'> ', matched_part)
            matched_part = re.sub(old_tag_close, ' </'+new_tag+'>\n', matched_part)
        return matched_part
