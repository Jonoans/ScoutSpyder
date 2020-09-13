from ScoutSpyder.utils.configuration import get_config
from ScoutSpyder.utils.logging import initialise_logging
import json
import pika

__all__ = [
    'rabbitmq_conn_init',
    'rabbitmq_conn_kill',
    'persistent_pub',
    'start_consumption_loop'
]

LOGGER = initialise_logging(__name__)
connection, channel, parameters = None, None, None
MESSAGE_PROPS = pika.BasicProperties(delivery_mode=2)
EXCHANGES = [
    {'name': 'start_crawler', 'type': 'fanout'}
]
QUEUES = [
    {'name': 'worker.start_crawler', 'exchange': 'start_crawler'}
]

def start_consumption_loop(queue_func_mappings):
    while True:
        try:
            for mapping in queue_func_mappings:
                def wrapped_function(*args, **kwargs):
                    try: 
                        mapping['function'](*args, **kwargs)
                    except Exception as error:
                        queue_name = mapping['queue']
                        LOGGER.exception(f'Error in function for queue: {queue_name}')
                channel.basic_consume(mapping['queue'], wrapped_function)
            channel.start_consuming()
        except (pika.exceptions.ConnectionClosedByBroker, pika.exceptions.AMQPConnectionError):
            create_connection()

def persistent_pub(exchange, message, routing_key=''):
    try:
        channel.basic_publish(exchange, routing_key, json.dumps(message), MESSAGE_PROPS)
    except (pika.exceptions.ConnectionClosedByBroker, pika.exceptions.AMQPConnectionError):
        create_connection()
        channel.basic_publish(exchange, routing_key, json.dumps(message), MESSAGE_PROPS)

def create_connection():
    global connection, channel
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

def rabbitmq_conn_init():
    global parameters
    config = get_config()
    host = config['RABBITMQ']['Host']
    port = config['RABBITMQ']['Port']
    username = config['RABBITMQ'].get('username')
    username = username.strip() if username else None
    password = config['RABBITMQ'].get('password')
    password = password.strip() if password else None
    credentials = pika.PlainCredentials(username, password) if username and password else None
    parameters = pika.ConnectionParameters(host, port, credentials=credentials)
    create_connection()

    for exchange in EXCHANGES:
        channel.exchange_declare(exchange['name'], exchange['type'], durable=True)

    for queue in QUEUES:
        channel.queue_declare(queue['name'], durable=True)
        channel.queue_bind(queue['name'], queue['exchange'])

def rabbitmq_conn_kill():
    channel.stop_consuming()
    connection.close()