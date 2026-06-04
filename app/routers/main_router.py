from fastapi import APIRouter, Request
from app.config import templater

main_router = APIRouter()

@main_router.get("/")
async def home(request: Request):
    return templater.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "message": "lol"
        }
    )