from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import app.routers as routers

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(routers.main_router)