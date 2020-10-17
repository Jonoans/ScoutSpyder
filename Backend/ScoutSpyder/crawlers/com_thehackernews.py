from ScoutSpyder.crawlers.base_crawler import *
from dateutil.parser import parse
from lxml import html

class TheHackerNewsCrawler(BaseCrawler):
    crawler_id = 'com.thehackernews'
    requests_per_sec = 1
    start_url = [
        'https://thehackernews.com/'
    ]
    robots_url = 'https://thehackernews.com/robots.txt'

    def __init__(self, download_doc=None):
        super().__init__(download_doc)

        self.blacklist_regex = [
            'http[s]?://.*/p/.*'
        ]
    
    def pre_extract_actions(self):
        share_opts = self.parsed_lxml.xpath('.//div[contains(@class, "float-share") or contains(@class, "mobile-share")]')
        if share_opts:
            for opt in share_opts:
                opt.getparent().remove(opt)
            mod_html = html.tostring(self.parsed_lxml).decode()
            self.html = mod_html

    def extract_content(self):
        if self.valid_url and self.valid_body:
            author_name = self.w3cmicrodata['author']['name']
            self.authors = [author_name] if type(author_name) != list else author_name
            self.publish_date = parse(self.w3cmicrodata['datePublished'])
            self.has_content = True
            self.has_date = True