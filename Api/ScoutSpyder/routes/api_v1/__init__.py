from .crawler import app as crawlerApi
from fastapi import FastAPI

app = FastAPI()

app.mount('/crawler', crawlerApi)