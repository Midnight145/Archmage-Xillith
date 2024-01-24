import os
import uvicorn

from fastapi import FastAPI, Request, APIRouter
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from .ParsedTicket import ParsedTicket

router = APIRouter()
templates = Jinja2Templates(directory="ticket_site/templates")


cache = {}


@router.get("/")
@router.get("/tickets")
async def root(request: Request):
    # logged in check
    # else login with discord

    files = [i for i in os.listdir("./tickets") if i.endswith(".txt")]
    ticket_files = []
    for i in files:
        parsed = ParsedTicket(i)
        cache[i] = parsed
        ticket_files.append(parsed)
    context = {"request": request, "files": ticket_files, "ticket": None}

    return templates.TemplateResponse(name="template.html", context=context)


@router.get("/tickets/{ticket}")
async def tickets(request: Request, ticket: str):
    files = [i for i in os.listdir("./tickets") if i.endswith(".txt")]
    parsed_tickets = []
    for i in files:
        if i in cache:
            parsed_tickets.append(cache[i])
        else:
            parsed = ParsedTicket(i)
            cache[i] = parsed
            parsed_tickets.append(parsed)
    if ticket not in files:
        return templates.TemplateResponse(name="404.html", context={"request": request})
    context = {"request": request, "files": parsed_tickets, "ticket": cache[ticket]}
    return templates.TemplateResponse(name="template.html", context=context)

