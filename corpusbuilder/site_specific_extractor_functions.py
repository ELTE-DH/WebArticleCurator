#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

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
    if next_page is not None:
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
    div = soup.find(class_='archiveDayRow2')
    a_tags = div.find_all('a')
    for a_tag in a_tags:
        if a_tag.text == 'Következő oldal' and 'href' in a_tag.attrs:
            ret = 'https:{0}'.format(a_tag['href'])
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
    if next_page is not None:
        ret = next_page['href']
    return ret


def extract_next_page_url_nol(archive_page_raw_html):
    """
        extracts and returns next page URL from an HTML code if there is one...
        Specific for nol.hu

        :returns string of url if there is one, None otherwise
    """
    ret = None
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    next_page = soup.find(class_='next')
    # .a is a must, because on the last page there is only the div and no a (pl. nol.hu/archivum?page=14670 )
    if next_page.a is not None:
        ret = 'http://nol.hu{0}'.format(next_page.a['href'])
    return ret


def extract_next_page_url_test():
    """Quick test"""
    import requests  # TODO: SAVE THE REQUIRED HTMLs to the tests folder OR BETTER: in WARC file!

    # Some of these are intentionally yields None
    r = requests.get('https://444.hu/2018/04/08')
    print(extract_next_page_url_444(r.text))
    r = requests.get('https://444.hu/2018/04/08?page=3')
    print(extract_next_page_url_444(r.text))
    r = requests.get('https://444.hu/2013/04/13')
    print(extract_next_page_url_444(r.text))

    r = requests.get('http://nol.hu/archivum?page=14669')
    print(extract_next_page_url_nol(r.text))
    r = requests.get('http://nol.hu/archivum?page=14670')
    print(extract_next_page_url_nol(r.text))

    r = requests.get('https://magyarnemzet.hu/archivum/page/99643')
    print(extract_next_page_url_mno(r.text))
    r = requests.get('https://magyarnemzet.hu/archivum/page/99644')
    print(extract_next_page_url_mno(r.text))

    r = requests.get('https://www.blikk.hu/archivum/online?date=2018-10-15')
    print(extract_next_page_url_blikk(r.text))
    r = requests.get('https://www.blikk.hu/archivum/online?date=2018-10-15&page=4')
    print(extract_next_page_url_blikk(r.text))

# END SITE SPECIFIC extract_next_page_url FUNCTIONS ####################################################################

# BEGIN SITE SPECIFIC extract_article_urls_from_page FUNCTIONS #########################################################


def extract_article_urls_from_page_nol(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='middleCol')
    for middle_cols in main_container:
        for a_tag in middle_cols.find_all('a'):
            if a_tag is not None\
              and 'class' in a_tag.attrs\
              and 'vezetoCimkeAfter' in a_tag['class']\
              and len(a_tag['class']) == 1\
              and 'href' in a_tag.attrs:
                urls.add(a_tag['href'])
    return urls


def extract_article_urls_from_page_origo(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(id='archive-articles')
    for middle_cols in main_container:
        for a_tag in middle_cols.find_all(class_='archive-cikk'):
            urls.add(a_tag.a['href'])
    return urls


def extract_article_urls_from_page_444(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='card')
    for a_tag in main_container:
        urls.add(a_tag.find('a')['href'])
    return urls


def extract_article_urls_from_page_blikk(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all(class_='archiveDayRow')
    for a_tag in main_container:
        urls.add(a_tag.find('a')['href'])
    return urls


def extract_article_urls_from_page_index(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('article')
    for a_tag in main_container:
        urls.add(a_tag.find('a')['href'])
    return urls


def extract_article_urls_from_page_mno(archive_page_raw_html):
    """
        extracts and returns as a list the URLs belonging to articles from an HTML code
    :param archive_page_raw_html: archive page containing list of articles with their URLs
    :return: list that contains URLs
    """
    urls = set()
    soup = BeautifulSoup(archive_page_raw_html, 'lxml')
    main_container = soup.find_all('h2')
    for a_tag in main_container:
        if a_tag.a is not None:
            urls.add(a_tag.a['href'])
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
            url = soup.a['href']
            urls.add('https://vs.hu{0}'.format(url))
    return urls


def extract_article_urls_from_page_test():
    def extract_article_urls_from_page_test_helper(inp_file, fun):
        with open(inp_file, encoding='UTF-8') as my_html:
            raw_html = my_html.read()
            urls = fun(raw_html)
            for i, url in enumerate(urls):
                print(url)
                i += 1
            print(i)

    from os.path import join, dirname
    test_dir = join(dirname(__file__), '../tests/archive_htmls')
    """Nol.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, 'nol_p37.html'),
                                               extract_article_urls_from_page_nol)

    """Origo.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, 'origo_p190119.html'),
                                               extract_article_urls_from_page_origo)

    """444.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, '444_190706.html'),
                                               extract_article_urls_from_page_444)

    """blikk.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, 'blikk_archiv.html'),
                                               extract_article_urls_from_page_blikk)

    """index.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, 'index.html'),
                                               extract_article_urls_from_page_index)

    """mno.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, 'mno_p99000.html'),
                                               extract_article_urls_from_page_mno)

    """vs.hu teszt"""
    extract_article_urls_from_page_test_helper(join(test_dir, 'vs.json'),
                                               extract_article_urls_from_page_vs)

# END SITE SPECIFIC extract_article_urls_from_page FUNCTIONS ###########################################################


if __name__ == '__main__':
    # extract_next_page_url_test()
    extract_article_urls_from_page_test()
