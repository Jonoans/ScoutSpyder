from .routes import app as routes
from fastapi import FastAPI

__all__ = [
    'app'
]

app = FastAPI()
app.mount('/', routes)