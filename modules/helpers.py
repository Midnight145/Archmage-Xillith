import discord
import datetime

class Helpers:
    def __init__(self):
        pass

    @staticmethod
    async def create_embed(string: str = "New Ticket", author: discord.Member = None, guild: discord.Guild = None,
                                attachments=None, send: bool=False, receive: bool=False) -> discord.Embed:
        if attachments is None:
            attachments = []
        title = ""
        if send:
            title = "Message Sent"
        elif receive:
            title = "Message Received"
        embed = discord.Embed(
            title=title,
            description=string,
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        for i in range(len(attachments)):
            embed.add_field(name=f"Attachment {i + 1}", value=attachments[i].url)
        embed.set_author(name=str(author) + " | " + str(author.id), icon_url=author.display_avatar.url)
        embed.set_footer(text=str(guild) + " | " + str(guild.id), icon_url=guild.icon)

        return embed

    @staticmethod
    async def new_ticket_staff_embed(member: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title="New Ticket",
            description="Type a message in this channel to reply. Messages starting with the server "
                        "prefix `>` are ignored, and can be used for staff discussion. Use the "
                        "command `>close_modmail [reason]` to close this ticket.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name=str(member) + " | " + str(member.id), icon_url=member.display_avatar.url)
        embed.set_footer(text=str(member) + " | " + str(member.id), icon_url=member.display_avatar.url)
        return embed

    @staticmethod
    async def new_ticket_mebers_embed(member: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title="New Ticket",
            description="Type a message in this channel to reply. Messages sent here are logged by staff.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name=str(member) + " | " + str(member.id), icon_url=member.display_avatar.url)
        embed.set_footer(text=str(member) + " | " + str(member.id), icon_url=member.display_avatar.url)
        return embed