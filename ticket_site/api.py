import sqlite3

import os
from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from .ParsedTicket import ParsedTicket, TicketHeader

db: sqlite3.Cursor

router = APIRouter()
templates = Jinja2Templates(directory="ticket_site/templates")


cache = {}


@router.get("/")
@router.get("/tickets")
async def root(request: Request):
    # logged in check
    # else login with discord
    resp = db.execute("SELECT * FROM tickets").fetchall()
    ticket_headers = [TicketHeader(i) for i in resp]

    context = {"request": request, "tickets": ticket_headers}

    return templates.TemplateResponse(name="template.html", context=context)


@router.get("/tickets/{ticket}")
async def tickets(request: Request, ticket: int):

    resp = db.execute("SELECT * FROM tickets").fetchall()
    ticket_headers = [TicketHeader(i) for i in resp]

    ticket = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket,)).fetchone()
    if ticket is None:
        return templates.TemplateResponse(name="404.html", context={"request": request})

    if ticket["id"] not in cache:
        cache[ticket["id"]] = ParsedTicket(ticket, db)
    context = {"request": request, "tickets": ticket_headers, "ticket": cache[ticket["id"]]}
    return templates.TemplateResponse(name="template.html", context=context)
