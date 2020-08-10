from .api_v1 import app as api_v1
from fastapi import FastAPI

app = FastAPI()

app.mount('/api/v1', api_v1)