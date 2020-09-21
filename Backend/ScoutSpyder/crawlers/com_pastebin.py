from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.logging import *
from urllib.parse import urlparse
import re

LOGGER = initialise_logging(__name__)

class PastebinCrawler(BaseCrawler):
    crawler_id = 'com.pastebin'
    requests_per_sec = 1
    start_url = [
        'https://pastebin.com/archive'
    ]
    robots_url = 'https://pastebin.com/robots.txt'

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)
        self.blacklist_regex = [
            'http[s]?://pastebin.com/index/(.*)'
        ]
    
    def extract_content(self):
        forbidden_paths = [
            '/dl/.*',
            '/raw/.*'
        ]
        url_path = urlparse(self.url).path
        for path in forbidden_paths:
            if re.fullmatch(path, url_path):
                return

        paste_code = self.parsed_lxml.find('.//textarea[not(@id)]')
        if paste_code is not None:
            self.text = paste_code.text
            self.has_content = True