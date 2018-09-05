#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import os
import sys
import datetime


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
        print(datetime.datetime.now(), url, msg, sep=';', file=self.file_log, flush=True)

    def __del__(self):
        if hasattr(self, 'file_log'):
            self.log('', 'Logging finished')
            self.file_log.close()
