#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

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
    # .a azért kell, mert az utolsó oldalon nincs link csak div (pl. nol.hu/archivum?page=14670 )
    if next_page.a is not None:
        ret = 'http://nol.hu{0}'.format(next_page.a['href'])
    return ret


if __name__ == '__main__':
    """Gyors teszt"""
    import requests

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
