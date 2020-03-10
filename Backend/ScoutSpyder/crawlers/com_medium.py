from ScoutSpyder.crawlers.base_crawler import *
from ScoutSpyder.utils.helper import *
from ScoutSpyder.utils.logging import initialise_logging
from time import sleep

LOGGER = initialise_logging(__name__)

class MediumCrawler(BaseCrawler):
    crawler_id = 'com.medium'
    requests_per_sec = 1
    start_url = [
        'https://medium.com/topic/artificial-intelligence',
        'https://medium.com/topic/blockchain',
        'https://medium.com/topic/cybersecurity',
        'https://medium.com/topic/machine-learning'
    ]
    cookies_url = ['https://medium.com']
    fqdns_in_scope = [
        'onezero.medium.com',
        'www.towardsdatascience.com',
        'codeburst.io'
    ]

    def __init__(self, downloaded_doc=None):
        super().__init__(downloaded_doc)
        self.blacklist_suffix += [
            '&quot;);',
            ')'
        ]
        self.blacklist_regex = [
            'http[s]?://medium.com/m/signout/(.*)'
        ]

    def signin(self, browser):
        """
        Returns `True` on successful login, otherwise returns `False`
        """
        auth_link = get_env('COM_MEDIUM_AUTH_LINK')
        if auth_link == 'COM_MEDIUM_AUTHED':
            return True
        elif not auth_link:
            return False
        browser.get(get_env('COM_MEDIUM_AUTH_LINK'))
        if not browser.get_cookies():
            return False
        return True
    
    def extract_content(self):
        article = self.soup.find('article')
        if article and self.valid_body:
            self.has_content = True