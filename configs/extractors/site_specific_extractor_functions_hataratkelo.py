#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import re
from os.path import abspath, dirname, join as os_path_join

from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader, Logger


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_hataratkelo(archive_page_raw_html):
    """extracts and returns next page URL from an HTML code if there is one...
        Specific for https://hataratkelo.blog.hu koronavirus
        :returns string of url if there is one, None otherwise"""
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_div = soup.find('div', class_='pager next')
    if next_page_div is not None:
        next_page = next_page_div.find('a', {'href': True})
        if next_page is not None and next_page.has_attr('href'):
            ret = re.sub('token=[0-9-a-f]+&?', '', next_page.attrs['href'])  # Remove token parameter!
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing hataratkelo')
    text = w.download_url('https://hataratkelo.blog.hu/page/2')
    assert extract_next_page_url_hataratkelo(text) == 'https://hataratkelo.blog.hu/page/3'
    text = w.download_url('https://hataratkelo.blog.hu/page/686')
    assert extract_next_page_url_hataratkelo(text) is None
    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC extract_next_page_url FUNCTIONS ####################################################################

# BEGIN SITE SPECIFIC extract_article_urls_from_page FUNCTIONS #########################################################


def safe_extract_hrefs_from_a_tags(main_container):
    """
    Helper function to extract href from a tags
    :param main_container: An iterator over Tag()-s
    :return: Generator over the extracted links
    """
    for a_tag in main_container:
        a_tag_a = a_tag.find('a')
        if a_tag_a is not None and 'href' in a_tag_a.attrs:
            yield a_tag_a['href']


def extract_article_urls_from_page_hataratkelo(archive_page_raw_html):
    """extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs"""
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing hataratkelo')
    text = w.download_url('https://hataratkelo.blog.hu/page/2')
    extracted = extract_article_urls_from_page_hataratkelo(text)
    expected = {'https://hataratkelo.blog.hu/2021/07/16/utcazeneszbol_adotanacsado_svajcban',
                'https://hataratkelo.blog.hu/2021/07/17/bringaval_a_duna_menten',
                'https://hataratkelo.blog.hu/2021/07/18/hogyan_lehetsz_nemet_allampolgar',
                'https://hataratkelo.blog.hu/2021/07/15/kiderult_hol_elnek_a_nagy-britanniai_magyarok',
                'https://hataratkelo.blog.hu/2021/07/19/etelek_es_turokeszites_a_paradicsomban'}
    assert (extracted, len(extracted)) == (expected, 5)

    text = w.download_url('https://hataratkelo.blog.hu/page/686')
    extracted = extract_article_urls_from_page_hataratkelo(text)
    expected = {'https://hataratkelo.blog.hu/2012/07/19/miert_megyek_el',
                'https://hataratkelo.blog.hu/2012/07/19/hat_ok_amiert_maradni_kell',
                'https://hataratkelo.blog.hu/2012/07/19/valasztunk_egy_orszagot_magunknak',
                'https://hataratkelo.blog.hu/2012/07/19/ket_het_mulva_svedorszagba_koltozunk'}
    assert (extracted, len(extracted)) == (expected, 4)

    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################


def main_test():
    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_hataratkelo.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)), '../../tests/extract_article_urls_from_'
                                                                   'page_hataratkelo.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
