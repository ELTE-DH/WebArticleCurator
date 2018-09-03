#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import datetime
import os


class Logger:
    """
        handles log file
        writes out log messages
        checks in log file if the current article is processed already
    """
    def __init__(self, log_filename):
        if not os.path.exists(log_filename):
            open(log_filename, 'w+', encoding='UTF-8').close()  # TODO: Is it a better way?
        self.file_log = open(log_filename, 'r+', encoding='UTF-8')

        self.processed_urls = set()
        if os.stat(log_filename).st_size == 0:
            print('TIME;URL;LOG MESSAGE', file=self.file_log)
            self.log('', 'Logging started')
        else:
            for line in self.file_log:
                if ';' in line:
                    line_splitted = line.strip().split(';')
                    url = line_splitted[1]
                    if len(url) > 3:  # We can safely conclude that an url is longer than 3 -> url != 'URL'
                        self.processed_urls.add(url)
            print('TIME;URL;LOG MESSAGE', file=self.file_log)

    def log(self, url, msg):
        if len(url) == 0:
            print(msg)
        else:
            self.processed_urls.add(url)
            print(url, msg, sep=';')
        print(datetime.datetime.now(), url, msg, sep=';', file=self.file_log)

    def is_url_processed(self, url):
        return url in self.processed_urls

    def __del__(self):
        self.log('', 'Logging finished')
        self.file_log.close()
