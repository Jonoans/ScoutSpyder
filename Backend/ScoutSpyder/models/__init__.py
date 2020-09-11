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
    username = config['DATABASE'].get('username')
    if username:
        username = username.strip() if username.strip() else None
    password = config['DATABASE'].get('password')
    if password:
        password = password.strip() if username and password.strip() else None
    tls = config['DATABASE'].getboolean('TlsEnabled', fallback=False)
    tls_ca_file = config['DATABASE'].get('TlsCaCertificate') if tls else None

    args = {
        'alias': 'global',
        'name': name,
        'host': host,
        'port': port,
        'username': username,
        'password': password,
        'tls': tls,
        'tlsCAFile': tls_ca_file
    }

    # Register connection
    mongoengine.register_connection(**args)

def db_conn_kill():
    mongoengine.disconnect_all()