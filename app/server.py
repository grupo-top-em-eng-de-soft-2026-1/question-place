import app.config

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import app.routers as routers
from app.database import Base, engine
from app.models.media import MediaObject

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Question Place",
    docs_url= app.config.ENV_DOCS_URL,
    redoc_url= app.config.ENV_REDOC_URL,
    openapi_url= app.config.ENV_OPENAPI_URL
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(routers.main_router)

app.include_router(routers.auth_router)

app.include_router(routers.user_router)
app.include_router(routers.media_router)
