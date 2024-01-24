import re
from datetime import datetime


class ParsedTicket:
    def __init__(self, ticket: str):
        self.ticket = ticket
        self.author = None
        self.id = None
        self.timestamp = None
        self.messages = []
        self.parse()

    def parse(self):
        with open(f"tickets/{self.ticket}") as f:
            lines = f.readlines()
            print(lines)
            if lines[0].startswith("TICKET_START"):
                line = lines.pop(0)
                args = line.split("::")
                self.author = args[1]
                self.id = args[2]
                self.timestamp = datetime.fromtimestamp(float(args[3])).strftime("%-m/%d/%y, %-I:%M %p")
            else:
                print("returning")
                return
            for i in lines:
                print(i)
                if not i.startswith("MESSAGE_START"):
                    continue
                self.messages.append(Message(i))

    def __iter__(self):
        return iter(self.messages)


class Message:
    def __init__(self, message: str):
        self.message = message
        self.avatar = None
        self.author = None
        self.id = None
        self.content = None
        self.attachments = None
        self.time = None
        self.parse()
        self.avatar = f"/pfps/{self.id}.png"

    def parse(self):
        args = self.message.split("::")
        dummy = args.pop(0)
        self.author = args.pop(0)
        self.id = args.pop(0)
        self.content = args.pop(0)
        self.time = datetime.fromtimestamp(float(args.pop(0))).strftime("%-m/%d/%y, %-I:%M %p")
        if args:
            self.attachments = args


