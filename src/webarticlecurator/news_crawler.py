#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from mplogger import Logger

from .utils import write_set_contents_to_file
from .enhanced_downloader import WarcCachingDownloader
from .strategies import date_range, gen_article_urls_and_subpages


class NewsArchiveCrawler:
    """
        Using the provided regexes
        1) Generates URLs of lists of articles (archives)
        2) Extracts URLs of articles from these lists (with helper functions and config)
    """
    def __init__(self, settings, existing_archive_filenames, new_archive_filename, archive_just_cache=False,
                 known_article_urls=None, debug_params=None, downloader_params=None):

        # List the used properties
        self._archive_page_urls_by_date = None
        self._archive_url_format = None
        self._date_from = None
        self._date_until = None
        self._go_reverse_in_archive = None
        self._min_pagenum = None
        self._initial_page_num = None
        self._ignore_archive_cache = None
        self._infinite_scrolling = None
        self._extract_article_urls_from_page_fun = None
        self._find_next_page_url = None
        self._max_tries = None

        # Save the original settings for using it with all columns
        self._settings = settings
        # Get columns, if there is only one we use None to keep default settings
        self._columns = settings['columns']

        # Initialise the logger
        if debug_params is None:
            debug_params = {}
        self._logger = Logger(settings['log_file_archive'], **debug_params)

        # Open files for writing gathered URLs if needed
        self.good_urls = set()
        self._good_urls_filename = settings.get('new_good_archive_urls')

        self.problematic_urls = set()
        self._problematic_urls_filename = settings.get('new_problematic_archive_urls')

        # Setup the list of cached article URLs to stop archive crawling in time
        self.known_article_urls = set()
        if known_article_urls is not None:
            if isinstance(known_article_urls, str):
                with open(known_article_urls, encoding='UTF-8') as fh:
                    self.known_article_urls = {line.strip() for line in fh}
            elif isinstance(known_article_urls, set):
                self.known_article_urls = known_article_urls

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(existing_archive_filenames, new_archive_filename, self._logger,
                                                 archive_just_cache, downloader_params)
        # Known bad URLs (read-only, available at __init__ time)
        self.bad_urls = self._downloader.bad_urls
        # Known good URLs (read-only, available at __init__ time from cache)
        self.url_index = self._downloader.url_index

    def _store_settings(self, column_spec_settings):
        # Settings for URL iterator
        self._archive_page_urls_by_date = self._settings['archive_page_urls_by_date']
        self._archive_url_format = column_spec_settings['archive_url_format']
        self._max_tries = column_spec_settings.get('max_tries', 1)
        if self._archive_page_urls_by_date:
            self._date_from = column_spec_settings['DATE_FROM']
            self._date_until = column_spec_settings['DATE_UNTIL']
            self._go_reverse_in_archive = self._settings['go_reverse_in_archive']

        # Settings for gen_article_urls_including_subpages()
        self._min_pagenum = column_spec_settings['min_pagenum']
        self._initial_page_num = column_spec_settings['INITIAL_PAGENUM']
        self._ignore_archive_cache = self._settings['ignore_archive_cache']
        self._infinite_scrolling = self._settings['infinite_scrolling']
        self._extract_article_urls_from_page_fun = self._settings['EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN']

        # Store the constant parameters for the actual function used later
        self._find_next_page_url = \
            self._find_next_page_url_factory(self._settings['EXTRACT_NEXT_PAGE_URL_FUN'],
                                             self._settings['next_url_by_pagenum'],
                                             self._settings['infinite_scrolling'], column_spec_settings['max_pagenum'],
                                             self._settings['new_article_url_threshold'], self.known_article_urls,
                                             self._settings['stop_on_empty_archive_page'],
                                             self._settings['stop_on_taboo_set'], self._settings['TABOO_ARTICLE_URLS'],
                                             column_spec_settings.get('last_archive_page_url'))


    def url_iterator(self):
        """
            The URL generation logic. We have one or more base URL to the archive (or column archives if there is more)
                and it is complete with portal-specific ending.
            The archive can be stored in groups (mostly the creation date) or ordered in a flat list paginated.
            This two main method can also be mixed.
            Pagination can be implemented in various ways, see the appropriate function for details
        :return: Every page of the archive contain multiple URL to the actual articles, which are extracted and
         then returned as an iterator based on URLs.
        """
        for column_name, params in self._columns.items():
            self._logger.log('INFO', 'Starting column:', column_name)
            # 1) Set params for the actual column
            self._store_settings(params)
            # 2) By date with optional pagination (that is handled separately)
            if self._archive_page_urls_by_date:
                archive_page_urls = date_range(self._archive_url_format, self._date_from, self._date_until,
                                               self._go_reverse_in_archive)
            # 3) Stored in groups represented by pagination only which will be handled separately
            else:
                archive_page_urls = [self._archive_url_format]  # Only the base URL is added

            # 4) Iterate the archive URLs and process them, while generating the required page URLs on demand
            for base_url in archive_page_urls:
                yield from gen_article_urls_and_subpages(base_url, self.bad_urls, self._downloader,
                                                         self._extract_articles_and_gen_next_page_link_fun,
                                                         self.good_urls, self._good_urls_filename,
                                                         self.problematic_urls, self._problematic_urls_filename,
                                                         self._initial_page_num, self._min_pagenum,
                                                         self._infinite_scrolling,
                                                         self._max_tries, self._ignore_archive_cache,
                                                         self._logger)

    def _extract_articles_and_gen_next_page_link_fun(self, archive_page_url_base, archive_page_raw_html, curr_page_url,
                                                     infinite_scrolling, first_page, page_num, logger):
        """Use preset site-specific functions to extract articles and next page link"""
        article_urls = self._extract_article_urls_from_page_fun(archive_page_raw_html)
        if len(article_urls) == 0 and (not infinite_scrolling or first_page):
            logger.log('WARNING', curr_page_url, 'Could not extract URLs from the archive!', sep='\t')
        # 2) Generate next-page URL or None if there should not be any
        next_page_url = self._find_next_page_url(archive_page_url_base, page_num, archive_page_raw_html,
                                                 article_urls)
        return article_urls, next_page_url

    @staticmethod
    def _find_next_page_url_factory(extract_next_page_url_fun, next_url_by_pagenum, infinite_scrolling, max_pagenum,
                                    art_url_threshold, known_article_urls, stop_on_empty_archive_page,
                                    stop_on_taboo_set, taboo_article_urls, last_archive_page_url):

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
            # Method #2: Stop on empty archive or on taboo URLs if they are defined
            if (stop_on_empty_archive_page and len(article_urls) == 0) or \
                    (stop_on_taboo_set and len(taboo_article_urls.intersection(article_urls)) > 0):
                next_page_url = None
            # Method #3: Use special function to follow the link to the next page
            elif extract_next_page_url_fun is not None:
                next_page_url = extract_next_page_url_fun(raw_html)
                # Method #3.b: Stop on last archive page specified in config
                if next_page_url == last_archive_page_url:
                    next_page_url = None
            elif (next_url_by_pagenum and  # There are page numbering
                    # Method #4: No link, but infinite scrolling! (also good for inactive archive, without other clues)
                    ((infinite_scrolling and len(article_urls) > 0) or
                     # Method #5: Has predefined max_pagenum! (also good for inactive archive, with known max_pagenum)
                     (max_pagenum is not None and page_num <= max_pagenum) or
                     # Method #6: Active archive, just pages -> We allow intersecting elements
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
        4) Filter articles by date (depends on corpus converter)
        5) Save them in corpus format (depends on corpus converter)
        6) Follow the links on page (depends on corpus converter)
    """

    def __init__(self, settings, articles_existing_warc_filenames, articles_new_warc_filename,
                 archive_existing_warc_filenames, archive_new_warc_filename, articles_just_cache=False,
                 archive_just_cache=False, known_article_urls=None, debug_params=None, download_params=None):

        # Initialise the logger
        self._logger = Logger(settings['log_file_articles'])

        # Open files for writing gathered URLs if needed
        self._new_urls = set()
        self._new_urls_filename = settings.get('new_good_urls')

        self.problematic_article_urls = set()
        self._problematic_article_urls_filename = settings.get('new_problematic_urls')

        # Store values at init-time
        self._filter_by_date = settings['FILTER_ARTICLES_BY_DATE']
        if self._filter_by_date:  # Global date intervals, only if they are explicitly set!
            self._date_from = settings['date_from']
            self._date_until = settings['date_from']

        # Get the initialised corpus converter (can be dummy) and set the appropriate logger
        self._converter = settings['CORPUS_CONVERTER']
        self._converter.logger = self._logger

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(articles_existing_warc_filenames, articles_new_warc_filename,
                                                 self._logger, articles_just_cache, download_params)

        if known_article_urls is None:  # If None is supplied copy the ones from the article archive
            known_article_urls = self._downloader.url_index  # All URLs in the archive are known good!

        if archive_just_cache and articles_just_cache:
            # Full offline mode for processing articles only without the archive
            self._archive_downloader = NewsArchiveDummyCrawler(self._downloader.url_index)
        else:  # known_bad_urls are common between the NewsArchiveCrawler and the NewsArticleCrawler
            # For downloading the articles from a (possibly read-only) archive
            self._archive_downloader = NewsArchiveCrawler(settings, archive_existing_warc_filenames,
                                                          archive_new_warc_filename, archive_just_cache,
                                                          known_article_urls, debug_params, download_params)

    def __del__(self):
        if hasattr(self, '_archive_downloader'):  # Make sure that the previous files are closed...
            del self._archive_downloader

    def _is_problematic_url(self, url):
        # Explicitly marked as bad URL (either Article or Archive) OR
        # Download failed in this session and requires manual check (either Article or Archive)
        return url in self._downloader.bad_urls or url in self._archive_downloader.bad_urls or \
               url in self.problematic_article_urls or url in self._archive_downloader.problematic_urls

    def _is_processed_good_url(self, url):
        # New good URL newly downloaded (either Article or Archive)
        # We do not count old good URLs (url_index) have taken from the cache WARC (either Article or Archive)
        #  as they are needed to be copied to the target WARC!
        return url in self._downloader.good_urls or url in self._archive_downloader.good_urls

    def download_and_extract_all_articles(self):
        self.process_urls(self._archive_downloader.url_iterator())

    def process_urls(self, it):
        urls = set()
        with write_set_contents_to_file(self.problematic_article_urls,
                                        self._problematic_article_urls_filename) as problematic_article_urls_add, \
                write_set_contents_to_file(self._new_urls, self._new_urls_filename) as new_urls_add:

            for url in it:
                urls.add(url)
                while len(urls) > 0:
                    # This loop runs only one iteration if no URLs are extracted in step (6) else it consumes them first
                    url = urls.pop()
                    # 1) Check if the URL is
                    # 1a) Explicitly marked as bad URL (either Article or Archive) -> Skip it, only INFO log!
                    if url in self._downloader.bad_urls or url in self._archive_downloader.bad_urls:
                        self._logger.log('DEBUG', url, 'Skipping URLs explicitly marked as bad!', sep='\t')
                        continue
                    # 1b) Download succeeded in this session either Article or Archive (duplicate)
                    # 1c) Download failed in this session
                    # and requires manual check either Article or Archive (duplicate)
                    elif self._is_processed_good_url(url) or \
                            url in self.problematic_article_urls or url in self._archive_downloader.problematic_urls:
                        self._logger.log('WARNING', url, 'Not processing URL, because it is an URL already'
                                                         ' encountered in this session (including the caches)'
                                                         ' or it is known to point to the portal\'s archive!', sep='\t')
                        continue

                    # 2) "Download" article
                    article_raw_html = self._downloader.download_url(url)
                    if article_raw_html is None:  # Download failed, must be investigated!
                        self._logger.log('ERROR', url, 'Article was not processed because download failed!', sep='\t')
                        problematic_article_urls_add(url)  # New problematic URL for manual checking
                        continue
                    new_urls_add(url)  # New article URLs

                    # TODO Do we need this?
                    # 3) Identify the site scheme of the article to be able to look up the appropriate extracting method
                    scheme = self._converter.identify_site_scheme(url, article_raw_html)

                    # TODO This is not used. To be removed in 2.0
                    # 4) Filter: time filtering when archive page URLs are not generated by date if needed
                    if self._filter_by_date:
                        # a) Retrieve the date
                        article_date = self._converter.extract_article_date(url, article_raw_html, scheme)
                        if article_date is None:
                            self._logger.log('ERROR', url, 'DATE COULD NOT BE PARSED!', sep='\t')
                            continue
                        # b) Check date interval
                        elif not self._date_from <= article_date <= self._date_until:
                            self._logger.log('WARNING', url, 'Date ({0}) is not in the specified interval: {1}-{2}'
                                                             ' didn\'t use it in the corpus'.
                                             format(article_date, self._date_from, self._date_until), sep='\t')
                            continue

                    # TODO This is not used. To be removed in 2.0
                    # 5) Extract text to corpus
                    self._converter.article_to_corpus(url, article_raw_html, scheme)

                    # 6) Extract links to other articles and check for already extracted urls (also in the archive)?
                    urls_to_follow = self._converter.follow_links_on_page(url, article_raw_html, scheme)
                    # Only add those which has not been already handled to avoid loops!
                    urls |= {url for url in urls_to_follow
                             if not self._is_processed_good_url(url) and not self._is_problematic_url(url)}
