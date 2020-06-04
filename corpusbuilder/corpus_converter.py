#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from argparse import Namespace
from datetime import datetime

""" An example converter to showcase API and to suppress any article processing at crawling time (for new portals) """


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
