from ScoutSpyder.crawlers.base_crawler import *
from dateutil.parser import parse
from lxml import etree
import re

class DarkReadingCrawler(BaseCrawler):
    crawler_id = 'com.darkreading'
    requests_per_sec = 1
    start_url = [
        'https://www.darkreading.com/'
    ]

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)

        self.blacklist_regex = [
            r'http[s]?://.*/.*\?cid.*',
            r'http[s]?://.*/.*\?tag.*',
            r'http[s]?://.*/.*\?itc.*',
            r'http[s]?://.*/.*\?utm_campaign.*',
            r'http[s]?://.*/.*\?pid.*',
            r'http[s]?://.*/.*\?print.*',
            r'http[s]?://.*/(rss_|author-bio|document|email).*\.asp.*',
            r'http[s]?://.*/v/d-id/.*'
        ]
    
    def extract_content(self):
        article_body = self.parsed_lxml.find('.//div[@id="article-main"]')
        if article_body is not None:
            # Remove image captions
            captions = article_body.findall('.//span[@class="docimagecaptiontext"]')
            for x in captions:
                x.getparent().remove(x)

            # Remove related content table
            tables = article_body.xpath('.//table')
            for table in tables:
                if 'Related Content:' in table.text_content():
                    table.getparent().remove(table)

            # Extract body text
            texts = article_body.xpath('.//*[self::p or self::span or self::li]')
            for text in texts:
                for br in text.xpath('.//br'):
                    br.tail = '\n' + br.tail if br.tail else '\n'
            self.text = '\n'.join(x.text_content() for x in texts if x.text_content().strip())
            index = 0
            for index, line in enumerate(self.text.splitlines()):
                if re.match(r'.*(Recommended Reading:|View Full Bio|Comment.*\|).*', line):
                    break
            self.text = '\n'.join(self.text.splitlines()[:index])

            with open('output.txt', 'a', encoding='utf-8') as file:
                file.write(f'URL: {self.url}\nTitle: {self.title}\n\n{self.text}\n\n' + '=' * 20 + '\n\n')

            # Extract author
            self.authors = []
            author = self.ld_json.get('author')
            if author:
                self.authors = [author['name']]
            else:
                author = self.parsed_lxml.find('.//div[@class="author-info-block"]//span')
                if author is not None:
                    self.authors = [author.text_content()]
            
            # Extract published date
            publish_date = self.ld_json.get('datePublished')
            if publish_date:
                self.publish_date = parse(publish_date)
            else:
                publish_date = self.parsed_lxml.find('.//div[@id="aside-inner"]//span')
                if publish_date is not None:
                    br = publish_date.find('br')
                    br.tail = ' ' + br.tail if br.tail else ' '
                    self.publish_date = parse( publish_date.text_content() )
            self.has_date = bool(self.publish_date)

            self.has_content = True