from datetime import timedelta, date
from calendar import monthrange, isleap

from mplogger import Logger, DummyLogger

from .utils import write_set_contents_to_file

# These are just examples and helpers and can be combined e.g. date + pagination

def date_range(base_url: str, date_from: date, date_until: date = date.today, go_reverse_in_archive=False):
    """
        Generates the URLs of a page that contains URLs of articles published on that day.
        This function allows URLs to be grouped by years or month as there is no guarantee that all fields exists.
        We also enable using open ended interval of dates. eg. from 2018-04-04 to 2018-04-05 (not included)
         or with month 2018-04-04 to 2018-05-04 (not included)
        One must place #year #month #day and #next-year #next-month #next-day labels into the base_url variable.
    """
    # 1) Unique the generated archive page URLs using "every day" from date_from to the end of date_until
    archive_page_urls = set()  # We sort at the end eiter forward or reverse
    for curr_day in range((date_until - date_from).days + 1):
        curr_date = date_from + timedelta(days=curr_day)

        if '#next-day' in base_url:
            # Plus one day (open ended interval): vs.hu, hvg.hu
            next_date = curr_date + timedelta(days=1)
        elif '#next-month' in base_url:
            # Plus one month (open interval): magyarnarancs.hu
            days_in_curr_month = monthrange(curr_date.year, curr_date.month)[1]
            next_date = curr_date + timedelta(days=days_in_curr_month - curr_date.day + 1)
        else:
            # Plus one year (open interval): ???
            next_date = curr_date + timedelta(
                days=365 + int(isleap(curr_date.year)) - curr_date.timetuple().tm_yday + 1)

        art_list_url = base_url. \
            replace('#year', f'{curr_date.year:04d}'). \
            replace('#month', f'{curr_date.month:02d}'). \
            replace('#day', f'{curr_date.day:02d}'). \
                                                            \
            replace('#next-year', f'{next_date.year:04d}'). \
            replace('#next-month', f'{next_date.month:02d}'). \
            replace('#next-day', f'{next_date.day:02d}')

        archive_page_urls.add(art_list_url)

    # 2) Sort the generated archive page URLs
    archive_page_urls = sorted(archive_page_urls, reverse=go_reverse_in_archive)

    return archive_page_urls

def next_page_by_link(raw_html, last_archive_page_url=None):
    """If there is a "next page" link, find it and use that"""
    extract_next_page_url_fun = lambda x: ''
    next_page_url = extract_next_page_url_fun(raw_html)  # TODO this function is site specific

    # Stop on last archive page specified in config (The default is None, which will match nothing)
    if next_page_url == last_archive_page_url:
        next_page_url = None

    return next_page_url

def infinite_scrolling(base_url: str, article_urls: set, page_num: int):
    """If there is "infinite scrolling", we use pagenum from base to infinity (=No article URLs detected)
       No link, but infinite scrolling! (also good for inactive archive, without other clues)"""
    next_page_url = None
    if len(article_urls) > 0:
        next_page_url = base_url.replace('#pagenum', str(page_num))  # Must generate URL

    return next_page_url

def until_maxpagenum(base_url: str, page_num: int, max_pagenum: int):
    """Has predefined max_pagenum! (also good for inactive archive, with known max_pagenum)"""
    next_page_url = None
    if page_num <= max_pagenum:
        next_page_url = base_url.replace('#pagenum', str(page_num))  # Must generate URL

    return next_page_url

def intersecting_pages(base_url: str, article_urls: set, known_article_urls: set, art_url_threshold: int,
                       page_num: int):
    """Active archive. We allow intersecting elements as the archive may have been moved"""
    next_page_url = None
    if len(known_article_urls) == 0 or len(article_urls - known_article_urls) > art_url_threshold:
        next_page_url = base_url.replace('#pagenum', str(page_num))  # Must generate URL

    return next_page_url

def stop_on_empty_or_taboo(base_url: str, article_urls: set, taboo_article_urls: set, page_num: int):
    """Stop on empty archive or on taboo URLs if they are defined"""
    if len(article_urls) == 0 or len(taboo_article_urls.intersection(article_urls)) > 0:
        next_page_url = None
    else:
        next_page_url = base_url.replace('#pagenum', str(page_num))  # Must generate URL

# TODO there is more! E.g. when the item order is not stable

def extract_articles_and_gen_next_page_link(base_url: str, curr_page_url: str, archive_page_raw_html: str,
                                            is_infinite_scrolling: bool = False,
                                            first_page: bool = False, page_num: int = 1,
                                            logger: Logger = DummyLogger()):
    # 1) We need article URLs here to reliably determine the end of pages in some cases
    # TODO insert the appropriate strategy here!
    extract_article_urls_from_page_fun = lambda *x: ''
    article_urls = extract_article_urls_from_page_fun(archive_page_raw_html)
    if len(article_urls) == 0 and (not is_infinite_scrolling or first_page):
        logger.log('WARNING', curr_page_url, 'Could not extract URLs from the archive!', sep='\t')
    # 3a-I) Generate next-page URL or None if there should not be any
    # TODO insert the appropriate strategy here!
    find_next_page_url = lambda *x: ''
    next_page_url = find_next_page_url(base_url, page_num, archive_page_raw_html, article_urls)
    return article_urls, next_page_url


# This is a general strategy to crawl an archive
def gen_article_urls_and_subpages(base_url: str, downloader, extract_articles_and_gen_next_page_link_fun,
                                  bad_urls: set = None, good_urls: set = None, good_urls_filename: str = None,
                                  problematic_urls: set = None, problematic_urls_filename: str = None,
                                  initial_page_num: str = '0', min_pagenum: int = 0,
                                  is_infinite_scrolling: bool = False, max_tries: int = 3,
                                  ignore_archive_cache: bool = False, logger: Logger = DummyLogger()):
    """Generates article URLs from a supplied URL including the on-demand sub-pages that contains article URLs"""
    if bad_urls is None:
        bad_urls = set()
    if good_urls is None:
        good_urls = set()
    if problematic_urls is None:
        problematic_urls = set()

    page_num = min_pagenum
    tries_left = max_tries
    first_page = True

    with write_set_contents_to_file(good_urls, good_urls_filename) as good_urls_add, \
            write_set_contents_to_file(problematic_urls, problematic_urls_filename) as problematic_urls_add:
        # 1) Add initial pagenum if there is any
        next_page_url = base_url.replace('#pagenum', initial_page_num)
        while next_page_url is not None or tries_left > 0:
            # 2) Download the page
            raw_html = downloader.download_url(next_page_url, ignore_archive_cache)
            tries_left -= 1
            curr_page_url = next_page_url
            next_page_url = None

            # 3) Process downloaded page
            if raw_html is not None:  # 3a) Download succeeded
                # 3a-I) Note good URL
                good_urls_add(curr_page_url)
                # 3a-II) Do site-specific extractions
                article_urls, next_page_url = extract_articles_and_gen_next_page_link_fun(base_url, raw_html,
                                                                                          curr_page_url,
                                                                                          first_page,
                                                                                          is_infinite_scrolling,
                                                                                          page_num, logger)

                # 3a-III) Handle if there is a next page or not
                if next_page_url is not None:
                    tries_left = max_tries  # Restore tries_left for the next page
                else:
                    tries_left = 0  # We have arrived to the end
                page_num += 1  # Bump pagenum for next round
                first_page = False
                logger.log('DEBUG', 'URLs/ARCHIVE PAGE', curr_page_url, len(article_urls), sep='\t')

                # 3a-IV) Yield article urls
                yield from article_urls

            elif tries_left > 0:  # 3b) Retry download
                logger.log('WARNING', curr_page_url, f'Retrying URL ({max_tries - tries_left})!', sep='\t')
                next_page_url = curr_page_url  # 3b-I) Restore URL for retrying
            else:  # 3c) Download failed
                if curr_page_url not in bad_urls and curr_page_url not in downloader.good_urls and \
                        curr_page_url not in downloader.url_index:  # URLs in url_index should not be a problem
                    problematic_urls_add(curr_page_url)  # New possibly bad URL
                    logger.log('ERROR', curr_page_url, f'There are no tries left for URL!', sep='\t')
