from fastapi import FastAPI
import app.routers as routers

app = FastAPI()

app.include_router(routers.main_router)