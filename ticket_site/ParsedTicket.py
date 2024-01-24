import base64

import sqlite3

import re
from datetime import datetime


class ParsedTicket:
    def __init__(self, ticket: dict, db: sqlite3.Cursor):
        self.db = db
        self.ticket = ticket
        self.author = None
        self.id = None
        self.timestamp = None
        self.messages = []
        self.parse()

    def parse(self):
        messages = self.db.execute("SELECT * FROM messages WHERE ticket_id = ?", (self.ticket["id"],)).fetchall()
        for message in messages:
            attachments = self.db.execute("SELECT * FROM attachments WHERE message_id = ?", (message["id"],)).fetchall()
            self.messages.append(Message(message, attachments, self.db))

    def __iter__(self):
        return iter(self.messages)


class Message:
    def __init__(self, message: dict, attachments: list[dict], db):
        self.db = db
        self.message = message
        self.attachment_list = attachments
        self.avatar = None
        self.author = None
        self.id = None
        self.content = None
        self.attachments = []
        self.time = None
        self.parse()

    def parse(self):
        print(self.message["author"])
        pfp = self.db.execute("SELECT data FROM pfps WHERE id = ?", (self.message["author_id"],)).fetchone()
        if pfp is None:
            pfp = self.db.execute("SELECT data FROM pfps WHERE username = ?", (self.message["author"],)).fetchone()
        self.avatar = base64.b64encode(pfp["data"]).decode()

        self.author = self.message["author"]
        self.id = self.message["author_id"]
        self.content = self.message["content"]
        for i in self.attachment_list:
            self.attachments.append((i["name"], base64.b64encode(i["data"]).decode()))
        self.time = datetime.fromtimestamp(self.message["time"]).strftime("%-m/%d/%y, %-I:%M %p")


class TicketHeader:
    def __init__(self, row: dict):
        self.author = row["creator_name"]
        self.id = row["id"]
        self.timestamp = datetime.fromtimestamp(row["creation_time"]).strftime("%-m/%d/%y, %-I:%M %p")