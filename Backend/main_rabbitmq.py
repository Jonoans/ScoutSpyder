from ScoutSpyder.rabbitmq import *
from ScoutSpyder.utils.logging import initialise_logging
from os import environ
import json
import pika
import signal
import subprocess

LOGGER = initialise_logging('ScoutSpyder.rabbitmq')

def signal_handler(signal, frame):
    LOGGER.info('Terminating...')
    rabbitmq_conn_kill()

def setup_signal_handler():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def start_crawler(channel, method_frame, header_frame, body):
    body = json.loads(body)
    crawl_id = body.get('crawl_id')
    duration = body.get('duration')
    environments = body.get('environments')
    activated_crawlers = body.get('activatedCrawlers')
    env_vars = environ.copy()
    for env in environments:
        env_vars.update( { env.get('name'): env.get('value') } )
    
    if activated_crawlers:
        activated_crawlers = ', '.join(activated_crawlers)
        subprocess.Popen(f'python main.py -id {crawl_id} -d {duration} -c "{activated_crawlers}"', start_new_session=True, env=env_vars, shell=True)
    else:
        subprocess.Popen(f'python main.py -id {crawl_id} -d {duration}', start_new_session=True, env=env_vars, shell=True)

    channel.basic_ack(method_frame.delivery_tag)

def main():
    queue_to_func = [
        {'queue': 'worker.start_crawler', 'function': start_crawler}
    ]
    LOGGER.info('Starting consumption loop...')
    start_consumption_loop(queue_to_func)

if __name__ == '__main__':
    LOGGER.info('Starting worker process...')
    setup_signal_handler()
    rabbitmq_conn_init()
    main()