from ScoutSpyder.crawlers import *
from ScoutSpyder.models import *
from ScoutSpyder.utils.configuration import *
from ScoutSpyder.utils.logging import *
from collections import namedtuple
from os import urandom
from selenium.webdriver import Chrome, ChromeOptions, Remote
from string import hexdigits
from time import sleep
from urllib.robotparser import RobotFileParser
from uuid import UUID
import argparse
import tldextract

LOGGER = initialise_logging(__name__)
ARGS = None
REMOTE_URL = 'http://selenium:4444/wd/hub'
EXP_OPTIONS = {
    'profile.default_content_setting_values': {
        'images': 2, 'plugins': 2, 'popups': 2, 'geolocation': 2, 'notifications': 2,
        'auto_select_certificate': 2, 'fullscreen': 2, 'mouselock': 2, 'media_stream': 2,
        'media_stream_mic': 2, 'media_stream_camera': 2, 'protocol_handlers': 2, 'ppapi_broker': 2,
        'automatic_downloads': 2, 'midi_sysex': 2, 'push_messaging': 2, 'ssl_cert_decisions': 2,
        'metro_switch_to_desktop': 2, 'protected_media_identifier': 2, 'app_banner': 2, 
        'site_engagement': 2, 'durable_storage': 2, 'mixed_script': 2
    }
}

def initialise_remote_browser():
    config = get_config()
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument('--user-agent={}'.format(config['SELENIUM']['UserAgent']))
    options.add_experimental_option('prefs', EXP_OPTIONS)
    browser = Remote(REMOTE_URL, keep_alive=True, options=options)
    return browser

def initialise_master_browser():
    config = get_config()
    options = ChromeOptions()
    options.add_argument('--disable-logging')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument('--user-agent={}'.format(config['SELENIUM']['UserAgent']))
    options.add_argument("--user-data-dir=browser-store") # Session persistance
    browser = Chrome(config['SELENIUM']['Path'], options=options, service_log_path='NUL')
    browser.set_window_position(0, 0)
    browser.set_window_size(1920, 1080)
    return browser

def initialise_child_browser(headless=True):
    config = get_config()
    options = ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument('--user-agent={}'.format(config['SELENIUM']['UserAgent']))
    browser = Chrome(config['SELENIUM']['Path'], options=options, service_log_path='NUL')
    return browser

def read_arguments():
    parser = argparse.ArgumentParser(description='ScoutSpyder Single Crawler')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-u', '--url', type=str, help='URL of page to crawl'
    )
    group.add_argument(
        '-i', '--id', type=str, help='ID of crawled document in database to crawl and update'
    )
    args = parser.parse_args()
    return args

def init_crawlers():
    return [crawler() for crawler in EXPORTED_CRAWLERS.values()]

def navigate(browser, url):
    try:
        browser.get(url)
    except Exception:
        return False
    return True

def start_crawler(child_browser=initialise_remote_browser):
    global ARGS
    ###########################################################
    # Attaining arguments and configurations for single crawl #
    ###########################################################
    LOGGER.info('Reading arguments and configurations for single crawl...')
    ARGS = read_arguments()
    LOGGER.info('Arguments and configurations initialised!')

    url = None
    if ARGS.id:
        db_conn_init()
        crawled_doc = CrawledDocument.objects(uuid=ARGS.id).first()
        db_conn_kill()
        if not crawled_doc:
            LOGGER.info(f'Document {ARGS.id} not found, terminating...')
            return
        url = crawled_doc.url
    else:
        url = ARGS.url

    fqdn = tldextract.extract(url).fqdn

    found_crawler = None
    for crawler in init_crawlers():
        if fqdn in crawler.fqdns_in_scope:
            found_crawler = crawler
            break
    
    if not found_crawler:
        LOGGER.info('No matching crawler found, terminating...')
        return
    
    LOGGER.info('Preparing session for authenticated crawl...')
    browser = child_browser()
    try:
        cookies = {}
        try:
            if crawler.signin(browser):
                sleep(3)
                auth_cookies = crawler.extract_auth_cookies(browser)
                for key in auth_cookies.keys():
                    cookies[key] = auth_cookies[key]
        except Exception as e:
            raise e
        LOGGER.info('Session for authenticated crawl prepared!')

        if crawler.robots_url:
            robots = RobotFileParser(crawler.robots_url)
            robots.read()
            if not robots.can_fetch('Googlebot', url):
                LOGGER.info(f'Link {url} cannot be crawled according to the site\'s robots.txt, terminating...')
                return

        if not navigate(browser, url):
            LOGGER.info(f'Single crawl for {url} failed, terminating...')
            return
        
        uuid = UUID(bytes=urandom(16), version=4)
        downloaded_doc = DownloadedDocument()
        downloaded_doc.html = browser.page_source
        downloaded_doc.crawl_id = uuid.hex
        downloaded_doc.fqdn = fqdn
        downloaded_doc.url = url
        downloaded_doc.depth = 0
        downloaded_doc.depth_limit = 0
        crawler = found_crawler.__class__(downloaded_doc)
        crawler.scrap()
        new_doc = crawler.prepare_db_entries()
        
        db_conn_init()
        if ARGS.id:
            crawled_doc.html = new_doc.html
            crawled_doc.authors = new_doc.authors
            crawled_doc.title = new_doc.title
            crawled_doc.text = new_doc.text
            crawled_doc.publish_date = new_doc.publish_date
            crawled_doc.save()
            LOGGER.info(f'Updated: {url}')
            db_conn_kill()
            return
        
        existing = CrawledDocument.objects(url=url).first()
        if existing:
            existing.delete()
        new_doc.save()
        db_conn_kill()
        LOGGER.info(f'Scrapped: {url}')
    finally:
        browser.close()
        browser.quit()