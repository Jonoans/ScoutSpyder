from .com_channelnewsasia import ChannelNewsAsiaCrawler
from .com_darkreading import DarkReadingCrawler
from .com_medium import MediumCrawler
from .com_nytimes import NewYorkTimesCrawler
from .com_pastebin import PastebinCrawler
from .com_thehackernews import TheHackerNewsCrawler
from .com_threatpost import ThreatpostCrawler
from .com_washingtonpost import WashingtonPostCrawler

__all__ = ['EXPORTED_CRAWLERS']

ENABLED_CRAWLERS = [
    ChannelNewsAsiaCrawler,
    DarkReadingCrawler,
    MediumCrawler,
    NewYorkTimesCrawler,
    PastebinCrawler,
    TheHackerNewsCrawler,
    ThreatpostCrawler,
    WashingtonPostCrawler
]

EXPORTED_CRAWLERS = {}
def export_crawlers(crawlers=ENABLED_CRAWLERS):
    global EXPORTED_CRAWLERS
    for crawler in crawlers:
        EXPORTED_CRAWLERS[crawler.crawler_id] = crawler

export_crawlers()