from fastapi import FastAPI
from . import routes

app = FastAPI()

app.include_router(routes.router)
