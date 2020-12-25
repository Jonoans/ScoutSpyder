from ScoutSpyder.rocket import init_push_consumer
from ScoutSpyder.utils.logging import initialise_logging
from os import environ
from rocketmq.client import ConsumeStatus
from time import sleep
import json
import signal
import subprocess

LOGGER = initialise_logging('ScoutSpyder.rocket')
TERMINATED = False

def signal_handler(signal, frame):
    global TERMINATED
    LOGGER.info('Termination signal received...')
    TERMINATED = True

def setup_signal_handler():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def start_crawler(message):
    body = json.loads(message.body)
    type_ = body.get('type') or 'manual'
    crawl_id = body.get('crawl_id')
    duration = body.get('duration')
    environments = body.get('environments') or []
    activated_crawlers = body.get('activatedCrawlers') or []
    env_vars = environ.copy()
    for env in environments:
        env_vars.update( { env.get('name'): env.get('value') } )
    
    if activated_crawlers:
        activated_crawlers = ', '.join(activated_crawlers)
        subprocess.Popen(f'python main.py -id {crawl_id} -d {duration} -t {type_} -c "{activated_crawlers}"', start_new_session=True, env=env_vars, shell=True)
    else:
        subprocess.Popen(f'python main.py -id {crawl_id} -d {duration} -t {type_}', start_new_session=True, env=env_vars, shell=True)
    return ConsumeStatus.CONSUME_SUCCESS

def start_single_crawler(message):
    body = json.loads(message.body)
    article_id = body.get('article_id')
    subprocess.Popen(f'python main_single.py -i {article_id}', start_new_session=True, env=environ, shell=True)
    return ConsumeStatus.CONSUME_SUCCESS

# PushConsumer subscribe function memoization causes
# issues with have different callback functions
def start_callback(message):
    tag = message.tags.decode()
    if tag == 'crawler.cmd.start':
        return start_crawler(message)
    elif tag == 'crawler_single.cmd.start':
        return start_single_crawler(message)
    return ConsumeStatus.CONSUME_SUCCESS

def main():
    LOGGER.info('Starting worker process...')

    consumer = init_push_consumer('crawler')
    consumer.subscribe('crawler', start_callback, 'crawler.cmd.start')
    consumer.subscribe('crawler_single', start_callback, 'crawler_single.cmd.start')

    LOGGER.info('Starting consumption loop...')
    consumer.start()
    while not TERMINATED:
        sleep(15)
    LOGGER.info('Terminating...')
    consumer.shutdown()

if __name__ == '__main__':
    setup_signal_handler()
    main()