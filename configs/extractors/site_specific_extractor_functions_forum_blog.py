#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from os.path import abspath, dirname, join as os_path_join

from bs4 import BeautifulSoup

from webarticlecurator import WarcCachingDownloader, Logger


# BEGIN SITE SPECIFIC extract_next_page_url FUNCTIONS ##################################################################


def extract_next_page_url_forum_index(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for forum.index.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_list = soup.find('td', class_='navilinks')
    if next_page_list is not None:
        for page_a_tag in next_page_list.find_all('a'):
            if page_a_tag is not None \
                    and page_a_tag.find(attrs={'src': 'https://img.index.hu/forum/ikonz/pager_tovabb.gif'}):
                url_end = page_a_tag['href']
                ret = f'https://forum.index.hu/Topic/showTopicList{url_end}'
    return ret


def extract_next_page_url_test(filename, test_logger):
    """Quick test for extracting "next page" URLs when needed"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing Index forum')
    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=200&nt_step=100&t=32&tl_o=41')
    assert extract_next_page_url_forum_index(text) == 'https://forum.index.hu/Topic/showTopicList?nt_start=300&' \
                                                      'nt_step=100&t=32&tl_o=41'
    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=0&nt_step=100&t=9118048&tl_o=41')
    assert extract_next_page_url_forum_index(text) == 'https://forum.index.hu/Topic/showTopicList?nt_start=100&' \
                                                      'nt_step=100&t=9118048&tl_o=41'
    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=1900&nt_step=100&t=1&tl_o=41')
    assert extract_next_page_url_forum_index(text) == 'https://forum.index.hu/Topic/showTopicList?nt_start=2000&' \
                                                      'nt_step=100&t=1&tl_o=41'
    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=0&nt_step=100&t=21&tl_o=41')
    assert extract_next_page_url_forum_index(text) is None
    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=100&nt_step=100&t=9148227&tl_o=41')
    assert extract_next_page_url_forum_index(text) is None

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


def extract_article_urls_from_page_gyakorikerdesek(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('div', class_='kerdeslista_szoveg')
    urls = {f'https://www.gyakorikerdesek.hu{link}' for link in safe_extract_hrefs_from_a_tags(main_container)}
    return urls


def extract_article_urls_from_page_forum_index(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('td', class_='tle_subject')
    container = set()
    urls = set()
    # Replace is for changing the number of posts on a page.
    # Replacing does not work, if the url contains an id for the latest posts (la=), therefore these urls are truncated.
    # The list of topics always starts with "Cim"/"Title", which is unnecessary, its url starts with showTopicList.
    for url_end in safe_extract_hrefs_from_a_tags(main_container):
        if '&la=' in url_end:
            container.add(url_end.split('&la=', 1)[0].replace('showArticle?t', 'showArticle?na_start=0&na_step=500&t'))
        else:
            container.add(url_end.replace('showArticle?t', 'showArticle?na_start=0&na_step=500&t'))
        urls = {f'https://forum.index.hu{url_end}' for url_end in container if not url_end.startswith('showTopicList?')}
    return urls


def extract_article_urls_from_page_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})

    test_logger.log('INFO', 'Testing Index forum')
    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=0&nt_step=100&t=9119072&tl_o=41')
    extracted = extract_article_urls_from_page_forum_index(text)
    expected = {'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9156288',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9107177',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9020690',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9096196',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9111242',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9047275',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9024784',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9243992',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9122348',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9009529',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9119176',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9231645',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9011441',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9249011',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9237247',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9178313',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9240387',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9197804',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9143203',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9101056',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9148730',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9231584',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9166269',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=2000046',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9004925',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9237300',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=2000017',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9135417',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9009102',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9127030',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9242856',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9235085',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9123037',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9236727',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9005998',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9018669',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9002859',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9148288',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9005862',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9098273',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9239134',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9209517',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9105174',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9131443',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9091136',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9233622',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9008933',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9043720',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9084502',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9127195',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9013747',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9164771',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9022479',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9240821',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9209713',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9237676',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9133681',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9105397',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9022515',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=2000042',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9128345',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9135373',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9027663',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9000523',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9243094',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9162651',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9196978',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9009429',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9243674',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9191584',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9171769',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9001390',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9002173',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9248839',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9124836',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9146220',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9107778',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9107755',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9125719',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9232930',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9135932',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9209101',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9230835',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9119172',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9117933',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9236084',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9239978',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9241695',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9161760',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9157190',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9240818',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9163524',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9248882',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9206703',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9004057',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9248854',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9237368',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9221602',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9136194',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9105159'
                }
    assert (extracted, len(extracted)) == (expected, 100)

    text = w.download_url('https://forum.index.hu/Topic/showTopicList?nt_start=300&nt_step=100&t=61&tl_o=41')
    extracted = extract_article_urls_from_page_forum_index(text)
    expected = {'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9110874',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9112535',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9010172',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9116274',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9118475',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9109519',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9116849',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9105570',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9105536',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9104227',
                'https://forum.index.hu/Article/showArticle?na_start=0&na_step=500&t=9115442'
                }
    assert (extracted, len(extracted)) == (expected, 11)

    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################


# BEGIN SITE SPECIFIC next_page_of_article FUNCTIONS ###################################################################

def next_page_of_article_forum_index(archive_page_raw_html):
    """
        Extract next page url from current archive page
        Specific for forum.index.hu
        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page_of_art_list = soup.find('td', class_='navilinks')
    if next_page_of_art_list is not None:
        for page_a_tag in next_page_of_art_list.find_all('a'):
            if page_a_tag is not None \
                    and page_a_tag.find(attrs={'src': 'https://img.index.hu/forum/ikonz/pager_tovabb.gif'}):
                url_end = page_a_tag['href']
                ret = f'https://forum.index.hu/Article/{url_end}'
    return ret


def next_page_of_article_test(filename, test_logger):
    """Quick test for extracting URLs form an archive page"""
    # This function is intended to be used from this file only as the import of WarcCachingDownloader is local to main()
    w = WarcCachingDownloader(filename, None, test_logger, just_cache=True, download_params={'stay_offline': True})
    test_logger.log('INFO', 'Testing Index forum')
    text = w.download_url('https://forum.index.hu/Article/showArticle?na_start=500&na_step=500&t=9158096&na_order=')
    assert next_page_of_article_forum_index(text) == 'https://forum.index.hu/Article/showArticle?' \
                                                     'na_start=1000&na_step=500&t=9158096&na_order='
    text = w.download_url('https://forum.index.hu/Article/showArticle?na_start=50000&na_step=500&t=9073785&na_order=')
    assert next_page_of_article_forum_index(text) == 'https://forum.index.hu/Article/showArticle?na_start=50500&' \
                                                     'na_step=500&t=9073785&na_order='
    text = w.download_url('https://forum.index.hu/Article/showArticle?na_start=1500&na_step=500&t=9206571&na_order=')
    assert next_page_of_article_forum_index(text) is None
    test_logger.log('INFO', 'Test OK!')


# END SITE SPECIFIC next_page_of_article FUNCTIONS #####################################################################

def main_test():
    main_logger = Logger()

    # Relative path from this directory to the files in the project's test directory
    choices = {'nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_url_forum_blog.warc.gz'),
               'article_nextpage': os_path_join(dirname(abspath(__file__)), '../../tests/next_page_of_article_'
                                                                            'forum_blog.warc.gz'),
               'archive': os_path_join(dirname(abspath(__file__)),
                                       '../../tests/extract_article_urls_from_page_forum_blog.warc.gz')
               }

    # Use the main module to modify the warc files!
    extract_next_page_url_test(choices['nextpage'], main_logger)
    extract_article_urls_from_page_test(choices['archive'], main_logger)
    next_page_of_article_test(choices['article_nextpage'], main_logger)


if __name__ == '__main__':
    main_test()
