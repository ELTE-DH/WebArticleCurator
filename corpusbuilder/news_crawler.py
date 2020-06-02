#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import timedelta

from .enhanced_downloader import WarcCachingDownloader
from .utils import Logger, write_on_exit


class NewsArchiveCrawler:
    """
        Using the provided regexes
        1) Generates URLs of lists of articles (archives)
        2) Extracts URLs of articles from these lists (with helper functions and config)
    """
    def __init__(self, settings, existing_archive_filename, new_archive_filename, archive_just_cache=False,
                 known_article_urls=None, debug_params=None, downloader_params=None):

        self._settings = settings

        self._initial_page_num = self._settings['INITIAL_PAGENUM']
        self._infinite_scrolling = self._settings['infinite_scrolling']
        self._ignore_archive_cache = self._settings['ignore_archive_cache']
        self._extract_article_urls_from_page_fun = self._settings['EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN']

        if debug_params is None:
            debug_params = {}
        self._logger = Logger(self._settings['log_file_archive'], **debug_params)

        # For external use
        self.good_urls = set()
        self.problematic_urls = set()

        # Setup the list of cached article URLs to stop archive crawling in time
        self.known_article_urls = set()
        if known_article_urls is not None:
            if isinstance(known_article_urls, str):
                with open(known_article_urls, encoding='UTF-8') as fh:
                    self.known_article_urls = {line.strip() for line in fh}
            elif isinstance(known_article_urls, set):
                self.known_article_urls = known_article_urls

        # Store the constant parameters for the actual function used later
        self._find_next_page_url = \
            self._find_next_page_url_factory(self._settings['EXTRACT_NEXT_PAGE_URL_FUN'],
                                             self._settings['next_url_by_pagenum'],
                                             self._settings['infinite_scrolling'], self._settings['MAX_PAGENUM'],
                                             self._settings['NEW_ARTICLE_URL_THRESHOLD'], self.known_article_urls)

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(existing_archive_filename, new_archive_filename, self._logger,
                                                 archive_just_cache, downloader_params)

        self.known_good_urls = self._downloader.url_index  # All URLs in the archive are known good!

    def __del__(self):  # Write newly found URLs to files when output files supplied...
        # Save the good URLs...
        write_on_exit(self, 'good_urls', self._settings['NEW_GOOD_ARCHIVE_URLS_FH'], self.good_urls)
        # Save the problematic URLs...
        write_on_exit(self, 'problematic_urls', self._settings['NEW_PROBLEMATIC_ARCHIVE_URLS_FH'],
                      self.problematic_urls)

    def url_iterator(self):
        """
            The URL generation logic. We have a base URL to the archive and it is complete with portal-specific ending.
            The archive can be stored in groups (mostly the creation date) or ordered in a flat list paginated.
            This two main method can also be mixed.
            Pagination can be implemented in various vays see the appropriate function for details
        :return: Every page of the archive contain multiple URL to the actual articles, which are extrated and
         then returned as an iterator based on URLs.
        """
        archive_page_urls = []

        # 1) By date with optional pagination (that is handled separately)
        if self._settings['archive_page_urls_by_date']:
            date_from = self._settings['DATE_FROM']
            date_until = self._settings['DATE_UNTIL']
            url_format = self._settings['archive_url_format']

            # a) Unique the generated archive page URLs using every day from date_from to the end of date_until
            archive_page_urls = list(set(self._gen_url_from_date(date_from + timedelta(days=curr_day), url_format)
                                         for curr_day in range((date_until - date_from).days + 1)))
            # b) Sort the generated archive page URLs
            archive_page_urls.sort(reverse=self._settings['go_reverse_in_archive'])
        # 2) Stored in groups represented by pagination only which will be handled separately
        else:
            archive_page_urls.append(self._settings['archive_url_format'])  # Only the base URL is added

        # 3) Run through the list of archive URLs and process them, while generating the required page URLs on demand
        for archive_page_url in archive_page_urls:
            yield from self._gen_article_urls_including_subpages(archive_page_url)

    @staticmethod
    def _gen_url_from_date(curr_date, url_format):
        """
            Generates the URLs of a page that contains URLs of articles published on that day.
            This function allows URLs to be grouped by years or month as there is no guarantee that all fields exists.
            We also enable using one day open ended interval of dates. eg. from 2018-04-04 to 2018-04-05 (not included)
            One must place #year #month #day and #next-year #next-month #next-day labels into the url_format variable.
        """
        next_date = curr_date + timedelta(days=1)  # Plus one day (open ended interval): vs.hu, hvg.hu
        art_list_url = url_format.\
            replace('#year', '{0:04d}'.format(curr_date.year)).\
            replace('#month', '{0:02d}'.format(curr_date.month)).\
            replace('#day', '{0:02d}'.format(curr_date.day)). \
                                                              \
            replace('#next-year', '{0:04d}'.format(next_date.year)). \
            replace('#next-month', '{0:02d}'.format(next_date.month)). \
            replace('#next-day', '{0:02d}'.format(next_date.day))
        return art_list_url

    def _gen_article_urls_including_subpages(self, archive_page_url_base):
        """
            Generates article URLs from a supplied URL inlcuding the on-demand sub-pages that contains article URLs
        """
        page_num = self._settings['min_pagenum']
        first_page = True
        next_page_url = archive_page_url_base.replace('#pagenum', self._initial_page_num)
        while next_page_url is not None:
            archive_page_raw_html = self._downloader.download_url(next_page_url,
                                                                  ignore_cache=self._ignore_archive_cache)
            curr_page_url = next_page_url
            if archive_page_raw_html is not None:  # Download succeeded
                self.good_urls.add(next_page_url)
                # 1) We need article URLs here to reliably determine the end of pages in some cases
                article_urls = self._extract_article_urls_from_page_fun(archive_page_raw_html)
                if len(article_urls) == 0 and (not self._infinite_scrolling or first_page):
                    self._logger.log('WARNING', '{0}\t{1}'.format(next_page_url,
                                                                  'Could not extract URLs from the archive!'))
                # 2) Generate next-page URL or None if there should not be any
                next_page_url = self._find_next_page_url(archive_page_url_base, page_num, archive_page_raw_html,
                                                         article_urls)
            else:  # Download failed
                if next_page_url not in self._downloader.bad_urls and next_page_url not in self._downloader.good_urls:
                    self.problematic_urls.add(next_page_url)  # New possibly bad URL
                next_page_url = None
                article_urls = []
            page_num += 1
            self._logger.log('DEBUG', 'URLs/ARCHIVE PAGE\t{0}\t{1}'.format(curr_page_url, len(article_urls)))
            yield from article_urls
            first_page = False

    @staticmethod
    def _find_next_page_url_factory(extract_next_page_url_fun, next_url_by_pagenum, infinite_scrolling, max_pagenum,
                                    art_url_threshold, known_article_urls):

        def find_nex_page_url_spec(archive_page_url_base, page_num, raw_html, article_urls):
            """
                The next URL can be determined by various conditions (no matter how the pages are grouped):
                 1) If there is no pagination we return None
                 2) If there is a "next page" link, we find it and use that
                 3) If there is "infinite scrolling", we use pagenum from base to infinity (=No article URLs detected)
                 4) If there is only page numbering, we use pagenum from base to config-specified maximum
                 5) If there is only page numbering, we expect the archive to move during crawling (or partial crawling)
            """
            # Method #1: No pagination (default) or no page left
            next_page_url = None
            # Method #2: Use special function to follow the link to the next page
            if extract_next_page_url_fun is not None:
                next_page_url = extract_next_page_url_fun(raw_html)
            elif (next_url_by_pagenum and  # There are page numbering
                    # Method #3: No link, but infinite scrolling! (also good for inactive archive, without other clues)
                    ((infinite_scrolling and len(article_urls) > 0) or
                     # Method #4: Has predefined max_pagenum! (also good for inactive archive, with known max_pagenum)
                     (max_pagenum is not None and page_num <= max_pagenum) or
                     # Method #5: Active archive, just pages -> We allow intersecting elements
                     #  as the archive may have been moved
                     (art_url_threshold is not None and
                      (len(known_article_urls) == 0 or
                       len(article_urls.minus(known_article_urls)) > art_url_threshold)))):
                next_page_url = archive_page_url_base.replace('#pagenum', str(page_num))  # must generate URL

            return next_page_url
        return find_nex_page_url_spec


class NewsArchiveDummyCrawler:
    def __init__(self, url_index_keys, *_, **__):
        self._url_index_keys = url_index_keys

    def url_iterator(self):
        return self._url_index_keys


class NewsArticleCrawler:
    """
        1) Get the list of articles (eg. NewsArchiveCrawler)
        2) Download article pages
        3) Extract the text of articles from raw HTML
        4) save them in corpus format
    """
    def __init__(self, settings, articles_existing_warc_filename, articles_new_warc_filename,
                 archive_existing_warc_filename, archive_new_warc_filename, articles_just_cache=False,
                 archive_just_cache=False, known_article_urls=None, debug_params=None, download_params=None):
        self._settings = settings
        self._logger = Logger(self._settings['log_file_articles'])

        self._copied_urls = set()
        self.problematic_article_urls = set()
        self._new_urls = set()

        # Store values at init-time
        self._filter_by_date = self._settings['FILTER_ARTICLES_BY_DATE']
        self._create_corpus = self._settings['OUTPUT_CORPUS_FH'] is not None

        if self._create_corpus:
            # Create new corpus converter class from the available methods...
            self._converter = self._settings['CORPUS_CONVERTER'](self._settings, self._logger)

        self._follow_links_on_page = self._settings['follow_links_on_page']

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(articles_existing_warc_filename, articles_new_warc_filename,
                                                 self._logger, articles_just_cache, download_params)

        if known_article_urls is None:  # If None is supplied put the ones from the article archive
            known_article_urls = set(self._downloader.url_index.keys())  # All URLs in the archive are known good!

        if archive_just_cache and articles_just_cache:
            # Full offline mode for processing articles only withouht the archive
            self._archive_downloader = NewsArchiveDummyCrawler(self._downloader.url_index.keys())
        else:  # known_bad_urls are common between the NewsArchiveCrawler and the NewsArticleCrawler
            # For downloading the articles from a (possibly read-only) archive
            self._archive_downloader = NewsArchiveCrawler(self._settings, archive_existing_warc_filename,
                                                          archive_new_warc_filename, archive_just_cache,
                                                          known_article_urls, debug_params, download_params)

    def __del__(self):
        if hasattr(self, '_archive_downloader'):  # Make sure that the previous files are closed...
            del self._archive_downloader

        # Save the new URLs...
        write_on_exit(self, '_new_urls', self._settings['NEW_GOOD_URLS_FH'], self._new_urls)
        # Save the problematic URLs...
        write_on_exit(self, 'problematic_article_urls', self._settings['NEW_PROBLEMATIC_URLS_FH'],
                      self.problematic_article_urls)

    def _is_problematic_url(self, url):
        return \
            (url in self.problematic_article_urls or  # Download failed in this session (requries manual check)
             url in self._archive_downloader.problematic_urls)  # Archive URLs failed to download in this session

    def process_urls(self, it):
        for url in it:
            # 1) Check if the URL is a duplicate (archive URL or problematic)
            if url in self._archive_downloader.good_urls or self._is_problematic_url(url):
                self._logger.log('WARNING', '{0}\tNot processing URL, because it is a problematic URL already'
                                            ' encountered in this session or it points to the portal\'s archive!'.
                                            format(url))
                continue

            # 2) "Download" article
            article_raw_html = self._downloader.download_url(url)
            if article_raw_html is None:
                # If the URL is not cached, not listed as explicitly bad, and not already downloaded successfully
                # (=duplicate), then there is a download error to be logged!
                if url not in self._downloader.cached_urls and \
                        url not in self._downloader.bad_urls and url not in self._downloader.good_urls:
                    self._logger.log('ERROR', '{0}\tArticle was not processed because download failed!'.format(url))
                    self.problematic_article_urls.add(url)  # New problematic URL for manual checking
                continue

            # 3) Identify the site scheme of the article to be able to look up the appropriate extracting method
            scheme = self._converter.identify_site_scheme(url)

            # 4) Filter: time filtering when archive page URLs are not generated by date if needed
            if self._filter_by_date:
                # a) Retrieve the date
                article_date = self._converter.extract_article_date(url, article_raw_html, scheme)
                if article_date is None:
                    self._logger.log('ERROR', '{0}\tDATE COULD NOT BE PARSED!'.format(url))
                    continue
                # b) Check date interval
                elif not self._settings['DATE_FROM'] <= article_date <= self._settings['DATE_UNTIL']:
                    self._logger.log('WARNING',
                                     '{0}\tDate ({1}) is not in the specified interval: {2}-{3} didn\'t use it'
                                     ' in the corpus'.format(url, article_date, self._settings['DATE_FROM'],
                                                             self._settings['DATE_UNTIL']))
                    continue

            # 5) Extract text to corpus
            if self._create_corpus:
                self._converter.article_to_corpus(url, article_raw_html, scheme)

            # 6) Extract links to other articles and check for already extracted urls (also in the archive)?
            # TODO: This could be used for multipage articles...

    def download_and_extract_all_articles(self):
        self.process_urls(self._archive_downloader.url_iterator())
