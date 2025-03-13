from dataclasses import dataclass

import discord


@dataclass()
class MessageInfo:
    message: int
    parent: int
    channel: int
    author: discord.User
    content: str
