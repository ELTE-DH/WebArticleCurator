#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import json
from os.path import abspath, dirname, join as os_path_join

from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader, Logger


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################
def extract_next_page_url_24hu(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for 24.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='next page-numbers')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_alfahir(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for alfahir.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('li', class_='pager__item pager__item--next')
    if next_page is not None:
        next_page_link = next_page.find('a')
        if next_page_link is not None and 'href' in next_page_link.attrs:
            url_end = next_page_link.attrs['href']
            ret = f'https://alfahir.hu/kereso{url_end}'
    return ret


def extract_next_page_url_hvg(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for hvg.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='arrow next')
    if next_page is not None and next_page.attrs is not None:
        url_end = next_page.attrs['href'].replace('?ver=1', '')
        ret = f'https://hvg.hu{url_end}'
    return ret


def extract_next_page_url_magyarnarancs(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for magyarnarancs.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('div', class_='text-left my-5')
    if next_page is not None:
        next_page_link = next_page.find('a')
        if next_page_link is not None and 'href' in next_page_link.attrs:
            url_end = next_page_link.attrs['href']
            ret = f'https://magyarnarancs.hu{url_end}'
    return ret


def extract_next_page_url_merce(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for merce.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(attrs={'class': 'track-act', 'data-act': 'next-posts'})
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing 24hu')
    text = w.download_url('https://24.hu/kultura/2019/03/15/')
    assert extract_next_page_url_24hu(text) is None
    text = w.download_url('https://24.hu/szorakozas/2018/04/18/')
    assert extract_next_page_url_24hu(text) == 'https://24.hu/szorakozas/2018/04/18/page/2/'
    text = w.download_url('https://24.hu/belfold/2018/04/08/')
    assert extract_next_page_url_24hu(text) == 'https://24.hu/belfold/2018/04/08/page/2/'
    text = w.download_url('https://24.hu/belfold/2018/04/08/page/5/')
    assert extract_next_page_url_24hu(text) == 'https://24.hu/belfold/2018/04/08/page/6/'
    text = w.download_url('https://24.hu/belfold/2018/04/08/page/9/')
    assert extract_next_page_url_24hu(text) is None
    text = w.download_url('https://24.hu/fn/gazdasag/2014/04/16/')
    assert extract_next_page_url_24hu(text) is None
    text = w.download_url('https://24.hu/fn/kozelet/2017/03/13/')
    assert extract_next_page_url_24hu(text) is None

    test_logger.log('INFO', 'Testing istentudja_24hu')
    text = w.download_url('https://istentudja.24.hu/tag/bun-es-bunhodes/')
    assert extract_next_page_url_24hu(text) == 'https://istentudja.24.hu/tag/bun-es-bunhodes/page/2/'
    text = w.download_url('https://istentudja.24.hu/tag/csaladi-otthonteremtesi-kedvezmeny-csok/')
    assert extract_next_page_url_24hu(text) is None

    test_logger.log('INFO', 'Testing rangado_24hu')
    text = w.download_url('https://rangado.24.hu/author/rangado/')
    assert extract_next_page_url_24hu(text) == 'https://rangado.24.hu/author/rangado/page/2/'
    text = w.download_url('https://rangado.24.hu/author/pincesil/page/5/')
    assert extract_next_page_url_24hu(text) is None

    test_logger.log('INFO', 'Testing roboraptor_24hu')
    text = w.download_url('https://roboraptor.24.hu/film/')
    assert extract_next_page_url_24hu(text) == 'https://roboraptor.24.hu/film/page/2/'
    text = w.download_url('https://roboraptor.24.hu/kepregeny/page/11/')
    assert extract_next_page_url_24hu(text) is None

    test_logger.log('INFO', 'Testing sokszinuvidek_24hu')
    text = w.download_url('https://sokszinuvidek.24.hu/author/sokszinuvidek/')
    assert extract_next_page_url_24hu(text) == 'https://sokszinuvidek.24.hu/author/sokszinuvidek/page/2/'
    text = w.download_url('https://sokszinuvidek.24.hu/author/dobocsa/page/3/')
    assert extract_next_page_url_24hu(text) is None

    test_logger.log('INFO', 'Testing alfahir')
    text = w.download_url('https://alfahir.hu/kereso?kereses=&from=2015-08-31&to=2015-08-31&'
                          'field_authors&field_tags&page=0')
    assert extract_next_page_url_alfahir(text) == 'https://alfahir.hu/kereso?kereses=&from=2015-08-31&to=2015-08-31&' \
                                                  'field_authors&field_tags&page=1'
    text = w.download_url('https://alfahir.hu/kereso?kereses=&from=2011-12-31&to=2011-12-31&'
                          'field_authors&field_tags&page=2')
    assert extract_next_page_url_alfahir(text) is None

    test_logger.log('INFO', 'Testing hvg')
    text = w.download_url('https://hvg.hu/itthon/9999')
    assert extract_next_page_url_hvg(text) == 'https://hvg.hu/itthon/10000'
    text = w.download_url('https://hvg.hu/vilag/1')
    assert extract_next_page_url_hvg(text) == 'https://hvg.hu/vilag/2'
    text = w.download_url('https://hvg.hu/gazdasag/2850')
    assert extract_next_page_url_hvg(text) == 'https://hvg.hu/gazdasag/2851'
    text = w.download_url('https://hvg.hu/tudomany/1800')
    assert extract_next_page_url_hvg(text) == 'https://hvg.hu/tudomany/1801'
    text = w.download_url('https://hvg.hu/w/15')
    assert extract_next_page_url_hvg(text) is None
    text = w.download_url('https://hvg.hu/kultura/1')
    assert extract_next_page_url_hvg(text) == 'https://hvg.hu/kultura/2'
    text = w.download_url('https://hvg.hu/elet/1600')
    assert extract_next_page_url_hvg(text) == 'https://hvg.hu/elet/1601'

    test_logger.log('INFO', 'Testing magyarnarancs')
    text = w.download_url('https://magyarnarancs.hu/kereses?search_txt=.&search_szerzo='
                          '&search_idoszak_tol=2021-03-23&search_idoszak_ig=2021-03-23')
    assert extract_next_page_url_magyarnarancs(text) == 'https://magyarnarancs.hu/kereses?search_txt=.&' \
                                                        'search_szerzo=&search_idoszak_tol=2021-03-23&' \
                                                        'search_idoszak_ig=2021-03-23&page=2'
    text = w.download_url('https://magyarnarancs.hu/kereses?search_txt=.&search_szerzo=&'
                          'search_idoszak_tol=2006-03-23&search_idoszak_ig=2006-03-23&page=2')
    assert extract_next_page_url_magyarnarancs(text) == 'https://magyarnarancs.hu/kereses?search_txt=.&' \
                                                        'search_szerzo=&search_idoszak_tol=2006-03-23&' \
                                                        'search_idoszak_ig=2006-03-23&page=3'
    text = w.download_url('https://magyarnarancs.hu/kereses?search_txt=.&search_szerzo=&'
                          'search_idoszak_tol=2004-11-18&search_idoszak_ig=2004-11-18&page=3')
    assert extract_next_page_url_magyarnarancs(text) is None

    test_logger.log('INFO', 'Testing merce')
    text = w.download_url('https://merce.hu/tag/oktatas/page/72/')
    assert extract_next_page_url_merce(text) is None
    text = w.download_url('https://merce.hu/tag/nok/')
    assert extract_next_page_url_merce(text) == 'https://merce.hu/tag/nok/page/2/'
    text = w.download_url('https://merce.hu/tag/nok/page/12/')
    assert extract_next_page_url_merce(text) == 'https://merce.hu/tag/nok/page/13/'
    text = w.download_url('https://merce.hu/tag/media/page/23/')
    assert extract_next_page_url_merce(text) is None
    text = w.download_url('https://merce.hu/tag/roma/page/6/')
    assert extract_next_page_url_merce(text) == 'https://merce.hu/tag/roma/page/7/'
    text = w.download_url('https://merce.hu/tag/szegenyseg/page/31/')
    assert extract_next_page_url_merce(text) is None
    text = w.download_url('https://merce.hu/tag/kulfold/')
    assert extract_next_page_url_merce(text) == 'https://merce.hu/tag/kulfold/page/2/'
    text = w.download_url('https://merce.hu/tag/kulfold/page/100/')
    assert extract_next_page_url_merce(text) == 'https://merce.hu/tag/kulfold/page/101/'
    text = w.download_url('https://tett.merce.hu/page/5/')
    assert extract_next_page_url_merce(text) == 'https://tett.merce.hu/page/6/'

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


def safe_remove_hashtag_anchor(main_container, urls):
    """
    Instead of the URL of the posts, we need to take the main URL of the article to avoid duplication
     (the URLs of each post point to the same HTML)
     e.g. https://24.hu/kulfold/2015/11/24/terrorizmus_lelott_orosz_repulo_putyin_sziria_putyin_
           elo/#az-egyik-pilota-biztosan-halott
          ->
          https://24.hu/kulfold/2015/11/24/terrorizmus_lelott_orosz_repulo_putyin_sziria_putyin_elo/
    """

    for link in safe_extract_hrefs_from_a_tags(main_container):
        hashtag_index = link.rfind('#')
        if hashtag_index > -1:
            link = link[:hashtag_index]
        urls.add(link)


def extract_article_urls_from_page_24hu(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('article', class_='-listPost')
    if len(main_container) > 0:
        large = soup.find('article', class_='-largeEntryPost')
        if large is not None:
            main_container.append(large)
    else:  # rangado + sokszinuvidek
        main_container = soup.find_all('h3', attrs={'class': 'm-articleWidget__title -fsMedium'})
    urls = set()
    safe_remove_hashtag_anchor(main_container, urls)
    return urls


def extract_article_urls_from_page_alfahir(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2')
    urls = {f'https://alfahir.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_hang(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    container = soup.find('div', attrs={'class': 'entry post-list col-12 col-md-7'})
    if container is not None:
        main_container = container.find_all('div', class_='entry-title')
        urls = {f'https://hang.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_hvg(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2', class_='heading-3')
    if len(main_container) == 0:  # The "nagyitas" column has a different structure
        main_container = soup.find_all('h1')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    urls_fixed = set()
    for url in urls:
        if not url.startswith('/'):  # Some of the links do not start with '/'.
            url = f'/{url}'
        if not url.startswith('https://hvg.hu'):
            url = f'https://hvg.hu{url}'
        urls_fixed.add(url)
    if not all(url.startswith('https://hvg.hu/brandc') for url in urls_fixed):
        urls_fixed = {url for url in urls_fixed if not url.startswith('https://hvg.hu/brandc')}
    # Filter "brandcontent" and "brandchannel", the same ads appear on every page,
    # it keeps them in the brandcontent column.
    return urls_fixed


def extract_article_urls_from_page_istentudja_roboraptor_24hu(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(attrs={'class': 'm-entryPost__title'})
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_magyarnarancs(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h3', class_='card-title')
    urls = {f'https://magyarnarancs.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_merce(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    container = soup.find('div', attrs={'class': 'postlist track-cat'})
    if container is not None:
        main_container = container.find_all('div', class_='entry-text')
        urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_nepszava(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    archive_json = json.loads(archive_page_raw_html)
    for date_day, day_data in archive_json.items():
        for archive_item in day_data:
            if isinstance(archive_item, dict):  # Handle {"error": "404"}
                urls.add(f'https://nepszava.hu/json/cikk.json?id={archive_item["link"]}')
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing 24')

    text = w.download_url('https://24.hu/kulfold/2002/12/')
    extracted = extract_article_urls_from_page_24hu(text)
    expected = set()
    assert (extracted, len(extracted)) == (expected, 0)

    text = w.download_url('https://24.hu/fn/gazdasag/2009/07/30/')
    extracted = extract_article_urls_from_page_24hu(text)
    expected = {'https://24.hu/fn/gazdasag/2009/07/30/267_alatt_euro/',
                'https://24.hu/fn/gazdasag/2009/07/30/tudomanyos_tippek_magyar_kilabalasra/',
                'https://24.hu/fn/gazdasag/2009/07/30/euforikus_hangulatban_emelkedett_bux/',
                'https://24.hu/fn/gazdasag/2009/07/30/london_240_alatt_lehet/',
                'https://24.hu/fn/gazdasag/2009/07/30/harmas_kormanynak_heim_petertol/',
                'https://24.hu/fn/gazdasag/2009/07/30/meleg_ellenere_sem_fogy/',
                'https://24.hu/fn/gazdasag/2009/07/30/makroadatokra_figyel_bet/'
                }
    assert (extracted, len(extracted)) == (expected, 7)

    text = w.download_url('https://24.hu/belfold/1848/12/15/')
    extracted = extract_article_urls_from_page_24hu(text)
    expected = {'https://24.hu/belfold/1848/12/15/amit_meg_nem_ert_el/'}
    assert (extracted, len(extracted)) == (expected, 1)

    text = w.download_url('https://24.hu/kulfold/2015/11/page/15/')
    extracted = extract_article_urls_from_page_24hu(text)
    expected = {'https://24.hu/kulfold/2015/11/24/az-easyjet-iden-mar-nem-mer-gepet-inditani-sarm-es-sejkbe/',
                'https://24.hu/kulfold/2015/11/24/olaszorszagban-tanitottak-az-ongyilkos-merenyleteket-a-kiutasitott'
                '-marokkoiak/',
                'https://24.hu/kulfold/2015/11/24/nem-hevertek-ki-a-negy-hettel-ezelotti-iskolai-meszarlast'
                '-svedorszagban/',
                'https://24.hu/kulfold/2015/11/24/az-agyonlott-francia-rendorkutya-honapokra-volt-a-nyugdijtol/',
                'https://24.hu/kulfold/2015/11/24/videofelvetelen-buktattak-le-az-iszlam-allamnak-toborzo-noket/',
                'https://24.hu/kulfold/2015/11/24/orban-beallt-montenegro-nato-tagsaga-moge/',
                'https://24.hu/kulfold/2015/11/24/metilalkoholbol-hamisitottak-az-oroszok-a-whiskyt-25-halott/',
                'https://24.hu/kulfold/2015/11/24/ragyujthattak-a-hazat-a-menedekkerokre-nemetorszagban/',
                'https://24.hu/kulfold/2015/11/24/kanada-nem-ker-az-egyedulallo-szir-ferfiakbol/',
                'https://24.hu/kulfold/2015/11/24/a-lelott-orosz-harci-repulo-halott-pilotajarol-tettek-kozze'
                '-felvetelt/',
                'https://24.hu/kulfold/2015/11/24/a-bevarrt-szaju-iraniak-nem-tagitanak-duzzad-a-tomeg-a-gorog'
                '-macedon-hataron/',
                'https://24.hu/kulfold/2015/11/24/terrorizmus_lelott_orosz_repulo_putyin_sziria_putyin_elo/',
                'https://24.hu/kulfold/2015/11/24/orosz-ujsagirokat-ert-raketatalalat-sziriaban/',
                'https://24.hu/kulfold/2015/11/24/a-cia-veszelyesen-alulertekeli-az-iszlam-allamot/',
                'https://24.hu/kulfold/2015/11/24/orban-kinanak-kulcsszerepe-van-a-beke-vedelmeben/',
                'https://24.hu/kulfold/2015/11/24/benzinnel-locsolta-le-beteget-az-orvos-majd-fel-akarta-gyujtani/',
                'https://24.hu/kulfold/2015/11/24/parizsi-terrortamadas-birosag-ele-allitjak-a-terroristak'
                '-szallasadojat/',
                'https://24.hu/kulfold/2015/11/24/porosenko-a-magyar-kepviselok-kettos-allampolgarsagat-vizsgaltatja/',
                'https://24.hu/kulfold/2015/11/24/tombol-a-vihar-gorogorszagban-kevesebb-menedekkero-erkezik/',
                'https://24.hu/kulfold/2015/11/24/sok-menekult-meghalt-az-algeriai-menekulttaborban-pusztito-tuzben/',
                'https://24.hu/kulfold/2015/11/24/szurjak-a-koran-arusok-a-becsiek-szemet/',
                'https://24.hu/kulfold/2015/11/24/egy-egesz-varos-osszefogott-a-felgyujtott-mecset-helyrehozasaert/',
                'https://24.hu/kulfold/2015/11/24/terrorista-szalat-talaltak-a-bosnyak-ejszakai-robbantasban/'
                }
    assert (extracted, len(extracted)) == (expected, 23)

    test_logger.log('INFO', 'Testing alfahir')
    text = w.download_url('https://alfahir.hu/'
                          'kereso?kereses=&from=2015-08-31&to=2015-08-31&field_authors&field_tags&page=0')
    extracted = extract_article_urls_from_page_alfahir(text)
    expected = {'https://alfahir.hu/porosenko_hatbatamadas_es_ukranellenes_megmozdulas_tortent',
                'https://alfahir.hu/vona_nem_a_keritesnek_a_honvedsegnek_kell_megvedeni_a_hatart',
                'https://alfahir.hu/bukarest_fegyverkezik',
                'https://alfahir.hu/miert_nem_keszultunk_fel_idejeben_a_bevandorlasra',
                'https://alfahir.hu/antifasisztak_provokaltak_a_jobbikosokat',
                'https://alfahir.hu/halott_migransok_ket_gyanusitottat_mar_ismert_a_rendorseg',
                'https://alfahir.hu/visszazavarjak_hozzank_becsbol_a_vizum_nelkuli_bevandorlokat',
                'https://alfahir.hu/az_izlandiak_szivesen_latnak_a_bevandorlokat',
                'https://alfahir.hu/a_lelemenyes_migrans_az_eszaki_sarkkor_felol_erkezik',
                'https://alfahir.hu/megdolt_a_fovarosi_melegrekord_1',
                'https://alfahir.hu/szvoboda_orizetbe_vettek_az_ukran_rendor_gyilkosat',
                'https://alfahir.hu/oroszorszag_lemondott_europarol_uj_birodalom_szuletik_keleten',
                'https://alfahir.hu/felrobbant_a_tuzijatekgyar',
                'https://alfahir.hu/elsopro_gyozelem_tapolcan',
                'https://alfahir.hu/harom_reszre_szakadt_orszag',
                }
    assert (extracted, len(extracted)) == (expected, 15)

    text = w.download_url('https://alfahir.hu/'
                          'kereso?kereses=&from=2011-12-31&to=2011-12-31&field_authors&field_tags&page=2')
    extracted = extract_article_urls_from_page_alfahir(text)
    expected = {'https://alfahir.hu/munkasz%C3%BCneti_nap_lesz_valentin-nap-20111231',
                'https://alfahir.hu/j%C3%B6v%C5%91re_csak_interneten_%C3%A1rverezhetik_lak%C3%A1sokat-20111231',
                'https://alfahir.hu/szebb_magyar_%C3%BAj_%C3%A9vet_vide%C3%B3-20111231',
                'https://alfahir.hu/%C3%BAj_t%C3%B6rv%C3%A9nnyel_t%C3%B6rn%C3%A9k_le_az_orvossztr%C3%A1jkot-20111231',
                'https://alfahir.hu/2011_legh%C3%BCly%C3%A9bb_szab%C3%A1lyai-20111231',
                'https://alfahir.hu/janu%C3%A1r_1-t%C5%91l_j%C3%B6n_k%C3%A9nyszert%C3%B6rl%C3%A9s-20111231'
                }
    assert (extracted, len(extracted)) == (expected, 6)

    test_logger.log('INFO', 'Testing hang')
    text = w.download_url('https://hang.hu/publicisztika?page=181')
    extracted = extract_article_urls_from_page_hang(text)
    expected = {'https://hang.hu/publicisztika/novekvo-arnyak-102709',
                'https://hang.hu/marabu/valahol-a-kereszteny-europaban-102708',
                'https://hang.hu/publicisztika/a-jatek-es-a-nemzet-102693',
                'https://hang.hu/publicisztika/ader-janos-allamfo-es-a-kormanyalakitasi-megbizas-102691',
                'https://hang.hu/publicisztika/bantalmazott-orszag-102687',
                'https://hang.hu/publicisztika/kinyirjak-a-kulturat-102668',
                'https://hang.hu/marabu/szezonjelleg-102653',
                'https://hang.hu/publicisztika/a-hus-es-a-serelem-piaca-102637',
                'https://hang.hu/publicisztika/puha-selyemzsinor-barsonyos-zabola-102631',
                'https://hang.hu/marabu/szabad-tarsadalom-102623',
                'https://hang.hu/publicisztika/diszletdemokracia-102601',
                'https://hang.hu/publicisztika/a-hadvezer-102596',
                'https://hang.hu/publicisztika/tommy-robinson-szabadsaga-102579',
                'https://hang.hu/marabu/junius-16dikan-102568',
                'https://hang.hu/publicisztika/klerikaldemokracia-102559',
                }
    assert (extracted, len(extracted)) == (expected, 15)

    text = w.download_url('https://hang.hu/szamizdat-podcast')
    extracted = extract_article_urls_from_page_hang(text)
    expected = {'https://hang.hu/featured/soros-helyett-oktatas-es-egeszsegugy-manipulacio-helyett-igazi-temak-'
                'szamizdat-minipodcast-113729',
                'https://hang.hu/featured/egy-lista-ket-lista-jakab-gyurcsany-mazsola-szamizdat-a-magyar-hang-'
                'minipodcastja-112977',
                'https://hang.hu/szamizdat-podcast/fenyegetett-mentok-egy-halott-ferfi-es-egy-terseg-ahol-mindenki-'
                'aldozat-112796',
                'https://hang.hu/featured/elhittek-a-gyoriek-hogy-van-ket-fidesz-szamizdat-a-magyar-hang-'
                'minipodcastja-112691',
                'https://hang.hu/featured/penzt-vagy-eletet-avagy-kiirthato-e-a-halapenz-az-egeszsegugybol-112602',
                'https://hang.hu/szamizdat-podcast/orban-es-a-rabok-avagy-negy-negyzetmeter-boldogtalansag-112453',
                }
    assert (extracted, len(extracted)) == (expected, 6)

    test_logger.log('INFO', 'Testing hvg')
    text = w.download_url('https://hvg.hu/kultura/1050')
    extracted = extract_article_urls_from_page_hvg(text)
    expected = {'https://hvg.hu/kultura/20140804_Spielbergnek_vegre_osszejott_megkapta_aki',
                'https://hvg.hu/kultura/20140804_Megtalaltak_a_legjobb_szineszt_Balu_megsz',
                'https://hvg.hu/kultura/20140804_Megrongaltak_a_Szepmuveszeti_kiallitasat',
                'https://hvg.hu/kultura/20140804_Ozorara_Crosssound_fesztival',
                'https://hvg.hu/kultura/20140804_batman_kepregeny_arveres',
                'https://hvg.hu/kultura/20140804_Mar_csak_napijegyet_vehet_a_Szigetre',
                'https://hvg.hu/kultura/20140804_Udvaros_Dorottya_60_nezze_vegig_a_szinesz',
                'https://hvg.hu/kultura/20140804_Madonna_producere_dolgozik_az_uj_Queenal',
                'https://hvg.hu/kultura/20140804_Reszeg_hofeherke_fuvezo_Donald_kacsa_rajt',
                'https://hvg.hu/kultura/20140804_Bill_Muray_lesz_Balu_az_uj_Dzsungel_Konyv',
                'https://hvg.hu/kultura/20140804_Elerheto_kozelsegbe_kerul_Tom_Cruise',
                'https://hvg.hu/kultura/20140803_Gigabevetelt_hoz_a_Transformers_folytatas',
                'https://hvg.hu/kultura/20140803_Video_Belerugta_az_etellel_odacsalt_mokus',
                'https://hvg.hu/elet/20140803_Elhunyt_a_Magyar_Radio_vezeto_hangmestere',
                'https://hvg.hu/kultura/20140802_Bors_Nem_lesz_per_Ordog_Nora_fizetett',
                'https://hvg.hu/kultura/20140802_Kiss_Tibor_Noe_interju',
                'https://hvg.hu/kultura/20140801_Tovabb_burjanzik_a_nagy_Petofihistoria',
                'https://hvg.hu/kultura/20140801_Helmut_Kohl_pert_nyert_a_visszaemlekezese',
                'https://hvg.hu/gazdasag/20140801_Meses_gazdagsagok_a_jovoben_nem_lesznek_a',
                'https://hvg.hu/kultura/20140801_A_kutya_az_ember_legjobb_baratja__es_orv',
                }
    assert (extracted, len(extracted)) == (expected, 20)

    text = w.download_url('https://hvg.hu/kultura/2159')
    extracted = extract_article_urls_from_page_hvg(text)
    expected = {'https://hvg.hu/kultura/000000000022B825',
                'https://hvg.hu/kultura/000000000022BBCB',
                'https://hvg.hu/kultura/000000000022331E',
                'https://hvg.hu/kultura/00000000001CE898',
                'https://hvg.hu/kultura/00000000001C9FAE',
                'https://hvg.hu/kultura/00000000001A90D6',
                'https://hvg.hu/kultura/000000000018EAD0',
                'https://hvg.hu/kultura/000000000018862E',
                'https://hvg.hu/kultura/000000000015DF32',
                'https://hvg.hu/kultura/000000000012A04F',
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Testing istentudja_24hu')
    text = w.download_url('https://istentudja.24.hu/tag/agyhalal/')
    extracted = extract_article_urls_from_page_istentudja_roboraptor_24hu(text)
    expected = {'https://istentudja.24.hu/2018/05/20/ki-dont-egy-haldoklo-gyermekrol-isten-tudja/',
                'https://istentudja.24.hu/2014/02/05/ki-dont-eletrol-es-halalrol/'
                }
    assert (extracted, len(extracted)) == (expected, 2)

    test_logger.log('INFO', 'Testing magyarnarancs')
    text = w.download_url('https://magyarnarancs.hu/kereses?search_txt=.&'
                          'search_szerzo=&search_idoszak_tol=2021-03-23&search_idoszak_ig=2021-03-23&page=1')
    extracted = extract_article_urls_from_page_magyarnarancs(text)
    expected = {'https://magyarnarancs.hu/katasztrofa/gerendai-becslesek-szerint-az-ettermek-30-40-'
                'szazaleka-a-nem-fog-kinyitni-a-jarvany-utan-236983',
                'https://magyarnarancs.hu/katasztrofa/a-pfizer-tesztelni-kezdte-szajon-at-szedheto-'
                'koronavirus-elleni-gyogyszeret-236989',
                'https://magyarnarancs.hu/kulpol/gorogorszagba-karanten-es-teszt-nelkul-utazhat-az-'
                'aki-megkapta-az-oltast-236984',
                'https://magyarnarancs.hu/mikrofilm/all-star-csapat-jott-ossze-a-mike-tyson-eletet-bemutato-'
                'sorozatra-236988',
                'https://magyarnarancs.hu/belpol/ezeket-javasolja-a-kamara-a-kereskedelmi-es-szolgaltato-'
                'szektor-mielobbi-ujrainditasa-erdekeben-236991',
                'https://magyarnarancs.hu/katasztrofa/nnk-a-szennyvizben-mert-koronavirus-koncentracio-'
                'novekedese-megallt-236982',
                'https://magyarnarancs.hu/kulpol/aprilistol-az-oltoanyag-ismereteben-lehet-regisztralni-a-'
                'vakcinakra-romaniaban-236986',
                'https://magyarnarancs.hu/bun/halalra-gazolta-ferjet-de-felmentettek-236985',
                'https://magyarnarancs.hu/belpol/a-korhazak-iranyitasa-ala-kerulnek-az-onkormanyzati-'
                'szakrendelok-236993',
                'https://magyarnarancs.hu/lokal/az-onkormanyzat-figyelmeztet-a-normafan-is-elvart-a-'
                'maszkviseles-es-a-tavolsagtartas-236981',
                'https://magyarnarancs.hu/lokal/eltunik-a-belvaros-meghatarozo-uzlethaza-236844',
                'https://magyarnarancs.hu/kulpol/a-feherorosz-rendorseg-orizetbe-vette-a-lengyel-'
                'kisebbseg-vezetojet-236992',
                }
    assert (extracted, len(extracted)) == (expected, 12)

    text = w.download_url('https://magyarnarancs.hu/kereses?search_txt=.&'
                          'search_szerzo=&search_idoszak_tol=2006-03-23&search_idoszak_ig=2006-03-23&page=2')
    extracted = extract_article_urls_from_page_magyarnarancs(text)
    expected = {'https://magyarnarancs.hu/belpol/falvak_kezeben_-_billego_korzetek_varpalota-65289',
                'https://magyarnarancs.hu/belpol/eloversenges_-_lezarult_a_jeloltallitas-65290',
                'https://magyarnarancs.hu/belpol/maskent_gondolkodok_-_civil_szervezetek_birosagi_bejegyzese-65291',
                'https://magyarnarancs.hu/kulpol/mi_mennyi_-_nigeria-65292',
                'https://magyarnarancs.hu/lelek/gatlastalan_kandelaberek_-_tamas_gabor_neurobiologus-65293',
                'https://magyarnarancs.hu/tudomany/ho_alatt_-_lavina-65294',
                'https://magyarnarancs.hu/film2/jol_szoktam_donteni_-_csakanyi_eszter_szineszno-65295',
                'https://magyarnarancs.hu/szinhaz2/halasz_peter_koporsojanal-65296',
                'https://magyarnarancs.hu/zene2/reszletes_amnezia_-_a_holokauszt_mint_kiallitas-65297',
                'https://magyarnarancs.hu/zene2/a_taj_emlekei_-_konkoly_gyula_es_cseke_szilard_kiallitasai_'
                'kepzomuveszet-65298',
                'https://magyarnarancs.hu/zene2/revizionalas_-_hankiss_janos_europa_es_a_magyar_irodalom_a_'
                'honfoglalastol_a_kiegyezesig_konyv-65299',
                'https://magyarnarancs.hu/film2/ha_tulelem_-_aleksandar_zograf_kepregenyrajzolo-65300'
                }
    assert (extracted, len(extracted)) == (expected, 12)

    text = w.download_url('https://magyarnarancs.hu/kereses?search_txt=.&'
                          'search_szerzo=&search_idoszak_tol=2004-11-18&search_idoszak_ig=2004-11-18&page=3')
    extracted = extract_article_urls_from_page_magyarnarancs(text)
    expected = {'https://magyarnarancs.hu/publicisztika/ciganynota-52543'}
    assert (extracted, len(extracted)) == (expected, 1)

    test_logger.log('INFO', 'Testing merce')
    text = w.download_url('https://merce.hu/tag/egeszsegugy/page/69/')
    extracted = extract_article_urls_from_page_merce(text)
    expected = {'https://merce.hu/2015/12/01/az_emberek_donthetnenek_ugy_is_hogy_megvedik_a_berbol_es_'
                'fizetesbol_eloket/',
                'https://merce.hu/2015/11/03/gyurcsany_ferenc_jobbos_coming-outja/',
                'https://merce.hu/2015/10/13/a_helyzet_rendkivuli/',
                'https://merce.hu/2015/10/01/mikozben_a_kormany_a_menekultekkel_foglalkozik_darabjaira_esik_szet_az_'
                'egeszsegugy/',
                'https://merce.hu/2015/09/17/kulon_miniszterium_a_lelki_egeszsegert_a_brit_ellenzek_uj_vezere_szeretne_'
                'nalunk_is_fontos_lenne/',
                }
    assert (extracted, len(extracted)) == (expected, 5)

    test_logger.log('INFO', 'Testing nepszava')
    text = w.download_url('https://nepszava.hu/json/list.json?type_path=tag&data_path=velemeny&pageCount=1')
    extracted = extract_article_urls_from_page_nepszava(text)

    expected = {'https://nepszava.hu/json/cikk.json?id=3129925_az-afgan-kaosz-hete',
                'https://nepszava.hu/json/cikk.json?id=3129924_panoptikum',
                'https://nepszava.hu/json/cikk.json?id=3129923_vitatkozik-a-fidesz',
                'https://nepszava.hu/json/cikk.json?id=3129922_trojai-szent-istvan',
                'https://nepszava.hu/json/cikk.json?id=3129921_huxit',
                'https://nepszava.hu/json/cikk.json?id=3129776_hazai-rejtelmek',
                'https://nepszava.hu/json/cikk.json?id=3129775_rossz-es-rosszabb',
                'https://nepszava.hu/json/cikk.json?id=3129773_otkarikas-szomszedolas',
                'https://nepszava.hu/json/cikk.json?id=3129772_szent-istvan-emlekezete',
                'https://nepszava.hu/json/cikk.json?id=3129774_az-ellopott-alkotmany',
                'https://nepszava.hu/json/cikk.json?id=3129671_ofelsege-a-torpe',
                'https://nepszava.hu/json/cikk.json?id=3129672_hogyan-tovabb-kuba',
                'https://nepszava.hu/json/cikk.json?id=3129673_valsagos-gondolatok',
                'https://nepszava.hu/json/cikk.json?id=3129674_barsony',
                'https://nepszava.hu/json/cikk.json?id=3129675_ebredes',
                'https://nepszava.hu/json/cikk.json?id=3129561_kiveve-a-gyevi-birot',
                'https://nepszava.hu/json/cikk.json?id=3129562_a-tudas-es-a-gyozelem-anyja',
                'https://nepszava.hu/json/cikk.json?id=3129563_ferfias-nereny',
                'https://nepszava.hu/json/cikk.json?id=3129564_megszeliditve',
                'https://nepszava.hu/json/cikk.json?id=3129565_kiterok',
                'https://nepszava.hu/json/cikk.json?id=3129566_tuleles',
                'https://nepszava.hu/json/cikk.json?id=3129446_bekes-beketlenek',
                'https://nepszava.hu/json/cikk.json?id=3129447_a-surgossegin-tul-is-van-ami-surgos',
                'https://nepszava.hu/json/cikk.json?id=3129448_a-szuksegtelen-nulla',
                'https://nepszava.hu/json/cikk.json?id=3129449_beadjak',
                'https://nepszava.hu/json/cikk.json?id=3129450_a-szakallas-bacsi',
                'https://nepszava.hu/json/cikk.json?id=3129451_futtyszo',
                'https://nepszava.hu/json/cikk.json?id=3129333_olcso-benzinnel-a-klimaert',
                'https://nepszava.hu/json/cikk.json?id=3129335_kulon-ut',
                'https://nepszava.hu/json/cikk.json?id=3129336_torzszulott'
                }
    assert (extracted, len(extracted)) == (expected, 30)

    test_logger.log('INFO', 'Testing rangado_24hu')
    text = w.download_url('https://rangado.24.hu/author/dajkab/page/29/')
    extracted = extract_article_urls_from_page_24hu(text)
    expected = {'https://rangado.24.hu/magyar_foci/2020/09/23/dzsudzsak-balazs-debrecen-mezszam-dombi-tibor/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/22/luis-suarez-juventus-olasz-allampolgarsagi-'
                'vizsga-csalas/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/22/zlatan-ibrahimovic-milan-bologna-serie-a-'
                'nyilatkozat/',
                'https://rangado.24.hu/magyar_foci/2020/09/22/ftc-atigazolas-denis-alibec-astra/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/21/luis-suarez-atletico-madrid-atigazolas-alvaro-'
                'morata-juventus/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/21/thiago-alcantara-rekord-premier-league-debutalas-'
                'liverpool-chelsea/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/21/spanyol-bajnoksag-real-sociedad-real-madrid/',
                'https://rangado.24.hu/magyar_foci/2020/09/18/europa-liga-playoff-sorsolas-fehervar-standard-'
                'liege-vojvodina/',
                'https://rangado.24.hu/magyar_foci/2020/09/18/fehervar-europa-liga-playoff-sorsolas-lehetseges-'
                'ellenfelek/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/18/europa-liga-shamrock-rovers-milan-zlatan-'
                'ibrahimovic-mezcsere/',
                'https://rangado.24.hu/magyar_foci/2020/09/17/europa-liga-selejtezo-budapest-honved-malmo/',
                'https://rangado.24.hu/magyar_foci/2020/09/17/europa-liga-selejtezo-szalai-attila-gyoztes-gol/',
                'https://rangado.24.hu/magyar_foci/2020/09/17/europa-liga-selejtezo-hibernians-fehervar/',
                'https://rangado.24.hu/magyar_foci/2020/09/16/marton-gabor-europa-liga-hibernians-fehervar-'
                'koronavirus/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/16/angol-ligakupa-bournemouth-crystal-palace-'
                'buntetoparbaj-wayne-hennessey-asmir-begovic/',
                'https://rangado.24.hu/magyar_foci/2020/09/14/magyar-kupa-elso-fordulo-koronavirusteszt-'
                'nb-i-nb-ii-csapatok-es-ellenfeleik/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/14/kylian-mbappe-tavozas-paris-saint-germain-psg/',
                'https://rangado.24.hu/magyar_foci/2020/09/14/a-diosgyornel-nem-nyugszanak-bele-a-honved-ellen-'
                'tortentekbe/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/14/psg-marseille-balhe-ot-kiallitas-neymar-rasszizmus-'
                'alvaro-gonzalez/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/11/ligue-1-lens-psg-koronavirus-marcin-bulka-nagy-hiba/',
                'https://rangado.24.hu/magyar_foci/2020/09/10/szoboszlai-dominok-napoli-serie-a-salzburg/',
                'https://rangado.24.hu/magyar_foci/2020/09/10/nb-i-ftc-paks-koronavirus/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/10/nyolc-golt-lott-egy-felido-alatt-a-kupaban-a-'
                'szoboszlai-nelkul-felallo-salzburg/',
                'https://rangado.24.hu/nemzetkozi_foci/2020/09/09/ronaldo-real-madrid-bulizas-florentino-perez/',
                }
    assert (extracted, len(extracted)) == (expected, 24)

    test_logger.log('INFO', 'Testing roboraptor_24hu')
    text = w.download_url('https://roboraptor.24.hu/konyv/page/7/')
    extracted = extract_article_urls_from_page_istentudja_roboraptor_24hu(text)
    expected = {'https://roboraptor.24.hu/2018/08/30/a-ferfi-aki-verrel-irta-at-a-civilizaciok-tortenelmet-iain-m-'
                'banks-fegyver-a-kezben-konyvkritika/',
                'https://roboraptor.24.hu/2018/08/25/kapudrog-az-irodalomhoz-megszolalnak-a-magyar-ya-sok/',
                'https://roboraptor.24.hu/2018/08/16/nonel-mar-csak-varazslonak-rosszabb-lenni-a-vilagvege-idejen-'
                'n-k-jemisin-a-megkovult-egbolt-kritika/',
                'https://roboraptor.24.hu/2018/08/15/isten-meg-mindig-odaat-van-konyvkritika-res-a-valosag-szurke-'
                'szoveten/',
                'https://roboraptor.24.hu/2018/08/14/halalos-tura-a-remalmok-vilagaba-amy-plum-alomcsapda-'
                'konyvkritika/',
                'https://roboraptor.24.hu/2018/08/13/a-korrupt-vilagbol-meg-csodaorszag-sem-jelent-kiutat-lorinczy-'
                'judit-elveszett-gondvana-konyvkritika/',
                'https://roboraptor.24.hu/2018/08/11/kapudrog-az-irodalomhoz-a-darkos-cucc-a-jo-ya-anyag/',
                'https://roboraptor.24.hu/2018/08/04/kapudrog-az-irodalomhoz-a-young-adult-irodalom-kezdetei/',
                'https://roboraptor.24.hu/2018/08/01/a-legrosszabb-ami-az-emberiseggel-tortenhet-hogy-eleri-utopikus-'
                'almait-arkagyij-es-borisz-sztrugackij-vegallomas-amalthea-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/30/ez-a-harc-lesz-a-vegso-cixin-liu-a-sotet-erdo-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/25/szurke-lett-ez-a-noir-christopher-moore-noir-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/24/te-mit-tennel-ha-a-ragadozo-vadaszna-rad-predator-verozon-'
                'konyvkritika/',
                'https://roboraptor.24.hu/2018/07/20/kivagy-ha-az-uj-csajod-a-tapetara-petezik-veres-attila-ejfeli-'
                'iskolak-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/18/a-fold-eselye-a-sajat-multjaban-van-wesley-chu-idoostrom-'
                'konyvkritika/',
                'https://roboraptor.24.hu/2018/07/17/szazadokon-ativelo-harc-az-emberek-lelkeert-benyak-zoltan-'
                'az-utolso-emberig-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/16/geek-konyvek-amik-nelkul-nem-elhetsz/',
                'https://roboraptor.24.hu/2018/07/14/ket-vilag-hataran-nem-egyszeru-az-elet-china-mieville-a-'
                'varos-es-a-varos-kozott-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/07/a-negy-majom-gyilkos-csak-az-idodet-lopja-el-j-d-barker-a-'
                'negyedik-majom-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/04/a-nyugdijas-zsoldosok-konnyen-visszatertek-a-munka-vilagaba-'
                'nicholas-eames-a-wadon-kiralyai-konyvkritika/',
                'https://roboraptor.24.hu/2018/07/03/a-cli-fi-terhoditasa-es-a-tengeristen-bosszuja-wu-ming-yi-'
                'rovarszemu-ember-konyvkritika/',
                'https://roboraptor.24.hu/2018/06/25/john-scalzi-lett-a-sci-fi-leslie-l-lawrence-e-john-scalzi-'
                'fejvesztve-kritika/',
                'https://roboraptor.24.hu/2018/06/23/gyarmati-haboru-nemi-magiaval-fuszerezve-az-ezer-nev-kritika/',
                'https://roboraptor.24.hu/2018/06/21/a-magyar-zombiapokalipszis-eloszor-a-muveszvilagot-emeszti-'
                'fel-terey-janos-kali-holtak-konyvkritika/',
                'https://roboraptor.24.hu/2018/06/20/steampunk-utazas-a-loveszarkokon-at-az-alternativ-vilagokba-'
                'szilagyi-zoltan-kaoszsziv-trilogia-konyvkritika/',
                }
    assert (extracted, len(extracted)) == (expected, 24)

    test_logger.log('INFO', 'Testing sokszinuvidek_24hu')
    text = w.download_url('https://sokszinuvidek.24.hu/author/kuno/page/6/')
    extracted = extract_article_urls_from_page_24hu(text)
    expected = {'https://sokszinuvidek.24.hu/otthon-keszult/2020/02/29/kavekapszula-ekszerek-ujrahasznositas/',
                'https://sokszinuvidek.24.hu/kertunk-portank/2020/02/26/haz-hazfelujitas-kiskunmajsa/',
                'https://sokszinuvidek.24.hu/otthon-keszult/2020/02/24/csutka-eszti-csutkamanok-tunderek/',
                'https://sokszinuvidek.24.hu/mozaik/2020/02/24/szokonap-februar-24-szokasok/',
                'https://sokszinuvidek.24.hu/kertunk-portank/2020/02/18/szines-ajtok-pecs/',
                'https://sokszinuvidek.24.hu/mozaik/2020/02/11/nagyvilag-erdekes-piacai/',
                'https://sokszinuvidek.24.hu/kertunk-portank/2020/02/09/florarium-palackkert-magikus-kert/',
                'https://sokszinuvidek.24.hu/viragzo-videkunk/2020/02/03/kocsonyarol-farsangrol-csokoladerol-es-a-'
                'busokrol-szol-a-februar/',
                'https://sokszinuvidek.24.hu/viragzo-videkunk/2020/01/31/5-termeszeti-csoda-magyarorszag/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/27/tv-maci-fules-macko-vackor-retro/',
                'https://sokszinuvidek.24.hu/kertunk-portank/2020/01/26/alomotthon-ihasz/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/19/magyar-telepulesek-teszt/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/11/szahara-vilag-leghosszabb-vonata-train-du-desert/',
                'https://sokszinuvidek.24.hu/otthon-keszult/2020/01/11/kavicskovek-muveszet-ko-lelke/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/08/csuzli-tudnivalok-praktikak/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/03/programok-fesztivalok-januar/',
                'https://sokszinuvidek.24.hu/viragzo-videkunk/2020/01/01/tel-kirandulohely-dobogo-ko-zirc-matra/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/01/kolozsvar-matyas-kiraly-haza/',
                'https://sokszinuvidek.24.hu/mozaik/2020/01/01/feher-hollo-vadmento-alapitvany-allatmentes-pele/',
                'https://sokszinuvidek.24.hu/otthon-keszult/2019/12/30/bole-szilveszter/',
                'https://sokszinuvidek.24.hu/mozaik/2019/12/29/tel-magyarorszag-80-eve/',
                'https://sokszinuvidek.24.hu/kertunk-portank/2019/12/28/sokszinu-videk-legszebb-hazai-2019-valogatas/',
                'https://sokszinuvidek.24.hu/mozaik/2019/12/26/konyyvtarak-nagyvilag-konyvek-templomai/',
                'https://sokszinuvidek.24.hu/kertunk-portank/2019/12/26/szlovakia-csicsmany-hazak-csipke-diszites/',
                }
    assert (extracted, len(extracted)) == (expected, 24)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################

def next_page_of_article_merce(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for merce.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', attrs={'data-act': 'load-more'})
    last_page = soup.select('div.pplive__loadmore-wrap.text-center.d-none')
    if next_page is not None and 'href' in next_page.attrs and len(last_page) == 0:
        # post url eg.: https://merce.hu/pp/2018/04/08/magyarorszag-valaszt/
        # lemondott-az-egyutt-teljes-elnoksege-a-part-jovoje-is-kerdeses/"
        # The next page link can be compiled from the page's own url and the 'loadall=1' from 'pars' (if it exists).
        # We can compile the main url from one of the posts url with truncating the end and the 'pp/' substring
        # which refers to the post.
        firstpost_tag = soup.find('a', {'data-act': 'pp-item-title', 'class': 'track-act', 'href': True})
        if firstpost_tag:
            post_url_cut = firstpost_tag['href'][0:-1].replace('pp/', '')
            url = post_url_cut[:post_url_cut.rfind('/')]
            pars = next_page.attrs['href']
            ret = f'{url}/{pars}'
    return ret


def next_page_of_article_24hu(curr_html):
    # Rangado 24.hu operates with a reverse multipage logic: the start page is the newest page of the article
    bs = BeautifulSoup(curr_html, 'lxml')
    current_page = bs.find('span', class_='page-numbers current')
    if current_page is not None and current_page.get_text().isdecimal():
        current_page_num = int(current_page.get_text())
        other_pages = bs.find_all('a', class_='page-numbers')
        for i in other_pages:
            # Filter span to avoid other tags with class page-numbers (next page button is unreliable!)
            if i.find('span') is None and int(i.get_text()) + 1 == current_page_num and 'href' in i.attrs.keys():
                next_link = i.attrs['href']
                return next_link
    return None


def next_page_of_article_hvg(curr_html):
    bs = BeautifulSoup(curr_html, 'lxml')
    if bs.find('div', class_='G-pagination') is not None:
        next_tag = bs.find('a', {'class': 'arrow next', 'rel': 'next', 'href': True})
        if next_tag is not None:
            next_link = next_tag.attrs['href'].replace('amp;', '')
            link = f'https://hvg.hu{next_link}'
            return link
    return None


def next_page_of_article_alfahir(curr_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for alfahir.hu
        :returns string of url if there is one, None otherwise
    """
    # this function finds the next page till a next button is present on the page
    # sometimes the same post is present on multiple pages and the last page is usually empty
    ret = None
    soup = BeautifulSoup(curr_html, 'lxml')
    next_page_button = soup.find('a', {'class': 'button', 'rel': 'next'})
    if next_page_button is not None and 'href' in next_page_button.attrs:
        url_end = next_page_button.attrs['href']
        ret = f'https://alfahir.hu{url_end}'
    return ret


def next_page_of_article_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing Merce')
    text = w.download_url('https://merce.hu/2018/04/08/magyarorszag-valaszt/')
    assert next_page_of_article_merce(text) == 'https://merce.hu/2018/04/08/magyarorszag-valaszt/?loadall=1'
    text = w.download_url('https://merce.hu/2018/04/08/magyarorszag-valaszt/?loadall=1')
    assert next_page_of_article_merce(text) is None
    text = w.download_url('https://merce.hu/2015/10/12/nincs_mas_valasztas_baratkozni_kell_irannal_kozel'
                          '-keleti_kilatasok/')
    assert next_page_of_article_merce(text) is None

    test_logger.log('INFO', 'Testing rangado_24hu')
    # Test example, 3-page-long-article: starting page without page number [3] >> 2 >> 1 >> None
    text = w.download_url('https://rangado.24.hu/magyar_foci/2019/10/10/eb-selejtezo-horvat-magyar/')
    assert next_page_of_article_24hu(text) == \
           'https://rangado.24.hu/magyar_foci/2019/10/10/eb-selejtezo-horvat-magyar/2/'
    text = w.download_url('https://rangado.24.hu/magyar_foci/2019/10/10/eb-selejtezo-horvat-magyar/2/')
    assert next_page_of_article_24hu(text) == \
           'https://rangado.24.hu/magyar_foci/2019/10/10/eb-selejtezo-horvat-magyar/1/'
    text = w.download_url('https://rangado.24.hu/magyar_foci/2019/10/10/eb-selejtezo-horvat-magyar/1/')
    assert next_page_of_article_24hu(text) is None
    # Test example, 2-page-long-article: starting page without page number [2] >> 1
    text = w.download_url('https://rangado.24.hu/magyar_foci/2019/06/08/eb-selejtezo-azerbajdzsan-magyarorszag/')
    assert next_page_of_article_24hu(text) == \
           'https://rangado.24.hu/magyar_foci/2019/06/08/eb-selejtezo-azerbajdzsan-magyarorszag/1/'
    # Test example, 2-page-long-article: starting page without page number [2] >> 1
    text = w.download_url('https://rangado.24.hu/nemzetkozi_foci/2019/05/29/chelsea-arsenal-europa-liga-donto-baku/')
    assert next_page_of_article_24hu(text) == \
           'https://rangado.24.hu/nemzetkozi_foci/2019/05/29/chelsea-arsenal-europa-liga-donto-baku/1/'
    # Test example, 1-page-long-article: 1 >> None
    text = w.download_url('https://rangado.24.hu/nemzetkozi_foci/2019/05/01/bajnokok-ligaja-elodonto-barcelona'
                          '-liverpool/1/')
    assert next_page_of_article_24hu(text) is None
    # Test example, 1-page-long-article: 1 >> None
    text = w.download_url('https://rangado.24.hu/magyar_foci/2019/11/07/europa-liga-ftc-cszka-moszkva-elo/1/')
    assert next_page_of_article_24hu(text) is None
    # Test example, 1-page-long-article: starting page without page number [1] >> None
    text = w.download_url('https://rangado.24.hu/nemzetkozi_foci/2020/03/10/bl-nyolcaddonto-leipzig-tottenham-valencia'
                          '-atalanta-elo/')
    assert next_page_of_article_24hu(text) is None
    # Test example, 1-page-long-article: starting page without page number [1] >> None
    text = w.download_url('https://rangado.24.hu/magyar_foci/2021/10/11/tenyleg-van-visszaut-boli-ujra-a-fradi-elso'
                          '-csapataval-edzett/')
    assert next_page_of_article_24hu(text) is None

    test_logger.log('INFO', 'Testing 24hu/ belfold, kulfold, rest 1-3')
    text = w.download_url('https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/')
    assert next_page_of_article_24hu(text) == \
           'https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/3/'
    text = w.download_url('https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/3/')
    assert next_page_of_article_24hu(text) == \
           'https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/2/'
    text = w.download_url('https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/2/')
    assert next_page_of_article_24hu(text) == \
           'https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/1/'
    text = w.download_url('https://24.hu/kultura/2016/02/29/oscar-meglehet-a-magyar-oscar/1/')
    assert next_page_of_article_24hu(text) is None
    test_logger.log('INFO', 'Test OK!')

    test_logger.log('INFO', 'Testing HVG')
    text = w.download_url('https://hvg.hu/itthon/20100112_bkv_sztrajk_januar_12_hirek')
    assert next_page_of_article_hvg(text) == \
           'https://hvg.hu/itthon/20100112_bkv_sztrajk_januar_12_hirek/2?isPrintView=False&liveReportItemId=0' \
           '&isPreview=False&ver=1&order=desc'
    text = w.download_url('https://hvg.hu/itthon/20091023_oktober_23_partok/2?isPrintView=False&liveReportItemId=0'
                          '&isPreview=False&ver=1&order=asc')
    assert next_page_of_article_hvg(text) == \
           'https://hvg.hu/itthon/20091023_oktober_23_partok/3?isPrintView=False&liveReportItemId=0&isPreview=' \
           'False&ver=1&order=asc'
    text = w.download_url('https://hvg.hu/itthon/20091023_oktober_23_partok/4?isPrintView=False&liveReportItemId=0'
                          '&isPreview=False&ver=1&order=desc')
    assert next_page_of_article_hvg(text) is None

    test_logger.log('INFO', 'Test OK!')

    test_logger.log('INFO', 'Testing alfahir')
    text = w.download_url('https://alfahir.hu/2021/08/08/olimpia_tokioi_olimpia'
                          '_japan_hosszu_katinka_szilagyi_aron_sport_nob_lelato')
    assert next_page_of_article_alfahir(
        text) == 'https://alfahir.hu/2021/08/08/olimpia_tokioi_olimpia' \
                 '_japan_hosszu_katinka_szilagyi_aron_sport_nob_lelato?page=1'
    text = w.download_url('https://alfahir.hu/2021/08/08/olimpia_tokioi_olimpia'
                          '_japan_hosszu_katinka_szilagyi_aron_sport_nob_lelato?page=3')
    assert next_page_of_article_alfahir(
        text) == 'https://alfahir.hu/2021/08/08/olimpia_tokioi_olimpia' \
                 '_japan_hosszu_katinka_szilagyi_aron_sport_nob_lelato?page=4'
    text = w.download_url('https://alfahir.hu/2021/08/08/olimpia_tokioi_olimpia'
                          '_japan_hosszu_katinka_szilagyi_aron_sport_nob_lelato?page=60')
    assert next_page_of_article_alfahir(text) is None
    text = w.download_url('https://alfahir.hu/raketavetovel_menekulnek_a_gyilkosok')
    assert next_page_of_article_alfahir(
        text) == 'https://alfahir.hu/raketavetovel_menekulnek_a_gyilkosok?page=1'
    text = w.download_url('https://alfahir.hu/raketavetovel_menekulnek_a_gyilkosok?page=1')
    assert next_page_of_article_alfahir(
        text) == 'https://alfahir.hu/raketavetovel_menekulnek_a_gyilkosok?page=2'
    text = w.download_url('https://alfahir.hu/raketavetovel_menekulnek_a_gyilkosok?page=5')
    assert next_page_of_article_alfahir(text) is None
    text = w.download_url('https://alfahir.hu/2021/10/18/'
                          'republikon_ellenzeki_elovalasztas')
    assert next_page_of_article_alfahir(text) is None
    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################


def main_test():
    main_logger = Logger()

    # Relative path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_news_ngvmt.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article_'
                                                                            'news_ngvmt.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_news_ngvmt.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
