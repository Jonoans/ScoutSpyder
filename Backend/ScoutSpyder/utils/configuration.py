import configparser
import os

__all__ = ['get_config']

CONFIG = None

def get_config():
    global CONFIG
    if not CONFIG:
        CONFIG = configparser.ConfigParser()
        read_files = CONFIG.read( os.path.join('..', 'config.ini') )
        if not os.path.join('..', 'config.ini') in read_files:
            raise Exception('Error parsing configuration file!')
    return CONFIG
