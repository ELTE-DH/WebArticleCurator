#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join

from mplogger import Logger
from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_termvil(archive_page_raw_html):
    """extracts and returns next page URL from an HTML code if there is one...
        Specific for https://termvil.hu
        :returns string of url if there is one, None otherwise"""
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_div = soup.find('p', class_='pageNext')
    if next_page_div is not None:
        next_page = next_page_div.find('a', {'href': True})
        if next_page is not None and next_page.has_attr('href'):
            ret = next_page.attrs['href']
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing termvil')
    text = w.download_url('https://termvil.hu/cikkek/page/1/')
    assert extract_next_page_url_termvil(text) == \
           'https://termvil.hu/cikkek/page/2/'
    text = w.download_url('https://termvil.hu/cikkek/page/2/')
    assert extract_next_page_url_termvil(text) == \
           'https://termvil.hu/cikkek/page/3/'
    text = w.download_url(
        'https://termvil.hu/cikkek/page/16/')
    assert extract_next_page_url_termvil(text) is None
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


def extract_article_urls_from_page_termvil(archive_page_raw_html):
    """extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs"""
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    article_list = soup.find('div', class_='btContent')
    main_container = article_list.find_all('span', class_='bt_bb_headline_content')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})
    test_logger.log('INFO', 'Testing termvil')
    text = w.download_url('https://termvil.hu/cikkek/page/1/')
    extracted = extract_article_urls_from_page_termvil(text)
    expected = {'https://termvil.hu/2021/05/18/szakkollegiumi-eredmenyhirdetes/',
                'https://termvil.hu/2021/04/08/egyedul-az-amazonason/',
                'https://termvil.hu/2021/04/06/olvasonaplo/',
                'https://termvil.hu/2021/05/06/2021-majusi-szamunkbol/',
                'https://termvil.hu/2021/05/06/xxx-eredmenyhirdetes/',
                'https://termvil.hu/2021/04/01/az-iss-szuletesnapjara/',
                'https://termvil.hu/2021/05/01/elhunyt-hamori-jozsef/',
                'https://termvil.hu/2021/06/02/2021-juniusi-szamunkbol/',
                'https://termvil.hu/2021/07/08/2021-juliusi-szamunkbol/',
                'https://termvil.hu/2021/04/13/fekezhetetlen-fellangolas/'}

    assert (extracted, len(extracted)) == (expected, 10)
    text = w.download_url('https://termvil.hu/cikkek/page/2/')
    extracted = extract_article_urls_from_page_termvil(text)
    expected = {'https://termvil.hu/2021/02/25/egy-meteoritgyujto-kalandjai/',
                'https://termvil.hu/2021/03/18/csillagkozi-portol-a-mofettakig/',
                'https://termvil.hu/2021/03/04/a-legkegyetlenebb-hely/',
                'https://termvil.hu/2021/03/02/a-2019-es-ev-asvanya-a-galenit/',
                'https://termvil.hu/2021/03/25/elenkulo-eghajlatvaltozas/',
                'https://termvil.hu/2021/03/16/hormonalis-rombolok/',
                'https://termvil.hu/2021/03/30/delrol-erkezo-hoditok/',
                'https://termvil.hu/2021/03/23/kalendariumok-es-orak/',
                'https://termvil.hu/2021/03/11/a-pikkelysomor-es-gyogyitasa/',
                'https://termvil.hu/2021/03/09/tibet-paleo-es-neotektonikaja/'}

    assert (extracted, len(extracted)) == (expected, 10)

    text = w.download_url('https://termvil.hu/cikkek/page/16/')
    extracted = extract_article_urls_from_page_termvil(text)
    expected = {'https://termvil.hu/2018/09/04/2018-szeptemberi-szamunkbol/',
                'https://termvil.hu/2018/08/03/2018-augusztusi-szamunkbol/',
                'https://termvil.hu/2018/07/04/2018-juliusi-szamunkbol/',
                'https://termvil.hu/2018/07/19/a-foldtan-szuletese-magyarorszagon/',
                'https://termvil.hu/2018/07/26/valtozo-eghajlatunk-nyomaban/',
                'https://termvil.hu/2018/07/03/xxviii-versenyszabalyzat/',
                'https://termvil.hu/2018/09/04/robbano-csillagok-videke/'}
    assert (extracted, len(extracted)) == (expected, 7)

    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################


def main_test():
    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_termvil.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_termvil.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
