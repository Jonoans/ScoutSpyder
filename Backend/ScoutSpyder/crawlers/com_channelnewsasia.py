from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.logging import initialise_logging
from dateutil.parser import parse
import re

LOGGER = initialise_logging(__name__)

class ChannelNewsAsiaCrawler(BaseCrawler):
    crawler_id = 'com.channelnewsasia'
    requests_per_sec = 1
    start_url = [
        'https://www.channelnewsasia.com/news/singapore',
        'https://www.channelnewsasia.com/news/asia',
        'https://www.channelnewsasia.com/news/world',
        'https://www.channelnewsasia.com/news/commentary',
        'https://www.channelnewsasia.com/news/business',
        'https://www.channelnewsasia.com/news/cnainsider',
        'https://www.channelnewsasia.com/news/topics/coronavirus-covid-19',
        'https://www.channelnewsasia.com/news/technology'
    ]
    robots_url = 'https://www.channelnewsasia.com/robots.txt'

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)

        self.blacklist_regex = [
            'http[s]?://.*/video-on-demand/.*'
        ]
    
    def extract_content(self):
        if self.valid_url:
            publish_date = self.parsed_lxml.find('.//meta[@name="cXenseParse:recs:publishtime"]')
            if publish_date is not None:
                self.publish_date = parse( publish_date.get('content') )
                self.text = re.sub(r'(BOOKMARK THIS|READ|WATCH):.*\n?', '', self.text)
                self.has_content = True
                self.has_date = True