from fastapi import APIRouter, Request

from app.config import templater

main_router = APIRouter()


@main_router.get("/")
async def index_page(request: Request):
    return templater.TemplateResponse(request=request, name="index.html", context={})


@main_router.get("/login")
async def login_page(request: Request):
    return templater.TemplateResponse(request=request, name="login.html", context={})


@main_router.get("/register")
async def register_page(request: Request):
    return templater.TemplateResponse(request=request, name="register.html", context={})


@main_router.get("/me")
async def me_page(request: Request):
    return templater.TemplateResponse(
        request=request, name="me.html", context={}
    )


@main_router.get("/me/edit")
async def edit_profile_page(request: Request):
    return templater.TemplateResponse(
        request=request, name="edit_profile.html", context={}
    )
