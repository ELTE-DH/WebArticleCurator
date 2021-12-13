#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from itertools import groupby
from collections import defaultdict

from webarticlecurator.enhanced_downloader import WarcCachingDownloader
from webarticlecurator.utils import create_or_check_clean_dir, write_content_to_url_named_file


def validate_warc_file(source_warcfiles, validator_logger):
    reader = WarcCachingDownloader(source_warcfiles, None, validator_logger, True,
                                   download_params={'stay_offline': True, 'strict_mode': True, 'check_digest': True})
    validator_logger.log('INFO', 'OK!', len(reader.url_index), 'records read!')
    return reader.url_index


def online_test(url='https://index.hu/belfold/2018/08/27/fidesz_media_helyreigazitas/', filename='example.warc.gz',
                test_logger=None):
    w = WarcCachingDownloader(None, filename, test_logger)
    t = w.download_url(url)
    test_logger.log('INFO', t)


def sample_warc_by_urls(source_warcfiles, new_urls, sampler_logger, target_warcfile=None, out_dir=None, offline=True,
                        just_cache=False, negative=False, extract_article_urls_from_page_plus_fun=None, max_tries=3,
                        allow_cookies=False):
    """ Create new warc file for the supplied list of URLs from an existing warc file """
    is_out_dir_mode = out_dir is not None
    if is_out_dir_mode:
        create_or_check_clean_dir(out_dir)

    if extract_article_urls_from_page_plus_fun is not None:
        def test_raw_html(cont, ulrs_already_seen):
            article_urls_w_meta = set(extract_article_urls_from_page_plus_fun(cont))
            ok = len(ulrs_already_seen & article_urls_w_meta) == 0
            ulrs_already_seen |= article_urls_w_meta
            return ok
    else:
        def test_raw_html(*_):
            return True

    w = WarcCachingDownloader(source_warcfiles, target_warcfile, sampler_logger, just_cache=just_cache,
                              download_params={'stay_offline': offline, 'allow_cookies': allow_cookies})

    new_urls = {url.strip() for url in new_urls}
    if negative:
        new_urls = w.url_index - new_urls

    already_seen_urls = set()
    for url in sorted(new_urls):
        sampler_logger.log('INFO', 'Adding url', url)
        if not offline or url in w.url_index:
            url_ok = False
            tries_left = max_tries
            while not url_ok and tries_left > 0:
                resp = w.download_url(url, ignore_cache=tries_left < max_tries, return_warc_records_wo_writing=True)
                tries_left -= 1
                if resp is not None:
                    rec, raw_html = resp
                    url_ok = test_raw_html(raw_html, already_seen_urls)
                    if url_ok:
                        w.write_records_for_url(url, rec)
                        if is_out_dir_mode and raw_html is not None:
                            fname = write_content_to_url_named_file(url, raw_html, out_dir)
                            sampler_logger.log('INFO', 'Creating file', fname)
                    elif tries_left == 0:
                        sampler_logger.log('ERROR', url, f'There are no tries left for URL!', sep='\t')
                        w.write_records_for_url(url, rec)  # Keep the URL anyway
                    else:
                        sampler_logger.log('WARNING', url, f'Retrying URL ({max_tries - tries_left})!', sep='\t')
        else:
            sampler_logger.log('ERROR', 'URL not present in archive and can not be downloaded (offline True)', url)


def archive_page_contains_article_url(extract_article_urls_from_page_plus_fun, source_warcfiles, checked_urls,
                                      sampler_logger, out_dir):
    """Extract HTML content for archive URLs which contains checked_urls as article urls (for debugging the portal)"""

    checked_urls = {url.rstrip() for url in checked_urls}
    create_or_check_clean_dir(out_dir)

    w = WarcCachingDownloader(source_warcfiles, None, sampler_logger, just_cache=True,
                              download_params={'stay_offline': True})

    url_to_fname = {}
    archive_page_for_checked_urls = defaultdict(set)
    for url in sorted(w.url_index):
        raw_html = w.download_url(url)
        if raw_html is not None:
            article_urls_w_meta = extract_article_urls_from_page_plus_fun(raw_html)
            if len(article_urls_w_meta) > 0:
                checked_urls_in_page = sorted((e for e in article_urls_w_meta if e[0] in checked_urls))
                for checked_url, *checked_url_meta in checked_urls_in_page:
                    # Defaultdict-like behaviour for writing a file only once
                    fn = url_to_fname.get(url)
                    if fn is None:
                        fn = write_content_to_url_named_file(url, raw_html, out_dir)
                        url_to_fname[url] = fn
                    archive_page_for_checked_urls[checked_url].add((tuple(checked_url_meta), url, fn))
            else:
                sampler_logger.log('WARNING', url, 'Could not extract URLs from the archive!', sep='\t')
        else:
            sampler_logger.log('ERROR', 'URL present in index, but not present in archive!', url, sep='\t')

    unique_metas_list = []
    sampler_logger.log('INFO', 'Summary:')
    for checked_url, occurences in archive_page_for_checked_urls.items():
        duplicates_w_uniq_metas = set()
        occurences = sorted(occurences)  # Sort on the first elem of the tuple (metas)
        for k, group_iter in groupby(occurences, key=lambda x: x[0]):
            group = list(group_iter)
            # Separate matching metas (real duplicates, should not occur)
            # from direct linked subelements of live event commentaries (duplicates to be ignored)
            if len(group) > 1:
                sampler_logger.log('INFO', checked_url, 'has found in the following files (with matching metas):')
                for ch_url_metas, url, fn in group:
                    sampler_logger.log('INFO', '', url, fn, sep='\t')
                    duplicates_w_uniq_metas.add((ch_url_metas, url, fn))
            else:
                duplicates_w_uniq_metas.add(group[0])
        unique_metas_list.append((checked_url, duplicates_w_uniq_metas))

    # Write duplicates with unique metas separately (after all matching metas has written)
    for checked_url, duplicates_w_uniq_metas in unique_metas_list:
        sampler_logger.log('INFO', checked_url, 'has found in the following files (with unique metas):')
        for metas, url, fn in duplicates_w_uniq_metas:
            sampler_logger.log('INFO', '', url, *metas, fn, sep='\t')
