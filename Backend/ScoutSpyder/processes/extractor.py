from ScoutSpyder.crawlers import *
from ScoutSpyder.models import *
from ScoutSpyder.utils.logging import *
from ScoutSpyder.utils.patcher import patch_autoproxy
from mongoengine.errors import NotUniqueError
from multiprocessing import Process

LOGGER = initialise_logging(__name__)

class Extractor(Process):
    def __init__(self, crawl_id, start_event,
        terminate_event, fqdn_metadata, query_lock):
        super().__init__()
        self.crawl_id = crawl_id.hex
        self.start_event = start_event
        self.terminate_event = terminate_event
        self.fqdn_metadata = fqdn_metadata
        self.query_lock = query_lock
    
    def init_crawler(self, downloaded_doc):
        Crawler = self.fqdn_metadata[downloaded_doc.fqdn]['class']
        return Crawler(downloaded_doc)
    
    def prepare_crawled_doc(self, crawler):
        crawled_doc = CrawledDocument()
        crawled_doc.crawl_id = crawler.crawl_id
        crawled_doc.fqdn = crawler.fqdn
        crawled_doc.html = crawler.html
        crawled_doc.url = crawler.url
        if crawler.has_content:
            crawled_doc.authors = crawler.authors
            crawled_doc.title = crawler.title
            crawled_doc.text = crawler.text
        if crawler.has_date:
            crawled_doc.publish_date = crawler.publish_date
        return crawled_doc
    
    def save_crawled_doc(self, crawled_doc):
        try:
            crawled_doc.save()
        except NotUniqueError:
            return False
        return True
    
    def main(self):
        fqdns = self.fqdn_metadata.keys()
        while not self.terminate_event.is_set():
            for fqdn in fqdns:
                if self.terminate_event.is_set():
                    break

                with self.query_lock:
                    downloaded_doc = DownloadedDocument \
                        .objects(crawl_id=self.crawl_id, fqdn=fqdn).first()
                    if not downloaded_doc:
                        continue
                    downloaded_doc.delete()
                
                crawler = self.init_crawler(downloaded_doc)
                crawler.scrap()
                LOGGER.info(f'Processed: {crawler.url}')
                crawled_doc = self.prepare_crawled_doc(crawler)
                if self.save_crawled_doc(crawled_doc):
                    LOGGER.info(f'Scrapped: {crawled_doc.url}')
                del crawler, crawled_doc
    
    def run(self):
        patch_autoproxy()
        db_conn_init()
        self.start_event.wait()
        self.main()
        db_conn_kill()