from .routes import *
from flask import Flask
from flask_session import Session
from os import urandom
from redis import Redis
from werkzeug.routing import BaseConverter

__all__ = ['app']

class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super().__init__(url_map)
        self.regex = items[0]

app = Flask(__name__)

# Configurations
#app.config['SESSION_TYPE'] = 'redis'
#app.config['SESSION_REDIS'] = Redis('redis')
app.config['SECRET_KEY'] = urandom(32)
app.config['ERROR_404_HELP'] = False
app.config['RESTX_VALIDATE'] = True

# Custom converters
app.url_map.converters['regex'] = RegexConverter

# API registrations
app.register_blueprint(api_v1)

# Session app
Session(app)