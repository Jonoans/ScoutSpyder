from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.logging import initialise_logging
import re

LOGGER = initialise_logging(__name__)

class WashingtonPostCrawler(BaseCrawler):
    crawler_id = 'com.washingtonpost'
    requests_per_sec = 1
    start_url = [
        'https://www.washingtonpost.com/business/technology/',
        'https://www.washingtonpost.com/consumer-tech/',
        'https://www.washingtonpost.com/news/innovations/'
    ]
    robots_url = 'https://www.washingtonpost.com/robots.txt'

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)
        self.blacklist_regex = [
            'http[s]?://subscribe.washingtonpost.com(.*)',
            'http[s]?://www.washingtonpost.com/(rss-)?terms-of-service(.*)',
            'http[s]?://www.washingtonpost.com/privacy-policy(.*)'
        ]

        for suffix in self.blacklist_suffix:
            self.blacklist_regex.append('http[s]?://(.*)\{}(.*)'.format(suffix))
    
    def extract_content(self):
        if self.valid_url and self.valid_body:
            self.text = re.sub('Read more:.*', '', self.text)
            self.has_content = True