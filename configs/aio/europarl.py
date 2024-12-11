#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import date

from bs4 import BeautifulSoup
from mplogger import Logger, DummyLogger

from webarticlecurator import WarcCachingDownloader, gen_article_urls_and_subpages, date_range


def next_page_by_link_europarl(raw_html, last_archive_page_url=None):
    """If there is a "next page" link, find it and use that"""
    soup = BeautifulSoup(raw_html, 'lxml')
    next_page_tag = soup.find('a', title='Next Page')

    next_page_url = None
    if next_page_tag is not None and next_page_tag.has_attr('href'):
        next_page_url = f'https://eur-lex.europa.eu{next_page_tag.attrs["href"][1:]}'

    # Stop on last archive page specified in config (The default is None, which will match nothing)
    if next_page_url == last_archive_page_url:
        next_page_url = None

    return next_page_url


def extract_article_urls_from_page_europarl(raw_html):
    soup = BeautifulSoup(raw_html, 'lxml')

    ret = []
    for div_tag in soup.find_all('div', class_='SearchResult'):
        a_tag = div_tag.find('a', class_='title')
        if a_tag is not None and a_tag.has_attr('href'):
            ret.append(f'https://eur-lex.europa.eu{a_tag.attrs["href"][1:]}')

    return ret

def extract_articles_and_gen_next_page_link_europarl(base_url: str, curr_page_url: str, archive_page_raw_html: str,
                                                     is_infinite_scrolling: bool = False,
                                                     first_page: bool = False, page_num: int = 1,
                                                     logger: Logger = DummyLogger()):
    # 1) We need article URLs here to reliably determine the end of pages in some cases
    # TODO insert the appropriate strategy here!
    article_urls = extract_article_urls_from_page_europarl(archive_page_raw_html)
    if len(article_urls) == 0 and (not is_infinite_scrolling or first_page):
        logger.log('WARNING', curr_page_url, 'Could not extract URLs from the archive!', sep='\t')
    # 3a-I) Generate next-page URL or None if there should not be any
    # TODO insert the appropriate strategy here!
    next_page_url = next_page_by_link_europarl(archive_page_raw_html)
    return article_urls, next_page_url

def gen_article_links(logger):
    # Crawler stuff
    downloader = WarcCachingDownloader(None, 'europarl_new.warc.gz', logger)

    # Portal stuff
    base_url_template = 'https://eur-lex.europa.eu/search.html?lang=en&scope=EURLEX&type=quick&' \
                        'sortOne=IDENTIFIER_SORT&sortOneOrder=desc&&page=#pagenum&DD_YEAR=#year'

    # Early years not continous
    years= ['FV_OTHER', 1001, 1807, 1808, 1809, 1854, 1865, 1867, 1868, 1870, 1872, 1878, 1879, 1881, 1882, 1883, 1885,
            1889, 1897, 1900, 1902, 1903, 1904, 1906, 1909, 1917, 1918, 1921, 1922, 1924, 1925, 1927] + \
           list(range(1929, 1941))  # 1941 is missing

    for year in years:
        base_url = base_url_template.replace('#year', str(year))
        g = gen_article_urls_and_subpages(base_url, downloader, extract_articles_and_gen_next_page_link_europarl,
                                          initial_page_num='1', min_pagenum=1, logger=logger)
        yield from g

    # From this year all years appear
    for base_url in date_range(base_url_template, date(1942, 1, 1), date(date.today().year + 1, 1, 1), False):
        g = gen_article_urls_and_subpages(base_url, downloader, extract_articles_and_gen_next_page_link_europarl,
                                          initial_page_num='1', min_pagenum=1, logger=logger)
        yield from g

    logger.log('INFO', 'Done')

def main():
    logger = Logger('europarl_new.log', logfile_level='DEBUG', console_level='DEBUG')
    article_downloader = WarcCachingDownloader(None, 'europarl_articles.warc.gz', logger,
                                               download_params={'err_threshold': 100})
    for link in gen_article_links(logger):
        article_downloader.download_url(link)

if __name__ == '__main__':
    main()
