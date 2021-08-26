#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import timedelta
from calendar import monthrange, isleap

from webarticlecurator import WarcCachingDownloader, Logger


def add_and_write_factory(attr, fname):
    """A helper function to write gathered URLs to a file handle if it is supplied"""
    if fname is None:
        return None, attr.add
    else:
        fh = open(fname, 'w', encoding='UTF-8')  # To store FH (for closing it)

        def add_fun(elem):
            attr.add(elem)
            print(elem, file=fh, flush=True)

        return fh, add_fun


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

        # Save the original settings for using it with all columns
        self._settings = settings
        # Get columns, if there is only one we use None to keep default settings
        self._columns = settings['columns']

        # Initialise the logger
        if debug_params is None:
            debug_params = {}
        self._logger = Logger(settings['log_file_archive'], **debug_params)

        # Open files for writing gathered URLs if needed,
        self.good_urls = set()
        self._new_good_archive_urls_fh, self._good_urls_add = \
            add_and_write_factory(self.good_urls, settings.get('new_good_archive_urls'))

        self.problematic_urls = set()
        self._new_problematic_archive_urls_fh, self._problematic_urls_add = \
            add_and_write_factory(self.problematic_urls, settings.get('new_problematic_archive_urls'))

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
                                             self._settings['new_article_url_threshold'], self.known_article_urls)

    def __del__(self):  # Write newly found URLs to files when output files supplied...
        # Save the good URLs...

        if hasattr(self, '_new_good_archive_urls_fh') and hasattr(self, 'close'):
            self._new_good_archive_urls_fh.close()

        if hasattr(self, '_new_problematic_archive_urls_fh') and hasattr(self, 'close'):
            self._new_problematic_archive_urls_fh.close()

    def url_iterator(self):
        """
            The URL generation logic. We have one or more base URL to the archive (or column archives if there is more)
                and it is complete with portal-specific ending.
            The archive can be stored in groups (mostly the creation date) or ordered in a flat list paginated.
            This two main method can also be mixed.
            Pagination can be implemented in various vays see the appropriate function for details
        :return: Every page of the archive contain multiple URL to the actual articles, which are extrated and
         then returned as an iterator based on URLs.
        """
        for column_name, params in self._columns.items():
            self._logger.log('INFO', 'Starting column:', column_name)
            # 1) Set params for the actual column
            self._store_settings(params)
            # 2) By date with optional pagination (that is handled separately)
            if self._archive_page_urls_by_date:
                # a) Unique the generated archive page URLs using every day from date_from to the end of date_until
                archive_page_urls = list(set(self._gen_url_from_date(self._date_from + timedelta(days=curr_day),
                                                                     self._archive_url_format)
                                             for curr_day in range((self._date_until - self._date_from).days + 1)))
                # b) Sort the generated archive page URLs
                archive_page_urls.sort(reverse=self._go_reverse_in_archive)
            # 3) Stored in groups represented by pagination only which will be handled separately
            else:
                archive_page_urls = [self._archive_url_format]  # Only the base URL is added

            # 4) Iterate the archive URLs and process them, while generating the required page URLs on demand
            for archive_page_url in archive_page_urls:
                yield from self._gen_article_urls_including_subpages(archive_page_url)

    @staticmethod
    def _gen_url_from_date(curr_date, url_format):
        """
            Generates the URLs of a page that contains URLs of articles published on that day.
            This function allows URLs to be grouped by years or month as there is no guarantee that all fields exists.
            We also enable using open ended interval of dates. eg. from 2018-04-04 to 2018-04-05 (not included)
             or with month 2018-04-04 to 2018-05-04 (not included)
            One must place #year #month #day and #next-year #next-month #next-day labels into the url_format variable.
        """
        if '#next-day' in url_format:
            # Plus one day (open ended interval): vs.hu, hvg.hu
            next_date = curr_date + timedelta(days=1)
        elif '#next-month' in url_format:
            # Plus one month (open interval): magyarnarancs.hu
            days_in_curr_month = monthrange(curr_date.year, curr_date.month)[1]
            next_date = curr_date + timedelta(days=days_in_curr_month - curr_date.day + 1)
        else:
            # Plus one year (open interval): ???
            next_date = curr_date + timedelta(days=365 + int(isleap(curr_date.year))
                                              - curr_date.timetuple().tm_yday + 1)

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
        page_num = self._min_pagenum
        first_page = True
        next_page_url = archive_page_url_base.replace('#pagenum', self._initial_page_num)
        while next_page_url is not None:
            archive_page_raw_html = self._downloader.download_url(next_page_url, self._ignore_archive_cache)
            curr_page_url = next_page_url
            if archive_page_raw_html is not None:  # Download succeeded
                self._good_urls_add(next_page_url)
                # 1) We need article URLs here to reliably determine the end of pages in some cases
                article_urls = self._extract_article_urls_from_page_fun(archive_page_raw_html)
                if len(article_urls) == 0 and (not self._infinite_scrolling or first_page):
                    self._logger.log('WARNING', next_page_url, 'Could not extract URLs from the archive!', sep='\t')
                # 2) Generate next-page URL or None if there should not be any
                next_page_url = self._find_next_page_url(archive_page_url_base, page_num, archive_page_raw_html,
                                                         article_urls)
            else:  # Download failed
                if next_page_url not in self.bad_urls and next_page_url not in self._downloader.good_urls and \
                        next_page_url not in self._downloader.url_index:  # URLs in url_index should not be a problem
                    self._problematic_urls_add(next_page_url)  # New possibly bad URL
                next_page_url = None
                article_urls = []
            page_num += 1
            self._logger.log('DEBUG', 'URLs/ARCHIVE PAGE', curr_page_url, len(article_urls), sep='\t')
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
        self._new_good_urls_fh, self._new_urls_add = \
            add_and_write_factory(self._new_urls, settings.get('new_good_urls'))

        self.problematic_article_urls = set()
        self._new_problematic_urls_fh, self._problematic_article_urls_add = \
            add_and_write_factory(self.problematic_article_urls, settings.get('new_problematic_urls'))

        # Store values at init-time
        self._filter_by_date = settings['FILTER_ARTICLES_BY_DATE']
        if self._filter_by_date:  # Global date intervals, only if they are explicitly set!
            self._date_from = settings['date_from']
            self._date_until = settings['date_from']

        # Get the initialised corpus converter (can be dummy) and set the apropriate logger
        self._converter = settings['CORPUS_CONVERTER']
        self._converter.logger = self._logger

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(articles_existing_warc_filenames, articles_new_warc_filename,
                                                 self._logger, articles_just_cache, download_params)

        if known_article_urls is None:  # If None is supplied copy the ones from the article archive
            known_article_urls = self._downloader.url_index  # All URLs in the archive are known good!

        if archive_just_cache and articles_just_cache:
            # Full offline mode for processing articles only withouht the archive
            self._archive_downloader = NewsArchiveDummyCrawler(self._downloader.url_index)
        else:  # known_bad_urls are common between the NewsArchiveCrawler and the NewsArticleCrawler
            # For downloading the articles from a (possibly read-only) archive
            self._archive_downloader = NewsArchiveCrawler(settings, archive_existing_warc_filenames,
                                                          archive_new_warc_filename, archive_just_cache,
                                                          known_article_urls, debug_params, download_params)

    def __del__(self):
        if hasattr(self, '_archive_downloader'):  # Make sure that the previous files are closed...
            del self._archive_downloader

        if hasattr(self, '_new_good_urls_fh') and hasattr(self, 'close'):
            self._new_good_urls_fh.close()

        if hasattr(self, '_new_problematic_urls_fh') and hasattr(self, 'close'):
            self._new_problematic_urls_fh.close()

    def _is_problematic_url(self, url):
        # Explicitly marked as bad URL (either Article or Archive) OR
        # Download failed in this session and requries manual check (either Article or Archive)
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
                # 1b) Download succeded in this session either Article or Archive (duplicate)
                # 1c) Download failed in this session and requries manual check either Article or Archive (duplicate)
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
                    self._problematic_article_urls_add(url)  # New problematic URL for manual checking
                    continue
                self._new_urls_add(url)  # New article URLs

                # 3) Identify the site scheme of the article to be able to look up the appropriate extracting method
                scheme = self._converter.identify_site_scheme(url, article_raw_html)

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

                # 5) Extract text to corpus
                self._converter.article_to_corpus(url, article_raw_html, scheme)

                # 6) Extract links to other articles and check for already extracted urls (also in the archive)?
                urls_to_follow = self._converter.follow_links_on_page(url, article_raw_html, scheme)
                # Only add those which has not been already handled to avoid loops!
                urls |= {url for url in urls_to_follow
                         if not self._is_processed_good_url(url) and not self._is_problematic_url(url)}
