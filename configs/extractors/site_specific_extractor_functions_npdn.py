#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join

from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader, Logger


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_demokrata(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for demokrata.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(class_='paginate arrow right p-0 d-flex col')
    if next_page is not None:
        next_page_a = next_page.find('a')
        if next_page_a is not None and 'href' in next_page_a.attrs:
            ret = next_page_a['href']
    return ret


def extract_next_page_url_nlc(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for nlc.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', attrs={'class': 'next page-numbers'})
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_portfolio(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for portfolio.hu
        :returns string of url if there is one, None otherwise
        To find the next page button it has to be identified by multiple attributes simultaneously.
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(attrs={'class': 'page-link', 'rel': 'next'})
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing demokrata')
    text = w.download_url('https://demokrata.hu/page/2/?s=&column=&pauthor=&start=2005.03.03&end=2005.03.03')
    assert extract_next_page_url_demokrata(text) == 'https://demokrata.hu/page/3/?s=&column=&pauthor=' \
                                                    '&start=2005.03.03&end=2005.03.03'
    text = w.download_url('https://demokrata.hu/?s=&column=&pauthor=&start=2020.03.13&end=2020.03.13')
    assert extract_next_page_url_demokrata(text) == 'https://demokrata.hu/page/2/?s=&column=&pauthor=' \
                                                    '&start=2020.03.13&end=2020.03.13'
    text = w.download_url('https://demokrata.hu/page/5/?s=&column=&pauthor=&start=2020.03.13&end=2020.03.13')
    assert extract_next_page_url_demokrata(text) is None
    text = w.download_url('https://demokrata.hu/?s=&column=&pauthor=&start=2005.06.16&end=2005.06.16')
    assert extract_next_page_url_demokrata(text) is None

    test_logger.log('INFO', 'Testing nlc.hu')
    text = w.download_url('https://nlc.hu/egeszseg/')
    assert extract_next_page_url_nlc(text) == 'https://nlc.hu/egeszseg/page/2/'
    text = w.download_url('https://nlc.hu/lelek/page/44/')
    assert extract_next_page_url_nlc(text) == 'https://nlc.hu/lelek/page/45/'
    text = w.download_url('https://nlc.hu/ezvan/page/1444/')
    assert extract_next_page_url_nlc(text) == 'https://nlc.hu/ezvan/page/1445/'
    text = w.download_url('https://nlc.hu/sztarok/page/2000/')
    assert extract_next_page_url_nlc(text) == 'https://nlc.hu/sztarok/page/2001/'
    text = w.download_url('https://nlc.hu/utazas/page/278/')
    assert extract_next_page_url_nlc(text) is None
    text = w.download_url('https://nlc.hu/otthon/page/462/')
    assert extract_next_page_url_nlc(text) is None

    test_logger.log('INFO', 'Testing portfolio')
    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=2022-01-27&dt=2022-01-27&c=')
    assert extract_next_page_url_portfolio(text) == 'https://www.portfolio.hu/kereses?q=&a=&df=2022-01-27&' \
                                                    'dt=2022-01-27&c=&page=2'
    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=2016-05-02&dt=2016-05-02')
    assert extract_next_page_url_portfolio(text) == 'https://www.portfolio.hu/kereses?q=&a=&df=2016-05-02&' \
                                                    'dt=2016-05-02&c=&page=2'
    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=2007-07-17&dt=2007-07-17&c=&page=3')
    assert extract_next_page_url_portfolio(text) is None
    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=2017-07-08&dt=2017-07-08&c=')
    assert extract_next_page_url_portfolio(text) is None
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


def extract_article_urls_from_page_demokrata(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h4', class_='mb-2')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_nlc(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2', class_='m-articleWidget__title -secondFont')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_portfolio(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    To avoid returning non-relevant article links the html document is restricted to the 'article-lists' block.
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    container = soup.find('section', class_='article-lists')
    main_container = container.find_all('h3')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing demokrata')
    text = w.download_url('https://demokrata.hu/page/3/?s=&column=&pauthor=&start=2005.04.13&end=2005.04.13')
    extracted = extract_article_urls_from_page_demokrata(text)
    expected = {'https://demokrata.hu/magyarorszag/a-magyar-szep-56920/',
                'https://demokrata.hu/magyarorszag/idegen-vezetok-56919/',
                'https://demokrata.hu/magyarorszag/ki-kell-birni-valahogy-56918/',
                'https://demokrata.hu/magyarorszag/meleg-helyzet-56917/',
                'https://demokrata.hu/velemeny/a-larmas-latszat-56916/',
                'https://demokrata.hu/velemeny/csak-hogy-tudjuk-hol-elunk-56915/'
                }
    assert (extracted, len(extracted)) == (expected, 6)

    text = w.download_url('https://demokrata.hu/?s=&column=&pauthor=&start=2018.04.14&end=2018.04.14')
    extracted = extract_article_urls_from_page_demokrata(text)
    expected = {'https://demokrata.hu/magyarorszag/ellenzekiek-tuntettek-103758/',
                'https://demokrata.hu/magyarorszag/hadhazy-eljatszotta-a-hattyu-halalat-103757/',
                'https://demokrata.hu/gazdasag/paks-es-a-naperomuvek-103733/',
                'https://demokrata.hu/gazdasag/kozep-europa-a-selyemuton-103730/',
                'https://demokrata.hu/magyarorszag/nem-lep-senki-szinpadra-a-jobbiktol-103756/',
                'https://demokrata.hu/kultura/ok-is-budapestet-valasztottak-103755/',
                'https://demokrata.hu/magyarorszag/hadhazy-akosra-rontott-parttarsa-103754/',
                'https://demokrata.hu/magyarorszag/9624-szazalek-szavazott-a-fidesz-kdnp-re-103753/',
                'https://demokrata.hu/gazdasag/hazank-kezdi-elfoglalni-az-ot-megilleto-helyet-103752/',
                'https://demokrata.hu/gazdasag/befektetesbarat-szemlelet-103751/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Testing nlc.hu')
    text = w.download_url('https://nlc.hu/foto/page/4/')
    extracted = extract_article_urls_from_page_nlc(text)
    expected = {'https://nlc.hu/foto/20180517/egy-nagy-latvanyos-igen-ezek-az-idei-ev-legjobb-eljegyzesi-fotoi/',
                'https://nlc.hu/foto/20180327/sony-world-photography-awards-fotopalyazat-radisics-milan/',
                'https://nlc.hu/foto/20171224/ezek-voltak-2017-legmeghatobb-kepriportjai-az-nlcafen/',
                'https://nlc.hu/foto/20171222/ezt-kertek-nagyszuleink-a-jezuskatol-retro-jatekok-a-30-as-40-es-'
                'evekbol/',
                'https://nlc.hu/foto/20180111/tozeglap-es-izlandi-latkep-egy-meghokkento-elmenynap-foton/',
                'https://nlc.hu/foto/20171227/tekezni-vitte-a-kiskundorozsmai-gyerekeket-a-szegedi-roma-tanoda/',
                'https://nlc.hu/foto/20180119/kiraly-gyogyfurdo-atepitese-felujitas-termalfurdo-buda/',
                'https://nlc.hu/foto/20180524/kisertethajok-a-dunan-a-pilismaroti-hajotemeto/',
                'https://nlc.hu/foto/20180226/kallo-peter-lebeges-fotosorozat/',
                'https://nlc.hu/foto/20171225/az-idei-ev-meghatarozo-esemenyei-kepekben/',
                'https://nlc.hu/foto/20180219/ime-az-ev-leglatvanyosabb-viz-alatti-fotoi/',
                'https://nlc.hu/foto/20180123/hasselblad-masters-2018-fotopalyazat-gyoztes-kepei/',
                'https://nlc.hu/foto/20180130/fekete-feher-bpoty-fotopalyazat-gyoztes-kepei-dijazottak-fotomuveszet/',
                'https://nlc.hu/foto/20180307/15-lenyugozo-felvetel-a-smithsonian-fotopalyazat-dontos-kepeibol/',
                'https://nlc.hu/foto/20180612/ime-a-smithsonian-magazin-idei-fotopalyazatanak-8-gyoztes-fotoja/',
                'https://nlc.hu/foto/20180312/ezek-az-idei-ev-legjobb-fekete-feher-gyerekfotoi/',
                'https://nlc.hu/foto/20180613/a-ferfiak-tekinteten-keresztul-kell-meghataroznunk-magunkat-albert-'
                'anna-fotos-kepekben-keresi-a-valaszt/',
                'https://nlc.hu/foto/20180212/teli-olimpia-2018-phjongcsang-latvanyos-kepek/',
                'https://nlc.hu/foto/20180305/20-ikonikus-cimlap-a-95-eves-time-magazinbol/',
                'https://nlc.hu/foto/20180126/a-negy-legszennyezettebb-varos-koze-kerult-szeged-a-szmogterkepen/',
                'https://nlc.hu/foto/20171229/ozdi-csibeszek-utolso-menedek-embereletnyi-szeretet-ezek-voltak-'
                'fotosaink-kedvenc-anyagai-2017-bol/',
                'https://nlc.hu/foto/20180106/a-leegett-ferto-tavi-colophazak-helye-ma-ilyen-gyaszosan-fest/',
                'https://nlc.hu/foto/20180102/muveszetterapiaval-a-depresszio-ellen-mentalis-betegek-festik-ki-'
                'magukbol-demonaikat/',
                'https://nlc.hu/foto/20180214/busojaras-foto/',
                'https://nlc.hu/foto/20180114/101-eves-fotoriporterno/'
                }
    assert (extracted, len(extracted)) == (expected, 25)

    text = w.download_url('https://nlc.hu/tv_sztarok/page/74/')
    extracted = extract_article_urls_from_page_nlc(text)
    expected = {'https://nlc.hu/tv_sztarok/20190308/shane-tusup-magyarorszag-interju-hosszu-katinka/',
                'https://nlc.hu/tv_sztarok/20190310/dancs-annamari-uj-par-kisfia/',
                'https://nlc.hu/tv_sztarok/20190308/vv-hunor-sebestyen-agi-randiznak/',
                'https://nlc.hu/tv_sztarok/20190310/curtis-visszateres-uj-dal/',
                'https://nlc.hu/tv_sztarok/20190308/szexi-koreografia-joban-rosszban-lanyok/',
                'https://nlc.hu/tv_sztarok/20190308/cicciolina-kossuth-lajos-kolto-baki-gyertek-at/',
                'https://nlc.hu/tv_sztarok/20190308/fucsovics-marton-edzo-szakitas-savolt-attila/',
                'https://nlc.hu/tv_sztarok/20190308/des-laszlo-benulas-interju-slager/',
                'https://nlc.hu/tv_sztarok/20190308/kelemen-anna-enb-lali-gyertek-at-flort/',
                'https://nlc.hu/tv_sztarok/20190308/megszuletett-szabo-gyozo-gyermeke/',
                'https://nlc.hu/tv_sztarok/20190311/szabo-zsofi-gyerekneveles-velemeny-instamami/',
                'https://nlc.hu/tv_sztarok/20190309/pataki-zita-utolso-lombik-eredmeny/',
                'https://nlc.hu/tv_sztarok/20190308/czippan-anett-szules-utani-hasa-elegedetlen-lapos-has/',
                'https://nlc.hu/tv_sztarok/20190308/epres-panni-30-kilo-plusz-terhesseg-benedek-tibor/',
                'https://nlc.hu/tv_sztarok/20190307/vasvari-vivien-luxus-vivi-rejtelyes-betegseg-verzes-vizsgalatok-'
                'harmadik-baba/',
                'https://nlc.hu/tv_sztarok/20190308/lakatos-levente-iro-instanovella-harom-esely/',
                'https://nlc.hu/tv_sztarok/20190308/kiraly-linda-huszka-zsombor-volegeny-szakitas-9-ev-egyedul-best/',
                'https://nlc.hu/tv_sztarok/20190309/szabo-gyozo-rezes-judit-gyereke-szuletes-majdnem-lekeste/',
                'https://nlc.hu/tv_sztarok/20190307/cicciolina-toplessmusorok-vetkozes-olaszorszag-rtl-klub-'
                'gyertek-at/',
                'https://nlc.hu/tv_sztarok/20190308/demjen-ferenc-facebook-oldala-meghekkeltek-aluzenetek-zaklatas/',
                'https://nlc.hu/tv_sztarok/20190308/koos-janos-halala-reszletek-ozvegye-dekany-sarolta-korhaz-'
                'rosszul-lett-szivproblema/',
                'https://nlc.hu/tv_sztarok/20190309/sas-jozsef-rosszullet-thaifold-feleseg-hazautazas-kulon/',
                'https://nlc.hu/tv_sztarok/20190308/sas-jozsef-thaifold-rosszul-lett-hazaerkezett-kulongep/',
                'https://nlc.hu/tv_sztarok/20190308/cooky-menyasszonya-szecsi-debora-ruha/',
                'https://nlc.hu/tv_sztarok/20190308/aurelio-baratnoje-mate-dominika-reka-penzt-vagy-eveket-stressz/'
                }
    assert (extracted, len(extracted)) == (expected, 25)

    test_logger.log('INFO', 'Testing portfolio')
    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=1999-02-09&dt=1999-02-09')
    extracted = extract_article_urls_from_page_portfolio(text)
    expected = {'https://www.portfolio.hu/uzlet/19990209/varakozasok-alatt-a-tvk-1'
                }
    assert (extracted, len(extracted)) == (expected, 1)

    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=2016-05-02&dt=2016-05-02&c=&page=4')
    extracted = extract_article_urls_from_page_portfolio(text)
    expected = {'https://www.portfolio.hu/allashirdetesek/20160502/az-mnb-felugyelo-auditor-munkatarsat-keres-230916',
                'https://www.portfolio.hu/allashirdetesek/20160502/az-mnb-felugyelo-likviditas-szakertot-keres-230922'
                }
    assert (extracted, len(extracted)) == (expected, 2)

    text = w.download_url('https://www.portfolio.hu/kereses?q=&a=&df=2000-12-22&dt=2000-12-22')
    extracted = extract_article_urls_from_page_portfolio(text)
    expected = {'https://www.portfolio.hu/uzlet/20001222/emelkedoben-8061',
                'https://www.portfolio.hu/uzlet/20001222/karacsonyi-hangulat-a-bet-en-is-8060',
                'https://www.portfolio.hu/uzlet/20001222/mikor-kereskedunk-jovore-8059',
                'https://www.portfolio.hu/gazdasag/20001222/usa-rendelesallomany-varakozasok-felett-8058',
                'https://www.portfolio.hu/deviza/20001222/divatban-az-euro-8057',
                'https://www.portfolio.hu/uzlet/20001222/pontositas-a-slovnaft-igazgatosagrol-8056',
                'https://www.portfolio.hu/deviza/20001222/aktiv-kereskedes-8055',
                'https://www.portfolio.hu/befektetes/20001222/flexibilitas-es-szabad-penzeszkozok-8054',
                'https://www.portfolio.hu/uzlet/20001222/botranyok-a-neuer-markton-szigorubb-szabalyozas-8053',
                'https://www.portfolio.hu/uzlet/20001222/sikertelen-vagyonhanyad-aukcio-8052',
                'https://www.portfolio.hu/uzlet/20001222/poziciozaras-8051',
                'https://www.portfolio.hu/uzlet/20001222/szervezeti-valtozasok-a-titasznal-8050',
                'https://www.portfolio.hu/uzlet/20001222/megallt-a-csokkenes-japanban-is-8049',
                'https://www.portfolio.hu/gazdasag/20001222/fontos-az-adoforintok-felhasznalasanak-'
                'transzparensse-tetele-8048',
                'https://www.portfolio.hu/uzlet/20001222/ford-egy-honapon-belul-a-masodik-figyelmeztetes-8047',
                'https://www.portfolio.hu/uzlet/20001222/47-m-ft-pplast-veszteseg-a-sajatreszvenyen-8046',
                'https://www.portfolio.hu/gazdasag/20001222/az-elozetesnel-01ponttal-alacsonyabb-a-gdp'
                '-novekedese-2-8045',
                'https://www.portfolio.hu/uzlet/20001222/a-vodafone-ausztraliaban-is-nyomul-8044',
                'https://www.portfolio.hu/uzlet/20001222/9-mrd-dollaros-kibocsatast-tervez-a-docomo-8043',
                'https://www.portfolio.hu/uzlet/20001222/folytatja-a-leepitest-a-tvk-8042'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Test OK!')

# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################

# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################


def main_test():
    main_logger = Logger()

    # Relative path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/'
                                                                    'next_page_url_npdn.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article_npdn'
                                                                            '.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_npdn.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
