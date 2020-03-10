from .com_medium import MediumCrawler
from .com_nytimes import NewYorkTimesCrawler
from .com_pastebin import PastebinCrawler
from .com_washingtonpost import WashingtonPostCrawler
from .io_polyswarm_blog import PolyswarmBlogCrawler

__all__ = ['EXPORTED_CRAWLERS']

ENABLED_CRAWLERS = [
    MediumCrawler,
    NewYorkTimesCrawler,
    PastebinCrawler,
    WashingtonPostCrawler,
    PolyswarmBlogCrawler
]

EXPORTED_CRAWLERS = {}
def export_crawlers(crawlers=ENABLED_CRAWLERS):
    global EXPORTED_CRAWLERS
    for crawler in crawlers:
        EXPORTED_CRAWLERS[crawler.crawler_id] = crawler

export_crawlers()