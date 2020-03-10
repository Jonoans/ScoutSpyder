from .crawled_doc import CrawledDocument
from .downloaded_doc import DownloadedDocument
from .queued_link import QueuedLink
from ScoutSpyder.utils.configuration import *
import mongoengine

__all__ = [
    'db_conn_init',
    'db_conn_kill',
    'CrawledDocument',
    'DownloadedDocument',
    'QueuedLink'
]

def db_conn_init():
    config = get_config()
    name = config['DATABASE']['Name']
    host = config['DATABASE']['Host']
    port = int(config['DATABASE']['Port'])

    # Register connection
    mongoengine.register_connection(
        alias='global', name=name,
        host=host, port=port
    )

def db_conn_kill():
    mongoengine.disconnect_all()