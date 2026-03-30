from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        name="dashboard.html",
        request=request,
        context={
            "request": request,
        })