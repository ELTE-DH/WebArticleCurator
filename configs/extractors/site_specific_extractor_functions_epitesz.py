#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join
import json
from bs4 import BeautifulSoup
from webarticlecurator import WarcCachingDownloader


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_epiteszforum(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for https://epiteszforum.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='right')
    if next_page is not None and next_page.has_attr('href'):
        url_end = next_page.attrs['href']
        ret = f'https://epiteszforum.hu{url_end}'
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing epiteszforum')
    text = w.download_url('https://epiteszforum.hu/archivum?search=&p=2')
    assert extract_next_page_url_epiteszforum(text) == 'https://epiteszforum.hu/archivum?search=&p=3'
    text = w.download_url('https://epiteszforum.hu/archivum?search=&p=486')
    assert extract_next_page_url_epiteszforum(text) is None
    text = w.download_url('https://epiteszforum.hu/archivum?search=&p=487')
    assert extract_next_page_url_epiteszforum(text) == 'https://epiteszforum.hu/archivum?search=&p=488'
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


def extract_article_urls_from_page_epiteszforum(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='title')
    urls = {f'https://epiteszforum.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing epiteszforum')
    text = w.download_url('https://epiteszforum.hu/archivum?search=&p=2')
    extracted = extract_article_urls_from_page_epiteszforum(text)
    expected = {'https://epiteszforum.hu/okologikus-epiteszet--epiteszeti-eszkozok',
                'https://epiteszforum.hu/otvenlakasos-tarsashaz-epult-az-egykori-balatonlellei-szot-udulo-helyen',
                'https://epiteszforum.hu/kerekparos-kozlekedesfejlesztes-budapesten-',
                'https://epiteszforum.hu/architizer-szakmai-zsuri-dijat-nyert-a-bord-epitesz-studio-a-debreceni'
                '-aquaticum-terveivel',
                'https://epiteszforum.hu/toronyhaz-vita-a-felhokarcolo-mint-innovacio',
                'https://epiteszforum.hu/kozepiskolasok-terveztek-uszo-egyetemet-a-balatoni-kozseg-vizpartjara-',
                'https://epiteszforum.hu/nehany-gondolat-a-budai-var-varoskeperol--roth-janos-irasa',
                'https://epiteszforum.hu/pillantasok-a-feny-fele-tiz-kulonleges-templom-a-szocializmus-eveibol',
                'https://epiteszforum.hu/kiirtak-a-meghivasos-tervpalyazatot-az-uj-pazmany-campusra',
                'https://epiteszforum.hu/templomot-irodat-es-csaladi-hazat-is-jutalmaztak--atadtak-az-ev-tetoje'
                '-nivodijakat',
                'https://epiteszforum.hu/jo-egyutt-ujrakezdeni--a-2021-es-epitesz-regatta-margojara',
                'https://epiteszforum.hu/esztergom-szalloda',
                'https://epiteszforum.hu/mi-lesz-veled-nyugati-ter-ii--az-aluljaro-fejlesztese-',
                'https://epiteszforum.hu/modernizmus-ujratoltve--lang-muvelodesi-kozpont',
                'https://epiteszforum.hu/egy-hely--matyasfold',
                'https://epiteszforum.hu/kandalloval-is-teljesitheto-a-megujulo-energia-reszarany',
                'https://epiteszforum.hu/het-evtized-szarnyas-vaskereken--a-budapesti-gyermekvasut-allomasai',
                'https://epiteszforum.hu/az-epuletek-szelloztetese-',
                'https://epiteszforum.hu/otthon-az-egykori-nyaralotelepen',
                'https://epiteszforum.hu/101--falvai-balazs-dla',
                'https://epiteszforum.hu/nehany-gondolat-a-budai-var-varoskeperol-22--roth-janos-irasa',
                'https://epiteszforum.hu/pontipoly-fesztival-es-ter-kepzo-epitotabor---a-leptek-ami-igazan-szeretheto',
                'https://epiteszforum.hu/hamarosan-elkeszul-az-uj-pasareti-kozossegi-haz-',
                'https://epiteszforum.hu/56-os-magyar-epiteszek-schweger-peter',
                'https://epiteszforum.hu/101--arkovics-lilla',
                'https://epiteszforum.hu/megujult-a-rumbach-utcai-zsinagoga--ismet-vallasi-es-kulturalis-elet-koltozik'
                '-az-epuletbe',
                'https://epiteszforum.hu/ne-vonjak-el-a-figyelmunket-az-oriasi-falmatricak--az-europa-design-es-az-ev'
                '-irodai',
                'https://epiteszforum.hu/elkezdodott-az-uj-csepeli-kozpark-kialakitasanak-tervezese--kerdoivben-varjak'
                '-a-javaslatokat',
                'https://epiteszforum.hu/othernity--a-magyar-pavilon-nemzetkozi-visszhangja',
                'https://epiteszforum.hu/ha-eppen-a-zaj-a-baj--egy-szombathelyi-epuletegyuttes-akusztikai-megoldasa',
                'https://epiteszforum.hu/megjelent-az-archicad-25-a-graphisoft-piacvezeto-bim-szoftverenek-legujabb'
                '-valtozata',
                'https://epiteszforum.hu/a-szervezok-varjak-a-javaslatokat-a-8-ugo-rivolta-dij-jeloltjeire'}

    assert (extracted, len(extracted)) == (expected, 32)

    text = w.download_url('https://epiteszforum.hu/archivum?search=&p=486')
    extracted = extract_article_urls_from_page_epiteszforum(text)
    expected = {'https://epiteszforum.hu/elkeszult-a-komaromi-csillagerod-felujitasa',
                'https://epiteszforum.hu/abbol-hogy-valamit-valaki-jol-megcsinalt-meg-soha-nem-szarmazott-hiba',
                'https://epiteszforum.hu/vidor-ferenc-hidveres-a-varosokat-erinto-elmeletek-es-a-gyakorlat'
                '-mindennapjaink-valosaga-kozott',
                'https://epiteszforum.hu/borvendeg-bela-torzo',
                'https://epiteszforum.hu/nyilvanos-vita-a-nemzeti-szinhaz-kapcsan-felmerult-epiteszeti-etikai'
                '-kerdesekrol',
                'https://epiteszforum.hu/az-orszagos-foepiteszi-kollegium-1999-2000',
                'https://epiteszforum.hu/ybl-dij-2000',
                'https://epiteszforum.hu/solymos-sandor-a-posztmodern-manierizmus',
                'https://epiteszforum.hu/nyitott-ter-elvalasztva',
                'https://epiteszforum.hu/alkotoi-het-az-epiteszkaron-2000'}

    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################


if __name__ == '__main__':
    from webarticlecurator import WarcCachingDownloader, Logger

    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_epiteszforum.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)), '../../tests/extract_article_urls_from_'
                                                                   'page_epiteszforum.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)
