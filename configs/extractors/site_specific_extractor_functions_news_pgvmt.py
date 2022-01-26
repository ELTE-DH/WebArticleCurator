#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import json
from itertools import chain
from os.path import abspath, dirname, join as os_path_join

from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader, Logger


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################
def extract_next_page_url_p888(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for 888.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('div', class_='navigation').find('div', class_='alignright')
    if next_page is not None:
        next_page_link = next_page.find('a')
        if next_page_link is not None and 'href' in next_page_link.attrs:
            ret = next_page_link.attrs['href']
    return ret


def extract_next_page_url_feol(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for feol.hu
        From the second page, only the end of the url is in the html, not the full url.
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('div', class_='enews-pagination-right')
    if next_page is not None:
        for next_page_url in next_page.find_all('a', recursive=False):
            if next_page_url.find('div', class_='enews-bottom-pagination-box enews-bottom-pagination-right') \
                    is not None and 'href' in next_page_url.attrs:
                url_end = next_page_url.attrs['href']
                if url_end.startswith('https'):
                    ret = url_end
                    break
                elif url_end.startswith('/'):  # From the second page the url does not contain the resource name.
                    ret = f'https://www.feol.hu{url_end}'
                    break
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing p888')
    text = w.download_url('https://888.hu/piszkostizenketto/page/75/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/piszkostizenketto/page/76/'
    text = w.download_url('https://888.hu/ketharmad/page/58/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/ketharmad/page/59/'
    text = w.download_url('https://888.hu/amerika-london-parizs/page/1/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/amerika-london-parizs/page/2/'
    text = w.download_url('https://888.hu/big-pikcsor/page/3/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/big-pikcsor/page/4/'
    text = w.download_url('https://888.hu/hajra-magyarok/page/13/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/hajra-magyarok/page/14/'
    text = w.download_url('https://888.hu/csak-neked-csak-most/page/7/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/csak-neked-csak-most/page/8/'
    text = w.download_url('https://888.hu/feher-ferfi/page/2/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/feher-ferfi/page/3/'
    text = w.download_url('https://888.hu/pszicho/page/6/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/pszicho/page/7/'
    text = w.download_url('https://888.hu/egy-soros-egy-forditott/page/1/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/egy-soros-egy-forditott/page/2/'
    text = w.download_url('https://888.hu/kinyilott-a-pitypang/page/9/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/kinyilott-a-pitypang/page/10/'
    text = w.download_url('https://888.hu/censored/page/12/')
    assert extract_next_page_url_p888(text) is None
    text = w.download_url('https://888.hu/sivalkodjatok/page/5/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/sivalkodjatok/page/6/'
    text = w.download_url('https://888.hu/759/page/17/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/759/page/18/'
    text = w.download_url('https://888.hu/889/page/22/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/889/page/23/'
    text = w.download_url('https://888.hu/888/page/42/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/888/page/43/'
    text = w.download_url('https://888.hu/century-on/page/4/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/century-on/page/5/'
    text = w.download_url('https://888.hu/szabad-vasarnap/page/17/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/szabad-vasarnap/page/18/'
    text = w.download_url('https://888.hu/bulvar/page/159/')
    assert extract_next_page_url_p888(text) is None
    text = w.download_url('https://888.hu/okojobb/page/11/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/okojobb/page/12/'
    text = w.download_url('https://888.hu/maccabi/page/2/')
    assert extract_next_page_url_p888(text) == 'https://888.hu/maccabi/page/3/'

    test_logger.log('INFO', 'Testing feol')
    text = w.download_url('https://www.feol.hu/sport/page/4523/')
    assert extract_next_page_url_feol(text) == 'https://www.feol.hu/sport/page/4524/'
    text = w.download_url('https://www.feol.hu/kek-hirek/page/75/')
    assert extract_next_page_url_feol(text) == 'https://www.feol.hu/kek-hirek/page/76/'
    text = w.download_url('https://www.feol.hu/orszag-vilag/page/169/')
    assert extract_next_page_url_feol(text) == 'https://www.feol.hu/orszag-vilag/page/170/'
    text = w.download_url('https://www.feol.hu/kultura/')
    assert extract_next_page_url_feol(text) == 'https://www.feol.hu/kultura/page/2'
    text = w.download_url('https://www.feol.hu/gazdasag/page/369/')
    assert extract_next_page_url_feol(text) == 'https://www.feol.hu/gazdasag/page/370/'
    text = w.download_url('https://www.feol.hu/kozelet/page/7268/')
    assert extract_next_page_url_feol(text) is None

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


def extract_article_urls_from_page_p888(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = chain(soup.find_all('div', class_='fig-wrap'), soup.find_all('div', class_='text-frame'),
                           soup.find_all('div', class_='bg-stretch'))  # Articles are found in 3 types of elements.
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_hirado(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    archive_json = json.loads(archive_page_raw_html)
    for item in archive_json:
        url = item['link'].replace('http://', 'https://')
        if not url.startswith('https:'):  # In some cases, the protocol is missing from the start of the url.
            url = f'https:{url}'
        urls.add(url)
    return urls


def extract_article_urls_from_page_feol(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='et_pb_column enews-tax-article')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing p888')
    text = w.download_url('https://888.hu/ketharmad/page/21/')
    extracted = extract_article_urls_from_page_p888(text)
    expected = {'https://888.hu/ketharmad/kidolgoztak-a-harmadik-oltas-beadasanak-eljarasrendjet-4326717/',
                'https://888.hu/ketharmad/kontroll-nelkul-kerulnek-szembe-a-fiatalok-a-szexualis-'
                'mediatartalmakkal-4326733/',
                'https://888.hu/ketharmad/a-kormany-bunteto-feljelentest-tesz-a-konzultacios-oldalt-ert-informatikai-'
                'tamadas-miatt-4326714/',
                'https://888.hu/ketharmad/szijjarto-peter-a-magyar-torok-sportugyi-egyuttmukodest-meltatta-'
                'isztambulban-4326660/',
                'https://888.hu/ketharmad/johetnek-magyarorszagra-az-orosz-turistak-4326572/',
                'https://888.hu/ketharmad/nincs-ujabb-aldozata-a-jarvanynak-161-uj-fertozottet-regisztraltak-'
                'magyarorszagon-4326570/',
                'https://888.hu/ketharmad/rodrigo-ballester-atirtak-az-unios-jatekszabalyokat-4326568/',
                'https://888.hu/ketharmad/4326471-4326471/',
                'https://888.hu/ketharmad/ide-veled-regi-kardunk-bravo-szilagyi-aron-4326406/',
                'https://888.hu/ketharmad/a-keresztenydemokrataknak-meg-kell-szervezniuk-magukat-europaban-4326390/',
                'https://888.hu/ketharmad/tobb-23-ezren-vesznek-reszt-a-nyari-diakmunka-programban-4326385/',
                'https://888.hu/ketharmad/mar-husz-orszag-utazhatnak-szabadon-a-magyarok-4326344/',
                'https://888.hu/ketharmad/minden-kepzesi-formaban-nott-a-felvetelizok-szama-4326333/',
                'https://888.hu/ketharmad/fejlesztesi-donteseket-hozott-a-gazdasag-ujrainditasaert-felelos-'
                'operativ-torzs-4326314/',
                'https://888.hu/ketharmad/orban-viktor-magyarorszag-ma-egy-nyitott-orszag-4326324/',
                'https://888.hu/ketharmad/fidesz-felhaborito-hogy-vadai-agnes-hulyenek-nezi-a-magyar-embereket-'
                '4326320/',
                'https://888.hu/ketharmad/jarvanyugyi-szempontbol-ma-magyarorszag-a-legbiztonsagosabb-orszag-'
                'europaban-4326280/',
                'https://888.hu/ketharmad/orban-viktor-oriasi-nyomas-ala-helyeztek-bennunket-4326237/',
                'https://888.hu/ketharmad/tovabbra-is-nagy-a-nepszerusege-az-otthonfelujitasi-tamogatasnak-4326227/',
                'https://888.hu/ketharmad/nincs-ujabb-aldozata-a-jarvanynak-85-tel-nott-a-fertozottek-szama-'
                'magyarorszagon-4326210/'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    text = w.download_url('https://888.hu/pszicho/page/2/')
    extracted = extract_article_urls_from_page_p888(text)
    expected = {'https://888.hu/pszicho/migransmesekonyvek-hateveseknek-4283097/',
                'https://888.hu/pszicho/nincs-itt-semmi-latnivalo-szex-es-eroszak-az-rtl-klub-on-4295622/',
                'https://888.hu/pszicho/marcius-15-nyerj-amennyit-csak-tudsz-4234889/',
                'https://888.hu/pszicho/tudtat-e-hogy-egy-atlag-gyerek-mar-altalanos-iskolas-koraban-lat-pornot-'
                '4286795/',
                'https://888.hu/pszicho/a-szelsobaloldali-amerikaiak-42-szazalekat-diagnosztizaltak-mar-valamilyen-'
                'mentalis-zavarral-4278867/',
                'https://888.hu/pszicho/elvezed-te-a-verest-kulonben-mar-reg-leleptel-volna-4285823/',
                'https://888.hu/pszicho/tibi-atya-a-kocsmarosok-robin-hoodja-nyitasra-buzdit-4295806/',
                'https://888.hu/pszicho/ez-meg-tiszta-holiday-a-neheze-meg-hatra-van-4242073/',
                'https://888.hu/pszicho/karacsony-koronavirus-idejen-4290870/',
                'https://888.hu/pszicho/ne-szexelj-mert-terhes-leszel-es-meghalsz-4300554/',
                'https://888.hu/pszicho/ez-nem-csak-meztelen-4303207/',
                'https://888.hu/pszicho/ma-van-a-koraszulottek-vilagnapja-4284205/',
                'https://888.hu/pszicho/csunyat-kommenteltel-kirugatlak-4291687/',
                'https://888.hu/pszicho/freud-es-a-koronavirus-4277075/',
                'https://888.hu/pszicho/a-no-az-no-4302687/',
                'https://888.hu/pszicho/eljott-a-kepernyoemberek-kora-4266851/',
                'https://888.hu/pszicho/otthon-kell-maradni-4235828/',
                'https://888.hu/pszicho/a-ferfiakat-lelovik-ugye-4297547/',
                'https://888.hu/pszicho/a-jobboldal-nem-a-kozepkor-4301153/',
                'https://888.hu/pszicho/meg-kell-tanitani-a-kisgyereket-maszturbalni-4247102/'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Testing hirado')
    text = w.download_url('https://hirado.hu/wp-content/plugins/hirado.hu.widgets/widgets/newSubCategory/'
                          'ajax_loadmore.php?cat_id=269&post_type=post&blog_id=0&page_number=10')
    extracted = extract_article_urls_from_page_hirado(text)
    expected = {'https://hirado.hu/kultura-eletmod/cikk/2021/09/26/vasary-tamas-es-gertler-teo-az-'
                'egeszsegugyert-koncertezik',
                'https://hirado.hu/kultura-eletmod/cikk/2021/09/26/semjen-soha-nem-allt-ilyen-kihivas-elott-a-vadaszat',
                'https://hirado.hu/kultura-eletmod/bulvar/cikk/2021/09/26/tarantino-huzta-ki-a-csavabol-'
                'rendezo-baratjat',
                'https://hirado.hu/kultura-eletmod/mozi/cikk/2021/09/26/ket-magyar-filmet-is-dijaztak-a-parmai-'
                'nemzetkozi-filmfesztivalon',
                'https://hirado.hu/kultura-eletmod/cikk/2021/09/26/10-tonna-agancsbol-szuletett-a-magyarok-toteme',
                'https://hirado.hu/kultura-eletmod/zene/cikk/2021/09/26/elhunyt-a-legendas-brit-rockzenesz',
                'https://hirado.hu/kultura-eletmod/bulvar/cikk/2021/09/26/szineszek-akiket-szivesen-latnanak-az-'
                'amerikaiak-leendo-elnokukkent',
                'https://hirado.hu/kultura-eletmod/cikk/2021/09/26/ma-kezdodik-a-budapesti-oszi-fesztival',
                'https://hirado.hu/kultura-eletmod/bulvar/cikk/2021/09/26/eldolt-a-downton-abbey-kedvenc-'
                'karakterenek-sorsa',
                'https://hirado.hu/kultura-eletmod/cikk/2021/09/26/strandforma-utan-nagyobb-izmokat-epitene-'
                'segitunk-hogyan-csinalja'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    text = w.download_url('https://hirado.hu/wp-content/plugins/hirado.hu.widgets/widgets/newSubCategory/'
                          'ajax_loadmore.php?cat_id=443&post_type=video&blog_id=4&page_number=3')
    extracted = extract_article_urls_from_page_hirado(text)
    expected = {'https://hirado.cms.mtv.hu/videok/almaszuret-sziberiaban',
                'https://hirado.cms.mtv.hu/videok/hatalmas-pusztitast-vegzett-az-ida-hurrikan',
                'https://hirado.cms.mtv.hu/videok/sarki-feny-latkepe-a-vilagurbol',
                'https://hirado.cms.mtv.hu/videok/veget-ert-a-las-fallas-fesztival',
                'https://hirado.cms.mtv.hu/videok/2001-szeptember-11-ei-terrortamadasok',
                'https://hirado.cms.mtv.hu/videok/keritest-epit-lengyelorszag-a-feherorosz-hataron',
                'https://hirado.cms.mtv.hu/videok/pandabebi-szuletett',
                'https://hirado.cms.mtv.hu/videok/78-velencei-nemzetkozi-filmfesztival',
                'https://hirado.cms.mtv.hu/videok/kiegett-egy-20-emeletes-toronyhaz-milanoban',
                'https://hirado.cms.mtv.hu/videok/lecsapott-az-ida-hurrikan'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    text = w.download_url('https://hirado.hu/wp-content/plugins/hirado.hu.widgets/widgets/newSubCategory/'
                          'ajax_loadmore.php?cat_id=235&post_type=gallery&blog_id=0&page_number=1')
    extracted = extract_article_urls_from_page_hirado(text)
    expected = {'https://hirado.hu/tudomany-high-tech/galeria/2019/04/18/csodalatos-asvanyok-matraszentimren',
                'https://hirado.hu/tudomany-high-tech/galeria/2020/10/14/bronzkori-tomegsirt-tartak-fel-'
                'tiszafured-hataraban',
                'https://hirado.hu/tudomany-high-tech/galeria/2020/08/24/korai-iszlam-regeszeti-lelet-izraelben',
                'https://hirado.hu/tudomany-high-tech/galeria/2020/05/07/uj-favizsgalo-berendezest-mutattak-be-gyorben',
                'https://hirado.hu/kultura-eletmod/galeria/2020/05/25/regeszeti-feltaras-solton',
                'https://hirado.hu/tudomany-high-tech/urkutatas/galeria/2019/08/13/perseidak',
                'https://hirado.hu/tudomany-high-tech/zold/galeria/2019/04/24/gus-wuppertali-allatkert-uj-jovevenye',
                'https://hirado.hu/belfold/galeria/2019/11/29/a-duna-partjan-szedtek-a-szemetet-a-pet-kupa-onkentesei',
                'https://hirado.hu/tudomany-high-tech/minden-mas/galeria/2019/05/22/arveresre-kerulnek-a-mult-kincsei',
                'https://hirado.hu/tudomany-high-tech/galeria/2019/08/29/megtalalhattak-ii-andras-kiraly-es-'
                'felesege-sirhelyenek-alapjat'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Testing feol')
    text = w.download_url('https://www.feol.hu/orszag-vilag/page/169/')
    extracted = extract_article_urls_from_page_feol(text)
    expected = {'https://www.feol.hu/orszag-vilag/felrobbantottak-egy-leanyiskolat-pakisztanban-5302736/',
                'https://www.feol.hu/orszag-vilag/babis-migracio-helyett-a-szuletesek-szamat-kell-novelni-5302694/',
                'https://www.feol.hu/orszag-vilag/letartoztattak-a-gyermekvedelmi-torvenyt-kritizalo-amerikai-ujsagirot'
                '-kotel-volt-a-nemi-szervehez-kotve-5302514/',
                'https://www.feol.hu/orszag-vilag/janez-jansa-a-demografia-orszagaink-jovojerol-szol-5302454/',
                'https://www.feol.hu/orszag-vilag/itt-az-uj-metoo-botrany-a-foszereplo-ismet-havas-henrik-5302445/',
                'https://www.feol.hu/orszag-vilag/tobb-mint-3700-fiatal-tehetseg-fejlodeset-segiti-az-mcc-az-uj-'
                'tanevben-5302439/',
                'https://www.feol.hu/orszag-vilag/a-kemfonok-szerint-hazugsag-hogy-ujabb-orosz-hirszerzot-gyanusitottak'
                '-meg-a-szkripal-ugyben-5302379/',
                'https://www.feol.hu/orszag-vilag/hamarosan-orban-viktor-is-felszolal-a-demografiai-csucson-elo'
                '-5302313/',
                'https://www.feol.hu/orszag-vilag/vucic-amikor-demografiarol-beszelunk-akkor-a-tulelesrol-beszelunk'
                '-5302175/',
                'https://www.feol.hu/orszag-vilag/novak-a-kormany-tizenkettedik-eve-a-csaladokert-dolgozik-5302121/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    text = w.download_url('https://www.feol.hu/kek-hirek/page/996/')
    extracted = extract_article_urls_from_page_feol(text)
    expected = {'https://www.feol.hu/rendorsegi/hetvenmillios-zsakmany-kabitoszerre-bukkantak-egy-garazsban-1114783/',
                'https://www.feol.hu/rendorsegi/videora-vettek-a-csoportos-nemi-eroszakot-1114779/',
                'https://www.feol.hu/rendorsegi/metanrobbanas-volt-egy-ukran-banyaban-1114776/',
                'https://www.feol.hu/rendorsegi/magyar-kerult-a-naci-haborus-bunosok-listajanak-elere-1114771/',
                'https://www.feol.hu/rendorsegi/kokain-a-szupermarketben-1114701/',
                'https://www.feol.hu/rendorsegi/elozetesben-a-soproni-kettos-gyilkossag-gyanusitottjai-1114685/',
                'https://www.feol.hu/rendorsegi/hamis-potencianovelok-indiabol-1114648/',
                'https://www.feol.hu/rendorsegi/munkagodorbe-esett-egy-rakodogep-budapesten-1114647/',
                'https://www.feol.hu/rendorsegi/ot-ev-bortonre-iteltek-egy-csalassal-vadolt-banki-alkalmazottat-'
                '1114642/',
                'https://www.feol.hu/rendorsegi/buszt-lopott-a-palyaudvarrol-1114792/'
                }
    assert (extracted, len(extracted)) == (expected, 10)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

def main_test():
    main_logger = Logger()

    # Relative path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_news_pgvmt.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)),
                                                '../../tests/next_page_of_article_news_prgvmt.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_news_pgvmt.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
