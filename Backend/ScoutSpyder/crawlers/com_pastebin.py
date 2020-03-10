from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.logging import *

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
        paste_code = self.soup.find('textarea', {'id': 'paste_code'})
        if paste_code:
            self.text = paste_code.text
            self.has_content = True