#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join
from bs4 import BeautifulSoup


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_atlatszo_ro(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for atlatszo.ro
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(attrs={'class': 'next page-numbers'})
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_kronikaonline(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for kronikaonline.ro
        The next_page_url contains the character "É", which has to be replaced to be readable by the crawler.
        :returns string of url if there is one, None otherwise
    """
    url = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('ul', class_='pagination')
    if next_page is not None:
        next_page_url = next_page.find('i', class_='fa fa-chevron-circle-right inherent_color')
        if next_page_url is not None:
            url = next_page_url.parent['href'].replace('\xc9', '%C3%89')
    return url


def extract_next_page_url_maszol(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for maszol.ro
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_url = soup.select_one('.page_next a')
    if next_page_url is not None and 'href' in next_page_url.attrs:
        ret = next_page_url['href']
    return ret


def extract_next_page_url_plakatmagany_transindex(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for plakatmagany.transindex.ro
        :returns string of url if there is one, None otherwise
    """
    url = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('nav', class_='navigation load-more')
    if next_page is not None:
        next_page_link = next_page.find('a')
        if next_page_link is not None and 'href' in next_page_link.attrs:
            url = next_page_link['href']
    return url


def extract_next_page_url_think_transindex(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for think.transindex.ro
        :returns string of url if there is one, None otherwise
    """
    url = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('div', class_='pagination')
    if next_page is not None:
        next_page_link = next_page.find('a', text='tovább >>')
        if next_page_link is not None and 'href' in next_page_link.attrs:
            url_end = next_page_link['href']
            url = f'https://think.transindex.ro{url_end}'
    return url


def extract_next_page_url_foter(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for foter.ro
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='next page-numbers')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing atlatszo_ro')
    text = w.download_url('https://atlatszo.ro/page/1/?s')
    assert extract_next_page_url_atlatszo_ro(text) == 'https://atlatszo.ro/page/2/?s'
    text = w.download_url('https://atlatszo.ro/page/43/?s')
    assert extract_next_page_url_atlatszo_ro(text) is None

    test_logger.log('INFO', 'Testing foter')
    text = w.download_url('https://foter.ro/cikk/category/hirek/')
    assert extract_next_page_url_foter(text) == 'https://foter.ro/cikk/category/hirek/page/2/'
    text = w.download_url('https://foter.ro/cikk/category/hirek/page/2844/')
    assert extract_next_page_url_foter(text) is None
    text = w.download_url('https://foter.ro/cikk/category/fotre/')
    assert extract_next_page_url_foter(text) == 'https://foter.ro/cikk/category/fotre/page/2/'
    text = w.download_url('https://foter.ro/cikk/category/terfigyelo/page/37/')
    assert extract_next_page_url_foter(text) is None
    text = w.download_url('https://foter.ro/cikk/category/holdbazis/')
    assert extract_next_page_url_foter(text) is None

    test_logger.log('INFO', 'Testing kronikaonline')
    text = w.download_url('https://kronikaonline.ro/kereses?op=search&src_words='
                          '.&src_author=&src_search=KERES%C3%89S&page=1')
    assert extract_next_page_url_kronikaonline(text) == \
           'https://kronikaonline.ro/kereses?op=search&src_words=.&src_author=&src_search=KERES%C3%89S&page=2'
    text = w.download_url('https://kronikaonline.ro/kereses?op=search&src_words='
                          '.&src_author=&src_search=KERES%C3%89S&page=774')
    assert extract_next_page_url_kronikaonline(text) == \
           'https://kronikaonline.ro/kereses?op=search&src_words=.&src_author=&src_search=KERES%C3%89S&page=775'
    text = w.download_url('https://kronikaonline.ro/kereses?op=search&src_words='
                          '.&src_author=&src_search=KERES%C3%89S&page=1584')
    assert extract_next_page_url_kronikaonline(text) is None

    test_logger.log('INFO', 'Testing maszol')
    text = w.download_url('https://maszol.ro/belfold/oldal/1')
    assert extract_next_page_url_maszol(text) == 'https://maszol.ro/belfold/oldal/68'
    text = w.download_url('https://maszol.ro/belfold/oldal/340')
    assert extract_next_page_url_maszol(text) == 'https://maszol.ro/belfold/oldal/408'
    text = w.download_url('https://maszol.ro/belfold/oldal/60384')
    assert extract_next_page_url_maszol(text) is None

    test_logger.log('INFO', 'Testing plakatmagany_transindex')
    text = w.download_url('https://plakatmagany.transindex.ro/archivum/page/1/')
    assert extract_next_page_url_plakatmagany_transindex(text) == 'https://plakatmagany.transindex.ro/archivum/page/2/'
    text = w.download_url('https://plakatmagany.transindex.ro/archivum/page/42/')
    assert extract_next_page_url_plakatmagany_transindex(text) == 'https://plakatmagany.transindex.ro/archivum/page/43/'
    text = w.download_url('https://plakatmagany.transindex.ro/archivum/page/62/')
    assert extract_next_page_url_plakatmagany_transindex(text) is None

    test_logger.log('INFO', 'Testing think_transindex')
    text = w.download_url('https://think.transindex.ro/?page=1')
    assert extract_next_page_url_think_transindex(text) == 'https://think.transindex.ro/?page=2'
    text = w.download_url('https://think.transindex.ro/?page=15')
    assert extract_next_page_url_think_transindex(text) == 'https://think.transindex.ro/?page=16'
    text = w.download_url('https://think.transindex.ro/?page=25')
    assert extract_next_page_url_think_transindex(text) is None

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


def extract_article_urls_from_page_atlatszo_ro(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.select('h4', class_='entry-title')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_foter(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.select('.entry-title')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_kronikaonline(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    for main_container in soup.find_all('div', class_='catinner'):
        a_tag = main_container.find('a', recursive=False)
        if a_tag is not None and 'href' in a_tag.attrs:
            urls.add(a_tag['href'])
    return urls


def extract_article_urls_from_page_maszol(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.select('h2')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_szekelyhon(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    for main_container in soup.find_all('div', class_='catinner'):
        a_tag = main_container.find('a', recursive=False)
        if a_tag is not None and 'href' in a_tag.attrs:
            urls.add(a_tag['href'])
    return urls


def extract_article_urls_from_page_transindex(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('a', class_='archivumcim')
    urls = {link['href'] for link in main_container if 'href' in link.attrs}
    return urls


def extract_article_urls_from_page_lelato_penzcsinalok_transindex(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    container = soup.find('section', class_='page-left-side rovat')
    if soup is not None:
        main_container = container.find_all('h2')
        urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_plakatmagany_transindex(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2', class_='entry-title archiveTitle h1')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_think_transindex(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    soup = soup.find('section', class_='page-left-side rovat')
    if soup is not None:
        main_container = soup.find_all('h2')
        urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)
                if link != 'https://regithink.transindex.ro' and link != '#'}
    return urls


def extract_article_urls_from_page_tv_transindex(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('section', class_='video-list')
    if len(main_container) > 0:
        # The second of the two identical horizontal scrolling boxes contain the column's articles.
        a_tags = main_container[-1].find_all('a')
        urls = {link['href'] for link in a_tags if 'href' in link.attrs}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs from an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing atlatszo_ro')
    text = w.download_url('https://atlatszo.ro/page/12/?s')
    extracted = extract_article_urls_from_page_atlatszo_ro(text)
    expected = {'https://atlatszo.ro/koronavalsag/ledonti-a-labarol-a-gazdasagot-a-koronavirus-de-gyorsan-felepulhet/',
                'https://atlatszo.ro/koronavalsag/mi-lesz-most/',
                'https://atlatszo.ro/kozpenzek/nyilt-kormanyzas/onkormanyzatok/'
                'hidegzuhany-gyergyoban-nagyon-dragan-fizetik-meg-az-olcso-tavfutest/',
                'https://atlatszo.ro/velunk-elo-tortenelem/'
                'autonomia-romaniaban-a-tortenelmi-eselyunk-salat-leventevel-beszelgettunk-2/',
                'https://atlatszo.ro/velunk-elo-tortenelem/mit-szurtunk-el-az-elmult-30-evben-salat-levente-interju-1/',
                'https://atlatszo.ro/szabad-sajto/media/miert-nezd-meg-a-colectiv-filmet/',
                'https://atlatszo.ro/szabad-sajto/segitene-a-szabad-sajtot-az-rmdsz-mutatjuk-mi-mindent-tehetne/',
                'https://atlatszo.ro/eroviszonyok/diszkriminacio/kiss-tamas-toro-tibor-ditro-tukreben/',
                'https://atlatszo.ro/eroviszonyok/diszkriminacio/'
                'klasszikus-kizsakmanyolast-keretez-a-ditroi-migransozas-video/',
                'https://atlatszo.ro/kozlemenyek/ennyibol-mukodott-az-atlatszo-erdely-2019-ben/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Testing foter')
    text = w.download_url('https://foter.ro/cikk/category/hirek/page/448/')
    extracted = extract_article_urls_from_page_foter(text)
    expected = {'https://foter.ro/cikk/'
                'ha-mostanaban-olaszba-repulne-szamoljon-azzal-hogy-drasztikusan-csokkentettek-a-jaratok-szamat/',
                'https://foter.ro/cikk/'
                'mindenkit-megtrollkodtak-a-liberalisok-ilyen-kormanynevsorra-meg-a-szovetsegeseik-sem-szamitottak/',
                'https://foter.ro/cikk/'
                'ha-mar-illegalisan-epitkezel-legalabb-az-aramot-ne-lopd-keri-az-energiaszabalyozo/',
                'https://foter.ro/cikk/hoppa-de-hiszen-a-februar-az-meg-tel-jutott-eszebe-hirtelen-az-idojarasnak/',
                'https://foter.ro/cikk/jol-elvesztette-a-szocialis-segelyt-az-aki-tudna-dolgozni-de-nem-akar/',
                'https://foter.ro/cikk/a-videobiro-vetett-veget-a-cfr-leghosszabb-europai-kupakalandjanak/',
                'https://foter.ro/cikk/'
                'ilyen-sem-volt-meg-betiltana-a-csokolozast-jarvanyhelyzetben-az-egeszsegugyi-allamtitkar/',
                'https://foter.ro/cikk/'
                'egy-reszben-mumifikalodott-romant-talaltak-egy-romai-korhaz-szelloztetocsovei-kozott/',
                'https://foter.ro/cikk/durci-2070-re-tobb-nyugdijas-lesz-az-orszagban-'
                'mint-ahany-melos-es-ez-nem-lesz-jo-sem-a-nyugdijasoknak-sem-a-melosoknak/',
                'https://foter.ro/cikk/'
                'hatarmenti-rogvalosag-nezzen-cigicsempeszekkel-egyutt-bulizo-rendoroket-videoval/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Testing kronikaonline')
    text = w.download_url('https://kronikaonline.ro/kereses?op=search&src_words='
                          '.&src_author=&src_search=KERES%C3%89S&page=574')
    extracted = extract_article_urls_from_page_kronikaonline(text)
    expected = {'https://kronikaonline.ro/belfold/'
                'ketszaz-fole-emelkedett-a-fertozottek-szama-johannis-intezkedeseket-surget',
                'https://kronikaonline.ro/erdelyi-hirek/'
                'uj-mindennapokat-szult-a-koronavirus-jarvany-meg-kell-tanulnunk-ujbol-sorban-allni-n',
                'https://kronikaonline.ro/kulfold/bezarkozik-az-europai-unio-a-jarvany-miatt',
                'https://kronikaonline.ro/belfold/'
                'felfuggesztettek-a-vasuti-szemelyszallitast-magyarorszag-es-romania-kozott',
                'https://kronikaonline.ro/sport/hivatalos-jovore-halasztjak-a-nyari-futball-eb-t',
                'https://kronikaonline.ro/belfold/cafolja-a-tanev-befagyasztasarol-keringo-hireket-a-tanugyminiszter',
                'https://kronikaonline.ro/kulfold/'
                'kinai-kutatok-szerint-nem-terjed-a-virus-varandos-anyarol-a-szuletendo-gyerekre',
                'https://kronikaonline.ro/gazdasag/a-jarvany-frontvonalaban-a-turizmus',
                'https://kronikaonline.ro/kulfold/'
                'bogdan-aurescu-humanitarius-folyosot-kert-az-osztraknmagyar-hataron-rekedt-romanoknak-budapesttol',
                'https://kronikaonline.ro/erdelyi-hirek/'
                'foterrel-kulturkozponttal-es-nyari-szinhazzal-gazdagodhat-szovata-bfalu-reszer',
                'https://kronikaonline.ro/kulfold/'
                'vasarnaptol-nem-tartanak-nyilvanos-miset-a-magyarorszagi-katolikus-templomokban',
                'https://kronikaonline.ro/gazdasag/'
                'ovnak-a-munkavallalokat-a-hatosagok-a-cegek-gondjaira-is-keresik-a-megoldasokat',
                'https://kronikaonline.ro/kultura/elhunyt-szilagyi-aladar-iro-helytortenesz-publicista',
                'https://kronikaonline.ro/belfold/'
                'szaznyolcvan-folott-jar-a-koronavirus-fertozottek-szama-romaniaban-tizenhatan-meggyogyultak',
                'https://kronikaonline.ro/belfold/felfuggesztettek-az-autovezetoi-vizsgakat-a-jarvany-miatt',
                'https://kronikaonline.ro/belfold/virus-a-roman-parlamentben-egyetlen-teszteredmeny-lett-pozitiv'
                }
    assert (extracted, len(extracted)) == (expected, 16)

    text = w.download_url('https://kronikaonline.ro/kereses?op=search&src_words=.'
                          '&src_author=&src_search=KERES%C3%89S&page=1583')
    extracted = extract_article_urls_from_page_kronikaonline(text)
    expected = {'https://kronikaonline.ro/erdelyi-hirek/februar-vegen-kezdodik-az-iskolai-beiratkozas',
                'https://kronikaonline.ro/erdelyi-hirek/'
                'marosvasarhelyi-kutatasokat-tamogat-a-magyar-tudomanyos-akademia',
                'https://kronikaonline.ro/belfold/a-kozkegyelmi-tervek-visszavonasara-szolit-johannis',
                'https://kronikaonline.ro/kultura/arany-kolteszetenek-egyenes-agi-leszarmazottja',
                'https://kronikaonline.ro/szines/felszenteltek-a-balea-to-melletti-jegtemplomot',
                'https://kronikaonline.ro/erdelyi-hirek/tortenelem-gyereknyelven',
                'https://kronikaonline.ro/kultura/elhunyt-mihaly-pal-a-kolozsvari-szinhaz-orokos-tagja',
                'https://kronikaonline.ro/erdelyi-hirek/nem-szorakoznak-a-biztonsaggal',
                'https://kronikaonline.ro/velemeny/nem-szabadulunk-a-szabadnapoktol',
                'https://kronikaonline.ro/kulfold/hat-halott-a-quebeci-mecsetben-tortent-lovoldozesben',
                'https://kronikaonline.ro/erdelyi-hirek/meghalt-solomon-adri',
                'https://kronikaonline.ro/velemeny/uzlet-es-politika',
                'https://kronikaonline.ro/sport/'
                'alazat-nelkul-nincs-siker-n-erdei-zsolt-a-szekelyfoldi-bokszakademiarol',
                'https://kronikaonline.ro/sport/ferfi-kezi-vb-ismet-veretlenul-nyertek-aranyat-a-franciak',
                'https://kronikaonline.ro/belfold/tizezrek-tiltakoznak-a-kormany-kozkegyelmi-tervezete-ellen',
                'https://kronikaonline.ro/erdelyi-hirek/'
                'elnapoltak-a-targyalast-n-nem-kell-hazat-bontani-az-uj-korondi-hulladekgyujto-telep-miatt'
                }
    assert (extracted, len(extracted)) == (expected, 16)

    test_logger.log('INFO', 'Testing maszol')
    text = w.download_url('https://maszol.ro/belfold/oldal/476')
    extracted = extract_article_urls_from_page_maszol(text)
    expected = {'https://maszol.ro/belfold/Megtortent-a-Renate-Weber-ombudsman-menesztesere-iranyulo-elso-lepes',
                'https://maszol.ro/belfold/Tanugyminiszter-eddig-10-ezer-tanulora-jut-egy-fertozott',
                'https://maszol.ro/belfold/'
                'Csikszeredaban-kezd-a-leginkabb-visszaallni-a-korhazi-betegellatas-a-jarvany-elotti-szintre',
                'https://maszol.ro/belfold/Felmeres-alacsony-az-oltasi-hajlandosag-a-diakok-kozott',
                'https://maszol.ro/belfold/'
                'Ellenzeki-nyomasra-a-kormany-bemutatja-a-parlamentben-a-nemzeti-helyreallitasi-tervet',
                'https://maszol.ro/belfold/Kigyogyult-a-koronavirus-fertozesbol-egy-99-eves-haborus-veteran',
                'https://maszol.ro/belfold/'
                'Sorban-allnak-az-emberek-a-csiksomlyoi-kegytemplom-kozeleben-kialakitott-oltokozpontnal',
                'https://maszol.ro/belfold/'
                'Szerdatol-fel-lehet-iratkozni-Janssen-vakcinara-kiskoruaknak-is-szerveznek-oltasmaratont',
                'https://maszol.ro/belfold/Fejbe-lotte-magat-egy-tinedzser-a-batyja-altal-talalt-puskaval',
                'https://maszol.ro/belfold/Tizenhatodik-szazadbeli-nemesember-sirjara-bukkantak-Szilagyperecsenben',
                'https://maszol.ro/belfold/A-Szilagysagban-jart-Zsigmond-Barna-Pal-orszaggyulesi-kepviselo',
                'https://maszol.ro/belfold/Kozel-hetszazezer-adag-Pfizer-vakcina-erkezik-hetfon-Romaniaba',
                'https://maszol.ro/belfold/Egy-nap-alatt-nyolc-medvehez-riasztottak-a-csendoroket-Tusnadfurdon',
                'https://maszol.ro/belfold/Haduzenet-a-patakparti-szemetelesnek-NAGYtakaritas-Kezdiszeken-X',
                'https://maszol.ro/belfold/Az-elmult-24-oraban-54-ezer-szemely-kapta-meg-a-COVID-19-elleni-vakcinat',
                'https://maszol.ro/belfold/Legkesobb-penteken-derul-ki-milyen-lazitasok-kovetkeznek-junius-elsejetol',
                'https://maszol.ro/belfold/'
                'A-hivatalos-adatok-szerint-tobb-mint-30-ezren-haltak-meg-eddig-a-koronavirussal-osszefuggesben',
                'https://maszol.ro/belfold/A-romaniai-tanarok-60-szazaleka-be-van-oltva-a-miniszter-szerint',
                'https://maszol.ro/belfold/'
                'Ugyeszsegi-feljelenteseket-tett-a-szamvevoszek-a-jarvanyidoszak-alatti-kozbeszerzesek-ugyeben',
                'https://maszol.ro/belfold/Medvekarok-Haromszeken-vendeglokbe-es-maganhazakba-tornek-be-az-allatok',
                'https://maszol.ro/belfold/Oltokozpont-nyilt-a-magyarroman-hataron-Bihar-megyeben',
                'https://maszol.ro/belfold/Videki-oltaskampanyokat-szerveznek-Haromszeken',
                'https://maszol.ro/belfold/Igy-fest-korosztalyokra-lebontva-a-lakossag-atoltottsaga-koronavirus-ellen',
                'https://maszol.ro/belfold/Megfizettetne-velunk-Orban-a-koronavirus-elleni-vakcinat',
                'https://maszol.ro/belfold/379-uj-fertozott-van-a-napi-jelentes-szerint',
                'https://maszol.ro/belfold/Hetfotol-visszaterhetnek-az-iskolakba-a-kolozsvari-diakok',
                'https://maszol.ro/belfold/'
                'Csiksomlyoi-bucsu-a-hithez-a-Szuz-Mariahoz-valo-ragaszkodast-hirdette-a-szonok',
                'https://maszol.ro/belfold/'
                'Visszautaltak-a-katonai-ugyeszsegnek-az-1989-es-forradalom-ugyenek-vadiratat',
                'https://maszol.ro/belfold/'
                'Igy-igenyelhetnek-vedettsegi-igazolvanyt-elektronikus-ugyintezessel-az-erdelyi-magyarok',
                'https://maszol.ro/belfold/A-felgyult-szemet-miatt-majdnem-kiaradt-a-Feher-Koros-Arad-megyeben',
                'https://maszol.ro/belfold/Elektromos-iskolabuszokra-keszitenek-elo-palyazatot-az-onkormanyzatoknak',
                'https://maszol.ro/belfold/'
                'Harom-nap-alatt-248-an-kaptak-meg-a-vakcinat-felrazo-akcionak-szantak-a-csiksomlyoi-oltasmaratont',
                'https://maszol.ro/belfold/'
                '20-eves-a-Sapientia-EMTE-szimbolikusan-visszaallitottak-a-Bocskai-emlektablat-Kolozsvaron',
                'https://maszol.ro/belfold/Maros-megye-is-reszt-vesz-a-Romaniai-Iskolaprogramban-X',
                'https://maszol.ro/belfold/'
                'Kivul-belul-felujitja-a-nagyvaradi-Ady-liceumot-a-Cseke-Attila-vezette-fejlesztesi-miniszterium',
                'https://maszol.ro/belfold/Ujabb-szallitmany-erkezett-az-AstraZeneca-altal-kifejlesztett-vakcinabol',
                'https://maszol.ro/belfold/Ujabb-lazito-intezkedeseket-jelentenek-be-jovo-heten-a-hatosagok',
                'https://maszol.ro/belfold/Videken-hazalnak-majd-a-koronavirus-elleni-vakcinaval',
                'https://maszol.ro/belfold/Autobalesetben-eletet-veszitette-egy-ferfi-Gyergyoalfaluban',
                'https://maszol.ro/belfold/Tobb-tucat-palesztin-tuntetett-pentek-delutan-Temesvar-kozpontjaban',
                'https://maszol.ro/belfold/Oltasparancsnok-nem-okoz-meddoseget-a-Covid-19-elleni-vakcina',
                'https://maszol.ro/belfold/75-ezer-szemelyt-oltottak-be-az-elmult-24-oraban',
                'https://maszol.ro/belfold/455-uj-fertozest-igazoltak-az-elmult-napban',
                'https://maszol.ro/belfold/Antal-Arpad-az-Orszagos-Onkormanyzati-Tanacs-uj-elnoke',
                'https://maszol.ro/belfold/Kelemen-Hunor-szerint-rendkivul-kiegyensulyozott-a-helyreallitasi-terv',
                'https://maszol.ro/belfold/Osszehivtak-a-Maros-Megyei-Tanacs-nyilvanos-soros-uleset-X',
                'https://maszol.ro/belfold/'
                'Autopalya-epites-roman-modra-hat-honapja-adtak-at-meg-mindig-dolgoznak-rajta',
                'https://maszol.ro/belfold/'
                'Az-orszagban-egyedulallo-buldozer-szimulator-segiti-a-szakiskolai-oktatast-Nagykagyan',
                'https://maszol.ro/belfold/Betort-a-lakasba-es-megeroszakolt-egy-85-eves-not-egy-fiatalember',
                'https://maszol.ro/belfold/'
                'Kelemen-Hunor-nincs-szo-a-nyugdijkorhatar-emeleserol-hanem-az-egyenlotlensegek-eltorleserol',
                'https://maszol.ro/belfold/Hevesen-biralja-a-PSD-az-orszagos-helyreallitasi-tervet',
                'https://maszol.ro/belfold/Eletfogytiglanit-kapott-a-kolozsvari-magyar-gyerekgyilkos',
                'https://maszol.ro/belfold/Bortonbuntetesre-iteltek-a-rendorakademia-ket-volt-vezetojet',
                'https://maszol.ro/belfold/'
                'Tanugyminiszter-barmilyen-lesz-a-helyzet-az-orszagos-vizsgakat-fizikai-jelenlettel-tartjuk-meg',
                'https://maszol.ro/belfold/Tragedia-holtan-talaltak-meg-az-eltunt-szaszfenesi-kisfiut',
                'https://maszol.ro/belfold/Tervezet-a-lakossag-is-hasznalhatja-az-iskolai-sportpalyakat',
                'https://maszol.ro/belfold/Gyermeknap-alkalmabol-egesz-napos-programot-szerveznek-Kaplonyban',
                'https://maszol.ro/belfold/230-uj-fertozott-van-tavaly-junius-ota-nem-volt-ilyen-keves-igazolt-eset',
                'https://maszol.ro/belfold/Munkaszuneti-nap-lehet-majus-31-e-is',
                'https://maszol.ro/belfold/Rogzitettek-a-kamerak-egy-ismert-nepdalenekes-halalos-balesetet',
                'https://maszol.ro/belfold/Hivatalos-mar-nem-kerulnek-karantenba-Romaniaban-a-Magyarorszagrol-erkezok',
                'https://maszol.ro/belfold/Eros-foldrenges-volt-az-ejjel-Vrancea-szeizmikus-tersegben',
                'https://maszol.ro/belfold/Citu-Ingyenes-marad-az-oltas',
                'https://maszol.ro/belfold/Csiksomlyo-a-pelda-az-Erdely-TV-musoraban',
                'https://maszol.ro/belfold/Szuksegunk-van-arra-hogy-talalkozzunk-a-bucsun-oltatta-be-magat-Bojte-Csaba',
                'https://maszol.ro/belfold/Az-uj-fertozesek-szama-11-honapja-nem-volt-ilyen-alacsony',
                'https://maszol.ro/belfold/A-jarvanyhelyzet-miatt-iden-sem-rendezik-meg-a-Tusvanyost',
                'https://maszol.ro/belfold/'
                'Tisztujitasra-keszul-a-PNL-Ludovic-Orban-es-Florin-Citu-ket-taborra-osztotta-a-liberalisokat'
                }
    assert (extracted, len(extracted)) == (expected, 68)

    test_logger.log('INFO', 'Testing szekelyhon')
    text = w.download_url('https://szekelyhon.ro/mod/open24h.php?p=50')
    extracted = extract_article_urls_from_page_szekelyhon(text)
    expected = {'https://szekelyhon.ro/aktualis/akik-nap-mint-nap-harcot-vivnak-a-koronavirussal',
                'https://szekelyhon.ro/vilag/elegendo-oltoanyagot-kap-romania-a-nyajimmunitas-eleresehez',
                'https://szekelyhon.ro/aktualis/megszuntetnek-a-kanyad-kozseg-falvaiban-fennallo-vizhianyt',
                'https://szekelyhon.ro/aktualis/'
                'mar-a-problemas-medvek-artalmatlanitasara-sem-kaphatnak-kilovesi-engedelyt-a-vadasztarsasagok',
                'https://szekelyhon.ro/aktualis/'
                'ezekre-a-szempontokra-erdemes-figyelni-hogy-ne-valjunk-online-vasarlasi-csalas-aldozatava',
                'https://szekelyhon.ro/aktualis/'
                'egyre-tobb-az-utcan-elo-kobor-macska-n-az-ivartalanitas-megoldast-jelenthet',
                'https://szekelyhon.ro/aktualis/otven-vallalkozas-kerte-az-oltast-maros-megyeben',
                'https://szekelyhon.ro/aktualis/megvan-belgium-is-ejfelkor-zarul-a-nemzeti-regios-alairasgyujtes',
                'https://szekelyhon.ro/aktualis/'
                'kozzetettek-a-hargita-megyei-tanintezmenyek-jovo-heti-mukodesere-vonatkozo-beosztasat',
                'https://szekelyhon.ro/aktualis/utcasepresi-es-portalanitasi-akcio-gyergyoszentmikloson',
                'https://szekelyhon.ro/aktualis/jarvanyhelyzet-csokkeno-ertekek-hargita-megyeben',
                'https://szekelyhon.ro/aktualis/haromszaz-fenyofacsemetet-ultettek-a-gyergyoi-zeneszek',
                'https://szekelyhon.ro/vilag/tovabbra-is-ezerotszaz-korul-mozog-az-uj-esetek-szama',
                'https://szekelyhon.ro/aktualis/'
                'honositasi-folyamat-csikszeken-a-volt-fokonzullal-egyeztetett-a-teruleti-rmdsz',
                'https://szekelyhon.ro/aktualis/negy-ev-a-halal-szigeten',
                'https://szekelyhon.ro/vilag/pesty-laszlo-ellenszelben-csinaltuk-vegig',
                }
    assert (extracted, len(extracted)) == (expected, 16)

    test_logger.log('INFO', 'Testing transindex')
    text = w.download_url('https://archivum.transindex.ro/?ev=2019&het=17&new=1')
    extracted = extract_article_urls_from_page_transindex(text)
    expected = {'https://eletmod.transindex.ro/?cikk=27774',
                'https://eletmod.transindex.ro/?cikk=27776',
                'https://eletmod.transindex.ro/?cikk=27777',
                'https://eletmod.transindex.ro/?cikk=27782',
                'https://eletmod.transindex.ro/?hir=23781',
                'https://eletmod.transindex.ro/?hir=23782',
                'https://eletmod.transindex.ro/?hir=23783',
                'https://eletmod.transindex.ro/?hir=23784',
                'https://eletmod.transindex.ro/?hir=23785',
                'https://eletmod.transindex.ro/?hir=23786',
                'https://eletmod.transindex.ro/?hir=23787',
                'https://eletmod.transindex.ro/?hir=23788',
                'https://eletmod.transindex.ro/?hir=23789',
                'https://eletmod.transindex.ro/?hir=23790',
                'https://eletmod.transindex.ro/?hir=23791',
                'https://eletmod.transindex.ro/?hir=23792',
                'https://eletmod.transindex.ro/?hir=23793',
                'https://itthon.transindex.ro/?cikk=27778',
                'https://itthon.transindex.ro/?cikk=27780',
                'https://itthon.transindex.ro/?hir=55227',
                'https://itthon.transindex.ro/?hir=55228',
                'https://itthon.transindex.ro/?hir=55229',
                'https://itthon.transindex.ro/?hir=55230',
                'https://itthon.transindex.ro/?hir=55231',
                'https://itthon.transindex.ro/?hir=55232',
                'https://itthon.transindex.ro/?hir=55233',
                'https://itthon.transindex.ro/?hir=55235',
                'https://itthon.transindex.ro/?hir=55236',
                'https://itthon.transindex.ro/?hir=55237',
                'https://itthon.transindex.ro/?hir=55238',
                'https://itthon.transindex.ro/?hir=55239',
                'https://itthon.transindex.ro/?hir=55240',
                'https://itthon.transindex.ro/?hir=55241',
                'https://itthon.transindex.ro/?hir=55242',
                'https://itthon.transindex.ro/?hir=55243',
                'https://itthon.transindex.ro/?hir=55244',
                'https://itthon.transindex.ro/?hir=55245',
                'https://itthon.transindex.ro/?hir=55246',
                'https://itthon.transindex.ro/?hir=55247',
                'https://itthon.transindex.ro/?hir=55248',
                'https://itthon.transindex.ro/?hir=55249',
                'https://itthon.transindex.ro/?hir=55250',
                'https://itthon.transindex.ro/?hir=55251',
                'https://itthon.transindex.ro/?hir=55252',
                'https://itthon.transindex.ro/?hir=55253',
                'https://itthon.transindex.ro/?hir=55254',
                'https://itthon.transindex.ro/?hir=55255',
                'https://itthon.transindex.ro/?hir=55256',
                'https://itthon.transindex.ro/?hir=55258',
                'https://itthon.transindex.ro/?hir=55259',
                'https://itthon.transindex.ro/?hir=55260',
                'https://itthon.transindex.ro/?hir=55261',
                'https://itthon.transindex.ro/?hir=55262',
                'https://itthon.transindex.ro/?hir=55263',
                'https://itthon.transindex.ro/?hir=55264',
                'https://itthon.transindex.ro/?hir=55265',
                'https://itthon.transindex.ro/?hir=55266',
                'https://itthon.transindex.ro/?hir=55267',
                'https://itthon.transindex.ro/?hir=55268',
                'https://itthon.transindex.ro/?hir=55269',
                'https://itthon.transindex.ro/?hir=55270',
                'https://itthon.transindex.ro/?hir=55272',
                'https://itthon.transindex.ro/?hir=55273',
                'https://itthon.transindex.ro/?hir=55274',
                'https://itthon.transindex.ro/?hir=55275',
                'https://itthon.transindex.ro/?hir=55276',
                'https://itthon.transindex.ro/?hir=55277',
                'https://itthon.transindex.ro/?hir=55278',
                'https://itthon.transindex.ro/?hir=55279',
                'https://itthon.transindex.ro/?hir=55280',
                'https://itthon.transindex.ro/?hir=55281',
                'https://itthon.transindex.ro/?hir=55282',
                'https://itthon.transindex.ro/?hir=55283',
                'https://multikult.transindex.ro/?hir=11090',
                'https://multikult.transindex.ro/?hir=11091',
                'https://multikult.transindex.ro/?hir=11093',
                'https://multikult.transindex.ro/?hir=11094',
                'https://multikult.transindex.ro/?hir=11095',
                'https://multikult.transindex.ro/?hir=11096',
                'https://multikult.transindex.ro/?hir=11097',
                'https://multikult.transindex.ro/?hir=11098',
                'https://think.transindex.ro/?cikk=27772',
                'https://think.transindex.ro/?cikk=27779',
                'https://vilag.transindex.ro/?cikk=27763',
                'https://vilag.transindex.ro/?cikk=27781',
                'https://vilag.transindex.ro/?hir=34555',
                'https://vilag.transindex.ro/?hir=34556',
                'https://vilag.transindex.ro/?hir=34557',
                'https://vilag.transindex.ro/?hir=34558',
                'https://vilag.transindex.ro/?hir=34559',
                'https://vilag.transindex.ro/?hir=34560',
                'https://vilag.transindex.ro/?hir=34561',
                'https://vilag.transindex.ro/?hir=34562',
                'https://vilag.transindex.ro/?hir=34563',
                'https://vilag.transindex.ro/?hir=34564',
                'https://vilag.transindex.ro/?hir=34565',
                'https://vilag.transindex.ro/?hir=34566',
                'https://vilag.transindex.ro/?hir=34567',
                'https://vilag.transindex.ro/?hir=34568',
                'https://vilag.transindex.ro/?hir=34570',
                'https://vilag.transindex.ro/?hir=34571',
                'https://vilag.transindex.ro/?hir=34572',
                'https://vilag.transindex.ro/?hir=34573',
                'https://vilag.transindex.ro/?hir=34574',
                'https://vilag.transindex.ro/?hir=34575',
                'https://vilag.transindex.ro/?hir=34576',
                'https://vilag.transindex.ro/?hir=34577',
                'https://vilag.transindex.ro/?hir=34578',
                'https://vilag.transindex.ro/?hir=34579',
                'https://vilag.transindex.ro/?hir=34580',
                'https://vilag.transindex.ro/?hir=34581',
                'https://vilag.transindex.ro/?hir=34582',
                'https://vilag.transindex.ro/?hir=34583',
                'https://vilag.transindex.ro/?hir=34584',
                'https://vilag.transindex.ro/?hir=34585'
                }
    assert (extracted, len(extracted)) == (expected, 115)

    test_logger.log('INFO', 'Testing lelato_transindex')
    text = w.download_url('https://lelato.transindex.ro/aktualis/4')
    extracted = extract_article_urls_from_page_lelato_penzcsinalok_transindex(text)
    expected = {'https://lelato.transindex.ro/aktualis/20201212-a-sepsi-idegenben-verte-a-gaz-metant',
                'https://lelato.transindex.ro/aktualis/'
                '20201211-papp-gabor-nagymester-a-sakkolimpia-tortenelmi-lehetoseg-magyarorszagnak',
                'https://lelato.transindex.ro/aktualis/20201210-oriasi-dramak-svajcban-kiesett-a-cfr-az-europa-ligabol',
                'https://lelato.transindex.ro/aktualis/'
                '20201210-bl-vege-a-csoportkornek-a-fradi-mellett-a-manchester-united-is-bucsuzott',
                'https://lelato.transindex.ro/aktualis/'
                '20201126-gyaszol-a-futballvilag-a-lelato-ot-ikonikus-gollal-bucsuzik-maradonatol',
                'https://lelato.transindex.ro/aktualis/20201124-sokkal-jobb-eredmenyt-ert-el-a-ferencvar',
                'https://lelato.transindex.ro/aktualis/'
                '20201123-tincu-sem-tudta-legyozni-a-sepsit-ket-hatalmas-gollal-forditottak-fulopek',
                'https://lelato.transindex.ro/aktualis/'
                '20201120-gyenes-mani-a-2021-es-dakaron-nem-a-malle-moto-megnyerese-a-cel',
                'https://lelato.transindex.ro/aktualis/'
                '20201119-nincsenek-szavak-a-magyar-futballra-iden-magyarorszag-csoportelso-a-b-ligaban',
                'https://lelato.transindex.ro/aktualis/20201111-ev-meccse-bemutatjuk-izland-valogatottjat',
                'https://lelato.transindex.ro/aktualis/'
                '20201107-liga1-nagyon-nagy-golt-lott-a-sepsi-a-hermannstadtnak-video',
                'https://lelato.transindex.ro/aktualis/'
                '20201105-bl-a-fradinak-tobb-pontja-van-mint-a-marseille-nek-az-angolok-vezetik-a-csoportjaikat',
                'https://lelato.transindex.ro/aktualis/20201101-liga1-a-cfr-a-medgyest-fogadta',
                'https://lelato.transindex.ro/aktualis/'
                '20201029-kemeny-meccsen-igazsagos-dontetlent-jatszott-a-cfr-az-europa-ligaban',
                'https://lelato.transindex.ro/aktualis/20201024-dinamikatlan-dinamo-Sepsi',
                'https://lelato.transindex.ro/aktualis/20201022-gyozelemmel-kezdett-a-cfr-az-europa-ligaban',
                'https://lelato.transindex.ro/aktualis/20201017-sepsi-jaszvasar-videoval',
                'https://lelato.transindex.ro/aktualis/'
                '20201016-rafael-nadal-tornagyozelme-es-a-roland-garros-labdabotranya',
                'https://lelato.transindex.ro/aktualis/20200924-videoton-a-reims-ell',
                'https://lelato.transindex.ro/aktualis/20200923-hatalmas-lepest-tett-a-ferencvaros-a-bl-csoportkor-fele'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Testing penzcsinalok_transindex')
    text = w.download_url('https://penzcsinalok.transindex.ro/globalis/4/')
    extracted = extract_article_urls_from_page_lelato_penzcsinalok_transindex(text)
    expected = {'https://penzcsinalok.transindex.ro/hir/'
                '20210309-nevetsegesen-rosszul-allunk-az-e-kormanyzati-megoldasok-hasznalataban',
                'https://penzcsinalok.transindex.ro/globalis/20210303-atlathatova-tenne-a-fizeteseket-'
                'igy-szamolna-le-a-nemek-kozotti-berszakadekkal-az-europai-bizottsag',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210308-ot-perc-alatt-feltoltheto-akkumulatort-fejleszt-elektromos-autokhoz-egy-izraeli-ceg',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210304-hongkong-lekerult-a-vilag-legszabadabb-gazdasagainak-listajarol',
                'https://penzcsinalok.transindex.ro/hir/20210303-az-europai-bizottsag-fontolora-veszi-a-'
                'koltsegvetesi-hianyra-vonatkozo-szabalyok-tovabbi-felfuggeszteset',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210303-cedukacio-neven-dijmentes-oktatasi-platform-indul-vallalkozoknak',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210301-erre-bukik-romania-is-a-google-a-meki-es-a-hm-toretlen-sikere',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210223-europai-bizottsag-a-szeniparnak-nincs-jovoje.-romania-hidrogenben-gondolkodunk',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210218-hol-nott-legjobban-az-online-kereskedelem-nepszerusege-az-eu-ban-hat-persze-hogy-nalunk',
                'https://penzcsinalok.transindex.ro/hir/20210216-a-roman-gazdasag-allva-hagyta-a-tobbi-eu-s-tagallamot',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210209-lagarde-mihamarabb-vegre-kell-halytani-az-eu-s-mentocsomagot',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210208-a-wizz-air-abban-bizik-hogy-nyaron-jelentos-fellendules-kovetkezik',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210208-sentix-az-euroovezeti-gazdasag-leszakadoban-van-a-vilag-tobbi-reszetol',
                'https://penzcsinalok.transindex.ro/globalis/20210208-angliaban-elo-magyarok-van-aki-'
                '48-ora-alatt-kapta-meg-a-letelepedesi-okmanyt-van-aki-masfel-honapja-varja',
                'https://penzcsinalok.transindex.ro/globalis/'
                '20210205-egy-magyar-ceg-lett-europa-legigeretesebb-technologiai-vallalkozasa',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210205-del-korea-az-elso-az-innovacios-vilagranglistan.-hogy-all-romania',
                'https://penzcsinalok.transindex.ro/globalis/20210202-vilaggazdasagi-forum',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210204-mennyivel-kapnak-kevesebb-nyugdijat-a-nok-a-ferfiaknal-romaniaban',
                'https://penzcsinalok.transindex.ro/hir/20210204-nevet-valt-a-mercedes-benz-anyacege',
                'https://penzcsinalok.transindex.ro/hir/'
                '20210203-oruletes-novekedesben-van-a-roman-uipath-mar-35-milliard-dollart-er'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Testing plakatmagany_transindex')
    text = w.download_url('https://plakatmagany.transindex.ro/archivum/page/12/')
    extracted = extract_article_urls_from_page_plakatmagany_transindex(text)
    expected = {'https://plakatmagany.transindex.ro/az-szfe-ahogy-kolozsvarrol-latszik/',
                'https://plakatmagany.transindex.ro/orosz-lujza-1926-2020-nekrolog-tamas-gaspar-miklos/',
                'https://plakatmagany.transindex.ro/'
                'ciganyellenesseg-integracio-munka-segelyezes-szilagyi-botond-2resz/',
                'https://plakatmagany.transindex.ro/nem-nekunk-velunk-rmdsz-kolozsvar-program-szekely-ors/',
                'https://plakatmagany.transindex.ro/'
                'szinmuveszeti-szfe-a-kavehaztol-a-nemzetkozi-hatterhatalomig-tompa-andrea/'
                }
    assert (extracted, len(extracted)) == (expected, 5)

    test_logger.log('INFO', 'Testing tv_transindex')
    text = w.download_url('https://tv.transindex.ro/?kategoria=14')
    extracted = extract_article_urls_from_page_tv_transindex(text)
    expected = {'https://tv.transindex.ro/?film=242&europa_elrablasa_v.',
                'https://tv.transindex.ro/?film=243&europa_elrablasa_vi.',
                'https://tv.transindex.ro/?film=239&europa_elrablasa_iii.',
                'https://tv.transindex.ro/?film=241&europa_elrablasa_iii.',
                'https://tv.transindex.ro/?film=234&the_rape_of_europe',
                }
    assert (extracted, len(extracted)) == (expected, 5)

    test_logger.log('INFO', 'Testing think_transindex')
    text = w.download_url('https://think.transindex.ro/?page=23')
    extracted = extract_article_urls_from_page_think_transindex(text)
    expected = {'https://think.transindex.ro/?hir=1010&vilagszerte_tobb_szazezer_'
                'fiatal_ment_ki_a_klimatuntetesre._greta_thunberg_bakoi_tuntetesrol_osztott_meg_kepet',
                'https://think.transindex.ro/?hir=1002&a_miniszterium_'
                'hivatalosan_elismerte_386_millio_kobmeternyi_fat_termelnek_ki_evente_romaniaban',
                'https://think.transindex.ro/?hir=1011&szaz_kilogrammnal_'
                'is_tobb_szemetet_talaltak_egy_partra_vetodott_ambrascet_tetemeben',
                'https://think.transindex.ro/?hir=998&tizenkilencezernel_'
                'is_tobb_madarat_sikerult_iden_meggyuruznie_a_milvus_csoportnak',
                'https://think.transindex.ro/?cikk=28137&'
                '160_eves_a_fajok_eredete_de_a_romaniai_tantervbe_megsem_fert_bele',
                'https://think.transindex.ro/?hir=1007&klimaveszhelyzetet_hirdetett_az_europai_parlament',
                'https://think.transindex.ro/?hir=1001&'
                'tobb_mint_10_millio_eurobol_ujitjak_fel_a_kolozsvari_vasutasparkot',
                'https://think.transindex.ro/?cikk=28153&'
                'hirdessenek_klimaveszhelyzetet_romaniaban_is__kovetelik_a_tuntetok',
                'https://think.transindex.ro/?hir=1009&'
                'becsben_penteken_kolozsvaron_vasarnap_vonulnak_a_romaniai_erintetlen_erdok_vedelmeben',
                'https://think.transindex.ro/?hir=1008&'
                'a_miniszterelnok_szerint_az_eloallatexport_leallitasa_kozeptavu_cel_kell_hogy_legyen',
                'https://think.transindex.ro/?hir=1004&'
                'a_heten_a_megszokottnal_melegebbet_josolnak_majd_egy_kis_lehulest',
                'https://think.transindex.ro/?hir=1006&'
                'romania_derogalast_ker_a_mehgyilkos_neonikotinoidok_tovabbi_hasznalata_erdekeben',
                'https://think.transindex.ro/?cikk=28129&lazan_kiadott_engedelyeket_es_'
                'rengeteg_elbukott_eus_penzt_hozott_az_ujonnan_kihirdetett_torveny_egy_szakerto_szerint',
                'https://think.transindex.ro/?hir=999&okologizalasi_es_ultetesi_kampanyt_indit_a_bbte',
                'https://think.transindex.ro/?hir=1000&'
                'romania_az_utolso_elotti_helyen_all_az_euban_hulladekujrahasznositas_teren',
                'https://think.transindex.ro/?hir=997&szakerto_megmenteni_nem_tudtak_volna_a_parajd_'
                'mellett_elutott_medvet_de_lett_volna_torvenyes_lehetoseg_a_gyors_lelovesere',
                'https://think.transindex.ro/?cikk=28127&fatolvajok_tamadtak_meg_a_netflix_stabjat_romaniaban',
                'https://think.transindex.ro/?cikk=28140&tej_ujra_visszavalthato_uvegbol?_almodjunk_fenntarthatosagrol',
                'https://think.transindex.ro/?cikk=28151&'
                'elmaradt_a_haromszeki_meszarlas_a_sertespestis_sem_eleg_ok_arra_hogy_a_vedett_ragadozokat_kiirtsak',
                'https://think.transindex.ro/?cikk=28132&'
                'a_8222roadkill8221jelenseg_sokkal_pusztitobb_romaniaban_mint_gondolnank',
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

if __name__ == '__main__':
    from webarticlecurator import WarcCachingDownloader, Logger

    main_logger = Logger()

    # Relative path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_htro.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)),
                                                '../../tests/next_page_of_article_htro.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_htro.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)
