from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from os import urandom
from typing import List, Optional
from uuid import UUID
import os
import subprocess

app = FastAPI()

class EnvironmentVariable(BaseModel):
    name: str
    value: str

class ManageParameters(BaseModel):
    duration: float
    environments: Optional[List[EnvironmentVariable]] = []
    activated_crawlers: Optional[List[str]] = []

@app.post('/manage')
def manage(body: ManageParameters):
    body = jsonable_encoder(body)
    duration = body.get('duration')
    environments = body.get('environments')
    activated_crawlers = body.get('activatedCrawlers')
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