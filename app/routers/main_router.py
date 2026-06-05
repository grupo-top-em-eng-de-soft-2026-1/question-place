from fastapi import APIRouter, Request
from app.config import templater

main_router = APIRouter()

@main_router.get("/")
async def login(request: Request):
    return templater.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@main_router.get("/cadastro")
async def register(request: Request):
    return templater.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )