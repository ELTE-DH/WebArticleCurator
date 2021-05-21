#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join
import json
from bs4 import BeautifulSoup


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_444(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for 444.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(class_='infinity-next button')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_blikk(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for blikk.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(class_='archiveDayRow2')
    if next_page is not None:
        next_page_a = next_page.find('a', text='Következő oldal')
        if next_page_a is not None and 'href' in next_page_a.attrs:
            ret = 'https:{0}'.format(next_page_a['href'])
    return ret


def extract_next_page_url_mno(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for magyarnemzet.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(class_='en-navigation-line-right-arrow')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_abcug(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for abcug.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='next')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_bbeacon(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for budapestbeacon.com
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_url = soup.select_one('.next')
    if next_page_url is not None and 'href' in next_page_url.attrs:
        ret = next_page_url['href']
    return ret


def extract_next_page_url_mosthallottam(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for mosthallottam.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='nextpostslink')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_gov_koronavirus(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for nnk.gov.hu koronavirus
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('li', class_='pagination-next')
    if next_page is not None:
        next_page_link = next_page.find('a')
        if next_page_link is not None and 'href' in next_page_link.attrs:
            url_end = next_page_link.attrs['href']
            ret = f'https://www.nnk.gov.hu{url_end}'
    return ret


def extract_next_page_url_telex(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for telex.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    pages = soup.find_all('a', class_='page')
    if pages is not None:
        for a_tag in pages:
            if a_tag.text.strip() == '>':
                url_end = a_tag.attrs['href']
                ret = f'https://telex.hu{url_end}'
                break
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing 444')
    text = w.download_url('https://444.hu/2018/04/08')
    assert extract_next_page_url_444(text) == 'https://444.hu/2018/04/08?page=2'
    text = w.download_url('https://444.hu/2018/04/08?page=3')
    assert extract_next_page_url_444(text) is None
    text = w.download_url('https://444.hu/2013/04/13')
    assert extract_next_page_url_444(text) is None

    test_logger.log('INFO', 'Testing magyarnemzet')
    text = w.download_url('https://magyarnemzet.hu/archivum/page/99643')
    assert extract_next_page_url_mno(text) == 'https://magyarnemzet.hu/archivum/page/99644/'
    text = w.download_url('https://magyarnemzet.hu/archivum/page/99644')
    assert extract_next_page_url_mno(text) is None

    test_logger.log('INFO', 'Testing blikk')
    text = w.download_url('https://www.blikk.hu/archivum/online?date=2018-10-15')
    assert extract_next_page_url_blikk(text) == 'https://www.blikk.hu/archivum/online?date=2018-10-15&page=1'
    text = w.download_url('https://www.blikk.hu/archivum/online?date=2018-10-15&page=4')
    assert extract_next_page_url_blikk(text) is None

    test_logger.log('INFO', 'Testing budapestbeacon')
    text = w.download_url('https://budapestbeacon.com/timeline/page/41/')
    assert extract_next_page_url_bbeacon(text) == 'https://budapestbeacon.com/timeline/page/42/'
    text = w.download_url('https://budapestbeacon.com/timeline/page/262/')
    assert extract_next_page_url_bbeacon(text) is None

    test_logger.log('INFO', 'Testing mosthallottam')
    text = w.download_url('https://www.mosthallottam.hu/page/2/?s')
    assert extract_next_page_url_mosthallottam(text) == 'https://www.mosthallottam.hu/page/3/?s'
    text = w.download_url('https://www.mosthallottam.hu/page/31/?s')
    assert extract_next_page_url_mosthallottam(text) is None

    test_logger.log('INFO', 'Testing SOTE koronavirus')
    text = w.download_url('https://semmelweis.hu/hirek/tag/koronavirus/page/3/')
    assert extract_next_page_url_mosthallottam(text) == 'https://semmelweis.hu/hirek/tag/koronavirus/page/4/'
    text = w.download_url('https://semmelweis.hu/hirek/tag/koronavirus/page/8/')
    assert extract_next_page_url_mosthallottam(text) is None

    test_logger.log('INFO', 'Testing NNK.gov.hu koronavirus')
    text = w.download_url('https://www.nnk.gov.hu/index.php/jarvanyugyi-es-infekciokontroll-foosztaly/'
                          'lakossagi-tajekoztatok/koronavirus?start=40')
    assert extract_next_page_url_gov_koronavirus(text) == \
           'https://www.nnk.gov.hu/index.php/jarvanyugyi-es-infekciokontroll-foosztaly/lakossagi-tajekoztatok/' \
           'koronavirus?start=60'
    text = w.download_url('https://www.nnk.gov.hu/index.php/jarvanyugyi-es-infekciokontroll-foosztaly/'
                          'lakossagi-tajekoztatok/koronavirus?start=140')
    assert extract_next_page_url_gov_koronavirus(text) is None

    test_logger.log('INFO', 'Testing Telex')
    text = w.download_url('https://telex.hu/rovat/koronavirus?oldal=4')
    assert extract_next_page_url_telex(text) == 'https://telex.hu/rovat/koronavirus?oldal=5'
    text = w.download_url('https://telex.hu/rovat/koronavirus?oldal=39')
    assert extract_next_page_url_telex(text) is None

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


def extract_article_urls_from_page_nol(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='middleCol')  # There are two of them!
    for a_tag in main_container:
        if a_tag is not None:
            a_tag_as = a_tag.find_all('a', class_='vezetoCimkeAfter')  # Here find_all()!
            for a_tag_a in a_tag_as:
                if a_tag_a is not None and 'href' in a_tag_a.attrs:
                    urls.add(a_tag_a['href'])
    return urls


def extract_article_urls_from_page_origo(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='archive-cikk')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_444(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='card')
    # % -> %25 if not found (escaping error is introduced between 2019 and 2021)
    urls = {link.replace('%', '%25') for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_blikk(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='archiveDayRow')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_index(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('article')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_mno(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_valasz(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')  # The column 'publi' has different name!
    container = soup.find('section', class_={'normal cikk lista', 'publi cikk lista'})
    if container is not None:
        main_container = container.find_all('article', itemscope='')
        urls = {'http://valasz.hu{0}'.format(link) for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_vs(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    my_json = json.loads(archive_page_raw_html)
    html_list = my_json['Data']['ArchiveContents']
    for html_fragment in html_list:
        for fragment in html_fragment['ContentBoxes']:
            soup = BeautifulSoup(fragment, 'lxml')
            for link in safe_extract_hrefs_from_a_tags([soup]):
                urls.add('https://vs.hu{0}'.format(link))
    return urls


def extract_article_urls_from_page_abcug(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2', class_='post-lead')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_magyaridok(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_bbeacon(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    articles = soup.select('.entry-title a')
    article_urls = {article['href'] for article in articles if article is not None and 'href' in article.attrs}
    return article_urls


def extract_article_urls_from_page_semmelweis(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='card-format')
    if len(main_container) == 0:
        main_container = soup.find_all('h3', class_='entry-title')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_gov_koronavirus(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h3', class_='tagtitle')
    urls = {f'https://www.nnk.gov.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_telex(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='article')
    urls = {f'https://telex.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing nol')
    text = w.download_url('http://nol.hu/archivum?page=37')
    extracted = extract_article_urls_from_page_nol(text)
    expected = {'http://nol.hu/archivum/szemelycsere_a_malev_gh_elen-1376265',
                'http://nol.hu/archivum/20130330-garancia-1376783',
                'http://nol.hu/archivum/20130330-politikus_es_kora-1376681',
                'http://nol.hu/belfold/rekord-sosem-volt-meg-ennyi-allami-vezetonk-1630907',
                'http://nol.hu/archivum/http://fsp.nolblog.hu/archives/2013/03/29/'
                'Szuletesnapi_retteges_a_Lendvay_utcaban/-1376849',
                'http://nol.hu/archivum/20130330-kassai_kerdesek-1376679',
                'http://nol.hu/archivum/20130330-kenyszeru_igen_simorra-1376787',
                'http://nol.hu/belfold/'
                'pilz-oliver-nem-akar-kormanyt-buktatni-egyuttmukodni-viszont-keptelenseg-1630901',
                'http://nol.hu/archivum/http://freeze.nolblog.hu/archives/2013/03/31/Vallomasok_Confessions/-1376909',
                'http://nol.hu/belfold/fuss-szijjarto-fuss-1630869',
                'http://nol.hu/belfold/megy-a-mazsolazas-botka-meg-a-raszorulokon-is-gunyolodott-egy-kicsit-1630861',
                'http://nol.hu/belfold/titkosszolgalat-zsarolas-sajtoszabadsag-magyarorszag-1630871',
                'http://nol.hu/belfold/a-kuria-megvedte-a-fidesz-frakcio-titkait-1630899',
                'http://nol.hu/belfold/zanka-tabor-fidesz-1630879'
                }
    assert (extracted, len(extracted)) == (expected, 14)

    text = w.download_url('http://nol.hu/archivum?page=3000')
    extracted = extract_article_urls_from_page_nol(text)
    expected = {'http://nol.hu/archivum/archiv-442261-250322',
                'http://nol.hu/archivum/archiv-442355-250404',
                'http://nol.hu/archivum/archiv-442300-250351',
                'http://nol.hu/archivum/archiv-442364-250413',
                'http://nol.hu/archivum/archiv-442359-250408',
                'http://nol.hu/archivum/archiv-442316-250366',
                'http://nol.hu/archivum/archiv-442362-250411'
                }
    assert (extracted, len(extracted)) == (expected, 7)

    test_logger.log('INFO', 'Testing origo')
    text = w.download_url('https://www.origo.hu/hir-archivum/2019/20190119.html')
    extracted = extract_article_urls_from_page_origo(text)
    expected = {'https://www.origo.hu/sport/csapat/20190119-kezilabda-vilagbajnoksag-a-magyarok-vbcsoportjaban-hozta-a-'
                'kotelezot-a-sved-kezicsapat.html',
                'https://www.origo.hu/sport/csapat/20190119-noi-kosarlabda-nb-i-magabiztosan-nyert-a-'
                'cimvedo-sopron.html',
                'https://www.origo.hu/techbazis/20190119-nemetorszag-apple-qualcomm-iphone-betiltas-'
                'felrevezeto-tajekoztatas.html',
                'https://www.origo.hu/auto/20190118-te-jo-eg-hiaba-kuzdott-a-sofor-siman-lefujta-a-szel-az-utrol-a-'
                'teherautot.html',
                'https://www.origo.hu/sport/futball/20190119-labdarugas-olasz-foci-serie-a-tovabb-tart-az-inter-'
                'remalma-a-kiscsapat-ellen.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-harmadszor-is-nyert-a-siofok-a-noi-kezilabda-'
                'ehfkupaban.html',
                'https://www.origo.hu/nagyvilag/20190119-torokorszagban-ezrek-tuntettek-egy-ehsegsztrajkot-folytato-'
                'kepviselono-mellett.html',
                'https://www.origo.hu/itthon/20190119-kigyulladt-egy-uzlethelyiseg-mezokovesden.html',
                'https://www.origo.hu/nagyvilag/20190119-migranskaravan-usa-honduras-guatemala.html',
                'https://www.origo.hu/sport/trashtalk/20190119-gregg-popovich-edzokent-rekorder-san-antonio-spurs-'
                'nba.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-nb-i-megszorongattak-a-fradit-a-noi-kezilabda-nb-'
                'iben.html',
                'https://www.origo.hu/sport/egyeni/20190119-fucsovics-marton-es-babos-timea-tenisztorteneti-diadala-az-'
                'australian-openen.html',
                'https://www.origo.hu/itthon/20190119-ket-auto-karambolozott-kulcs-kozeleben-a-balesetben-harom-ember-'
                'megserult.html',
                'https://www.origo.hu/gazdasag/20190118-madoff-botrany-tortenete-piramisjatek.html',
                'https://www.origo.hu/sport/futball/20190119-bundesliga-18-fordulo-rb-leipzig-borussia-dortmund-'
                'bajnoki-osszefoglalo-gulacsi-peter.html',
                'https://www.origo.hu/itthon/20190119-tuntetes-eroszak.html',
                'https://www.origo.hu/itthon/20190119-kisorsoltak-az-otos-lotto-nyeroszamait-amivel-majdnem-'
                'ketmilliard-forintot-lehetett-nyerni.html',
                'https://www.origo.hu/teve/20190117-videon-mutatta-meg-sulyos-balesetet-a-szinesz-matt-wilson.html',
                'https://www.origo.hu/itthon/20190119-matol-visszatert-a-tel-orszagszerte-havazas-kezdodik.html',
                'https://www.origo.hu/itthon/20190119-nezopont-ellenzek-kozos-ep-lista-nagy-daniel.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-ferfi-vilagbajnoksag-csaszar-gabor-nyilatkozata-'
                'a-hazautazasarol.html',
                'https://www.origo.hu/sport/futball/20190119-labdarugas-angol-foci-premier-league-hetgolos-pldrama-'
                'hiaba-allt-fel-ketszer-is-a-leicester-video.html',
                'https://www.origo.hu/auto/20190117-bucsu-a-benzinmotortol-smart-eq-forfour-teszt.html',
                'https://www.origo.hu/nagyvilag/20190119-ma-delben-elkezdodott-pawel-adamowicz-fopolgarmester-temetese-'
                'lengyelorszagban-akit-egy-hete.html',
                'https://www.origo.hu/sport/futball/20190119-labdarugas-bajnokok-ligaja-tuzgolyo-elkepesztoen-nez-ki-'
                'kieseses-szakasz-uj-bllabdaja.html',
                'https://www.origo.hu/techbazis/20190117-tmobile-huawei-lopas-amerika.html',
                'https://www.origo.hu/sport/loero/20190119-sebestyen-peter-motorverseny-teljes-szezon-supersport-'
                'vilagbajnoksag-ptr-honda.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-ferfi-vilagbajnoksag-magyarorszag-dania-'
                'elozetes.html',
                'https://www.origo.hu/sport/egyeni/20190119-australian-open-djokovic-zverev-serene-williams-is-'
                'tizenhat-kozott.html',
                'https://www.origo.hu/itthon/20190119-a-tetejere-borult-egy-auto-kaposvaron-a-balesetben-egy-ember-'
                'serult-meg.html',
                'https://www.origo.hu/sport/futball/20190117-a-bajnoki-cim-amiert-semmit-sem-adnak-bundesliga-oszi-'
                'szezon.html',
                'https://www.origo.hu/nagyvilag/20190119-most-egy-euroert-lakast-vehet-sziciliaban.html',
                'https://www.origo.hu/teve/20190119-gorog-zita-nehezen-fogadta-el-szules-utani-uj-kulsejet-tv.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-ferfi-vilagbajnoksag-magyar-dan-meccs-hangulat-a-'
                'meccs-elott.html',
                'https://www.origo.hu/sport/egyeni/20190119-uszas-magyar-uszo-gyozte-le-hosszu-katinkat-antwerpenben-'
                'szilagyi-liliana.html',
                'https://www.origo.hu/sport/kozvetites/20190119-kezilabda-vilagbajnoksag-kozepdonto-magyarorszag-dania-'
                'elo-kozvetites-online.html',
                'https://www.origo.hu/techbazis/20190117-europa-felhalmozodott-iphone-keszletek-alacsony-kereslet.html',
                'https://www.origo.hu/gazdasag/20190119-felsooktatasi-felveteli-2019-apolas-es-betegellatas.html',
                'https://www.origo.hu/tudomany/20190119-a-hang-ugyan-nem-fizikai-objektum-megis-hat-ra-a-'
                'gravitacio.html',
                'https://www.origo.hu/itthon/20190119-karambol-tortent-nagykatanal.html',
                'https://www.origo.hu/techbazis/20190118-windows-10-mobile-tamogatas-megszunese.html',
                'https://www.origo.hu/itthon/20190119-keresi-a-rendorseg-az-idos-tolvajt-aki-alkoholszondat-'
                'lopott.html',
                'https://www.origo.hu/sport/egyeni/20190119-atletika-serulese-utan-gyozelemmel-tert-vissza-marton-'
                'anita.html',
                'https://www.origo.hu/itthon/20190118-ahmedh-tudta-ha-rendoroket-dobal-akkor-bortonbe-megy.html',
                'https://www.origo.hu/sport/csapat/20190119-a-veszprem-jatekosa-sterbik-arpad-ugrik-be-a-spanyol-ferfi-'
                'kezilabdavalogatotthoz-a-vbn.html',
                'https://www.origo.hu/sport/futball/20190119-la-liga-20-fordulo-real-madrid-sevilla-osszefoglalo-video-'
                'casemiro-luka-modric.html',
                'https://www.origo.hu/sport/egyeni/20190119-hosszu-katinka-cseh-laszlo-milak-kristof-majusban-'
                'budapesten-versenyez.html',
                'https://www.origo.hu/nagyvilag/20190119-tobben-meghaltak-es-megegtek-egy-mexikoi-uzemanyagvezetek-'
                'robbanasaban.html',
                'https://www.origo.hu/nagyvilag/20190119-ujabb-onkormanyzat-esett-aldozatul-a-bevandorlasparti-macroni-'
                'rezsimnek.html',
                'https://www.origo.hu/sport/laza/20190119-labdarugas-laza-nemet-foci-rb-leipzig-gulacsi-peter-hegedure-'
                'valtotta-a-kapuskesztyut.html',
                'https://www.origo.hu/sport/futball/20190119-kilencet-lott-a-psg-ebbol-nyolcat-a-felelmetes-csatartrio-'
                'cavani-mbappe-neymar.html',
                'https://www.origo.hu/itthon/20190119-hat-fot-kellett-eltavolitania-a-rendorsegnek-a-lanchidrol.html',
                'https://www.origo.hu/itthon/20190116-jobbik.html',
                'https://www.origo.hu/nagyvilag/20190119-amerikai-legicsapasok-vegeztek-tobb-mint-felszaz-szomaliai-'
                'dzsihadistaval.html',
                'https://www.origo.hu/itthon/20190119-kormanyszovivo-a-tuntetesek-az-epvalasztasi-kampany-reszet-'
                'kepezik.html',
                'https://www.origo.hu/sport/laza/20190119-elo-sportkozvetitesek-a-teveben-januar-19en-szombaton.html',
                'https://www.origo.hu/itthon/20190119-semjen-zsolt-tortenelmi-bun-a-nemet-nemzetiseg-egykori-'
                'eluldozese.html',
                'https://www.origo.hu/sport/futball/20190118-lasha-dvali-ferencvaros-edzotabor-belek-interju.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-ferfi-vilagbajnoksag-a-magyarorszag-dania-'
                'merkozes-osszefoglaloj.html',
                'https://www.origo.hu/gazdasag/20190117-spotify-igy-mukodik-a-bevetel-elosztasa-jogdijak.html',
                'https://www.origo.hu/itthon/20190119-ellenzeki-kepviselok-nagykepu-nyilatkozatai-es-csufos-'
                'kudarcai.html',
                'https://www.origo.hu/sport/csapat/20190119-kezilabda-ferfi-vilagbajnoksag-nyilatkozatok-a-magyar-dan-'
                'meccs-utan.html',
                'https://www.origo.hu/sport/futball/20190119-fc-sion-ferencvaros-felkeszulesi-merkozes-belek.html',
                'https://www.origo.hu/itthon/20190119-ahmed-h-idegenrendeszeti-orizet.html',
                'https://www.origo.hu/sport/futball/20190119-labdarugas-olasz-foci-serie-a-az-as-roma-kis-hijan-'
                'elszorakozta-a-ketgolos-elonyet-video.html',
                'https://www.origo.hu/techbazis/20190117-szexbotrany-ces-vibrator.html',
                'https://www.origo.hu/techbazis/20190116-samsung-galaxy-a90-128-gb-tarhely.html',
                'https://www.origo.hu/nagyvilag/20190119-migranskaravan-regisztracio-nelkul-keltek-at-illegalis-'
                'bevandorlok-a-mexikoiguatemalai-hataron.html',
                'https://www.origo.hu/sport/futball/20190119-bundesliga-18-fordulo-frankfurt-freiburg-leverkusen-'
                'monchengladbach-hannover-werder-augsburg.html',
                'https://www.origo.hu/gazdasag/20190119-felsooktatasi-felveteli-2019-gepeszmernok-szak.html',
                'https://www.origo.hu/teve/20190119-peneszes-dohos-lakasukban-almodni-sem-mert-a-palmafakrol-liptai-'
                'claudia.html',
                'https://www.origo.hu/itthon/20190119-ket-auto-karambolozott-budapesten-tobben-megserultek.html',
                'https://www.origo.hu/itthon/20190119-ma-13-eve-zuhant-le-a-szlovak-legiero-csapatszallito-gepe-hejcen-'
                'a-helyi-emlekmunel-ma-megemlekezest.html',
                'https://www.origo.hu/itthon/20190119-tuntetes-budapesten-szombaton.html',
                'https://www.origo.hu/gazdasag/20190117-igy-nez-ki-a-starbucks-kaveszentelye-balin-galeria-1.html',
                'https://www.origo.hu/itthon/20190119-lelkesz-a-vallasi-uldozesek-70-szazalekaban-kereszteny-az-'
                'aldozat.html',
                'https://www.origo.hu/sport/egyeni/20190119-babos-timea-fucsovics-marton-az-australian-openen-a-vegyes-'
                'parosban.html',
                'https://www.origo.hu/techbazis/20190118-call-of-duty-balck-ops-4-sarga-felkialtojel-bug.html',
                'https://www.origo.hu/itthon/20190119-ellenzek-tuntetes.html',
                'https://www.origo.hu/itthon/20190119-ep-baloldal-civilek-tamogatasa.html',
                'https://www.origo.hu/nagyvilag/20190119-tovabb-erosodott-a-liga-olasz-kormanypart-tamogatottsaga.html',
                'https://www.origo.hu/sport/egyeni/20190119-roger-federer-oltozo-nem-engedtek-be-australian-open.html',
                'https://www.origo.hu/sport/egyeni/20190119-asztalitenisz-world-tour-ezustermes-a-szudi-pergel-vegyes-'
                'paros.html',
                'https://www.origo.hu/sport/futball/20190119-premier-league-23-fordulo-arsenal-chelsea-bajnoki-'
                'osszefoglalo.html',
                'https://www.origo.hu/itthon/20190119-harmas-karambol-kophazanal.html',
                'https://www.origo.hu/sport/egyeni/20190119-vandortabor-jelentkezes-januar-vegetol.html',
                'https://www.origo.hu/sport/futball/20190119-labdarugas-angol-foci-solskjaer-manchestere-verhetetlen-'
                'hetgolos-dramat-nyert-a-liverpool.html',
                'https://www.origo.hu/teve/20190117-megnyert-egy-teves-vetelkedot-de-inkabb-visszamegy-a-harcterre-'
                'sophie-faldo.html',
                'https://www.origo.hu/itthon/20190119-tavaly-augusztusba-egy-vaskuti-ferfi-eletveszelyesen-megkeselt-'
                'egy-soltvadkerti-ferfit.html',
                }
    assert (extracted, len(extracted)) == (expected, 89)

    test_logger.log('INFO', 'Testing 444')
    text = w.download_url('https://444.hu/2019/07/06')
    extracted = extract_article_urls_from_page_444(text)
    expected = {'https://444.hu/2019/07/06/azt-hiszed-szar-iroasztalod-van-nezd-meg-hova-ultettek-ursula-von-der-'
                'leyent',
                'https://444.hu/2019/07/06/kendernay-janos-lett-az-lmp-tars-nelkul-tarselnoke',
                'https://444.hu/2019/07/06/elhangzott-minden-idok-pride-ellenes-erve',
                'https://444.hu/2019/07/06/balmazujvaros-polgarmesterenek-egy-bulvarlap-szolt-hogy-eppen-atverik-oket-'
                'a-focicsapattal',
                'https://444.hu/2019/07/06/egy-nappal-kesobb-a-dk-is-csatlakozott-a-szegedi-ellenzeki-osszefogashoz',
                'https://444.hu/2019/07/06/tobb-szaz-kormanyellenes-tuntetot-vittek-el-a-rendorok-kazahsztanban',
                'https://444.hu/2019/07/06/dunaba-akart-ugrani-a-rendorok-huztak-vissza',
                'https://444.hu/2019/07/06/vaczi-zoltan-a-nyilatkozataval-futballtortenelmet-irt-az-uj-vasas-stadion-'
                'megnyitoja-utan',
                'https://444.hu/2019/07/06/az-utobbi-20-ev-legerosebb-foldrengese-razta-meg-del-kaliforniat',
                'https://444.hu/2019/07/06/lehet-hogy-meg-tobb-faval-lassithatnank-a-klimavaltozast-de-az-amazonasnal-'
                'pont-most-kapcsoltak-csucssebessegre-az-erdoirtok',
                'https://444.hu/2019/07/06/zivatarokkal-ront-az-orszagra-a-hidegfront',
                'https://444.hu/2019/07/06/letartoztattak-egy-het-orosz-titkosszolgalati-tisztbol-allo-fegyveres-'
                'rablobandat',
                'https://444.hu/2019/07/06/eves-auschwitzi-turaja-kozben-halt-meg-a-mengele-laboratoriumaban-'
                'megkinzott-hires-holokauszttulelo-de-elotte-meg-kiposztolta-a-legaranyosabb-holokauszttemaju-twitet',
                'https://444.hu/2019/07/06/cinikus-valaszt-adott-a-dk-arra-hogy-tegnap-miert-nem-alltak-be-botka-moge-'
                'ma-meg-miert-igen',
                'https://444.hu/2019/07/06/szombathely-fideszes-polgarmester-jeloltje-szerint-a-nagy-fejlesztesek-'
                'mellett-az-embereket-foglalkoztato-aprobb-dolgokra-kevesebb-figyelem-jutott',
                'https://444.hu/2019/07/06/vizi-e-szilveszter-elismerte-hogy-beszelt-palkoviccsal-az-mta-tol-elvett-'
                'kutatointezetek-vezeteserol',
                'https://444.hu/2019/07/06/remalom-kozossegi-gazdasagnak-nevezik-hogy-havi-1200-dollarert-kivehetsz-'
                'egy-agyat-egy-kimosakodott-hajlektalanszallason',
                'https://444.hu/2019/07/06/dj-snake-utan-sean-paul-is-lemondta-fellepeset-a-balaton-soundon',
                'https://444.hu/2019/07/06/kilora-vette-meg-a-hollywoodi-sztarokat-a-wall-street-farkasa-sikkasztasert-'
                'letartoztatott-producere',
                'https://444.hu/2019/07/06/fel-akarta-gyujtani-a-zsinagogat-a-balfasz-naci-sajat-magat-sikerult',
                'https://444.hu/2019/07/06/messit-kiallitottak-kakaskodasert',
                'https://444.hu/2019/07/06/lancfuresszel-faragott-vicces-szobrot-allitottak-szloveniai-szulovarosaban-'
                'melania-trumpnak',
                'https://444.hu/2019/07/06/lezarasok-lesznek-delutan-a-belvarosban-a-pride-miatt',
                'https://444.hu/2019/07/06/remiszto-hangu-leny-zaklatja-a-lakossagot-sasadon',
                'https://444.hu/2019/07/06/nem-hagyhatjuk-szo-nelkul-hogy-masodrendu-allampolgarokkent-kezeljenek-'
                'minket',
                'https://444.hu/2019/07/06/eszak-korea-szerint-kemkedett-a-letartoztatott-ausztral-diak',
                'https://444.hu/2019/07/06/kiugrott-egy-beteg-a-del-pesti-korhaz-masodik-emeleterol',
                'https://444.hu/2019/07/06/2rule-reklamot-gyartott-a-tenyek',
                'https://444.hu/2019/07/06/horvatorszag-hivatalosan-kerte-az-euro-bevezeteset',
                'https://444.hu/2019/07/06/makadon-talaltak-meg-a-hableany-utolso-elotti-aldozatat',
                'https://444.hu/2019/07/06/felhaborodtak-a-szulok-es-a-diakok-hogy-a-gyori-megyespuspok-kirugta-az-'
                'igazgatot',
                'https://444.hu/2019/07/06/a-magyar-allam-bankja-befektet-56-milliardot-meszaros-lorinc-izocukor-'
                'gyaraba',
                'https://444.hu/2019/07/06/eladja-uduloit-a-posta-hogy-legyen-penze-beremelesre',
                'https://444.hu/2019/07/06/ujabb-eros-foldrenges-razta-meg-del-kaliforniat',
                'https://444.hu/2019/07/06/havi-hatvenezres-osztondijat-kapnak-azok-az-egyetemistak-akik-hajlandok-'
                'kormanyparti-velemenyeket-irni-a-neten-az-onkormanyzati-valasztasok-elott',
                'https://444.hu/2019/07/06/durva-torlodas-alakult-ki-a-szantodi-kompnal-ezekben-a-percekben-kezd-'
                'lazulni-a-helyzet',
                'https://444.hu/2019/07/06/a-fidesz-frakciovezeto-helyettese-meg-kell-vedeni-a-gyerekeket-a-szexualis-'
                'aberraciotol-a-pride-ot-be-kell-tiltani4'
                }
    assert (extracted, len(extracted)) == (expected, 37)

    test_logger.log('INFO', 'Testing blikk')
    text = w.download_url('https://www.blikk.hu/archivum/online?date=2018-11-13&page=0')
    extracted = extract_article_urls_from_page_blikk(text)
    expected = {'https://www.blikk.hu/aktualis/belfold/szorenyi-levente/cr10wsw',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/sokk-kritika-konyhafonok-vip-sef/x7tzj86',
                'https://www.blikk.hu/sport/magyar-foci/megszolalt-merkozes-kozben-elhunyt-csornai-focista-menyasszony/'
                'ffe6ejf',
                'https://www.blikk.hu/sport/csapat/gyozelem-ferfi-vizilabda-gyozelem-oroszorszag/ewz4ql8',
                'https://www.blikk.hu/aktualis/belfold/penzvalto-rablas-motorosok-menekules-arulas-budapest/rfh8vr0',
                'https://www.blikk.hu/sport/magyar-foci/magyar-valogatott-ugrai-roland-bokaserules/96hfqer',
                'https://www.blikk.hu/sztarvilag/filmklikk/tronok-harca-uj-evead-hbo/lhvv61q',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/gaspar-evelin-torta-sutes-ruzsa-magdi/5bs2fe5',
                'https://www.blikk.hu/aktualis/belfold/motorost-gazolt-halalra-egy-kamion-hodmezovasarhelynel/8mh263s',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/dobo-kata-lampalaz-szineszet/f0vdqnq',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/szabo-gyozo-horkolas/xrp8rcd',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/a-legbatrabb-paros-kieso-cooky-sztarchat/7elsdbx',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/halle-berry-marokko-szahara/g9ntm4l',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/ratajkowski-bikini-napfeny/zyl4gld',
                'https://www.blikk.hu/aktualis/politika/poszony-cseh-andrej-babis/mnfhl9w',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/koncert-ingyenes-hosoktere/w2lfk5q',
                'https://www.blikk.hu/aktualis/kulfold/szaud-arabia-tronorokos-szaudi-ujsagiro/y9lchkn',
                'https://www.blikk.hu/sport/kulfoldi-foci/feczesin-robert-adana-torokorszag-foci-lovoldozes/k9xj0kz',
                'https://www.blikk.hu/aktualis/belfold/idojaras-tel-egyik-naprol-a-masikra-fagyok-magyarorszag-havazas-'
                'ho/203mly4',
                'https://www.blikk.hu/aktualis/belfold/szkopje-nikola-gruevszki-macedon-miniszterelnok-budapest/'
                'dhdnknm',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/stan-lee-marvel-elhunyt-felesege-halala-problemak-'
                'betegseg/b76ynlf',
                'https://www.blikk.hu/sport/kulfoldi-foci/gonzalo-higuain-ac-milan-eltiltas/h79v0dp',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/r-karpati-peter-szinesz/6whxb0h',
                'https://www.blikk.hu/sport/spanyol-foci/2021-real-madrid-kispad-edzo-santaigo-solari-szerzodes/'
                'tscq598',
                'https://www.blikk.hu/aktualis/politika/rick-perry-orban-viktor-ajandek-amerika/znw4rrw',
                'https://www.blikk.hu/aktualis/belfold/diak-szex-tanarno-szekesfehervar/n3z5ljp',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/vajna-timi-szexi-pucsit/2gslgww',
                'https://www.blikk.hu/sztarvilag/sztarsztorik/birsag-buntetes-autosok/x4zd3xp',
                'https://www.blikk.hu/hoppa/wtf/samsung-agyhullam-iranyitas/we73y0t',
                'https://www.blikk.hu/eletmod/egeszseg/film-cukorbetegseg-diabetesz-etkezes/35z7vws'
                }
    assert (extracted, len(extracted)) == (expected, 30)

    test_logger.log('INFO', 'Testing index')
    text = w.download_url('https://index.hu/24ora?s=&tol=2019-07-12&ig=2019-07-12&tarskiadvanyokbanis=1&profil=&rovat='
                          '&cimke=&word=1&pepe=1&page=')
    extracted = extract_article_urls_from_page_index(text)
    expected = {'https://index.hu/mindekozben/poszt/2019/07/12/mav_korhaz_vece_vakolat_csernobil/',
                'https://index.hu/mindekozben/poszt/2019/07/12/szornyszulotteket_keszitenek_a_ketezres_evek_kedvenc_'
                'gyerekjatekabol/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_wimbledon_elodonto_legyozte_djokovic/',
                'https://index.hu/nagykep/2019/07/12/rendszervaltas_kiallitas_bankuti_andras/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/kettos_hibaval_ket_'
                'breklabdahoz_jutott_nadal/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadalnak_a_szettben_'
                'maradasert_kell_szervalnia/',
                'https://index.hu/belfold/2019/07/12/elhagyott_a_brfk_egy_pendrive-ot_az_osszes_munkatarsuk_szemelyes_'
                'adataval/',
                'https://index.hu/kultur/2019/07/12/egy_honap_es_jon_a_mindhunter_masodik_evada/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/szep_pontok_egymas_'
                'utan/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/elonyben_a_harmadik_'
                'szettben_a_svajci/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/ujabb_ket_breklabda/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/a_meccs_legszebb_'
                'utese_federere_de_nadal_hozta_az_adogatasat/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/15-30-cal_indult_de_'
                'hozta_federer_a_szervajat/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/4_2/',
                'https://index.hu/sport/atletika/2019/07/12/atletikai_vilagcsucs_megdolt_noi_egy_merfold_sifan_hassan_'
                'monaco_gyemant_liga/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadal_kiegyenlitett_a_'
                'szetteket_tekintve/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_elrontotta_a_'
                'lecsapast_breklabda/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/fontos_hosszu_'
                'labdameneteket_is_nyert_federer/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/breklabdahoz_jutott_'
                'federer/',
                'https://index.hu/kultur/cinematrix/2019/07/12/leonardo_dicaprio_forrongo_jeg_ice_on_fire_'
                'dokumentumfilm_klimavaltozas/',
                'https://index.hu/belfold/2019/07/12/szombaton_visszaterhet_a_kanikula/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/megforditotta_a_'
                'svajci_megerositette_a_brekelonyt/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadal_haritott_egy_'
                'meccslabdat/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/magabiztosan_'
                'erositette_meg_a_breket_federer/',
                'https://index.hu/kultur/zene/2019/07/12/pataky_attila_kohaszruhaban_lepett_fel/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadal_emelt_a_jatekan_'
                'federer_szervaja_beragadt/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/meccslabdaja_van_'
                'federernek/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_ket_labdara_'
                'nadal_szervajanal/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/ket_meccslabdarol_'
                'megforditotta_nadal/',
                'https://galeria.index.hu/sport/tenisz/2019/07/12/nadal_es_federer_meccs_wimbledon/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/sima_jatek_nadaltol/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_mindketten_'
                'nagyon_magas_szinvonalon_jatszottunk/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_kiharcolt_'
                'ket_breklabdat/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/masodszor_is_'
                'meccslabdaja_van_federernek/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadal_kezdte_a_'
                'negyedik_szettet/',
                'https://index.hu/gazdasag/2019/07/12/ujabb_allami_ceg_dobta_meg_nehany_tizmillioval_a_rogan_'
                'cecilia-fele_fitneszrendezvenyeket/',
                'https://index.hu/sport/futball/2019/07/12/antoine_griezmann_atletico_madrid_jogi_lepesek_barcelona_'
                'igazolas/',
                'https://index.hu/sport/2019/07/12/toroltek_a_red_bull_air_race_szabadedzeseinek_repuleseit/',
                'https://index.hu/kulfold/2019/07/12/papirok_nelkuli_bevandorlok_rohantak_meg_a_parizsi_pantheont/',
                'https://index.hu/techtud/2019/07/12/5_milliard_dollart_fizetne_a_facebook_hogy_elsimitsa_az_'
                'adatvedelmi_vizsgalatot/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/30-30/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadal_masodszor_is_'
                'lebrekelte_a_svajcit/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_ujbol_semmire_'
                'hozta_a_szervajat/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_egy_jatekra_'
                'a_gyozelemtol/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/semmire_szervalta_ki_'
                'federer/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/ujabb_sima_jatek_'
                'federertol/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_legyozte_'
                'nadalt_12._wimbledoni_dontojebe_jutott_be/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/gyorsan_hozta_nadal_'
                'is/',
                'https://index.hu/gazdasag/2019/07/12/hol_a_penz_14_fesztival_kadar_tamas/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/nadal_egy_fonak_'
                'elutessel_haritotta/',
                'https://index.hu/gazdasag/2019/07/12/ujabb_vizsgalatok_a_johnson_johnson_ellen_a_rakkelto_hintopor_'
                'miatt/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/a_svajci_2_1_szett_'
                'melle_brekelonyben/',
                'https://divany.hu/offline/2019/07/12/szinfalak-mogotti-sztorik/',
                'https://index.hu/sport/futball/2019/07/12/szalai_adam_bundesliga_legszebb_tamadas_gol_video/',
                'https://index.hu/sport/uszas/2019/07/12/vizes_vb_2019_varakozasok_sportagak/',
                'https://index.hu/mindekozben/poszt/2019/07/12/az_amazonon_legalisan_lehet_venni_urant/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/haritotta_nadal_de_'
                'asszal_negyedik_is_van_federernek/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/federer_'
                'kiszervalhatja/',
                'https://galeria.totalcar.hu/blogok/2019/07/12/a_holdra_szallas_elozmenyei/',
                'https://index.hu/sport/tenisz/2019/07/12/federer_nadal_elodonto_wimbledon_ferfi/mindkettot_haritotta_'
                'federer/'
                }
    assert (extracted, len(extracted)) == (expected, 60)

    test_logger.log('INFO', 'Testing velvet')
    text = w.download_url('https://velvet.hu/24ora?s=&tol=2019-08-03&ig=2019-08-04&profil=&rovat=&cimke=&word=1&pepe=1')
    extracted = extract_article_urls_from_page_index(text)
    expected = {'https://velvet.hu/nyar/2019/08/04/sziget_nagyszinpad_fellepok_heti_trend/',
                'https://velvet.hu/randi/2019/08/04/randiblog_inbox_a_felesegem_mellett_van_2_szeretom/',
                'https://velvet.hu/nyar/2019/08/04/palvin_mihalik_bikini_trend_nyar/',
                'https://velvet.hu/gumicukor/2019/08/04/megszuletett_curtisek_kisfia/',
                'https://velvet.hu/elet/2019/08/04/hawaii_kokuszposta_galeria/',
                'https://velvet.hu/gumicukor/2019/08/04/lista_nepszeru_celeb/',
                'https://velvet.hu/nyar/2019/08/04/kiegeszitok_amelyek_feldobjak_a_fesztivalszettet/',
                'https://velvet.hu/gumicukor/2019/08/04/sztarok_akik_elarultak_latvanyos_fogyasuk_titkat/',
                'https://velvet.hu/gumicukor/2019/08/03/ha_vege_a_hagyateki_'
                'targyalasnak_vajna_timea_orokre_el_akarja_hagyni_magyarorszagot/',
                'https://velvet.hu/randi/2019/08/03/randiblog_inbox_munkahelyi_szerelem/',
                'https://velvet.hu/elet/2019/08/03/megteveszto_anya-lanya_paros_galeria/',
                'https://velvet.hu/gumicukor/2019/08/03/igy_elnek_a_palyboy_villa_lanyai/',
                'https://velvet.hu/gumicukor/2019/08/03/czutor_zoltan_tapasztalatai_alapjan_'
                'tobb_a_szexista_no_mint_ferfi/',
                'https://velvet.hu/gumicukor/2019/08/03/extrem_titkos_projekt_miatt_hagyta_ott_'
                'a_radiot_sebestyen_balazs/',
                'https://velvet.hu/elet/2019/08/03/hiressegek_akik_nem_kernek_az_anyasagbol_galeria/',
                'https://velvet.hu/gumicukor/2019/08/03/mick_jagger_kisfianak_minden_rezduleseben_ott_van_az_apja/',
                'https://velvet.hu/elet/2019/08/03/27_ev_van_kozottuk_megis_boldogok_galeria/'
                }
    assert (extracted, len(extracted)) == (expected, 17)

    test_logger.log('INFO', 'Testing mno')
    text = w.download_url('https://magyarnemzet.hu/archivum/page/99000/')
    extracted = extract_article_urls_from_page_mno(text)
    expected = {'https://magyarnemzet.hu/archivum/archivum-archivum/a-szuverenitas-hatarai-4473980/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/tajvan-ujra-teritekre-kerult-4473983/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/kie-legyen-az-iparuzesi-ado-4473989/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/allampolgari-javaslatra-terveznek-furdokozpontot-'
                'gyorott-4473992/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/felelem-bekes-megyeben-nappal-rendorok-ejszaka-'
                'ketes-hiru-vallalkozok-tarsai-4473998/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/precedens-per-4474004/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/csak-a-turelem-segithet-4473986/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/kozelit-a-vilag-zagrabhoz-4473977/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/tanitjak-az-onallo-eletvitelt-4474001/',
                'https://magyarnemzet.hu/archivum/archivum-archivum/veszelyforrasok-4473995/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Testing vs')
    text = w.download_url('https://vs.hu/ajax/archive?Data={%22QueryString%22:%22%22,%22ColumnIds%22:[],'
                          '%22SubcolumnIds%22:[],%22TagIds%22:[],%22HasPublicationMinFilter%22:true,'
                          '%22PublicationMin%22:%222018-04-04T00:00:00.000Z%22,%22HasPublicationMaxFilter%22:true,'
                          '%22PublicationMax%22:%222018-04-05T00:00:00.000Z%22,%22AuthorId%22:-1,'
                          '%22MaxPublished%22:%222018-04-05T00:00:00.000Z%22,%22IsMega%22:false,%22IsPhoto%22:false,'
                          '%22IsVideo%22:false}')
    extracted = extract_article_urls_from_page_vs(text)
    expected = {'https://vs.hu/kozelet/osszes/az-lmp-is-visszalep-csepelen-0404',
                'https://vs.hu/kozelet/osszes/visszalepesek-nehany-fontos-valasztokeruletben-0404',
                'https://vs.hu/magazin/osszes/fel-evszazada-startolt-az-urodusszeia-0404',
                'https://vs.hu/gazdasag/osszes/tovabb-terjeszkedne-az-otp-bulgariaban-0404',
                'https://vs.hu/kozelet/osszes/korszerusitettek-az-elte-15-epuletet-0404',
                'https://vs.hu/magazin/osszes/kitiltjak-romaniabol-a-vekony-muanyagszatyrokat-0404',
                'https://vs.hu/kozelet/osszes/orosz-trollokat-torolt-a-facebook-0404',
                'https://vs.hu/sport/osszes/a-liverpool-es-a-barcelona-is-haromgolos-elonyben-0404',
                'https://vs.hu/kozelet/osszes/vedjegy-a-gmo-mentessegrol-0404',
                'https://vs.hu/kozelet/osszes/az-lmp-sok-csaladnak-adna-eleget-es-nem-keveseknek-sokat-0404',
                'https://vs.hu/kozelet/osszes/eros-szel-es-kellemes-homerseklet-0404',
                'https://vs.hu/kozelet/osszes/czegledy-letartoztatasanak-meghosszabbitasat-inditvanyoztak-0404',
                'https://vs.hu/kozelet/osszes/meg-szombaton-is-agital-a-fidesz-0404',
                'https://vs.hu/gazdasag/osszes/a-kopint-tarki-4-szazalekos-gdp-bovulest-var-0404',
                'https://vs.hu/kozelet/osszes/a-szkripal-ugy-a-hideghaborura-emlekeztet-0404',
                'https://vs.hu/kozelet/osszes/foldosztas-ukrajnaban-0404',
                'https://vs.hu/magazin/osszes/rendbe-hozzak-a-nadasdladanyi-kastelyt-0404',
                'https://vs.hu/kozelet/osszes/nezopont-orban-nepszerusege-folyamatosan-no-0404',
                'https://vs.hu/magazin/osszes/komaromba-koltoztetik-a-szepmuveszeti-egy-reszet-0404'
                }
    assert (extracted, len(extracted)) == (expected, 19)

    test_logger.log('INFO', 'Testing valasz (normal)')
    text = w.download_url('http://valasz.hu/itthon/?page=1')
    extracted = extract_article_urls_from_page_valasz(text)
    expected = {'http://valasz.hu/itthon/ez-nem-autopalya-epites-nagyinterju-palinkas-jozseffel-a-tudomany-penzeirol-'
                '129168',
                'http://valasz.hu/itthon/itt-a-madaras-adidas-eletkepes-lehet-e-egy-nemzeti-sportmarka-129214',
                'http://valasz.hu/itthon/halapenzt-reszletre-129174',
                'http://valasz.hu/itthon/buda-gardens-ugy-lazar-verengzest-rendezett-a-miniszterelnoksegen-129175',
                'http://valasz.hu/itthon/minden-szinvonalat-alulmul-palinkas-jozsef-a-kormanymedia-tamadasarol-129173',
                'http://valasz.hu/itthon/szeressuk-a-szarkakat-129223',
                'http://valasz.hu/itthon/borokai-gabor-a-2rule-rol-129172',
                'http://valasz.hu/itthon/megsem-tiltottak-ki-a-belvarosbol-a-segwayeket-ez-tortent-valojaban-129222',
                'http://valasz.hu/itthon/a-heti-valasz-lap-es-konyvkiado-szolgaltato-kft-kozlemenye-129225',
                'http://valasz.hu/itthon/az-megvan-hogy-meleghazassag-es-migracioellenes-az-lmp-uj-elnoke-129211',
                'http://valasz.hu/itthon/a-nehezfiuknak-is-van-szive-129179',
                'http://valasz.hu/itthon/humboldt-dijas-kvantumfizikus-alapkutatas-nelkul-nincs-fejlodes-129197',
                'http://valasz.hu/itthon/hogyan-zajlik-egy-kereszteny-hetvege-a-fegyintezetekben-129165',
                'http://valasz.hu/itthon/ha-tetszik-ha-nem-ez-lehet-2019-sztorija-orban-vagy-macron-129201',
                'http://valasz.hu/itthon/abszurdra-sikerult-az-uj-gyulekezesi-torveny-borton-jarhat-gyurcsany-'
                'kifutyuleseert-129207'
                }
    assert (extracted, len(extracted)) == (expected, 15)

    test_logger.log('INFO', 'Testing valasz (publi)')
    text = w.download_url('http://valasz.hu/publi?page=2')
    extracted = extract_article_urls_from_page_valasz(text)
    expected = {'http://valasz.hu/publi/szelektiven-nemzeti-kormany-127741',
                'http://valasz.hu/publi/ha-orban-ezert-rasszista-en-is-az-vagyok-127737',
                'http://valasz.hu/publi/hat-allitas-a-fidesz-ujabb-ketharmados-gyozelmerol-128083',
                'http://valasz.hu/publi/egy-biztos-a-fidesz-nyeri-a-valasztast-128062',
                'http://valasz.hu/publi/remalom-lesz-az-aprilis-8-i-valasztas-127918',
                'http://valasz.hu/publi/az-ellenzeki-media-miatt-nyert-marki-zay-orban-sulyos-tevedese-127642',
                'http://valasz.hu/publi/ezert-hasalt-el-az-ellenzek-osszes-temaja-128099',
                'http://valasz.hu/publi/a-magyar-jobboldal-hat-halalos-ellensege-128048',
                'http://valasz.hu/publi/donald-trump-uj-energiafegyvere-127780',
                'http://valasz.hu/publi/ebbol-meg-baj-lesz-nem-mindenhol-gyoztunk-a-politikai-korrektseg-felett-127499',
                'http://valasz.hu/publi/edes-savanyu-kinai-puspokfalat-127614',
                'http://valasz.hu/publi/fidesz-vagy-nem-fidesz-egy-konzervativ-honpolgar-vallomasa-a-szavazasrol-'
                '128050',
                'http://valasz.hu/publi/valasztas-egy-ket-dolgot-felreertettunk-128150',
                'http://valasz.hu/publi/mi-a-kozos-lazar-becsi-filmjeben-es-a-kosa-fele-oroksegmilliardokban-127805',
                'http://valasz.hu/publi/a-nyugati-hanyatlas-uj-szimboluma-127602'
                }
    assert (extracted, len(extracted)) == (expected, 15)

    test_logger.log('INFO', 'Testing budapestbeacon (HU)')
    text = w.download_url('https://hu.budapestbeacon.com/archivum/page/1/')
    extracted = extract_article_urls_from_page_bbeacon(text)
    expected = {'https://hu.budapestbeacon.com/video/kunhalmi-ne-adjak-fel-mi-sem-adjuk-fel/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/juhasz-peter-teljesen-evidens-hogy-csalas-tortent/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/bar-budapesten-aratott-a-demokrata-oldal-a-mandatumok-'
                'mintegy-ketharmadat-nyerte-meg-a-fidesz/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/szivemhez-legkozelebb-a-momentum-all-interju-lukacsi-'
                'katalinnal/',
                'https://hu.budapestbeacon.com/video/az-egyuttnek-mint-politikai-partnak-nincsen-folytatasa-interju-'
                'szabo-szabolccsal/',
                'https://hu.budapestbeacon.com/video/gulyas-marton-uzenete-a-budapest-beacon-olvasoinak/',
                'https://hu.budapestbeacon.com/video/nyomas-mindig-van-a-kerdes-hogy-a-biro-ellen-tud-e-allni/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/el-nem-tudom-kepzelni-hogy-ez-az-ellenzek-le-tudja-'
                'gyozni-a-mostani-hatalmat-az-egesz-politikai-elitet-kiosztotta-eloadasaban-tolgyessy-peter/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/a-budapest-beacon-bucsuinterjuja/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/kovacs-gergely-a-444-a-jelleget-tekintve-megszorozta-'
                'magat-kettovel/',
                'https://hu.budapestbeacon.com/video/kovacs-gergely-a-444-a-jelleget-tekintve-megszorozta-magat-'
                'kettovel/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/kunhalmi-ne-adjak-fel-mi-sem-adjuk-fel/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/isten-mentsen-meg-minket-a-forradalomtol-vagy-a-'
                'polgarhaborutol-interju-ara-kovacs-attilaval/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/gulyas-marton-uzenete-a-budapest-beacon-olvasoinak/',
                'https://hu.budapestbeacon.com/egyebhirek/karacsony-szerint-a-fidesz-egyharmad-a-fidesz-plusz-jobbik-'
                'fel-alatt-lesz-az-uj-parlamentben-ez-tortent-csutortokon/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/az-egyuttnek-mint-politikai-partnak-nincsen-folytatasa-'
                'interju-szabo-szabolccsal/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/a-hatalom-azt-akarja-elerni-hogy-feljunk-atszavazni/',
                'https://hu.budapestbeacon.com/kiemelt-cikkek/szabo-szabolcs-ebbol-az-lesz-a-vegen-hogy-a-fidesz-fog-'
                'gyozni-es-akkor-ego-sepruvel-fognak-kergetni-minket-az-utcan-a-valasztok/',
                'https://hu.budapestbeacon.com/video/isten-mentsen-meg-minket-a-forradalomtol-vagy-a-polgarhaborutol-'
                'interju-ara-kovacs-attilaval/',
                'https://hu.budapestbeacon.com/video/juhasz-peter-teljesen-evidens-hogy-csalas-tortent/'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Testing budapestbeacon (EN)')
    text = w.download_url('https://budapestbeacon.com/search/?_sf_s&sf_paged=436')
    extracted = extract_article_urls_from_page_bbeacon(text)
    expected = {'https://budapestbeacon.com/moma-chairman-lajos-bokros-calls-opposition-unity/?_sf_s&sf_paged=436',
                'https://budapestbeacon.com/figyelo-eu-funds-embezzled-in-hungary/?_sf_s&sf_paged=436',
                'https://budapestbeacon.com/hungarian-teachers-preparing-strike/?_sf_s&sf_paged=436'
                }
    assert (extracted, len(extracted)) == (expected, 3)

    test_logger.log('INFO', 'Testing mosthallottam')
    text = w.download_url('https://www.mosthallottam.hu/page/2/?s')
    extracted = extract_article_urls_from_page_magyaridok(text)
    expected = {'https://www.mosthallottam.hu/hasznos_info/munkaszuneti-napok-2021-ev-munkarend/',
                'https://www.mosthallottam.hu/tudtad-hogy/regi-mertekegysegek-mertekek-1/',
                'https://www.mosthallottam.hu/erzelemertelem/a-koronavirus-utani-uj-vilag/',
                'https://www.mosthallottam.hu/erdekes/latod-az-orrodat-vagy-megsem/',
                'https://www.mosthallottam.hu/erdekes/online-tarskereses-a-karanten-maganyabol/',
                'https://www.mosthallottam.hu/uncategorized/boldog-husveti-unnepeket-2/',
                'https://www.mosthallottam.hu/tudtad-hogy/facebook-shops-ingyen-nyithatsz-webaruhazat/',
                'https://www.mosthallottam.hu/termeszet/azsiai-tigrisszunyog-azsiai-zebraszunyog/',
                'https://www.mosthallottam.hu/termeszet/ev-madara-2021/',
                'https://www.mosthallottam.hu/allat/ezert-szaritkozik-bundajat-razva-a-kutya/',
                'https://www.mosthallottam.hu/tudtad-hogy/ennyi-telefonszamot-hasznalnak-magyarorszagon/',
                'https://www.mosthallottam.hu/tudtad-hogy/regi-mertekegysegek-mertekek-2/',
                'https://www.mosthallottam.hu/erdekes/csaladnevek-kalandozas-a-nevek-vilagaban-2/',
                'https://www.mosthallottam.hu/tudtad-hogy/mennyi-nemzeti-unnepunk-van/'
                }
    assert (extracted, len(extracted)) == (expected, 14)

    text = w.download_url('https://www.mosthallottam.hu/page/31/?s')
    extracted = extract_article_urls_from_page_magyaridok(text)
    expected = {'https://www.mosthallottam.hu/about/'}
    assert (extracted, len(extracted)) == (expected, 1)

    test_logger.log('INFO', 'Testing SOTE koronavirus')
    text = w.download_url('https://semmelweis.hu/hirek/tag/koronavirus/page/3/')
    extracted = extract_article_urls_from_page_semmelweis(text)
    expected = {'https://semmelweis.hu/hirek/2020/06/13/latogatasi-tilalom/',
                'https://semmelweis.hu/hirek/2020/05/22/milesz-dora-konduktorkent-ebben-a-megvaltozott-helyzetben-'
                'itthonrol-igyekszem-segitseget-nyujtani/',
                'https://semmelweis.hu/hirek/2020/06/05/dr-fenyves-bank-sokunknak-ez-egy-eletre-szolo-tapasztalat/',
                'https://semmelweis.hu/hirek/2020/05/25/interaktiv-terkepen-kovethetoek-a-vilag-orszagainak-aktualis-'
                'utazasi-korlatozasai/',
                'https://semmelweis.hu/hirek/2020/05/19/kotelezo-maszkviseles-es-a-vedotavolsag-betartasa-mellett-nyit-'
                'az-egyetem/',
                'https://semmelweis.hu/hirek/2020/05/27/kozma-borbala-komoly-attorest-hozott-a-munkamban-a-jarvanyugyi-'
                'helyzet/',
                'https://semmelweis.hu/hirek/2020/05/18/h-uncover-reprezentativ-lett-az-orszagos-koronavirus-'
                'szurovizsgalat-eredmenye/',
                'https://semmelweis.hu/hirek/2020/05/13/lekerult-a-lelegeztetogeprol-a-covid-19-beteg-a-'
                'verplazmaterapianak-koszonhetoen-a-semmelweis-egyetemen/',
                'https://semmelweis.hu/hirek/2020/05/19/ajandekcsomagokat-kaptak-a-semmelweis-egyetem-apoloi-a-loreal-'
                'magyarorszagtol/',
                'https://semmelweis.hu/hirek/2020/06/04/a-semmelweis-egyetem-felel-a-jarvanyugyi-biztonsagert-az-idei-'
                'hungaroringen/',
                'https://semmelweis.hu/hirek/2020/05/29/az-orszagos-verellato-szolgalat-felhivasa-hallgatok-szamara/',
                'https://semmelweis.hu/hirek/2020/05/14/karantenba-zart-dolgozatok-erettsegi-a-jarvany-alatt/',
                'https://semmelweis.hu/hirek/2020/05/20/eletmento-szallitoinkubatort-adomanyozott-a-semmelweis-'
                'egyetemnek-a-meszaros-csoport/',
                'https://semmelweis.hu/hirek/2020/05/20/lepcsozetesen-oldja-fel-az-intezmenylatogatasi-tilalmat-a-'
                'semmelweis-egyetem/',
                'https://semmelweis.hu/hirek/2020/05/28/kozlemeny-dijat-kapott-dr-palko-judit/',
                'https://semmelweis.hu/hirek/2020/05/15/dr-jasz-mate-oktatasi-forradalom-11-nap-alatt/',
                'https://semmelweis.hu/hirek/2020/05/11/tajekoztato-az-ideiglenes-otthoni-munkavegzes-indokoltsaganak-'
                'felulvizsgalatarol/',
                'https://semmelweis.hu/hirek/2020/05/20/onjaro-robot-segiti-a-koronavirus-elleni-vedekezest-a-'
                'semmelweis-egyetemen/',
                'https://semmelweis.hu/hirek/2020/06/02/lukacs-maria-a-takarito-szemelyzeten-most-majdnem-ketszeres-a-'
                'terheles/',
                'https://semmelweis.hu/hirek/2020/05/14/kozlemeny-szombaton-zarul-az-orszagos-koronavirus-teszteles/',
                'https://semmelweis.hu/hirek/2020/06/10/betegtajekoztato-ismet-eredeti-helyen-mukodik-az-ortopediai-'
                'klinika-es-a-ful-orr-gegeszeti-es-fej-nyaksebeszeti-klinika/',
                'https://semmelweis.hu/hirek/2020/05/12/h-uncover-a-meghivottak-fele-mar-elment-a-koronavirus-'
                'szurovizsgalatra/',
                'https://semmelweis.hu/hirek/2020/05/29/lehoczky-gyozo-mindenki-megtanult-alkalmazkodni-a-kialakult-'
                'helyzethez/',
                'https://semmelweis.hu/hirek/2020/05/13/h-uncover-reszeredmenyek-8276-tesztbol-ketto-lett-pozitiv/'
                }
    assert (extracted, len(extracted)) == (expected, 24)

    text = w.download_url('https://semmelweis.hu/hirek/tag/koronavirus/page/8/')
    extracted = extract_article_urls_from_page_semmelweis(text)
    expected = {'https://semmelweis.hu/hirek/2020/03/02/a-semmelweis-egyetem-lakossagi-tajekoztatoja-az-uj-'
                'koronavirusrol/',
                'https://semmelweis.hu/hirek/2020/01/28/a-semmelweis-egyetem-felkeszult-a-koronavirussal-erintett-'
                'teruletrol-erkezo-hallgatok-fogadasara/'
                }
    assert (extracted, len(extracted)) == (expected, 2)

    test_logger.log('INFO', 'Testing NNK.gov.hu koronavirus')
    text = w.download_url('https://www.nnk.gov.hu/index.php/jarvanyugyi-es-infekciokontroll-foosztaly/'
                          'lakossagi-tajekoztatok/koronavirus?start=40')
    extracted = extract_article_urls_from_page_gov_koronavirus(text)
    expected = {'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/766-m-surile-restrictive-privind-accesul-n-'
                'ungaria-au-intrat-n-vigoare',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/777-32-het-enyhen-novekszik-a-koronavirus-'
                'orokitoanyag-mennyisege-a-szennyvizben',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/760-otthoni-koronavirus-tesztekkel-'
                'kapcsolatban-figyelmeztet-a-gvh',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/774-31-het-tovabbra-is-alacsony-a-'
                'szennyvizekben-mert-virus-koncentracioja',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/785-tanulok-cov-2-teszt',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/746-kanada-sarga-portugalia-zold-besorolast-'
                'kapott',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/740-the-restrictive-measures-regarding-the-'
                'access-to-hungary-have-come-into-force',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/739-az-orszag-valamennyi-teruleten-'
                'vizsgaljuk-a-szennyvizet',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/713-hazautaztak-megfigyelesre-a-ket-'
                'koronavirusos-taborozoval-erintkezok',
                'https://www.nnk.gov.hu/index.php/component/content/article/11-foosztalyok/782-33-het-stagnal-a-'
                'szennyvizben-a-koronavirus-orokitoanyaga?Itemid=1050',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/743-jelentos-emelkedes-a-megbetegedesek-'
                'szamaban-a-kovetkezo-1-2-hetben-tovabbra-sem-varhato',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/745-jarvanyugyi-szakertelem-szukseges-a-'
                'jarvanyugyi-adatok-megfelelo-ertekelesehez',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/742-orszagok-besorolasa',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/764-die-restriktiven-ma-nahmen-fur-den-'
                'zugang-zu-ungarn-sind-in-kraft-getreten',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/748-tovabbra-is-alacsony-a-szennyvizekben-'
                'mert-virus-koncentracioja',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/765-tajekoztatas-a-jarvanyugyi-keszultsegi-'
                'idoszak-alatt-betartando-altalanos-jarvanyugyi-megelozo-szabalyokrol',
                'https://www.nnk.gov.hu/index.php/component/content/article/175-a-nemzeti-nepegeszsegugyi-kozpont-'
                'kozlemenyei/736-kozlemeny-a-covid-19-betegseggel-valo-aktualis-fertozottsegi-viszonyok-alapjan-az-'
                'orszagok-besorolasarol-szolo-orszagos-tisztifoorvosi-hatarozatrol?Itemid=1050',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/780-tajekoztatas-a-koronavirus-'
                'vizsgalatokkal-kapcsolatos-leletek-email-cimre-torteno-megkuldesehez',
                'https://www.nnk.gov.hu/index.php/koronavirus-tajekoztato/769-30-heti-eredmenyek-a-szennyvizmintakbol-'
                'kimutathato-sars-cov-2-virussal-kapcsolatban',
                'https://www.nnk.gov.hu/index.php/component/content/article/11-foosztalyok/784-34-het-tovabbra-is-'
                'stagnal-a-szennyvizben-a-koronavirus-orokitoanyaga?Itemid=1050'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    text = w.download_url('https://semmelweis.hu/hirek/tag/koronavirus/page/8/')
    extracted = extract_article_urls_from_page_gov_koronavirus(text)
    expected = set()
    assert (extracted, len(extracted)) == (expected, 0)

    test_logger.log('INFO', 'Testing Telex')
    text = w.download_url('https://telex.hu/rovat/koronavirus?oldal=4')
    extracted = extract_article_urls_from_page_telex(text)
    expected = {'https://telex.hu/koronavirus/2021/01/21/szputnyik-v-nemetorszag-orosz-vakcina-tamogatas',
                'https://telex.hu/koronavirus/2021/01/22/nyerceknek-fejleszt-koronavirus-elleni-oltast-tobb-'
                'amerikai-ceg-is',
                'https://telex.hu/koronavirus/2021/01/22/vendeglatok-ettermek-koronavirus-zarva-tart-nagykanizsa',
                'https://telex.hu/koronavirus/2021/01/23/az-usa-vezeti-a-legfertozottebb-orszagok-listajat-majdnem-25-'
                'millio-fertozottel',
                'https://telex.hu/koronavirus/2021/01/23/megfertozodott-a-sri-lanka-i-egeszsegugyi-miniszter-miutan-'
                'nyilvanosan-kiallt-koronavirustol-vedo-varazsital-mellett',
                'https://telex.hu/koronavirus/2021/01/21/specialis-oltoing-oltas-romania-miniszter',
                'https://telex.hu/koronavirus/2021/01/21/operativ-torzs-tajekoztato-01-21',
                'https://telex.hu/koronavirus/2021/01/22/vizsgalat-nelkul-engedelyezte-az-astra-zeneca-vakcinat-az-'
                'ogyei',
                'https://telex.hu/koronavirus/2021/01/22/tomeges-oltas-helyett-egymast-szurkaljak-az-europai-vezetok',
                'https://telex.hu/koronavirus/2021/01/23/tomegkozlekedes-francia-orvos',
                'https://telex.hu/koronavirus/2021/01/23/rendorseg-romania-karanten',
                'https://telex.hu/koronavirus/2021/01/22/boris-johnson-nagy-britannia-koronavirus-varians',
                'https://telex.hu/koronavirus/2021/01/22/koronavirus-vakcina-mellekhatasok-kapcsolat-pfizer-moderna',
                'https://telex.hu/koronavirus/2021/01/23/friss-hazai-koronavirus-adatok-stagnalo-szamok',
                'https://telex.hu/koronavirus/2021/01/21/vakcina-oltas-koronavirus-autoimmun-reakcio-hosszu-tavu-'
                'mellekhatas-falus-andras',
                'https://telex.hu/koronavirus/2021/01/22/joe-biden-koronavirus-intezkedes',
                'https://telex.hu/koronavirus/2021/01/21/koronavirus-fertozes-nemetorszag',
                'https://telex.hu/koronavirus/2021/01/23/boston-oltas-zsinor-fagyaszto',
                'https://telex.hu/koronavirus/2021/01/21/adatok-koronavirus-magyarorszag-fertozottek-korhaz-2',
                'https://telex.hu/koronavirus/2021/01/22/uffizi-keptar-firenze-szabalyok-ujranyitas',
                'https://telex.hu/koronavirus/2021/01/21/albania-orosz-diplomata-kiutasitas-jarvany-szabalyok-'
                'megsertes',
                'https://telex.hu/koronavirus/2021/01/21/szputnyik-v-gyartas-szallitas-magyarorszag',
                'https://telex.hu/koronavirus/2021/01/22/gyartasi-gondok-miatt-kevesebb-vakcinat-fog-az-eu-ba-'
                'szallitani-az-astrazeneca',
                'https://telex.hu/koronavirus/2021/01/22/anthony-fauci-donald-trump-koronavirus',
                'https://telex.hu/koronavirus/2021/01/22/operativ-torzs-muller-cecilia-1',
                'https://telex.hu/koronavirus/2021/01/23/svedorszagban-csak-textilmaszknal-komolyabbakat-javasolnak',
                'https://telex.hu/koronavirus/2021/01/21/oltasprogramrol-es-vakcinaigazolasrol-is-kerdezzuk-a-'
                'kormanyt/elo',
                'https://telex.hu/koronavirus/2021/01/23/elmarad-az-orosz-vakcina-magyar-klinikai-vizsgalata',
                'https://telex.hu/koronavirus/2021/01/22/rioi-karneval-elmarad',
                'https://telex.hu/koronavirus/2021/01/22/adatok-koronavirus-fertozottek-korhaz-magyarorszag'
                }
    assert (extracted, len(extracted)) == (expected, 30)

    text = w.download_url('https://telex.hu/rovat/koronavirus?oldal=39')
    extracted = extract_article_urls_from_page_telex(text)
    expected = {'https://telex.hu/koronavirus/2020/09/26/ne-higgyen-az-alhireknek-nem-mertek-felre-94-szazalekkal-a-'
                'koronavirus-aldozatainak-szamat',
                'https://telex.hu/koronavirus/2020/09/30/angela-merkel-koronavirus-jarvany-vakcina-szazmillio-dollar-'
                'tamogatas',
                'https://telex.hu/koronavirus/2020/10/01/magyarorszag-koronavirus-fertozes-napi-adatok',
                'https://telex.hu/koronavirus/2020/09/28/magyarorszagot-telibe-kapta-a-masodik-hullam-es-meg-csak-most-'
                'jon-a-java',
                'https://telex.hu/koronavirus/2020/09/29/jon-a-szuksegallapot-csehorszagban',
                'https://telex.hu/koronavirus/2020/10/01/koronavirus-terapia-dpc-gyulladas-citokinvihar-valyi-nagy-'
                'istvan',
                'https://telex.hu/koronavirus/2020/09/26/mar-32-5-millioan-kaptak-el-vilagszerte-a-koronavirust',
                'https://telex.hu/koronavirus/2020/09/29/miert-erinthetetlenek-a-jarvanytagado-orvos-celebek',
                'https://telex.hu/koronavirus/2020/09/25/927-uj-koronavirus-fertozott-fertozott-9-en-meghaltak',
                'https://telex.hu/koronavirus/2020/09/26/kohog-lazas-volt-hat-napja-var-a-teszteredmenyere',
                'https://telex.hu/koronavirus/2020/09/29/petro-porosenko-is-koronavirusos',
                'https://telex.hu/koronavirus/2020/09/26/orban-viktor-van-eleg-korhazi-agy-eszkoz-es-szemelyzet-a-'
                'vedekezeshez',
                'https://telex.hu/koronavirus/2020/09/26/egy-maszkellenes-es-egy-turizmusvedo-tuntetest-is-hozott-a-'
                'virus',
                'https://telex.hu/koronavirus/2020/09/27/cikk-cime-3',
                'https://telex.hu/koronavirus/2020/10/01/koronavirus-jarvany-csehorszag-izrael-oroszorszag',
                'https://telex.hu/koronavirus/2020/09/29/koronavirus-magyarorszag-fertozes-influenzaoltas-kiskunhalasi-'
                'korhaz',
                'https://telex.hu/koronavirus/2020/09/26/50-ezer-forintra-buntethetik-aki-budapesten-megserti-a-'
                'maszkviselesi-szabalyokat',
                'https://telex.hu/koronavirus/2020/09/26/keresre-ingyenmaszkot-ad-a-vasarloknak-a-spar',
                'https://telex.hu/koronavirus/2020/09/29/becs-koronavirus-teszt',
                'https://telex.hu/koronavirus/2020/09/26/12-en-haltak-meg-589-koronavirusos-beteg-van-korhazban',
                'https://telex.hu/koronavirus/2020/09/26/927-ujabb-koronavirusos-beteget-azonositottak',
                'https://telex.hu/koronavirus/2020/09/26/othavi-csucsra-emelkedett-az-uj-esetek-szama-nemetorszagban',
                'https://telex.hu/koronavirus/2020/10/01/koronavirus-magyarorszag-jakab-ferenc-virologus',
                'https://telex.hu/koronavirus/2020/09/26/miert-erdemes-influenzaoltast-kerni-koronavirusjarvany-idejen',
                'https://telex.hu/koronavirus/2020/10/01/emmi-van-futes-a-kiskunhalasi-mobilkorhazban-es-orvosokat-is-'
                'vezenyelnek-oda',
                'https://telex.hu/koronavirus/2020/09/29/kulfold-koronavirus-fertozes-gorogorszag-kirandulohajo',
                'https://telex.hu/koronavirus/2020/09/27/937-uj-koronavirus-fertozott-hatan-meghaltak',
                'https://telex.hu/koronavirus/2020/09/28/csaknem-33-millioan-fertozodtek-meg-koronavirussal-'
                'vilagszerte',
                'https://telex.hu/koronavirus/2020/09/29/ecdc-magyarorszag-koronavirus-jarvany-dania-izland-hollandia'
                }
    assert (extracted, len(extracted)) == (expected, 29)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################


def next_page_of_article_telex(curr_html):  # https://telex.hu/koronavirus/2020/11/12/koronavirus-pp-2020-11-12/elo
    bs = BeautifulSoup(curr_html, 'lxml')
    if bs.find('div', class_='pagination') is not None:
        current_pagenum = int(bs.find('a', class_='current-page').attrs['href'][-1])
        for pagelink in bs.find_all('a', class_='page'):
            if pagelink.attrs['class'] != ['page', 'current-page']:
                href = pagelink.attrs['href']
                if href[-1].isdigit() and int(href[-1]) == current_pagenum + 1:
                    next_page = f'https://telex.hu{href}'
                    return next_page
    return None


def next_page_of_article_444(curr_html):
    bs = BeautifulSoup(curr_html, 'lxml')
    next_page_cont1 = bs.find('li', class_='arrow')
    next_page_link2 = bs.find('a', {'class': 'page-link', 'aria-label': 'Következő »'})
    if next_page_cont1 is not None:
        next_page_link = next_page_cont1.find('a', href=True)
        if next_page_link is not None and next_page_link.text.startswith('Következő'):
            return next_page_link.attrs['href']
        return None
    elif next_page_link2 is not None:
        return next_page_link2.attrs['href']
    return None


def next_page_of_article_valasz(curr_html):
    bs = BeautifulSoup(curr_html, 'lxml')
    if bs.find('article', class_='percro-percre-lista') is not None:
        next_tag = bs.find('a', rel='next')
        if next_tag is not None and 'href' in next_tag.attrs.keys():
            next_link = next_tag.attrs['href']
            link = f'http://valasz.hu{next_link}'
            return link
    return None


def next_page_of_article_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing Telex')
    text = w.download_url('https://telex.hu/koronavirus/2021/01/21/oltasprogramrol-es-vakcinaigazolasrol-is-kerdezzuk-'
                          'a-kormanyt/elo')
    assert next_page_of_article_telex(text) == 'https://telex.hu/koronavirus/2021/01/21/oltasprogramrol-es-' \
                                               'vakcinaigazolasrol-is-kerdezzuk-a-kormanyt/elo?oldal=2'
    text = w.download_url('https://telex.hu/koronavirus/2021/01/21/oltasprogramrol-es-vakcinaigazolasrol-is-kerdezzuk-'
                          'a-kormanyt/elo?oldal=2')
    assert next_page_of_article_telex(text) is None

    text = w.download_url('https://444.hu/2014/03/02/mindjart-kezdodik-az-oscar-dij-atadas')
    assert next_page_of_article_444(text) == 'https://444.hu/2014/03/02/mindjart-kezdodik-az-oscar-dij-atadas?page=2'
    text = w.download_url('https://444.hu/2014/03/02/mindjart-kezdodik-az-oscar-dij-atadas?page=4')
    assert next_page_of_article_444(text) is None
    text = w.download_url('https://444.hu/2014/03/23/real-madrid-barcelona-elo')
    assert next_page_of_article_444(text) == 'https://444.hu/2014/03/23/real-madrid-barcelona-elo?page=2'
    text = w.download_url('https://444.hu/2014/03/23/real-madrid-barcelona-elo?page=7')
    assert next_page_of_article_444(text) is None

    text = w.download_url('http://valasz.hu/itthon/percrol-percre-az-onkormanyzati-valasztasokrol-105350?page=3')
    assert next_page_of_article_valasz(text) == 'http://valasz.hu/itthon/percrol-percre-az-onkormanyzati' \
                                                '-valasztasokrol-105350?page=4'
    text = w.download_url('http://valasz.hu/vilag/kelet-ukrajna-percrol-percre-103699?page=3')
    assert next_page_of_article_valasz(text) is None
    text = w.download_url('http://valasz.hu/itthon/humboldt-dijas-kvantumfizikus-alapkutatas-nelkul'
                          '-nincs-fejlodes-129197')
    assert next_page_of_article_valasz(text) is None

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

if __name__ == '__main__':
    from webarticlecurator import WarcCachingDownloader, Logger

    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)), '../../tests/extract_article_urls_from_page.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    next_page_of_article_test(choices['article_nextpage'], main_logger)
