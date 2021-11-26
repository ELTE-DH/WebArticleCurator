from collections import defaultdict

from webarticlecurator.enhanced_downloader import WarcCachingDownloader
from webarticlecurator.utils import wrap_input_constants, create_or_check_clean_dir, write_content_to_url_named_file


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
                        just_cache=False):
    """ Create new warc file for the supplied list of URLs from an existing warc file """
    is_out_dir_mode = out_dir is not None
    if is_out_dir_mode:
        create_or_check_clean_dir(out_dir)

    w = WarcCachingDownloader(source_warcfiles, target_warcfile, sampler_logger, just_cache=just_cache,
                              download_params={'stay_offline': offline})
    for url in new_urls:
        url = url.strip()
        sampler_logger.log('INFO', 'Adding url', url)
        if not offline or url in w.url_index:
            cont = w.download_url(url)
            if is_out_dir_mode and cont is not None:
                fname = write_content_to_url_named_file(url, cont, out_dir)
                sampler_logger.log('INFO', 'Creating file', fname)
        else:
            sampler_logger.log('ERROR', 'URL not present in archive', url)


def archive_page_contains_article_url(config, source_warcfiles, checked_urls, sampler_logger, out_dir):
    """Extract HTML content for archive URLs which contains checked_urls as article urls (for debugging the portal)"""

    checked_urls = {url.rstrip() for url in checked_urls}

    w = WarcCachingDownloader(source_warcfiles, None, sampler_logger, just_cache=True,
                              download_params={'stay_offline': True})

    create_or_check_clean_dir(out_dir)

    archive_page_for_checked_urls = defaultdict(set)
    for url in w.url_index:
        raw_html = w.download_url(url)
        if raw_html is not None:
            extract_article_urls_from_page_fun = wrap_input_constants(config)['EXTRACT_ARTICLE_URLS_FROM_PAGE_FUN']
            article_urls = extract_article_urls_from_page_fun(raw_html)
            if len(article_urls) > 0:
                checked_urls_in_page = sorted(article_urls & checked_urls)
                if len(checked_urls_in_page) > 0:
                    fname = write_content_to_url_named_file(checked_urls_in_page[0], raw_html, out_dir)
                    for checked_url in checked_urls_in_page:
                        archive_page_for_checked_urls[checked_url].add((url, fname))
            else:
                sampler_logger.log('WARNING', url, 'Could not extract URLs from the archive!', sep='\t')
        else:
            sampler_logger.log('ERROR', 'URL present in index, but not present in archive', url)

    sampler_logger.log('INFO', 'Summary:')
    for checked_url, urls in archive_page_for_checked_urls.items():
        sampler_logger.log('INFO', checked_url, 'has found in the following files:')
        for url, fname in sorted(urls):
            sampler_logger.log('INFO', '\t', url, ':', fname)
