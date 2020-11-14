from ScoutSpyder.crawlers.base_crawler import *
from dateutil.parser import parse
from lxml import html
from urllib.parse import urlparse
import re

class ThreatpostCrawler(BaseCrawler):
    crawler_id = 'com.threatpost'
    requests_per_sec = 1
    start_url = [
        'https://threatpost.com/'
    ]
    article_regex = r'/[a-zA-Z0-9\-]+/\d+/'

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)

        self.blacklist_regex = [
            r'http[s]?://.*/[a-zA-Z0-9\-]+/\d+/#comments'
        ]
    
    def pre_extract_actions(self):
        comments = self.parsed_lxml.find('.//div[@id="comments"]')
        if comments is not None:
            comments.getparent().remove(comments)
            self.html = html.tostring(self.parsed_lxml).decode()

    def extract_content(self):
        invalid_paths = [
            '/category/.*',
            '/webinars/.*'
        ]
        url_path = urlparse(self.url).path
        for path in invalid_paths:
            if re.fullmatch(path, url_path):
                return
        
        if re.fullmatch(self.article_regex, url_path):
            publish_date = self.ld_json.get('datePublished')
            if publish_date:
                self.publish_date = parse(publish_date)
                self.has_date = True
        
            self.has_content = True