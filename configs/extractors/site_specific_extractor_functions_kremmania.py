#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join

from mplogger import Logger
from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_kremmania_forum(archive_page_raw_html):
    """extracts and returns next page URL from an HTML code if there is one...
        Specific for https://forum.kremmania.hu
        :returns string of url if there is one, None otherwise"""
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_div = soup.find('div', role='navigation')
    if next_page_div is not None:
        next_page = next_page_div.find('a', {'rel': 'next'})
        if next_page is not None and next_page.has_attr('href'):
            url_end = next_page.attrs['href']
            ret = f'https://forum.kremmania.hu{url_end}'
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing kremmania_forum')
    text = w.download_url('https://forum.kremmania.hu/latest?no_definitions=true&page=0')
    assert extract_next_page_url_kremmania_forum(text) == \
           'https://forum.kremmania.hu/latest?no_definitions=true&page=1'
    text = w.download_url('https://forum.kremmania.hu/latest?no_definitions=true&page=2')
    assert extract_next_page_url_kremmania_forum(text) == \
           'https://forum.kremmania.hu/latest?no_definitions=true&page=3'
    text = w.download_url(
        'https://forum.kremmania.hu/latest?no_definitions=true&page=8')
    assert extract_next_page_url_kremmania_forum(text) is None
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


def extract_article_urls_from_page_kremmania_forum(archive_page_raw_html):
    """extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs"""
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('span', class_='link-top-line')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing kremmania_forum')
    text = w.download_url('https://forum.kremmania.hu/latest?no_definitions=true&page=2')
    extracted = extract_article_urls_from_page_kremmania_forum(text)
    expected = {'https://forum.kremmania.hu/t/sminkjeink-avagy-smin-k-spiraciok/314',
                'https://forum.kremmania.hu/t/teljesen-kezdonek-tanacs-kerestetik/1375',
                'https://forum.kremmania.hu/t/kinek-milyen-haj-all-jol-ki-segit-ebben/398',
                'https://forum.kremmania.hu/t/javaslatok-a-kremmania-oldalhoz/147',
                'https://forum.kremmania.hu/t/hajdusitas-hajtoemeles/1415',
                'https://forum.kremmania.hu/t/mik-a-legikonikusabb-illatok-egy-egyszeru-szereny-40-50-ev-kozotti-no'
                '-szamara/564',
                'https://forum.kremmania.hu/t/probaltal-mar-purito-termekeket/1410',
                'https://forum.kremmania.hu/t/victoria-s-secret-pure-seduction/1419',
                'https://forum.kremmania.hu/t/megbizhato-parfumwebaruhaz/170',
                'https://forum.kremmania.hu/t/cruelty-free-beauty/333',
                'https://forum.kremmania.hu/t/kezdo-tanacs-keres/1493',
                'https://forum.kremmania.hu/t/borproblema-maszkhordas-ota/1487',
                'https://forum.kremmania.hu/t/arc-deco-avagy-arcdekoracio/444',
                'https://forum.kremmania.hu/t/lartisan-parfumeur-kupakban-mi-az-a-kis-kameralencse-szeru-ize-o/1444',
                'https://forum.kremmania.hu/t/podium-spray-avagy-posion-parfum/1434',
                'https://forum.kremmania.hu/t/legjobb-szemkornyekapolok-30-40-50/588',
                'https://forum.kremmania.hu/t/iskolai-fiktiv-szepsegszalon/1451',
                'https://forum.kremmania.hu/t/kedvenc-smink-markatok/101',
                'https://forum.kremmania.hu/t/bio-kozmetikai-termekek-szakdolgozati-kerdoiv/1448',
                'https://forum.kremmania.hu/t/mik-valtak-be-nektek/1421',
                'https://forum.kremmania.hu/t/menyasszonyi-parfum-oszi-eskuvore/1484',
                'https://forum.kremmania.hu/t/rezes-arnyalat-a-hajban-hogyan-semlegesititek/1442',
                'https://forum.kremmania.hu/t/apolt-kezek-labak/197',
                'https://forum.kremmania.hu/t/sminktarolas-otletgyujtes/249',
                'https://forum.kremmania.hu/t/pollenallergia-trukkok-gyogyszerek/1435',
                'https://forum.kremmania.hu/t/sminkecsetek-bevalt-termekek/105',
                'https://forum.kremmania.hu/t/pothaj-apolasa-hajtipusok-felrakasi-technikak/1440',
                'https://forum.kremmania.hu/t/mi-sem-50-osan-szulettunk/58',
                'https://forum.kremmania.hu/t/jo-minosegu-borotva/1416',
                'https://forum.kremmania.hu/t/glossier-rendeles/1433'}

    assert (extracted, len(extracted)) == (expected, 30)

    text = w.download_url('https://forum.kremmania.hu/latest?no_definitions=true&page=8')
    extracted = extract_article_urls_from_page_kremmania_forum(text)
    expected = {'https://forum.kremmania.hu/t/manna-natur-kozmetikum-kedvelok/98',
                'https://forum.kremmania.hu/t/eskuvos-nevu-koromlakk/308',
                'https://forum.kremmania.hu/t/estee-lauder-double-wear-light-utodja/67',
                'https://forum.kremmania.hu/t/k-beauty-az-a-bizonyos-soklepeses-rutin-es-egyeb-josagok/294',
                'https://forum.kremmania.hu/t/syoss-12-59-cool-platinum-blond/338',
                'https://forum.kremmania.hu/t/tester-vs-valosag/163',
                'https://forum.kremmania.hu/t/best-of-2018-evertekelo/204',
                'https://forum.kremmania.hu/t/hidratalo-olajos-borre/128',
                'https://forum.kremmania.hu/t/kivont-kedvencek/81',
                'https://forum.kremmania.hu/t/mi-lesz-a-nem-hasznalt-kedvencekkel/108',
                'https://forum.kremmania.hu/t/oszi-illatok-neked-mi-a-kedvenced/66',
                'https://forum.kremmania.hu/t/kollaboraciok-hiressegek-x-sminkmarkak/236',
                'https://forum.kremmania.hu/t/pattanasos-hatra-tippek/217',
                'https://forum.kremmania.hu/t/a-honap-sminktermeke/49',
                'https://forum.kremmania.hu/t/amerikai-kincsek/244',
                'https://forum.kremmania.hu/t/kulfoldi-oldalak-szepsegapolas-temakorben/230',
                'https://forum.kremmania.hu/t/megoldasok-zsiros-hajra/213',
                'https://forum.kremmania.hu/t/pigment-foltok-anti-aging-40/198',
                'https://forum.kremmania.hu/t/a-hamlo-orr-mindennapos-problemaja/280',
                'https://forum.kremmania.hu/t/ikonikus-termekek-mi-eri-meg-es-mi-nem/88',
                'https://forum.kremmania.hu/t/szajfeny-klasszikus-ruzs-formaban/304',
                'https://forum.kremmania.hu/t/sephora-must-haves/233',
                'https://forum.kremmania.hu/t/kozmetikai-kezelesek/132',
                'https://forum.kremmania.hu/t/2018-legjobb-illatai/167',
                'https://forum.kremmania.hu/t/szepsegvitaminok/175',
                'https://forum.kremmania.hu/t/termeszetesen-gondor-es-vagy-szaraz-haj-apolasa/216',
                'https://forum.kremmania.hu/t/tapasztalatok-organikus-kozmetikumokrol/99'}
    assert (extracted, len(extracted)) == (expected, 27)

    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS #########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ##################################################################


def next_page_of_article_kremmania_forum(archive_page_raw_html):
    """extracts and returns next page URL from an HTML code if there is one...
        Specific for https://forum.kremmania.hu (next page of forum topics)
        :returns string of url if there is one, None otherwise"""
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('link', rel='next')
    if next_page is not None and next_page.has_attr('href'):
        url_end = next_page.attrs['href']
        ret = f'https://forum.kremmania.hu{url_end}'
    return ret


def next_page_of_article_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing kremmania_forum')
    text = w.download_url('https://forum.kremmania.hu/t/mi-sem-50-osan-szulettunk/58?page=5')
    assert next_page_of_article_kremmania_forum(text) == 'https://forum.kremmania.hu/t/mi-sem-50-osan-szulettunk/58' \
                                                         '?page=6'
    text = w.download_url('https://forum.kremmania.hu/t/mi-sem-50-osan-szulettunk/58?page=9')
    assert next_page_of_article_kremmania_forum(text) is None
    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################


def main_test():
    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/'
                                                                    'next_page_url_kremmania_forum.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article_kremmania'
                                                                            '_forum.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_kremmania_forum.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
