import datetime

import sqlite3

import uuid

import hashlib

import io

import discord
import os
import pathlib
import re
from discord import Permissions
from discord.ext import commands


class Report(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reporting_channel = self.bot.config["reporting_channel"]
        self.bot.db.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, creator INTEGER, creation_time INTEGER, close_time INTEGER, closed_by INTEGER, closed_by_name TEXT)")
        self.bot.db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, ticket_id INTEGER, author INTEGER, content TEXT, time INTEGER, attachments TEXT DEFAULT '')")
        self.bot.db.execute("CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, message_id INTEGER, name TEXT, data BLOB)")
        self.bot.db.execute("CREATE TABLE IF NOT EXISTS pfps (id INTEGER PRIMARY KEY, data BLOB)")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id != self.reporting_channel and payload.message_id != self.bot.config["reporting_message"]:
            return

        if payload.emoji.name != "📝":
            return

        if payload.user_id != self.bot.user.id:
            message = await self.bot.get_channel(self.reporting_channel).fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, payload.member)

        ticket_category = self.bot.get_channel(self.bot.config["ticket_category"])
        count = 0
        for i in ticket_category.text_channels:
            if str(payload.user_id) in i.name:
                regex = r"ticket-(\d+)-(\d+)"
                match = re.search(regex, i.name)
                count = max(count, int(match.group(2)))
        channel = await ticket_category.create_text_channel(f"ticket-{payload.user_id}-{count + 1}")
        bot_role = channel.guild.get_role(self.bot.config["bot_role"])
        await channel.edit(overwrites={
            payload.member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            channel.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            bot_role: discord.PermissionOverwrite.from_pair(Permissions.all_channel(), Permissions.none())
        })
        await channel.send(f"Ticket created by {payload.member.mention} ({payload.member.id})")

    @commands.command()
    async def close(self, context: commands.Context, *, reason=""):
        if context.channel.category.id != self.bot.config["ticket_category"]:
            return
        await self.close_ticket(self, context, reason)
        await context.channel.delete()

    @staticmethod
    async def close_ticket(self, context: commands.Context, reason=""):
        messages = [i async for i in context.channel.history(oldest_first=True)]
        saved_pfps = []

        try:
            ticket_creator = context.guild.get_member(int(context.channel.name.split("-")[1]))
        except ValueError:
            ticket_creator = context.guild.get_member(int(context.channel.topic))
        creation_time = context.channel.created_at.timestamp()
        close_time = context.message.created_at.timestamp()
        closed_by = context.author.id

        self.bot.db.execute(
            "INSERT INTO tickets (creator, creator_name, creation_time, close_time, closed_by, closed_by_name) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ticket_creator.id, ticket_creator.display_name, int(creation_time), close_time, closed_by,
             context.author.display_name))
        id_ = self.bot.db.lastrowid

        for message in messages:
            if len(message.content) == 0 and len(message.attachments) == 0:
                continue
            if message.author.id not in saved_pfps:
                if message.webhook_id is not None:
                    user = await self.bot.get_member(message.author.name)
                else:
                    user = message.author

                saved_pfps.append(user.id)
                blob = io.BytesIO()
                try:
                    await user.avatar.save(blob)
                except AttributeError:
                    await user.default_avatar.save(blob)
                try:
                    self.bot.db.execute("INSERT INTO pfps (id, username, data) VALUES (?, ?, ?)",
                                        (message.author.id, message.author.name, blob.getvalue()))
                except sqlite3.IntegrityError:
                    pass
            content = re.sub(r'<@!?([0-9]+)>', lambda x: f"@{context.guild.get_member(int(x.group(1))).display_name}",
                             message.content)
            self.bot.db.execute(
                "INSERT INTO messages (ticket_id, author_id, author, content, time) VALUES (?, ?, ?, ?, ?)",
                (id_, message.author.id, message.author.display_name, content, int(message.created_at.timestamp())))
            message_id = self.bot.db.lastrowid
            if message.attachments:
                for file in message.attachments:
                    blob = io.BytesIO()
                    await file.save(blob)
                    self.bot.db.execute("INSERT INTO attachments (message_id, name, data) VALUES (?, ?, ?)",
                                        (message_id, file.filename, blob.getvalue()))

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"{reason}",
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name=str(context.author) + " | " + str(context.author.id),
                         icon_url=context.author.display_avatar.url)
        embed.set_footer(text=str(ticket_creator) + " | " + str(ticket_creator.id), icon_url=ticket_creator.display_avatar.url)

        embed.set_footer(text=str(ticket_creator.guild) + " | " + str(ticket_creator.guild.id), icon_url=ticket_creator.guild.icon)
        await ticket_creator.send(embed=embed)
        embed.description += f"\nhttps://moderation.nidmight.co/tickets/{id_}"
        await self.bot.get_channel(self.bot.config["admin_logs"]).send(embed=embed)
        self.bot.connection.commit()
        try:
            self.bot.db.execute("DELETE FROM modmail WHERE channel LIKE ?", (context.channel.id,))
            self.bot.connection.commit()
        except Exception:
            pass

        return embed


# Database Schema
# Ticket:
#   Ticket ID
#   Creator ID
#   Creation Time
#   Close Time
#   Closed By ID
#   Closed By Name

# CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, creator INTEGER, creation_time INTEGER, close_time INTEGER
# , closed_by INTEGER, closed_by_name TEXT)

# Message:
#   Ticket ID
#   Author ID
#   Content
#   Time
#   Attachments
#     Comma separated list of attachment names

# Attachment:
#   Attachment ID
#   Message ID
#   Attachment Name
#   Attachment Data

# CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, message_id INTEGER, name TEXT, data BLOB)
# CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, ticket_id INTEGER, author INTEGER, content
# TEXT, time INTEGER, attachments TEXT)


async def setup(bot):
    await bot.add_cog(Report(bot))
