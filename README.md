# Web Article Curator

A crawler program which can be used for downloading the content of portals (news, forums, blogs) and converting it to the desired output format, in accordance with the configuration.

## Requirements

- Python 3.6+
- (optional) for Newspaper3k, the installation of the following packages must precede the installation of this program: python3-dev libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev libpng12-dev

## Install

### pip

`pip3 install webarticlecurator`

### Manual

1. `git clone https://github.com/ELTE-DH/webarticlecurator.git`
2. Run `python3 setup.py install` (you may have to use `sudo` at the beginning of this command)

## Usage

The program can be used in multiple ways:

- Crawling (see the options below): `python3 -m webarticlecurator crawl CONFIGURATION [parameters]`
- Listing URLs in a previously created WARC file: `python3 -m webarticlecurator listurls -s SOURCE_WARC`
- Validating a previously created WARC file (with [warcio](https://github.com/webrecorder/warcio)): `python3 -m webarticlecurator validate -s SOURCE_WARC`
- Sampling a previously created WARC file based on a list of URLs (one URL per line, URLs not present in the source archive are downloaded if `--offline` is False): `python3 -m webarticlecurator sample -s SOURCE_WARC -i selected_urls.txt TARGET_WARC --offline True/False`
- Printing the content of the selected URLs into an empty directory: `python3 -m webarticlecurator cat -s SOURCE_WARC -i selected_urls.txt TARGET_DIR`
- Downloading a single URL (for testing purposes): `python3 -m webarticlecurator download SOURCE_URL TARGET_WARC`

# Configuration schema

The configuration is divided into three levels. On the first two levels, YAML is used for the configuration format with schema checks.
The third level of configuration uses Python functions.

## Crawl-level configuration

It specifies the configuration for the current crawling process with the following fields:

- `schema`: The filename pointing to the schema of the portal to be crawled (second level configuration)
- `output_corpus` (optional): The desired filename of the output corpus (default: no output corpus)
- `log_file_archive` (optional): The log file for the archive crawler (default: log is not saved)
- `log_file_articles` (optional): The log file for the article crawler (default: log is no saved)
- `new_problematic_archive_urls` (optional): The file where the problematic archive URLs should be written (default: URLs are not saved)
- `new_problematic_urls` (optional): The file where the problematic article URLs should be written (default: URLs are not saved)
- `new_good_archive_urls` (optional): The file where the newly downloaded, good archive URLs should be written (default: URLs are not saved)
- `new_good_urls` (optional): The file where the newly downloaded, good article URLs should be written (default: URLs are not saved)
- `date_from` (optional): The inclusive minimal date of the required articles in ISO 8601 format, YYYY-MM-DD (default: from the schema of the portal if applies)
- `date_until` (optional): The inclusive maximal date of the required articles in ISO 8601 format, YYYY-MM-DD (default: yesterday if applies)

## Site schemas

The following parameters must be filled in the case of every portal:

- `site_name`: A friendly name for the portal
- `new_article_url_threshold`: The minimal amount of new URLs required on an archive page (e.g. the archive pages slid due to new articles in case of an active portal)

Python functions:

- `portal_specific_exctractor_functions_file`: The filename pointing to the python file which contains the required extractor functions
- `extract_next_page_url_fun` (it can be NULL): The name of the function to be imported from the `portal_specific_exctractor_functions_file` to extract the "next page URL"
- `extract_article_urls_from_page_fun`: The name of the function to be imported from the `portal_specific_exctractor_functions_file` to extract the article URLs from the archive page
- `next_page_of_article_fun` (it can be NULL): The name of the function to be imported from the `portal_specific_exctractor_functions_file` if there are multipage articles. This function extracts the "next page URL" for the rest of the pages in a multipage article. (It must be used with `MultiPageArticleConverter` or similar as `corpus_converter` to work!)
- `corpus_converter_file`: The filename pointing to the python file which contains the required corpus extractor class
- `corpus_converter`: The name of the class to be imported from the `corpus_converter_file`. The default is to do nothing (`dummy-converter`).

Boolean features to describe the site:

- `next_url_by_pagenum`: Use page numbering for pagination of the archive, e.g. infinite scrolling (false means no pages or pages handled by `extract_next_page_url_fun`)
- `infinite_scrolling`: The crawler increment page numbers until the first page with zero article urls
- `archive_page_urls_by_date`: Group the archive page URLs by their dates
- `go_reverse_in_archive`: Go reverse (backwards in time) in the archive by date (when the earliest article is not known)
- `verify_request`: Suppress complaining about invalid HTTPS certificates
- `ignore_archive_cache`: Ignore archive cache (for those portals which only use pagination)

Column definitions:

In the `columns` dictionary, the following features can be set for each column (defined with a friendly name):

- `date_first_article` (optional): The date of the first article on the portal/column (also used for archive crawling)
- `date_first_article` (optional): The date of the last article on the portal/column (also used for archive crawling)
- `initial_pagenum` (optional): The initial page number which could be omitted (an empty string if not set, else it should be `min_pagenum` - 1)
- `min_pagenum` (optional): The "first" page number to increment (e.g. initial_pagenum + 1 = min_pagenum <= max_pagenum if not a single page column where only initial_pagenum must be specified, min_pagenum and max_pagenum must be omitted)
- `max_pagenum` (optional): The upper bound of the number of pages for safety or for stop criteria
- `archive_url_format`: The schema for the archive URL of the portal/column (supply `#year`, `#month`, `#day` and
 `#next-year`, `#next-month`, `#next-day` tags which have to be replaced with the actual field of date, and
 `#pagenum` with the actual page number during the crawling)

Note: One can iterate the archive by months or years by omitting `#day` (`#next-day`) or `#month` (`#next-month`) 

## Site-specific extractors

There are maximum three types of extractors to be included for each portal.
See the examples in the `configs` directory for further information and `DummyConverter` for the converter API.

## Command line parameters

The first two command-line parameters should be `crawl` and the filename pointing to the configuration file of the current crawl. These can be followed by some optional parameters:

- `--old-archive-warc OLD_ARCHIVE_WARC`: Existing WARC archives of the portal's archive (use them as cache)
- `--archive-warc ARCHIVE_WARC`: New WARC archive of the portal's archive (copy all cached pages if `--old-archive-warc` is specified)
- `--old-articles-warc OLD_ARTICLES_WARC`: Existing WARC archives of the portal's archive (use them as cache)
- `--articles-warc ARTICLES_WARC`: New WARC archive of the portal's archive (copy all cached pages if `--old-archive-warc` is specified)
- `--archive-just-cache [ARCHIVE_JUST_CACHE]`: Use only cached pages (no output WARC file): `--old-archive-warc` must be specified!
- `--articles-just-cache [ARTICLES_JUST_CACHE]`: Use only cached pages (no output WARC file): `--old-articles-warc` must be specified!
- `--debug-news-archive [DEBUG_NEWS_ARCHIVE]`: Set DEBUG logging on NewsArchiveCrawler and print the number of extracted URLs per page
- `--strict [STRICT]`: Set strict-mode in WARCReader to enable validation
- `--crawler-name CRAWLER_NAME`: The name of the crawler for the WARC info record
- `--user-agent USER_AGENT`: The User-Agent string to use in headers while downloading
- `--no-overwrite-warc`: Do not overwrite `--{archive,articles}-warc` if needed
- `--cumulative-error-threshold CUMULATIVE_ERROR_THRESHOLD`: The sum of download errors before giving up
- `--known-bad-urls KNOWN_BAD_URLS`: Known bad URLs to be excluded from download (filename, one URL per line)
- `--known-article-urls KNOWN_ARTICLE_URLS`: Known article URLs to mark the desired end of the archive (filename, one URL per line)
- `--max-no-of-calls-in-period MAX_NO_OF_CALLS_IN_PERIOD`: Limit the number of HTTP requests per period
- `--limit-period LIMIT_PERIOD`: Limit the period of HTTP requests (in seconds), see also `--max-no-of-calls-in-period`
- `--proxy-url PROXY_URL`: SOCKS Proxy URL to use, e.g. socks5h://localhost:9050
- `--allow-cookies [ALLOW_COOKIES]`: Allow session cookies
- `--stay-offline [STAY_OFFLINE]`: Do not download but write output WARC (see `--just-cache` when no output WARC file is needed)
- `--archive`: Crawl only the portal's archive
- `--articles`: Crawl articles (and optionally use cached WARC for the portal's archive), DEFAULT behaviour
- `--corpus`: Use `--old-articles-warc` to create a corpus (no crawling, equals to `--archive-just-cache` and `--articles-just-cache`)

# Licence

This project is licensed under the terms of the GNU LGPL 3.0 license.

# Acknowledgement

This software is the direct continuation of [corpusbuilder](https://github.com/ppke-nlpg/corpusbuilder).
The authors gratefully acknowledge the groundbreaking work of all pioneers who inspired this program.
Special thanks go to Tibor Kákonyi who put the initial implementation under the GNU LGPL 3.0 license and allowing us to continue his work.

# References

The DOI of the code is: https://doi.org/10.5281/zenodo.3755323

If you use this program, please cite the following paper:

[__The ELTE.DH Pilot Corpus – Creating a Handcrafted Gigaword Web Corpus with Metadata__ Balázs Indig, Árpád Knap, Zsófia Sárközi-Lindner, Mária Timári, Gábor Palkó _In the Proceedings of the 12th Web as Corpus Workshop (WAC XII)_, pages 33-41 Marseille, France 2020](https://www.aclweb.org/anthology/2020.wac-1.5.pdf)

```
@inproceedings{indig-etal-2020-elte,
    title = "The {ELTE}.{DH} Pilot Corpus {--} Creating a Handcrafted {G}igaword Web Corpus with Metadata",
    author = {Indig, Bal{\'a}zs  and
      Knap, {\'A}rp{\'a}d  and
      S{\'a}rk{\"o}zi-Lindner, Zs{\'o}fia  and
      Tim{\'a}ri, M{\'a}ria  and
      Palk{\'o}, G{\'a}bor},
    booktitle = "Proceedings of the 12th Web as Corpus Workshop",
    month = may,
    year = "2020",
    address = "Marseille, France",
    publisher = "European Language Resources Association",
    url = "https://www.aclweb.org/anthology/2020.wac-1.5",
    pages = "33--41",
    abstract = "In this article, we present the method we used to create a middle-sized corpus using targeted web crawling. Our corpus contains news portal articles along with their metadata, that can be useful for diverse audiences, ranging from digital humanists to NLP users. The method presented in this paper applies rule-based components that allow the curation of the text and the metadata content. The curated data can thereon serve as a reference for various tasks and measurements. We designed our workflow to encourage modification and customisation. Our concept can also be applied to other genres of portals by using the discovered patterns in the architecture of the portals. We found that for a systematic creation or extension of a similar corpus, our method provides superior accuracy and ease of use compared to The Wayback Machine, while requiring minimal manpower and computational resources. Reproducing the corpus is possible if changes are introduced to the text-extraction process. The standard TEI format and Schema.org encoded metadata is used for the output format, but we stress that placing the corpus in a digital repository system is recommended in order to be able to define semantic relations between the segments and to add rich annotation.",
    language = "English",
    ISBN = "979-10-95546-68-9",
}
```
