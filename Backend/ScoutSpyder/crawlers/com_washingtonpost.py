from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.logging import initialise_logging
from dateutil.parser import parse
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
    
    def insert_db_entries(self, db_entry):
        pass
    
    def extract_content(self):
        if self.valid_url and self.valid_body:
            self.text = re.sub('Read more:.*', '', self.text)
            self.has_content = True
        
        if self.has_content:
            publish_date = self.ld_json.get('datePublished')
            if publish_date is not None:
                self.publish_date = parse(publish_date)
            
            author = self.ld_json.get('author')
            if author is not None:
                if type(author) == list:
                    self.authors = [x['name'] for x in author]
                else:
                    self.authors = [author['name']]

            teaser_content = self.parsed_lxml.findall('.//div[@class="teaser-content"]//p')
            if teaser_content:
                teaser = [x.text_content().strip() for x in teaser_content]
                self.text = '\n\n'.join(teaser + [self.text.strip()])