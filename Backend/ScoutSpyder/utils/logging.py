import logging
import logging.config
import os
import yaml

__all__ = ['initialise_logging']

def initialise_logging(name):
    with open( os.path.join('..', 'logging.yaml') , 'r') as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)
    return logging.getLogger(name)