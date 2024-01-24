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
    async def close(self, context: commands.Context):
        if context.channel.category.id != self.bot.config["ticket_category"]:
            return
        messages = [i async for i in context.channel.history(oldest_first=True)]
        path = pathlib.Path(f"tickets/")
        path.mkdir(parents=True, exist_ok=True)
        uid = uuid.uuid4()
        log = open(f"tickets/{uid}.txt", "w")
        saved_pfps = []
        creator = context.guild.get_member(int(context.channel.name.split("-")[1]))
        log.write(f"TICKET_START::{creator.display_name}::{creator.id}::"
                  f"{context.channel.created_at.timestamp()}\n")
        for i in messages:
            if i.id not in saved_pfps:
                saved_pfps.append(i.id)
                path = pathlib.Path(f"pfps/")

                path.mkdir(parents=True, exist_ok=True)
                try:
                    await i.author.avatar.save(path.joinpath(f"{i.author.id}.png"))
                except AttributeError:
                    await i.author.default_avatar.save(path.joinpath(f"{i.author.id}.png"))
            if i.attachments:
                # save attachments
                for j in i.attachments:
                    byteobj = io.BytesIO()
                    await j.save(byteobj)
                    md5 = hashlib.md5(byteobj.getvalue()).hexdigest()
                    new_name = f"{md5}{pathlib.Path(j.filename).suffix}"
                    j.filename = new_name
                    path = pathlib.Path(f"tickets/images/{new_name}")
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    await j.save(path)
            log.write(f"MESSAGE_START::{i.author.name}::{i.author.id}::{i.content if i.content else 'n/a'}"
                      f"::{i.created_at.timestamp()}{'::' if i.attachments else ''}"
                      f"{'::'.join([j.filename for j in i.attachments])}\n")
        log.close()
        await context.channel.delete()


async def setup(bot):
    await bot.add_cog(Report(bot))
