#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join
from bs4 import BeautifulSoup


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_pestisracok(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for pestisracok.hu blogs.
        No specific tag or class for next button, code finds next url by looking for the string "Next ›".
        'Arcok' and "halozati-titkok" do not have a next button, so it finds the next sibling of current page
        in the pagination.
        :returns string of url if there is one, None otherwise
    """
    url = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_link = soup.find('a', text='Next ›')
    if next_page_link is not None and 'href' in next_page_link.attrs:
        url = next_page_link['href']
    elif next_page_link is None:
        curr_page = soup.find('span', class_='current')
        if curr_page.next_sibling is not None and 'href' in curr_page.next_sibling.attrs:
            url = curr_page.next_sibling['href']
    return url


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing pestisracok')
    text = w.download_url('https://pestisracok.hu/category/exkluziv/magyar-ugar/page/5/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/exkluziv/magyar-ugar/page/6/'
    text = w.download_url('https://pestisracok.hu/category/exkluziv/vilagugar/page/17/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/exkluziv/vilagugar/page/18/'
    text = w.download_url('https://pestisracok.hu/category/exkluziv/az-alvilag-titkai/page/10/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/exkluziv/az-alvilag-titkai/' \
                                                      'page/11/'
    text = w.download_url('https://pestisracok.hu/category/eco/page/12/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/eco/page/13/'
    text = w.download_url('https://pestisracok.hu/category/exkluziv/vezercikk/page/2/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/exkluziv/vezercikk/page/3/'
    text = w.download_url('https://pestisracok.hu/category/sport/page/34/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/sport/page/35/'
    text = w.download_url('https://pestisracok.hu/category/exkluziv/halozati-titkok/page/4/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/exkluziv/halozati-titkok/page/5/'
    text = w.download_url('https://pestisracok.hu/category/exkluziv/arcok/page/2/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/exkluziv/arcok/page/3/'
    text = w.download_url('https://pestisracok.hu/category/vesztegzar/page/5/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/vesztegzar/page/6/'
    text = w.download_url('https://pestisracok.hu/category/koronavirus/page/75/')
    assert extract_next_page_url_pestisracok(text) == 'https://pestisracok.hu/category/koronavirus/page/76/'
    text = w.download_url('https://pestisracok.hu/category/eco/page/34/')
    assert extract_next_page_url_pestisracok(text) is None

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


def extract_article_urls_from_page_pestisracok(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='widget-full-list-text left relative')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing pestisracok')
    text = w.download_url('https://pestisracok.hu/category/eco/page/19/')
    extracted = extract_article_urls_from_page_pestisracok(text)
    expected = {'https://pestisracok.hu/a-vakcinak-hatasara-tobb-evtizede-nem-tapasztalt-fellendules-kezdodhet-az-'
                'iden-a-vilaggazdasagban/',
                'https://pestisracok.hu/novemberben-45-ezerrel-nott-a-foglalkoztatottak-szama/',
                'https://pestisracok.hu/varga-mihaly-valaszolt-suranyinak-valaha-allitasait-tenyekre-alapozta-ezek-'
                'most-dk-es-momentum-szintu-ervek/',
                'https://pestisracok.hu/mar-kozel-37-milliard-forintot-nyertek-el-a-magyar-vallalkozasok-digitalis-'
                'fejlesztesekre/',
                'https://pestisracok.hu/magyarorszag-a-kovetkezo-evtized-gazdasagi-nyertese-lehet/',
                'https://pestisracok.hu/penzugyminiszterium-erdemes-kihasznalni-az-onkentes-penztari-befizetesek-'
                'adokedvezmenyet/',
                'https://pestisracok.hu/varga-mihaly-magyarorszag-az-elsok-kozott-teszi-elerhetove-az-uj-unios-'
                'fejlesztesi-idoszak-forrasait-video/',
                'https://pestisracok.hu/suppan-gergely-a-ps-nek-2021-masodik-feleben-eluralkodik-az-euforia-a-'
                'gazdasagban/',
                'https://pestisracok.hu/a-kormany-tizmilliard-forinttal-tamogatja-az-egyszer-hasznalatos-'
                'muanyagtermekek-csokkenteset-segito-cegeket/',
                'https://pestisracok.hu/junius-ota-no-az-epitoipari-termeles/',
                'https://pestisracok.hu/a-schneider-electric-12-millio-eurot-forditott-magyarorszagi-beruhazasokra-az-'
                'iden/',
                'https://pestisracok.hu/tobb-millios-birsagot-szabott-ki-az-mnb-jogosulatlan-portfoliokezelesert/',
                'https://pestisracok.hu/a-bankszovetseg-arra-keri-az-adosokat-hogy-merlegeljek-a-moratorium-vagy-a-'
                'torlesztes-folytatasanak-lehetoseget/',
                'https://pestisracok.hu/ujabb-milliardos-fejlesztessel-novelte-termelesi-kapacitasat-a-buttner-kft/',
                'https://pestisracok.hu/tallai-andras-magyarorszag-az-adocsokkentes-mintaallama/',
                'https://pestisracok.hu/szijjarto-megkezdi-a-tisztan-elektromos-meghajtasu-autok-gyartasat-a-mercedes-'
                'kecskemeten/',
                'https://pestisracok.hu/matolcsy-gyorgy-az-eu-tagallamai-kozul-a-legjobb-munkaeropiaci-teljesitmenyt-a-'
                'magyar-gazdasag-erte-el-2010-2019-kozott/',
                'https://pestisracok.hu/valsagallo-a-magyar-gazdasag-1200-milliard-forint-ado-elengedese-utan-is-180-'
                'milliardal-tobb-ado-folyt-be/',
                'https://pestisracok.hu/magyarorszag-elen-jar-az-elektromosauto-forradalomban/',
                'https://pestisracok.hu/ujabb-konnyiteseket-kapnak-a-lakasepitok/',
                'https://pestisracok.hu/a-kovetkezo-ket-evben-a-gazdasag-novekedese-meghaladhatja-a-4-szazalekot/',
                'https://pestisracok.hu/tallai-andras-az-adokedvezmenyek-altal-soha-nem-latott-osszeg-marad-a-'
                'csaladoknal/',
                'https://pestisracok.hu/rekordszamu-reszvenykibocsatassal-allnak-talpra-a-vilag-tozsdei/',
                'https://pestisracok.hu/alairtak-az-egt-es-norveg-alapokrol-szolo-egyuttmukodesi-megallapodasokat/',
                'https://pestisracok.hu/ot-eve-nem-volt-ennyi-devizatartaleka-magyarorszagnak/',
                'https://pestisracok.hu/magyar-fejlesztesu-app-segiti-a-tomeg-elkeruleset-a-bevasarlokozpontokban/',
                'https://pestisracok.hu/szijjarto-ujabb-gyaregyseggel-bovul-a-samvardhana-motherson-group-kecskemeten/',
                'https://pestisracok.hu/ket-bajor-vallalattal-allapodott-meg-szijjarto-peter/',
                'https://pestisracok.hu/az-epkar-tizenegy-milliard-forintnyi-kotvenyt-bocsat-ki/',
                'https://pestisracok.hu/vass-krisztian-mindannyiunk-kozos-felelossege-a-jovo-zold-civilizacioja/',
                'https://pestisracok.hu/matolcsy-gyorgy-az-nyeri-meg-a-kovetkezo-evtizedet-aki-levonja-a-megfelelo-'
                'tanulsagokat/',
                'https://pestisracok.hu/meg-egyszerubb-lesz-a-digitalis-ugyfel-azonositas/',
                'https://pestisracok.hu/londoni-elemzok-szerint-kina-sokkal-korabban-beelozheti-az-amerikai-'
                'gazdasagot/',
                'https://pestisracok.hu/ovatossagra-int-az-europai-biztositasfelugyelet-a-piaci-osztalekfizeteseknel/',
                'https://pestisracok.hu/megegyezes-a-kecskemeti-mercedesnel-beremeles-garantalt-munkahelyek/',
                'https://pestisracok.hu/elkepeszto-gazdasagi-fellendulest-hozhat-a-kovetkezo-ket-ev/',
                'https://pestisracok.hu/szijjarto-hazank-tamogatja-az-eu-torok-vamunio-megujitasat/',
                'https://pestisracok.hu/ujabb-tizmilliard-forinttal-tamogatja-a-kormany-a-gazdasag-zolditeset/',
                'https://pestisracok.hu/tallai-andras-a-kormany-akkor-is-folytatja-az-adocsokkentest-ha-a-baloldalnak-'
                'ez-kint-okoz/',
                'https://pestisracok.hu/itm-az-agazati-bertamogatasi-programban-eddig-tizenotmilliard-forintot-iteltek-'
                'meg-video/',
                'https://pestisracok.hu/varga-a-magyar-adossagkezeles-valtozatlanul-stabil/',
                'https://pestisracok.hu/hidvegi-krisztina-a-ps-nek-elerkezhet-a-klasszikus-media-reneszansza-ami-az-'
                'ertekteremtesrol-szol/',
                'https://pestisracok.hu/iden-is-milliardokat-koltenek-a-vasarlok-jatekokra-karacsonykor-egy-felmeres-'
                'szerint/',
                'https://pestisracok.hu/folyamat-csokken-az-allaskeresok-szama-a-kormanyzati-intezkedeseknek-'
                'koszonhetoen/',
                'https://pestisracok.hu/matolcsy-megvan-az-esely-az-elmult-szaz-ev-leggyorsabb-gazdasagi-'
                'helyreallasara/'
                }
    assert (extracted, len(extracted)) == (expected, 45)

    text = w.download_url('https://pestisracok.hu/category/exkluziv/halozati-titkok/page/7/')
    extracted = extract_article_urls_from_page_pestisracok(text)
    expected = {'https://pestisracok.hu/nem-volt-menekves-a-belugy-halojabol/',
                'https://pestisracok.hu/szexcsapda-es-allambiztonsag-diplomas-oromlanyokat-keresunk/',
                'https://pestisracok.hu/allambiztonsagi-iratokkal-cafoljuk-varkonyi-tibor-mesejet/',
                'https://pestisracok.hu/varkonyi-tibor-akit-francia-allam-es-az-allambiztonsag-kituntetett/',
                'https://pestisracok.hu/tgm-hata-iiiiii-hazugsagai-tragikomedia-parlamentben/',
                'https://pestisracok.hu/hankiss-agnes-sosem-hittem-a-szocialistak-megujulasaban-ps-mozi/',
                'https://pestisracok.hu/antiszemita-horthy-es-rakosi-babja-kethly-anna-lejaratasa/',
                'https://pestisracok.hu/igy-bomlasztottak-ok-allambiztonsagi-szalami-taktika/',
                'https://pestisracok.hu/nagy-imre-ujratemetese-az-elmaradt-forradalom-babmesterei/',
                'https://pestisracok.hu/sosem-ismerjuk-meg-az-igazi-bunosoket/',
                'https://pestisracok.hu/krasso-forro-es-havas-jo-rossz-es-csuf/',
                'https://pestisracok.hu/bevalt-terv-90-ben-bukunk-94-ben-visszajovunk/',
                'https://pestisracok.hu/reagantol-hornig-titkos-jelentesek-a-hideghaborurol/',
                'https://pestisracok.hu/rafinalt-gonoszsag-partallamban/',
                'https://pestisracok.hu/bevalt-az-allambiztonsag-ordogi-trukkje-megbujnak-az-igazi-bunosok-az-ugynokok-'
                'mogott/',
                'https://pestisracok.hu/nagy-daralas-allamvedelmi-szatira-modellvaltas-korabol/',
                'https://pestisracok.hu/jo-kadar-kormenetben-kell-oket-kivegezni/',
                'https://pestisracok.hu/de-miert-lesz-jobb-nekunk-lejaratas-es-bomlasztas-bemutatoja-video/',
                'https://pestisracok.hu/gyurcsany-es-a-nagy-roman-hadjarat-allambiztonsagi-jelentesek-1989-'
                'februarjabol/',
                'https://pestisracok.hu/allambiztonsagi-iratok-83-bol-cia-es-kgb-kuzdelme-ismetlodik-meg-ukrajnaban/',
                'https://pestisracok.hu/magatol-jelentkezett-ugynoknek-a-szechenyi-dijas-tortenesz/',
                'https://pestisracok.hu/bayern-allambiztonsag-2-0-golszerzok-burford-dalmady/',
                'https://pestisracok.hu/akiknek-balaton-riviera-az-eltunt-szazmilliardok-nyomaban/',
                'https://pestisracok.hu/szetszakadt-magyarorszag-bevalt-az-allambiztonsag-ek-muvelete/'
                }
    assert (extracted, len(extracted)) == (expected, 24)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

if __name__ == '__main__':
    from webarticlecurator import WarcCachingDownloader, Logger

    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_pestisracok.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)),
                                                '../../tests/next_page_of_article_pestisracok.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_pestisracok.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)
