from ScoutSpyder.crawlers import *
from ScoutSpyder.models import *
from ScoutSpyder.processes import *
from ScoutSpyder.rocket import oneway_publish
from ScoutSpyder.utils.configuration import *
from ScoutSpyder.utils.logging import *
from ScoutSpyder.utils.patcher import patch_autoproxy
from mongoengine.errors import NotUniqueError
from multiprocessing import Manager
from os import urandom
from selenium.webdriver import Chrome, ChromeOptions, Remote
from time import sleep
from urllib.robotparser import RobotFileParser
from uuid import UUID
import argparse
import tldextract

__all__ = ['start_crawler']

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
    parser = argparse.ArgumentParser(description='ScoutSpyder Crawler')
    parser.add_argument(
        '-t', '--type', type=str, choices=['manual', 'scheduled'], default='manual',
        help='Type of crawl, manual or scheduled'
    )
    parser.add_argument(
        '-d', '--duration', type=float, required=True,
        help='Duration of crawl in minutes'
    )
    parser.add_argument(
        '-id', '--identifier', type=str,
        help='A valid UUID value to be used as the identifier for the current crawl session'
    )
    parser.add_argument(
        '-c', '--crawlers', type=str,
        help='Identifier of crawlers to run in a comma-separated string'
    )
    args = parser.parse_args()
    return args

def init_crawl_id():
    try:
        crawl_id = UUID(ARGS.identifier) if ARGS.identifier else UUID(bytes=urandom(16), version=4)
    except ValueError:
        LOGGER.warn(f'Invalid identifier value "{ARGS.identifier}" provided, autogenerating instead!')
        crawl_id = UUID(bytes=urandom(16), version=4)
    return crawl_id

def init_enabled_crawlers():
    if ARGS.crawlers:
        enabled_crawlers = []
        enabled_crawler_ids = [_id.strip() for _id in ARGS.crawlers.split(',')]
        for _id in enabled_crawler_ids:
            Crawler = EXPORTED_CRAWLERS.get(_id)
            if Crawler:
                enabled_crawlers.append( Crawler() )
        return enabled_crawlers
    else:
        return [crawler() for crawler in EXPORTED_CRAWLERS.values()]

def save_queued_link(queued_link):
    try:
        queued_link.save()
    except NotUniqueError:
        pass

def prepare_queued_link(crawler, url):
    queued_link = QueuedLink()
    queued_link.crawl_id = crawler.crawl_id
    queued_link.fqdn = tldextract.extract(url).fqdn
    queued_link.url = url
    queued_link.depth = crawler.depth
    queued_link.depth_limit = crawler.depth_limit
    return queued_link

def add_queued_links(crawler):
    for link in [crawler.url] + crawler.decomposed_urls:
        queued_link = prepare_queued_link(crawler, link)
        save_queued_link(queued_link)

def start_crawler(master_browser=initialise_remote_browser,
    child_browser=initialise_remote_browser):
    global ARGS
    ######################################################
    # Attaining arguments and configurations for crawler #
    ######################################################
    LOGGER.info('Reading arguments and configurations for crawl session...')
    ARGS = read_arguments()
    config = get_config()
    downloader_count = int(config['MULTIPROCESSING']['Downloaders'])
    extractor_count = int(config['MULTIPROCESSING']['Extractors'])
    crawl_id = init_crawl_id()
    crawlers = init_enabled_crawlers()

    # Validate configurations
    if downloader_count <= 0 or extractor_count <= 0:
        LOGGER.error('Number of processes should be more than 0!')
        raise ValueError('Number of processes should be more than 0!')
        return
    if not crawlers:
        LOGGER.error('No crawlers enabled, ending crawl...')
        return
    LOGGER.info('Arguments and configurations initialised!')

    notification = {
        'crawl_id': crawl_id.hex,
        'type': ARGS.type
    }
    oneway_publish('crawler', notification, 'crawler.event.start')
    #######################################################
    # Initialise sessions needed for authenticated crawls #
    #######################################################
    LOGGER.info('Preparing sessions for authenticated crawls...')
    browser = master_browser()
    # Get cookies for crawlers
    cookies = {}
    try:
        for crawler in crawlers:
            if crawler.signin(browser):
                sleep(3) # Quick hack: Wait for all activities on browser to complete
                auth_cookies = crawler.extract_auth_cookies(browser)
                for key in auth_cookies.keys():
                    cookies[key] = auth_cookies[key]
        browser.close()
        browser.quit()
    except Exception as e:
        raise e
    LOGGER.info('Sessions for authenticated crawls prepared!')

    #############################
    # Preparing crawl processes #
    #############################
    LOGGER.info('Initialising processes and variables for crawl session...')
    try:
        patch_autoproxy()

        ## MANAGER START ##
        manager = Manager()

        fqdn_metadata = manager.dict()
        rate_limiters = manager.dict()
        db_conn_init()
        for crawler in crawlers:
            # Add to queued links
            crawler.crawl_id = crawl_id.hex
            add_queued_links(crawler)

            for fqdn in crawler.fqdns_in_scope:
                # Initialise variables
                fqdn_metadata[fqdn] = manager.dict({
                    'class': crawler.__class__,
                    'robots_txt': None
                })

                rate_limiters[fqdn] = manager.Event()

                if crawler.fqdn == fqdn:
                    if crawler.robots_url:
                        robots = RobotFileParser(crawler.robots_url)
                        robots.read()
                        fqdn_metadata[fqdn]['robots_txt'] = robots

                # Initialise rate limiters
                rl = RateLimiterThread(crawler.requests_per_sec, rate_limiters[fqdn])
                rl.daemon = True
                rl.start()
        db_conn_kill()
        
        # Synchronisation events
        start_event = manager.Event()
        terminate_event = manager.Event()

        # Processes
        downloader_procs = []
        for _ in range(downloader_count):
            downloader = Downloader(crawl_id, child_browser, terminate_event,
                cookies, fqdn_metadata, rate_limiters)
            downloader.start()
            downloader_procs.append(downloader)
        
        extractor_procs = []
        for _ in range(extractor_count):
            extractor = Extractor(crawl_id, start_event,
                terminate_event, fqdn_metadata)
            extractor.start()
            extractor_procs.append(extractor)
        
        for downloader in downloader_procs:
            downloader.browser_started.wait()
        
        processes = downloader_procs + extractor_procs
    except Exception as e:
        raise e
    LOGGER.info('Processes and variables initialised for crawl session!')

    ##########################################
    # Start crawl and sleep until time is up #
    ##########################################
    LOGGER.info(f'Crawl {crawl_id.hex} starting, come back in {ARGS.duration} minute(s)!')
    start_event.set()
    sleep(ARGS.duration * 60)
    terminate_event.set()
    LOGGER.info(f'Crawl {crawl_id.hex} completed! Cleaning up...')

    ##########################################
    # Clean up and wait for processes to end #
    ##########################################
    # Give processes time to finish
    sleep(15)
    
    # Clean up database
    db_conn_init()
    DownloadedDocument.objects(crawl_id=crawl_id.hex).delete()
    QueuedLink.objects(crawl_id=crawl_id.hex).delete()
    db_conn_kill()

    # Forcefully terminate if required
    forceful_terminations = 0
    for process in processes:
        try:
            process.browser.quit()
            process.browser.close()
        except:
            pass
        if process.is_alive():
            forceful_terminations += 1
            process.terminate()
        process.join()
        process.close()
    LOGGER.info(f'{forceful_terminations} process(es) had to be forcefully terminated.')

    oneway_publish('crawler', notification, 'crawler.event.end')