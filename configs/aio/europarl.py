#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from datetime import date

from bs4 import BeautifulSoup
from mplogger import Logger, DummyLogger

from webarticlecurator import WarcCachingDownloader, gen_article_urls_and_subpages, date_range


def next_page_by_link_europarl(raw_html, last_archive_page_url=None):
    """If there is a "next page" link, find it and use that"""
    soup = BeautifulSoup(raw_html, 'lxml')
    next_page_tag = soup.find('a', title='Next Page')

    next_page_url = None
    if next_page_tag is not None and next_page_tag.has_attr('href'):
        next_page_url = f'https://eur-lex.europa.eu{next_page_tag.attrs["href"][1:]}'

    # Stop on last archive page specified in config (The default is None, which will match nothing)
    if next_page_url == last_archive_page_url:
        next_page_url = None

    return next_page_url


def extract_article_urls_from_page_europarl(raw_html):
    soup = BeautifulSoup(raw_html, 'lxml')

    ret = []
    for div_tag in soup.find_all('div', class_='SearchResult'):
        a_tag = div_tag.find('a', class_='title')
        if a_tag is not None and a_tag.has_attr('href'):
            ret.append(f'https://eur-lex.europa.eu{a_tag.attrs["href"][1:]}')

    return ret

def extract_articles_and_gen_next_page_link_europarl(base_url: str, curr_page_url: str, archive_page_raw_html: str,
                                                     is_infinite_scrolling: bool = False,
                                                     first_page: bool = False, page_num: int = 1,
                                                     logger: Logger = DummyLogger()):
    # 1) We need article URLs here to reliably determine the end of pages in some cases
    # TODO insert the appropriate strategy here!
    article_urls = extract_article_urls_from_page_europarl(archive_page_raw_html)
    if len(article_urls) == 0 and (not is_infinite_scrolling or first_page):
        logger.log('WARNING', curr_page_url, 'Could not extract URLs from the archive!', sep='\t')
    # 3a-I) Generate next-page URL or None if there should not be any
    # TODO insert the appropriate strategy here!
    next_page_url = next_page_by_link_europarl(archive_page_raw_html)
    return article_urls, next_page_url

def gen_article_links(logger):
    # Crawler stuff
    # TODO Substitute None with one or (a list of) more exsisting warc.gz files to be used as cache
    #  (e.g. continuing the interrupted crawling)
    downloader = WarcCachingDownloader(None,
                                       'europarl_archive.warc.gz',
                                       logger)

    # Portal stuff  # TODO WARNING qid parameter is added automatically!
    base_url_template = 'https://eur-lex.europa.eu/search.html?lang=en&scope=EURLEX&type=quick&' \
                        'sortOne=IDENTIFIER_SORT&sortOneOrder=desc&&page=#pagenum&DD_YEAR=#year'

    # Early years not continous
    years= ['FV_OTHER', 1001, 1807, 1808, 1809, 1854, 1865, 1867, 1868, 1870, 1872, 1878, 1879, 1881, 1882, 1883, 1885,
            1889, 1897, 1900, 1902, 1903, 1904, 1906, 1909, 1917, 1918, 1921, 1922, 1924, 1925, 1927] + \
           list(range(1929, 1941))  # 1941 is missing

    for year in years:
        base_url = base_url_template.replace('#year', str(year))
        g = gen_article_urls_and_subpages(base_url, downloader, extract_articles_and_gen_next_page_link_europarl,
                                          initial_page_num='1', min_pagenum=1, logger=logger)
        yield from g

    # From this year all years appear (date_range uses closed intervals!)
    for base_url in date_range(base_url_template, date(1942, 1, 1), date(date.today().year + 1, 12, 31), False):
        g = gen_article_urls_and_subpages(base_url, downloader, extract_articles_and_gen_next_page_link_europarl,
                                          initial_page_num='1', min_pagenum=1, logger=logger)
        yield from g

    logger.log('INFO', 'Done')

def main():
    # TODO Set filenames accordingly or it will be unconditionally overwritten!
    logger = Logger('europarl.log', logfile_level='DEBUG', console_level='DEBUG')
    # TODO Substitute None with one or (a list of) more exsisting warc.gz files to be used as cache
    #  (e.g. continuing the interrupted crawling)
    article_downloader = WarcCachingDownloader(None,
                                               'europarl_articles.warc.gz',
                                               logger,
                                               download_params={'err_threshold': 10,  # To avoid ban, can be Increased
                                                                'known_bad_urls': 'known_bad_urls.txt'})
    LANGS = ('BG', 'ES', 'CS', 'DA', 'DE', 'ET', 'EL', 'EN', 'FR', 'GA', 'HR', 'IT', 'LV', 'LT', 'HU', 'MT', 'NL', 'PL',
             'PT', 'RO', 'SK', 'SL', 'FI', 'SV', 'NO', 'IS')
    # Init dowloaders
    # TODO Substitute None with one or (a list of) more exsisting warc.gz files to be used as cache
    #  (e.g. continuing the interrupted crawling)
    #  (e.g. f'old/europarl_documents_{lang}_{file_format}.warc.gz')
    downloaders = {(lang, file_format):
                       WarcCachingDownloader(None,
                                             f'new/europarl_documents_{lang}_{file_format}.warc.gz',
                                             logger,
                                             download_params={'err_threshold': 10000,
                                                              'allow_empty_warc': True,
                                                              'known_bad_urls': 'known_bad_urls.txt'})
                   for lang in LANGS for file_format
                    in ('DOC', 'HTML', 'PDF', 'Official Journal', 'PDF - authentic OJ', 'External link', 'e-signature')}
    # Header
    # TODO Set filenames accordingly or it will be unconditionally overwritten!
    with open('documents_by_lang_and_format.tsv', 'w', encoding='UTF-8') as output, \
            open('problematic_urls_to_check.txt', 'w', encoding='UTF-8') as problematic_urls:
        print('DOCID', *LANGS, 'LINK', sep='\t', file=output)
        for link in gen_article_links(logger):
            elem_html = article_downloader.download_url(link)
            if elem_html is None:
                # HTTP 404, 500 and similar (except the duplicates)
                if link not in article_downloader.good_urls and link not in article_downloader.bad_urls:
                    print(link, file=problematic_urls)
                continue

            elem_bs = BeautifulSoup(elem_html, 'lxml')
            doc_name = elem_bs.find('p', class_='DocumentTitle pull-left')
            if doc_name is None:
                logger.log('ERROR', f'No Document name found: {link}')
                continue
            doc_name_str = str(doc_name.get_text())

            # Initialise dict
            d = {k: [] for k in LANGS}

            # Exactly PubFormat nothing else
            formats = elem_bs.find_all(lambda x: x.name == 'div' and x.attrs.get('class') == ['PubFormat'])
            if len(formats) == 0:
                warn = elem_bs.find('div', class_='alert')
                # TODO Text may be available, but not handled...
                if warn is not None and \
                        warn.get_text().strip() in {'The HTML format is unavailable in your User interface language',
                                                    'Text is not available.',
                                                    'The HTML format is unavailable;'
                                                    ' for more information please view the other tabs.',
                                                    'The document is not available on EUR-Lex.'
                                                    ' Use the link to the European Parliament\'s website above.'}:
                    # We distingush this for later use
                    if warn.get_text().strip() == 'The document is not available on EUR-Lex.' \
                                                       ' Use the link to the European Parliament\'s website above.':
                        logger.log('INFO', f'Link to the European Parliament\'s website for {link}')
                    else:
                        logger.log('INFO', f'No documents for {link}')
                    # TAB separated values
                    print(doc_name_str, *('_' if len(e) == 0 else ', '.join(e) for e in d.values()), link,
                          sep='\t', file=output)
                else:
                    nat_website_div = elem_bs.find(lambda x: x.name == 'div' and x.attrs.get('class') == ['panel-body'])
                    if nat_website_div is not None:
                        nat_website_a = nat_website_div.find('a')
                        if nat_website_a is not None:
                            # Need to strip ZWSP separately. See https://bugs.python.org/issue13391
                            nat_website_text = nat_website_a.get_text().strip().strip('\u200b')
                            if nat_website_text.startswith('National website'):
                                logger.log('INFO', f'Only national website ({nat_website_text}) for {link}')
                                continue

                    # Unify all else branches with continue
                    logger.log('ERROR', f'No proper document missing text found: {link}')

                # No format found, and all possibilities are handled -> Continue
                continue

            for doc_format in formats:
                if len(doc_format['class']) > 1:
                    continue  # Not what we looking for
                format_type = doc_format.find('span', attrs=None)
                if format_type is None:
                    logger.log('ERROR', f'No format type found: {link}')
                    continue

                format_str = str(format_type.get_text())
                # Langs not disabled
                lang_elems = doc_format.find_all('li', class_=lambda x: x != 'disabled')
                if len(lang_elems) == 0:
                    logger.log('ERROR', f'No lang elems tag found: {link}')
                    continue
                for lang in lang_elems:
                    lang_str = str(lang.a.span.get_text().strip())
                    doc_link = str(lang.a['href']).replace('./../../../', 'https://eur-lex.europa.eu/')
                    # Decode only on non-PDF and DOC files
                    downloaders[(lang_str, format_str)]. \
                     download_url(doc_link,
                                  decode=format_str not in {'DOC', 'PDF', 'PDF - authentic OJ', 'External link'})
                    if lang_str not in d:
                        logger.log('ERROR', f'Unknown language ({lang_str}) for {link}')
                        continue

                    d[lang_str].append(format_str)

            # No erroneous keys added that would break TSV format
            assert len(d) == 26
            print(doc_name_str, *('_' if len(e) == 0 else ', '.join(e) for e in d.values()), link,
                  sep='\t', file=output)

if __name__ == '__main__':
    main()
