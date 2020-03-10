from .crawler import api as crawler
from flask import Blueprint
from flask_restx import Api

__all__ = ['blueprint']

blueprint = Blueprint('api-v1', __name__, url_prefix='/api/v1')
api_v1 = Api(
    blueprint,
    title='ScoutSpyder API v1',
    version='1.0',
)

# Apply mediatype
@blueprint.after_request
def apply_header(response):
    response.headers['Content-Type'] = 'application/vnd.ScoutSpyder.v1+json'
    return response

# Initialise endpoints
api_v1.add_namespace(crawler)