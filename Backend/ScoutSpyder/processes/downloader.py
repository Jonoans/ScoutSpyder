from ScoutSpyder.models import *
from ScoutSpyder.utils.logging import *
from ScoutSpyder.utils.patcher import patch_autoproxy
from mongoengine.errors import NotUniqueError
from multiprocessing import Event, Process
from selenium.common.exceptions import WebDriverException

LOGGER = initialise_logging(__name__)

class Downloader(Process):
    def __init__(self, crawl_id, init_browser, terminate_event,
        cookies, fqdn_metadata, rate_limiters, query_lock):
        super().__init__()
        self.crawl_id = crawl_id.hex
        self._init_browser = init_browser
        self.terminate_event = terminate_event
        self.cookies = cookies
        self.fqdn_metadata = fqdn_metadata
        self.rate_limiters = rate_limiters
        self.query_lock = query_lock
        self.browser_started = Event()
        self.browser = None
    
    def init_browser(self):
        browser = self._init_browser()
        for url, cookies in self.cookies.items():
            browser.get(url)
            for cookie in cookies:
                cookie.pop('expiry', None)
                browser.add_cookie(cookie)
        self.browser = browser
        self.browser_started.set()
    
    def navigate(self, url):
        try:
            self.browser.get(url)
        except Exception:
            return False
        return True
    
    def check_rate_limiter(self, fqdn):
        """Check if crawl is allowed by rate limiter

        [Returns]
            `True` if rate limiter allows, else `False`
        """
        return not self.rate_limiters[fqdn].is_set()

    def set_rate_limiter(self, fqdn):
        self.rate_limiters[fqdn].set()
    
    def prepare_downloaded_doc(self, queued_link):
        downloaded_doc = DownloadedDocument()
        downloaded_doc.html = self.browser.page_source
        downloaded_doc.crawl_id = queued_link.crawl_id
        downloaded_doc.fqdn = queued_link.fqdn
        downloaded_doc.url = queued_link.url
        downloaded_doc.depth = queued_link.depth
        downloaded_doc.depth_limit = queued_link.depth_limit
        downloaded_doc.resolved_url = self.browser.current_url
        return downloaded_doc
    
    def save_downloaded_doc(self, downloaded_doc):
        try:
            downloaded_doc.save()
        except NotUniqueError:
            return False
        return True
    
    def duplicate_found(self, url):
        return DownloadedDocument.objects(crawl_id=self.crawl_id, url=url).first()
    
    def main(self):
        fqdns = self.fqdn_metadata.keys()
        while not self.terminate_event.is_set():
            for fqdn in fqdns:
                if self.terminate_event.is_set():
                    break
                
                with self.query_lock:
                    queued_link = None
                    if self.check_rate_limiter(fqdn):
                        queued_link = QueuedLink.objects(crawl_id=self.crawl_id, fqdn=fqdn).first()
                    if not queued_link:
                        continue
                    queued_link.delete()
                    self.set_rate_limiter(fqdn)
                
                if self.duplicate_found(queued_link.url):
                    del queued_link
                    continue
                
                robots = self.fqdn_metadata[fqdn]['robots_txt']
                if robots:
                    if not robots.can_fetch('Googlebot', queued_link.url):
                        del queued_link, robots
                        continue
                
                if self.navigate(queued_link.url):
                    downloaded_doc = self.prepare_downloaded_doc(queued_link)
                    if self.save_downloaded_doc(downloaded_doc):
                        LOGGER.debug(f'Downloaded: {downloaded_doc.url}')
                    del downloaded_doc
                del queued_link, robots
    
    def clean_up(self):
        try:
            self.browser.close()
            self.browser.quit()
        except WebDriverException:
            pass

    def run(self):
        patch_autoproxy()
        db_conn_init()
        self.init_browser()
        self.main()
        self.clean_up()
        db_conn_kill()