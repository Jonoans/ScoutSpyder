from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.logging import *
import tldextract

LOGGER = initialise_logging(__name__)

class NewYorkTimesCrawler(BaseCrawler):
    crawler_id = 'com.nytimes'
    requests_per_sec = 1
    start_url = [
        'https://www.nytimes.com/section/technology',
        'https://cn.nytimes.com/technology/',
        'https://cn.nytimes.com/bits/',
        'https://cn.nytimes.com/personal-tech/'
    ]
    robots_url = 'https://www.nytimes.com/robots.txt'

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)
        for suffix in self.blacklist_suffix:
            self.blacklist_regex.append('http[s]?://(.*)\{}(.*)'.format(suffix))

    def extract_content(self):
        # Override for chinese support
        if tldextract.extract(self.url).subdomain == 'cn':
            article = self.parsed_lxml.find('.//section[@class="article-body"]')
            if article is not None:
                figures = article.findall('.//figure')
                for figure in figures:
                    figure.getparent().remove(figure)
                article_content = article.findall('.//div[@class="article-paragraph"]')
                article_content = [content.text.strip() for content in article_content if content.text and content.text.strip()]
                article_content = '\n\n'.join(article_content)
                if not len(article_content) <= 50: # Length enforcement
                    self.text = article_content
                    self.has_content = True
        elif self.valid_url:
            if self.text and '\n\nAdvertisement' in self.text:
                self.text = self.text.replace('\n\nAdvertisement', '')
                self.has_content = True