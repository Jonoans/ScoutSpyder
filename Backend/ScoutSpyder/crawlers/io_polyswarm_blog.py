from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.helper import *
from ScoutSpyder.utils.logging import initialise_logging
from urllib.parse import urlparse
import re

LOGGER = initialise_logging(__name__)

class PolyswarmBlogCrawler(BaseCrawler):
    crawler_id = 'io.polyswarm.blog'
    requests_per_sec = 1
    start_url = [
        'https://blog.polyswarm.io/'
    ]
    robots_url = 'https://blog.polyswarm.io/robots.txt'

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)
        self.blacklist_regex = [
            'http[s]?://(.*)#comments-listing',
            'http[s]?://(.*)#tab-[0-9]',
            'http[s]?://(.*)#'
        ]
    
    def extract_content(self):
        forbidden_paths = [
            '/',
            '/all',
            '/tag/.*',
            '/topic/.*',
            '/author/.*',
            '/page/.*'
        ]
        url_path = urlparse(self.url).path
        for path in forbidden_paths:
            if re.fullmatch(path, url_path):
                return
        if self.text:
            self.has_content = True