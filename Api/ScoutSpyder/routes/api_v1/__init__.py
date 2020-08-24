from .crawler import app as crawler
from fastapi import FastAPI

app = FastAPI()

app.include_router(crawler, prefix='/crawler')