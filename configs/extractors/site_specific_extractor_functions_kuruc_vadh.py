#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join
from bs4 import BeautifulSoup


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_kuruc(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for kuruc.info
        :returns string of url if there is one, None otherwise
        there is no next page button, only the pagenumbers, therefore it search for the current pagenumber,
        go out from its level, and search for the next a-tag on the same level to get the end of the url
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_list = soup.find('div', class_='cikkbanner')
    if next_page_list is not None:
        current_page_a = next_page_list.find('a', class_='alcikklista lapozo')
        if current_page_a is not None:
            current_pagenum = current_page_a.text.strip()
            if current_pagenum.isdigit():
                next_pagenum = int(current_pagenum) + 1
            next_page = next_page_list.find('a', string=next_pagenum)
            if next_page is not None and 'href' in next_page.attrs:
                url_end = next_page.attrs['href']
                ret = f'https://kuruc.info{url_end}'
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing kuruc')
    text = w.download_url('https://kuruc.info/t/26/')
    assert extract_next_page_url_kuruc(text) == 'https://kuruc.info/to/26/20/'
    text = w.download_url('https://kuruc.info/t/1/')
    assert extract_next_page_url_kuruc(text) == 'https://kuruc.info/to/1/20/'
    text = w.download_url('https://kuruc.info/to/57/70/')
    assert extract_next_page_url_kuruc(text) == 'https://kuruc.info/to/57/80/'
    text = w.download_url('https://kuruc.info/to/66/60/')
    assert extract_next_page_url_kuruc(text) == 'https://kuruc.info/to/66/70/'
    text = w.download_url('https://kuruc.info/to/22/2899/')
    assert extract_next_page_url_kuruc(text) is None

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


def extract_article_urls_from_page_kuruc(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='alcikkheader')
    urls = {f'https://kuruc.info{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_vadhajtasok(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    container = soup.find('div', attrs={'id': 'primary'})
    if container is not None:
        main_container = container.find_all('h2', class_='cs-entry__title')
        urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing kuruc')
    text = w.download_url('https://kuruc.info/t/52/')
    extracted = extract_article_urls_from_page_kuruc(text)
    expected = {'https://kuruc.info/r/2/67543/',
                'https://kuruc.info/r/2/67568/',
                'https://kuruc.info/r/2/67587/',
                'https://kuruc.info/r/52/67698/',
                'https://kuruc.info/r/52/67701/',
                'https://kuruc.info/r/52/67703/',
                'https://kuruc.info/r/2/67732/',
                'https://kuruc.info/r/2/67898/',
                'https://kuruc.info/r/2/70870/',
                'https://kuruc.info/r/34/56719/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    text = w.download_url('https://kuruc.info/to/22/2899/')
    extracted = extract_article_urls_from_page_kuruc(text)
    expected = {'https://kuruc.info/r/22/1136/',
                'https://kuruc.info/r/22/1020/',
                'https://kuruc.info/r/22/848/',
                'https://kuruc.info/r/22/814/'
                }
    assert (extracted, len(extracted)) == (expected, 4)

    test_logger.log('INFO', 'Testing vadhajtasok')
    text = w.download_url('https://www.vadhajtasok.hu/kulfold/217')
    extracted = extract_article_urls_from_page_vadhajtasok(text)
    expected = {'https://www.vadhajtasok.hu/2019/10/30/torokorszag-legalabb-ketmillio-menekult-sziriaba-torteno-'
                'visszatelepiteset-tervezi',
                'https://www.vadhajtasok.hu/2019/10/30/megint-viktornak-neveztek-az-olah-orban-t',
                'https://www.vadhajtasok.hu/2019/10/30/jair-netanjahu-soros-szervezetei-belulrol-romboljak-izraelt',
                'https://www.vadhajtasok.hu/2019/10/29/torokorszagbol-elkezdtek-gorogorszagba-szivarogni-a-migransok',
                'https://www.vadhajtasok.hu/2019/10/27/minden-afrikai-edesanyja-lett-angela-merkel',
                'https://www.vadhajtasok.hu/2019/10/28/salviniek-nyertek-a-balos-umbriaban',
                'https://www.vadhajtasok.hu/2019/10/28/a-spanyolok-is-utcara-vonultak-kataloniaban',
                'https://www.vadhajtasok.hu/2019/10/28/nincs-megallas-ujabb-migranstaxi-kothet-ki-maltan',
                'https://www.vadhajtasok.hu/2019/10/28/ego-benzines-palackkal-tamadott-a-mecsetre-egy-84-eves',
                'https://www.vadhajtasok.hu/2019/10/28/soros-gyorgy-megkezdte-kampanyat-trump-ellen',
                'https://www.vadhajtasok.hu/2019/10/28/a-kicsi-greta-menekult-a-kerdesek-elol-mar-a-kanadaiak-is-'
                'unjak-ot',
                'https://www.vadhajtasok.hu/2019/10/29/bezzegromania-az-adohivatal-foldre-kenyszeritette-a-legierot',
                'https://www.vadhajtasok.hu/2019/10/29/a-biztonsagi-rampa-akadalyozta-meg-a-tragediat-az-arsenal-'
                'crystal-palace-merkozes-elott',
                'https://www.vadhajtasok.hu/2019/10/29/az-always-bejelentette-2020-tol-eltavolitja-a-menstruacios-'
                'termekeinek-csomagolasarol-a-noi-nem-jelkepet',
                'https://www.vadhajtasok.hu/2019/10/27/salviniek-megszerezhetik-voros-umbriat',
                'https://www.vadhajtasok.hu/2019/10/26/elet-salvini-utan-az-uj-belugyminiszter-hivatalaban-fogadta-a-'
                'soros-delegaciot',
                'https://www.vadhajtasok.hu/2019/10/27/tobb-szazezer-katalan-tuntetett-az-elitelt-fuggetlensegi-'
                'vezetok-szabadon-engedeseert-barcelonaban-%f0%9f%93%ba',
                'https://www.vadhajtasok.hu/2019/10/26/a-balosok-altal-tamogatott-fopolgarmester-lemondasat-'
                'koveteltek-a-tuntetok-romaban',
                'https://www.vadhajtasok.hu/2019/10/26/ujabb-kislanyokat-molesztalo-bandat-itelt-el-a-birosag-'
                'nagy-britanniaban',
                'https://www.vadhajtasok.hu/2019/10/26/elismerte-egy-olasz-liberalis-politikus-hogy-penzt-kaptak-'
                'sorostol',
                'https://www.vadhajtasok.hu/2019/10/25/kurdbarat-tuntetok-elfoglaltak-a-cdu-irodajat-egy-keletnemet-'
                'varosban',
                'https://www.vadhajtasok.hu/2019/10/26/erdogan-4-millio-migrans-utnak-eresztesevel-fenyegette-meg-az-'
                'europai-uniot',
                'https://www.vadhajtasok.hu/2019/10/25/sokkolo-agyonlotte-nyolc-tarsat-egy-sorkatona',
                'https://www.vadhajtasok.hu/2019/10/26/trump-ellenes-szovegei-miatt-hallgattak-ki-eminemet-'
                '%f0%9f%93%ba',
                'https://www.vadhajtasok.hu/2019/10/26/visszasirjak-majd-a-keresztenyseget-a-szabadkomuvesek-is-'
                'amikor-a-muszlimok-lesznek-tobbsegben'
                }
    assert (extracted, len(extracted)) == (expected, 25)

    text = w.download_url('https://www.vadhajtasok.hu/ebredj-europa/70')
    extracted = extract_article_urls_from_page_vadhajtasok(text)
    expected = {'https://www.vadhajtasok.hu/2019/10/11/dania-langolo-korannal-a-kezeben-mentettek-ki-a-partvezetot-a-'
                'no-go-zonabol-%f0%9f%8e%a5',
                'https://www.vadhajtasok.hu/2019/10/09/becsben-a-diakoknak-mar-tobb-mint-a-fele-nem-nemet-anyanyelvu',
                'https://www.vadhajtasok.hu/2019/10/08/ujabb-terrorcselekmeny-egy-sziriai-migrans-nemetorszagban-'
                'direkt-belehajtott-lopott-teherautojaval-tobb-autoba',
                'https://www.vadhajtasok.hu/2019/10/07/autok-tucatjait-gyujtottak-fel-a-muszlimok-tobb-sved-varosban',
                'https://www.vadhajtasok.hu/2019/10/07/kedden-luxemburgban-dontenek-arrol-hogy-kotelezo-vagy-'
                'valaszthato-lesz-e-a-menekultek-elosztasa',
                'https://www.vadhajtasok.hu/2019/10/06/az-eddiginel-is-nagyobb-menekulthullam-erheti-el-az-eu-t',
                'https://www.vadhajtasok.hu/2019/10/06/angol-birosag-az-emberi-meltosagot-serti-ha-valaki-azt-'
                'allitja-csak-ket-nem-letezik',
                'https://www.vadhajtasok.hu/2019/10/05/muszlim-diakok-terrorizaljak-a-zsido-gyerekeket-most-a-'
                'cipojuket-csokoltattak-meg',
                'https://www.vadhajtasok.hu/2019/10/04/szocdem-politikus-embercsempeszkedett-svedorszagban',
                'https://www.vadhajtasok.hu/2019/10/03/svedorszag-3-evet-kapott-a-11-eves-lanyt-megeroszakolo-migrans',
                'https://www.vadhajtasok.hu/2019/10/02/az-olasz-oktatasi-miniszter-leszedetne-az-iskolakbol-a'
                '-kereszteket',
                'https://www.vadhajtasok.hu/2019/09/30/varhelyi-oliver-valthatja-trocsanyi-laszlot',
                'https://www.vadhajtasok.hu/2019/09/30/sved-iskolak-az-okori-tortenelem-oktatasanak-felfuggesztesere'
                '-keszulnek',
                'https://www.vadhajtasok.hu/2019/09/28/egy-friss-felmeres-is-azt-mutatja-elkezdodott-a-'
                'lakossagcsere-italiaban',
                'https://www.vadhajtasok.hu/2019/09/27/tobb-penzt-kernek-a-nemet-onkormanyzatok-a-migransok-ellatasara',
                'https://www.vadhajtasok.hu/2019/09/26/ilyen-aktivistakbol-kellene-minel-tobb-nem-greta-bol-'
                'tobbe-nem-erezzuk-biztonsagban-magunkat',
                'https://www.vadhajtasok.hu/2019/09/25/ozonlenek-a-migransok-az-egei-tengeri-szigetekre',
                'https://www.vadhajtasok.hu/2019/09/25/ujabb-artatlan-menekultekrol-derult-ki-hogy-dzsihadista-'
                'harcosok',
                'https://www.vadhajtasok.hu/2019/09/24/migrans-olhette-meg-a-migranssimogato-aktivistat-'
                'franciaorszagban',
                'https://www.vadhajtasok.hu/2019/09/23/szavazati-jogot-adna-a-migransoknak-az-osztrak-baloldal',
                'https://www.vadhajtasok.hu/2019/09/22/iszlamista-partok-alakulnak-svedorszagban-az-oroszok-segitik-'
                'az-ellenallast'
                }
    assert (extracted, len(extracted)) == (expected, 21)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

if __name__ == '__main__':
    from webarticlecurator import WarcCachingDownloader, Logger

    main_logger = Logger()

    # Relateive path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_kuruc_vadh.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)),
                                                '../../tests/next_page_of_article_kuruc_vadh.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_kuruc_vadh.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)
