from ScoutSpyder.crawlers import *
from ScoutSpyder.models import *
from ScoutSpyder.utils.logging import *
from ScoutSpyder.utils.patcher import patch_autoproxy
from datetime import datetime
from mongoengine.errors import NotUniqueError
from multiprocessing import Process

LOGGER = initialise_logging(__name__)

class Extractor(Process):
    def __init__(self, crawl_id, start_event, terminate_time, fqdn_metadata):
        super().__init__()
        self.crawl_id = crawl_id.hex
        self.start_event = start_event
        self.terminate_time = terminate_time
        self.fqdn_metadata = fqdn_metadata
    
    def init_crawler(self, downloaded_doc):
        Crawler = self.fqdn_metadata[downloaded_doc.fqdn]['class']
        return Crawler(downloaded_doc)
    
    def timeup(self):
        return self.terminate_time <= datetime.now()
    
    def main(self):
        fqdns = self.fqdn_metadata.keys()
        while not self.timeup():
            for fqdn in fqdns:
                if self.timeup():
                    break

                downloaded_doc = DownloadedDocument \
                    .objects(crawl_id=self.crawl_id, fqdn=fqdn).first()
                if not downloaded_doc:
                    continue
                deleted = DownloadedDocument.objects(pk=downloaded_doc.pk).delete()
                if deleted <= 0:
                    continue

                crawler = None
                try:
                    crawler = self.init_crawler(downloaded_doc)
                    crawler.scrap()
                    crawler.post_scrap()
                    LOGGER.info(f'Processed: {crawler.url}')
                except Exception as e:
                    LOGGER.exception(f'Error: {downloaded_doc.resolved_url}')
                del crawler, deleted, downloaded_doc
    
    def run(self):
        patch_autoproxy()
        db_conn_init()
        self.start_event.wait()
        self.main()
        db_conn_kill()