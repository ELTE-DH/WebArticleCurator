#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join
from bs4 import BeautifulSoup
from webarticlecurator import WarcCachingDownloader, Logger


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################

def extract_next_page_url_neokohn(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for neokohn.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find('a', class_='next page-numbers')
    if next_page is not None and 'href' in next_page.attrs:
        ret = next_page['href']
    return ret


def extract_next_page_url_szombat(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for szombat.org
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_url = soup.find('a', class_='nextpostslink')
    if next_page_url is not None and 'href' in next_page_url.attrs:
        ret = next_page_url['href']
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    # Some of these are intentionally yields None
    test_logger.log('INFO', 'Testing neokohn')
    text = w.download_url('https://neokohn.hu/2019/02/04/')
    assert extract_next_page_url_neokohn(text) == 'https://neokohn.hu/2019/02/04/page/2/'
    text = w.download_url('https://neokohn.hu/2022/01/20/')
    assert extract_next_page_url_neokohn(text) == 'https://neokohn.hu/2022/01/20/page/2/'
    text = w.download_url('https://neokohn.hu/2019/02/09/page/2/')
    assert extract_next_page_url_neokohn(text) is None
    text = w.download_url('https://neokohn.hu/2019/01/20/')
    assert extract_next_page_url_neokohn(text) is None

    test_logger.log('INFO', 'Testing szombat')
    text = w.download_url('https://szombat.org/archiv?q=&y=1990&mo=2')
    assert extract_next_page_url_szombat(text) == 'https://szombat.org/archiv/page/2?q&y=1990&mo=2'
    text = w.download_url('https://szombat.org/archiv/page/2?q&y=2020&mo=2')
    assert extract_next_page_url_szombat(text) == 'https://szombat.org/archiv/page/3?q&y=2020&mo=2'
    text = w.download_url('https://szombat.org/archiv/page/7?q&y=2022&mo=1')
    assert extract_next_page_url_szombat(text) == 'https://szombat.org/archiv/page/8?q&y=2022&mo=1'
    text = w.download_url('https://szombat.org/archiv/page/8?q&y=2022&mo=1')
    assert extract_next_page_url_szombat(text) is None

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_next_page_url FUNCTIONS ####################################################################


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


def extract_article_urls_from_page_greenfo(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    Not all links point to a real article (but the same news from other sites)
    hence the use of 'more-link' class instead of the 'h2' tag.
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='more-link')
    urls = {link['href'] for link in main_container}
    return urls


def extract_article_urls_from_page_neokohn(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h3', class_='entry-title mh-posts-list-title')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_szombat(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h1', class_='title')
    urls = {link for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing greenfo')
    text = w.download_url('https://greenfo.hu/page/1/?post_types=all&post_date=2001-01-26%202001-01-26')
    extracted = extract_article_urls_from_page_greenfo(text)
    expected = {'https://greenfo.hu/hir/tarifaemeles-helyett-esszeru-kozlekedesszervezest_980483759/#more-49915',
                'https://greenfo.hu/hir/a-hulladekgazdalkodasra-400-700-milliard-forint_980483643/#more-49909',
                'https://greenfo.hu/hir/a-4-es-metro-megepitese-sok-fa-elpusztitasaval-jarna_980463600/#more-49910',
                'https://greenfo.hu/hir/nemzeti-okologiai-kutatasi-program-indul_980463600/#more-49911',
                'https://greenfo.hu/hir/illes-zoltan-el-a-kezekkel-a-nemzeti-parkoktol_980463600/#more-49912',
                'https://greenfo.hu/hir/az-unios-tagsag-nem-oldja-meg-a-gondjainkat_980463600/#more-49913',
                'https://greenfo.hu/hir/lanyi-andras-iro-kornyezetvedo_980463600/#more-49914'
                }
    assert (extracted, len(extracted)) == (expected, 7)

    text = w.download_url('https://greenfo.hu/page/3/?post_types=all&post_date=2010-05-05%202010-05-05')
    extracted = extract_article_urls_from_page_greenfo(text)
    expected = {'https://greenfo.hu/hir/csikosfeju-nadiposzata-baranyaban_1273049570/#more-74036',
                }
    assert (extracted, len(extracted)) == (expected, 1)

    text = w.download_url('https://greenfo.hu/page/1/?post_types=all&post_date=2018-08-06%202018-08-06')
    extracted = extract_article_urls_from_page_greenfo(text)
    expected = {'https://greenfo.hu/hir/egymas-nyelvet-kepesek-megtanulni-a-madarak/#more-48578',
                'https://greenfo.hu/hir/a-magyar-mehallomany-fele-elpusztulhatott/#more-48577'
                }
    assert (extracted, len(extracted)) == (expected, 2)

    test_logger.log('INFO', 'Testing neokohn')
    text = w.download_url('https://neokohn.hu/2019/01/20/')
    extracted = extract_article_urls_from_page_neokohn(text)
    expected = {'https://neokohn.hu/2019/01/20/new-york-times-eilat-is-a-legjobb-uti-celok-kozott-szerepel/'
                }
    assert (extracted, len(extracted)) == (expected, 1)

    text = w.download_url('https://neokohn.hu/2021/09/21/')
    extracted = extract_article_urls_from_page_neokohn(text)
    expected = {'https://neokohn.hu/2021/09/21/biden-kudarcot-vallott-erotlen-vezetese-katasztrofak-sorozatat'
                '-okozta-es-artott-az-usa-nak/',
                'https://neokohn.hu/2021/09/21/donald-trump-szerint-hazaarulast-kovetett-el-mark-milley'
                '-vezerkari-fonok/',
                'https://neokohn.hu/2021/09/21/izgalmas-reszletek-derultek-ki-az-irani-atomprogram-atyjanak'
                '-kiiktatasarol/',
                'https://neokohn.hu/2021/09/21/hogyan-unnepeltek-a-szukkotot-2000-evvel-ezelott/',
                'https://neokohn.hu/2021/09/21/ensz-fotitkar-mindenaron-meg-kell-akadalyoznunk-az-usa'
                '-kina-hideghaborut/',
                'https://neokohn.hu/2021/09/21/parizs-hazugsag-ketszinuseg-a-bizalom-sulyos-megsertese'
                '-es-megvetese-tortent/'
                }
    assert (extracted, len(extracted)) == (expected, 6)

    text = w.download_url('https://neokohn.hu/2022/01/20/page/2/')
    extracted = extract_article_urls_from_page_neokohn(text)
    expected = {'https://neokohn.hu/2022/01/20/80-eve-dontottek-a-zsidokerdes-vegso-megoldasarol/'
                }
    assert (extracted, len(extracted)) == (expected, 1)

    test_logger.log('INFO', 'Testing szombat')
    text = w.download_url('https://szombat.org/archiv/page/5?q&y=2022&mo=1')
    extracted = extract_article_urls_from_page_szombat(text)
    expected = {'https://szombat.org/hirek-lapszemle/netanjahu-es-a-vadalku-lehetosege-mandelblit-nem-enged-a-het-ev-'
                'kozszolgalattol-valo-eltiltasbol',
                'https://szombat.org/hirek-lapszemle/borrell-szerint-lehetseges-a-megallapodas-az-irani-atomalkurol-'
                'parizs-ketelkedik',
                'https://szombat.org/hagyomany-tortenelem/a-birkanyiras-elseje-misna-magyarul-hulin-11',
                'https://szombat.org/kultura-muveszetek/uri-asaf-ujjaszuletesei',
                'https://szombat.org/politika/macron-unios-vitat-indit-az-istenkaromlasrol-es-dzsihadrol',
                'https://szombat.org/kultura-muveszetek/elhunyt-fenakel-judit',
                'https://szombat.org/tortenelem/lengyelorszag-tobb-mint-tizezer-onkentes-segitett-szaz-zsido-temeto-'
                'helyreallitasaban-2021-ben',
                'https://szombat.org/hirek-lapszemle/heisler-andras-egy-eros-mazsihisz-a-magyarorszagi-zsidosag-erdeke',
                'https://szombat.org/hirek-lapszemle/belgium-tiz-evre-kiutasitottak-a-legnagyobb-mecset-uszitassal-es-'
                'kemkedessel-vadolt-vezetojet',
                'https://szombat.org/hirek-lapszemle/izrael-tobb-mint-250-ezer-virushordozo-14-kneszet-kepviselo-'
                'karantenban',
                'https://szombat.org/hirek-lapszemle/izraeli-baleset-barati-tuz-vegzett-ket-kommandossal',
                'https://szombat.org/politika/zsidozasrol-es-antiszemitazasrol-magyarorszag-ideges-tele-a-valasztasok-'
                'elott',
                'https://szombat.org/kultura-muveszetek/77-eves-koraban-elhunyt-michael-lang',
                'https://szombat.org/kozosseg/tu-bisvat-i-szeder-az-orthodoxian',
                'https://szombat.org/hirek-lapszemle/izrael-sok-a-fertozott-de-tiz-naprol-hetre-csokkentik-a-karanten-'
                'idejet',
                'https://szombat.org/politika/europai-biralat-a-simon-wiesenthal-kozpont-antiszemitizmus-listajanak',
                'https://szombat.org/hirek-lapszemle/magyar-nemzeti-ongyuloletettel-vadolja-az-ellenzeket-szabo-gyorgy',
                'https://szombat.org/hirek-lapszemle/kibovitett-zsido-nepesseg-javaslat-izraeli-bevandorlok-'
                'statuszanak-rendezesere',
                'https://szombat.org/hirek-lapszemle/marki-zay-megprobaltak-engem-antiszemitanak-beallitani',
                'https://szombat.org/hirek-lapszemle/jair-lapid-izraeli-kulugyminiszter-koronavirusos'
                }
    assert (extracted, len(extracted)) == (expected, 20)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################

# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

def main_test():
    main_logger = Logger()

    # Relative path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_szng.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)),
                                                '../../tests/next_page_of_article_szng.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_szng.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    # next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
