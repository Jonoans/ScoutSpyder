from ScoutSpyder.models import *
from ScoutSpyder.utils.logging import *
from copy import deepcopy
from mongoengine.errors import NotUniqueError
from lxml import html
from newspaper import Article
from newspaper.configuration import Configuration
from urllib.parse import urljoin, urlparse
import json
import re
import tldextract
import trafilatura

__all__ = [
    'BaseCrawler'
]

LOGGER = initialise_logging(__name__)

# Shared variables
HTTP_REGEX = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
NEWLINE_REGEX = re.compile('\n+')
BLACKLIST_SUFFIX = [
    '.js',
    '.css',
    '.png',
    '.jpg',
    '.jpeg',
    '.pdf',
    '.ico',
    '.gif',
    '.m4a',
    '.woff2'
]
BLACKLIST_REGEX = [
    'http[s]?://(.*)signout(.*)'
]
NEWSPAPER_CONFIG = Configuration()
NEWSPAPER_CONFIG.fetch_images = False
NEWSPAPER_CONFIG.memoize_articles = False

class BaseCrawler:
    # Crawler Identifier
    crawler_id = 'com.base'

    # Rate limit configuration
    requests_per_sec = 1

    # robots.txt url
    robots_url = None

    # URLs of pages to crawl
    # start from
    start_url = []

    # URLs to extract cookies
    # for authentication
    cookies_url = []

    # Additional fqdns considered
    # part of this crawler's scope
    fqdns_in_scope = []

    def __init__(self, downloaded_doc=None):
        if downloaded_doc:
            # Crawl information
            self.crawl_id = downloaded_doc.crawl_id
            self.fqdn = downloaded_doc.fqdn
            self.html = downloaded_doc.html
            self.url = downloaded_doc.url

            # Depth crawl
            self.depth = downloaded_doc.depth
            self.depth_limit = downloaded_doc.depth_limit
            self.links_found = set()

            # Blacklists
            self.blacklist_suffix = deepcopy(BLACKLIST_SUFFIX)
            self.blacklist_regex = deepcopy(BLACKLIST_REGEX)

            # Extracted information
            self.authors = None
            self.title = None
            self.text = None
            self.publish_date = None
            self.ld_json = {}
            self.w3cmicrodata = {}

            # Flags
            self.has_content = False
            self.has_date = False

            # Other attributes
            self.valid_body = True
            self.valid_url = True
            self.np_article = self.__init_article()
            self.parsed_lxml = self.__init_lxml()
        else:
            self.crawl_id = None
            self.url, self.decomposed_urls = self.__init_url()
            self.fqdn = self.__extract_fqdn(self.url)
            self.fqdns_in_scope = set(self.fqdns_in_scope + [self.fqdn]
                + [self.__extract_fqdn(i) for i in self.decomposed_urls])
            self.depth = 0
            self.depth_limit = 5

            # Prevent errors
            self.blacklist_suffix = []
            self.blacklist_regex = []
    
    def signin(self, browser):
        """Flow for sign-in process to allow authenticated crawl"""
        return None
    
    def extract_content(self):
        """Developer-implemented menthod for refinement to content extraction algorithm"""
        raise NotImplementedError(f'extract_content not implemented for {__name__}')

    def prepare_db_entries(self):
        """
        Prepare `mongoengine.Document` object to be inserted by `insert_db_entries`.

        Developer may choose to override in child classes.
        """
        crawled_doc = CrawledDocument()
        crawled_doc.crawl_id = self.crawl_id
        crawled_doc.fqdn = self.fqdn
        crawled_doc.html = self.html
        crawled_doc.url = self.url
        if self.has_content:
            crawled_doc.authors = self.authors
            crawled_doc.title = self.title
            crawled_doc.text = self.text
        if self.has_date:
            crawled_doc.publish_date = self.publish_date
        return crawled_doc
    
    def insert_db_entries(self, db_entry):
        """
        Inserts previously prepared `mongoengine.Document` object

        Developer may choose to override in child classes
        """
        try:
            db_entry.save()
            LOGGER.info(f'Scrapped: {self.url}')
        except NotUniqueError:
            pass
        except:
            LOGGER.exception('')

    def scrap(self):
        """Scrap page and process content"""
        self.__extract_content()
        if self.depth < self.depth_limit:
            self.find_links()
            self.generate_children()
    
    def post_scrap(self):
        """Actions to be completed after scrapping content"""
        db_entry = self.prepare_db_entries()
        self.insert_db_entries(db_entry)

    def __extract_fqdn(self, url):
        """Shorthand method for fqdn extraction"""
        return tldextract.extract(url).fqdn
    
    def extract_auth_cookies(self, browser):
        """Extracts cookies for authenticated crawls"""
        cookies = {}
        for url in self.cookies_url:
            browser.get(url)
            cookies[url] = browser.get_cookies()
        return cookies
    
    def __init_url(self):
        """Initialises Crawler object's URL
        
        If `url` is None, extract first URL in `start_url`
        and puts it in as crawler's URL.

        [Returns :tuple(list, list):]
            url:
                URL to be set as crawler's URL

            decomposed_urls:
                Any URLs remaining after extracting URL
                from `start_urls`

        """
        decomposed_urls = []
        if len(self.start_url) <= 0:
            raise ValueError('No start_url passed into crawler, start_url list was empty')
        url = self.start_url.pop()
        decomposed_urls = self.start_url
        return url, decomposed_urls
    
    def __init_article(self):
        article = Article(self.url, config=NEWSPAPER_CONFIG)
        article.set_html(self.html)
        return article
    
    def __init_lxml(self):
        parsed_lxml = html.fromstring(self.html)
        return parsed_lxml
    
    def __main_content_extraction(self):
        try:
            text = trafilatura.extract(self.html, include_comments=False)
        except TypeError: # library appears to be buggy
            text = None
        if text:
            self.text = NEWLINE_REGEX.sub('\n\n', text)
            self.np_article.set_text(text)
    
    def __extract_metadata(self):
        """Extracts metadata of page with Newspaper3k"""
        # Disable main content extraction of Newspaper3k
        self.np_article.extractor.calculate_best_node = lambda x: None
        self.np_article.parse()
        if not self.np_article.is_valid_url():
            self.valid_url = False
            LOGGER.debug(f'Invalid URL: {self.url}')
        if not self.np_article.is_valid_body():
            self.valid_body = False
            LOGGER.debug(f'Invalid BODY: {self.url}')
        self.authors = self.np_article.authors
        self.title = self.np_article.title
        self.publish_date = self.np_article.publish_date
        if self.publish_date:
            self.has_date = True
    
    def __extract_ld_json(self):
        """Extracts JSON Linked Data"""
        ld_jsons = self.parsed_lxml.xpath('.//script[@type="application/ld+json"]')
        for ld in ld_jsons:
            self.ld_json.update( json.loads( ld.text_content()) )
    
    def __process_w3microdata_children(self, children, dict_):
        for child in children:
            extracted = self.__extract_w3cmicrodata_item(child)

            for key, val in extracted.items():
                existing = dict_.get(key)
                if existing is not None:
                    if type(existing) != list:
                        existing = list(existing)
                    dict_[key] = existing.append(val)
                    continue
                dict_.update({key: val})

    def __extract_w3cmicrodata_item(self, item):
        if item.get('itemscope') is not None:
            children = item.xpath('./*[@itemprop]')
            child_items = {}
            self.__process_w3microdata_children(children, child_items)
            return {item.get('itemprop'): child_items}
        
        return {item.get('itemprop'): item.get('content') or item.get('href')}
    
    def __extract_w3cmicrodata(self):
        itemscopes = self.parsed_lxml.xpath('.//*[@itemscope][not(ancestor::*[@itemscope])]')
        if len(itemscopes) == 0:
            return
        
        for scope in itemscopes:
            if not 'schema.org' in scope.get('itemtype'):
                continue

            children = scope.xpath('./*[@itemprop]')
            self.__process_w3microdata_children(children, self.w3cmicrodata)
            print(self.w3cmicrodata)

    def pre_extract_actions(self):
        """Developer-implemented method to run functions before content extraction"""
        pass

    def __extract_content(self):
        """Content extraction pipeline"""
        self.pre_extract_actions()
        self.__main_content_extraction()
        self.__extract_metadata()
        self.__extract_ld_json()
        self.__extract_w3cmicrodata()
        self.extract_content()
    
    def _complete_link(self, url):
        if not urlparse(url).scheme:
            url = urljoin(self.url, url)
        return url
    
    def __in_suffix_blacklist(self, link):
        for suffix in self.blacklist_suffix:
            if link.endswith(suffix):
                return True
        return False

    def __in_regex_blacklist(self, link):
        for regex in self.blacklist_regex:
            if re.match(regex, link):
                return True
        return False

    def link_is_valid(self, link):
        link = link.strip()
        checks = [
            self.__in_suffix_blacklist(link),
            self.__in_regex_blacklist(link)
        ]
        return False if True in checks else True
    
    def find_links(self):
        """Extract links from <a> tags within HTML of page"""
        elems = self.parsed_lxml.findall('.//a')
        for elem in elems:
            link = elem.get('href')
            if link:
                link = self._complete_link(link)
                if HTTP_REGEX.match(link):
                    link = link.strip()
                    if not self.link_is_valid(link):
                        continue
                    self.links_found.add(link)

    def prepare_queued_link(self, link, depth):
        queued_link = QueuedLink()
        queued_link.crawl_id = self.crawl_id
        queued_link.fqdn = self.__extract_fqdn(link)
        queued_link.url = link
        queued_link.depth = depth
        queued_link.depth_limit = self.depth_limit
        return queued_link
    
    def save_queued_link(self, queued_link):
        try:
            queued_link.save()
        except NotUniqueError:
            pass
        finally:
            del queued_link

    def generate_children(self):
        depth = self.depth + 1
        for link in self.links_found:
            if CrawledDocument.objects(crawl_id=self.crawl_id, url=link).first():
                continue
            queued_link = self.prepare_queued_link(link, depth)
            self.save_queued_link(queued_link)