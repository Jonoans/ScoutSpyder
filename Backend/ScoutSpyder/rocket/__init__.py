from ScoutSpyder.utils.configuration import get_config
from contextlib import contextmanager
from rocketmq.client import Message, Producer, PushConsumer
from threading import Lock
import json

__all__ = ['init_producer', 'init_push_consumer', 'oneway_publish']
config = get_config()
PROD_MUTEXES_MU = Lock()
PROD_MUTEXES = {}
PARSED_NS = None

def get_nameservers():
    global PARSED_NS
    if PARSED_NS == None:
        name_servers = config['ROCKETMQ']['NameServers'].split(',')
        ports = config['ROCKETMQ']['NameServerPorts'].split(',')

        if len(name_servers) != len(ports):
            raise ValueError('Number of RocketMQ NameServers != Number of NameServerPorts')

        for port in ports:
            port = int(port)
            if port <= 0 or port > 65535:
                raise ValueError(f'Invalid port number <{port}>')

        name_servers = [i.strip() for i in name_servers]
        ports = [i.strip() for i in ports]

        PARSED_NS = []
        for i, ns in enumerate(name_servers):
            PARSED_NS.append(f'{ns}:{ports[i]}')
    return ','.join(PARSED_NS) if type(PARSED_NS) == list else None

@contextmanager
def init_producer(group_id, orderly=True):
    ns = get_nameservers()
    producer = Producer(group_id, orderly)
    producer.set_name_server_address(ns)

    with PROD_MUTEXES_MU:
        mutex = PROD_MUTEXES.get(group_id)
        if not mutex:
            mutex = Lock()
            PROD_MUTEXES[group_id] = mutex

    with mutex:
        producer.start()
        yield producer
        producer.shutdown()

def oneway_publish(topic, body, subtopic=None, orderly=True, group_id='crawler'):
    body = json.dumps(body)
    message = Message(topic)
    message.set_body(body)
    if subtopic:
        message.set_tags(subtopic)

    with init_producer(group_id, orderly) as producer:
        producer.send_oneway(message)

def init_push_consumer(group_id, orderly=True):
    ns = get_nameservers()
    consumer = PushConsumer(group_id, orderly)
    consumer.set_name_server_address(ns)
    return consumer