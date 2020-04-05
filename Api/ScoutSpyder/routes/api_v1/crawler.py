from flask import request, session
from flask_restx import fields, Namespace, Resource
from flask_restx.errors import abort
from os import urandom
from uuid import UUID
import os
import subprocess

api = Namespace('crawler', description='Crawler management API')

##########
# Models #
##########
environments = api.model('Environments', {
    'name': fields.String(required=True),
    'value': fields.String(required=True)
})
start_crawl = api.model('StartCrawl', {
    'duration': fields.Integer(required=True),
    'environments': fields.Nested(environments, as_list=True),
    'activatedCrawlers': fields.List(fields.String)
})

##########
# Routes #
##########
@api.route('/manage')
class CrawlerManage(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Malformed request')
    @api.response(500, 'Unsupported platform')
    @api.expect(start_crawl)
    def post(self):
        body = request.get_json()
        duration = body.get('duration')
        environments = body.get('environments', [])
        activated_crawlers = body.get('activatedCrawlers', [])
        env_vars = os.environ.copy()
        for env in environments:
            env_vars.update( { env.get('name'): env.get('value') } )
        crawl_id = UUID(bytes=urandom(16), version=4)
        if activated_crawlers:
            activated_crawlers = ', '.join(activated_crawlers)
            subprocess.Popen(f'python main.py -id {crawl_id} -d {duration} -c "{activated_crawlers}"', cwd=os.path.join('..', 'Backend'), start_new_session=True, env=env_vars, shell=True)
        else:
            subprocess.Popen(f'python main.py -id {crawl_id} -d {duration}', cwd=os.path.join('..', 'Backend'), start_new_session=True, env=env_vars, shell=True)
        return {
            'status': 'Success',
            'crawl_id': crawl_id.hex
        }