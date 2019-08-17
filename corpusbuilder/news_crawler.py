#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import timedelta

from .extractor_functions import extract_article_urls_from_page, extract_article_date, identify_site_scheme
from .enhanced_downloader import WarcCachingDownloader
from .utils import Logger


class NewsArchiveCrawler:
    """
        Using the provided regexes
        1) Generates URLs of lists of articles (archives)
        2) Extracts URLs of articles from these lists (with helper functions and config)
    """
    def __init__(self, settings, existing_archive_filename, new_archive_filename, archive_just_cache=False,
                 known_article_urls=None, **downloader_params):

        self._settings = settings
        self._logger = Logger(self._settings['log_file_archive'])

        # For external use
        self.good_urls = set()
        self.problematic_urls = set()

        # Setup the list of cached article URLs to stop archive crawling in time
        if known_article_urls is not None and isinstance(known_article_urls, str):
            with open(known_article_urls, encoding='UTF-8') as fh:
                self.known_article_urls = {line.strip() for line in fh}
        elif known_article_urls is not None and isinstance(known_article_urls, set):
            self.known_article_urls = known_article_urls
        else:
            self.known_article_urls = set()

        # Create new archive while downloading, or simulate download and read the archive
        self._downloader = WarcCachingDownloader(existing_archive_filename, new_archive_filename, self._logger,
                                                 archive_just_cache, **downloader_params)

        self.known_good_urls = self._downloader.url_index  # All URLs in the archive are known good!

    def __del__(self):  # Write newly found URLs to files when output files supplied...
        if hasattr(self, '_new_urls_filehandles') and hasattr(self, 'good_urls') and hasattr(self, 'problematic_urls'):
            new_good_urls = self._settings['NEW_GOOD_ARCHIVE_URLS_FH']
            if new_good_urls is not None and len(self.good_urls) > 0:
                new_good_urls.writelines('{0}\n'.format(good_url) for good_url in self.good_urls)

            if new_good_urls is not None:
                new_good_urls.close()

            new_problematic_urls = self._settings['NEW_PROBLEMATIC_ARCHIVE_URLS_FH']
            if new_problematic_urls is not None and len(self.problematic_urls) > 0:
                new_problematic_urls.writelines('{0}\n'.format(problematic_url)
                                                for problematic_url in self.problematic_urls)

            if new_problematic_urls is not None:
                new_problematic_urls.close()

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
            Generates and returns the URLs of a page the contains URLs of articles published that day.
            This function allows URLs to be grouped by years or month as there is no guarantee that all fields exists.
            We also enable using one day open ended interval of dates. eg. from 2018-04-04 to 2018-04-05 (not included)
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
        ignore_archive_cache = self._settings['ignore_archive_cache']
        extract_article_urls_from_page_fun = self._settings['EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN']

        next_page_url = archive_page_url_base.replace('#pagenum', '')  # TODO: Empty string or explicit min_pagenum?
        while next_page_url is not None:
            archive_page_raw_html = self._downloader.download_url(next_page_url, ignore_cache=ignore_archive_cache)
            if archive_page_raw_html is not None:  # Download succeeded
                if next_page_url not in self.known_good_urls:
                    self.good_urls.add(next_page_url)
                # 1) We need article URLs here to reliably determine the end of pages in some cases
                article_urls = extract_article_urls_from_page_fun(archive_page_raw_html)
                # 2) Generate next-page URL or None if there should not be any
                next_page_url = self._find_next_page_url(self._settings, archive_page_url_base, page_num,
                                                         archive_page_raw_html, article_urls, self.known_article_urls)
            else:  # Download failed
                if next_page_url not in self._downloader.bad_urls:
                    self.problematic_urls.add(next_page_url)  # New possibly bad URL
                next_page_url = None
                article_urls = []
            page_num += 1
            yield from article_urls

    @staticmethod
    def _find_next_page_url(settings, archive_page_url_base, page_num, raw_html, article_urls, known_article_urls):
        """
            The next URL can be determined by various conditions (no matter how the pages are grouped):
                1) If there is no pagination we return None
                2) If there is a "next page" link, we find it and use that
                3) If there is "infinite scrolling", we use pagenum from base to infinity (=No article URLs detected)
                4) If there is only page numbering, we use pagenum from base to config-specified maximum
                5) If there is only page numbering, we expect the archive to move during crawling (or partial crawling)
        """
        max_pagenum = settings['MAX_PAGENUM']
        art_url_threshold = settings['NEW_ARTICLE_URL_THRESHOLD']
        # Method #1: No pagination (default)
        next_page_url = None

        # Method #2: Use special function to follow the link to the next page
        if settings['EXTRACT_NEXT_PAGE_URL_FUN'] is not None:
            next_page_url = settings['EXTRACT_NEXT_PAGE_URL_FUN'](raw_html)
        elif (settings['next_url_by_pagenum'] and  # TODO: Simplify?
                # Method #3: No link, but infinite scrolling! (also good for inactive archive, without other clues)
                (settings['infinite_scrolling'] and len(article_urls) > 0) or
                # Method #4: Has predefined max_pagenum! (also good for inactive archive, with known max_pagenum)
                (max_pagenum is not None or page_num < max_pagenum) or
                # Method #5: Active archive, just pages -> We allow intersecting elements
                #  as the archive may have been moved
                (art_url_threshold is not None and (len(known_article_urls) == 0 or
                                                    len(article_urls.minus(known_article_urls)) > art_url_threshold))):
            next_page_url = archive_page_url_base.replace('#pagenum', str(page_num))  # must generate URL

        return next_page_url


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
                 archive_just_cache=False, known_article_urls=None, **download_params):
        self._settings = settings
        self._logger = Logger(self._settings['log_file_articles'])

        self.good_article_urls = set()
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
                                                 self._logger, articles_just_cache, **download_params)

        self.known_good_article_urls = self._downloader.url_index  # All URLs in the archive are known good!
        if known_article_urls is None:  # If None is supplied put the ones from the article archive
            known_article_urls = self.known_good_article_urls

        if archive_just_cache and articles_just_cache:
            self._archive_downloader = NewsArchiveDummyCrawler(self._downloader.url_index.keys())
        else:  # known_bad_urls are common between the NewsArchiveCrawler and the NewsArticleCrawler
            self._archive_downloader = NewsArchiveCrawler(self._settings, archive_existing_warc_filename,
                                                          archive_new_warc_filename, archive_just_cache,
                                                          known_article_urls, **download_params)

    def __del__(self):
        if hasattr(self, '_file_out') and self._file_out is not None:
            self._file_out.close()
        if hasattr(self, '_archive_downloader'):  # Make sure that the previous files are closed...
            del self._archive_downloader

        # Save the new urls...
        if hasattr(self, '_new_urls_filehandles') and hasattr(self, '_new_urls') and \
                hasattr(self, 'problematic_article_urls'):

            new_good_urls = self._settings['NEW_GOOD_URLS_FH']
            if new_good_urls is not None and len(self._new_urls) > 0:
                new_good_urls.writelines('{0}\n'.format(good_url) for good_url in self._new_urls)

            if new_good_urls is not None:
                new_good_urls.close()

            problematic_article_urls = self._settings['NEW_PROBLEMATIC_URLS_FH']
            if problematic_article_urls is not None and len(self.problematic_article_urls) > 0:
                problematic_article_urls.writelines('{0}\n'.format(problematic_url)
                                                    for problematic_url in self.problematic_article_urls)

            if problematic_article_urls is not None:
                problematic_article_urls.close()

    def process_urls(self, it):
        for url in it:
            # 1) Check if it is a duplicate (we do not count those in the archive)
            if url not in self.known_good_article_urls and url not in self._archive_downloader.known_article_urls \
                    and not self._is_new_url(url):
                self._logger.log('WARNING', '\t'.join((url, 'Not processing article, because it is already processed'
                                                            ' in this session!')))
                continue

            # 2) "Download" article
            if url not in self._downloader.bad_urls:
                article_raw_html = self._downloader.download_url(url)
                if article_raw_html is None:
                    self._logger.log('ERROR', '\t'.join((url, 'Article was not processed because download failed!')))
                    self.problematic_article_urls.add(url)  # New problematic URL for manual checking
                    continue
                # 3) Note downloaded url, but only when it is truly new URL (ie. not in the old archive)
                elif url not in self.known_good_article_urls:
                    self.good_article_urls.add(url)
            else:
                self._logger.log('INFO', '\t'.join((url, 'Article was not processed '
                                                         'because it was listed as bad url!')))
                continue

            # 4) Filter: time filtering when archive page URLs are not generated by date if needed
            if self._filter_by_date:
                # a) Identify the site scheme of the article to be able to look up the appropriate extracting method
                scheme = identify_site_scheme(self._logger, self._settings, url)
                # b) Retrieve the date
                article_date = extract_article_date(self._settings, url, article_raw_html, scheme)
                if article_date is None:
                    self._logger.log('ERROR', '\t'.join((url, 'DATE COULD NOT BE PARSED!')))
                    continue
                # c) Check date interval
                elif not self._settings['DATE_FROM'] <= article_date <= self._settings['DATE_UNTIL']:
                    self._logger.log('WARNING', '\t'.join((url, 'Date ({0}) not in the specified interval: {1}-{2} '
                                                                'didn\'t use it in the corpus'.
                                     format(article_date, self._settings['DATE_FROM'], self._settings['DATE_UNTIL']))))
                    continue

            # TODO: FULLY OPTIONAL!
            """
            # 5) Extract text to corpus
            if self._create_corpus:
                self._converter.article_to_corpus(url, article_raw_html, scheme)  # TODO: scheme may not exists!
            """

            # 6) Extract links to other articles and check for already extracted urls (also in the archive)!
            # TODO: IMPLEMENT AS OPTIONAL!
            """
            if self._follow_links_on_page:
                extracted_article_urls = extract_article_urls_from_page(article_raw_html, self._settings)

                for extracted_url in extracted_article_urls:
                    if self._is_new_url(extracted_url):
                        self._new_urls.add(extracted_url)
            """

    def download_and_extract_all_articles(self):
        self.process_urls(self._archive_downloader.url_iterator())
        self.download_gathered_new_urls()

    def download_gathered_new_urls(self):
        # Recheck new urls (also in the archive!)
        self._new_urls = {url for url in self._new_urls if self._is_new_url(url)}
        while len(self._new_urls) > 0:  # Article URL-s not in the archive... Shouldn't be any!
            for url in self._new_urls:
                self._logger.log('ERROR', '\t'.join((url, 'TRUE NEW URL')))
            new_urls, self._new_urls = self._new_urls, set()
            self.process_urls(new_urls)  # Recursively get all new urls...

    def _is_new_url(self, url):
        return \
            (url not in self.good_article_urls and         # Downloaded succesfully in this session
             url not in self.known_good_article_urls and   # Present in old archive
             url not in self.problematic_article_urls and  # Download failed in this session (requries manual check)
             url not in self._downloader.bad_urls and      # Explicit bad URLs (supplied as parameter)
             url not in self._archive_downloader.good_urls and  # Archive URLs succesfully downloaded in this session
             url not in self._archive_downloader.problematic_urls and  # Archive URLs failed to download in this session
             url not in self._archive_downloader.known_article_urls)  # Article URLs explicitly known (as parameter)
