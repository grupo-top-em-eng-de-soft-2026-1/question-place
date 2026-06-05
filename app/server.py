from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import app.routers as routers
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(routers.main_router)

app.include_router(routers.auth_router)

app.include_router(routers.user_router)
