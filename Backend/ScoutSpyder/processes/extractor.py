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

                crawler = None
                try:
                    crawler = self.init_crawler(downloaded_doc)
                    crawler.scrap()
                    crawler.post_scrap()
                    LOGGER.info(f'Processed: {crawler.url}')
                except Exception as e:
                    LOGGER.error(f'Error: {downloaded_doc.url}')
                del crawler, downloaded_doc
    
    def run(self):
        patch_autoproxy()
        db_conn_init()
        self.start_event.wait()
        self.main()
        db_conn_kill()