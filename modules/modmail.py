import pathlib

import datetime
import discord
import io
from columnar import columnar
from discord.ext import commands

from .helpers import Helpers


class Modmail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        await self.modmail_sent_to_user(message)
        await self.user_sent_to_modmail(message)

    async def user_sent_to_modmail(self, message):
        if not message.channel.type == discord.ChannelType.private:
            return
        guild: discord.guild.Guild = self.bot.get_guild(self.bot.config["server"])
        channelid = self.bot.db.execute(f"SELECT channel FROM modmail WHERE id LIKE ?", (message.author.id,)).fetchone()

        embed = await Helpers.create_embed(string=message.content, author=message.author,
                                           guild=guild, attachments=message.attachments, send=True)

        await message.channel.send(embed=embed)

        if channelid is None:
            channel = await self.create_ticket(message.author, guild)
        else:
            channel = guild.get_channel(channelid["channel"])
        embed.title = "Message Received"

        files = [(await i.to_file()) for i in message.attachments]
        await channel.send(embed=embed, files=files)

    async def modmail_sent_to_user(self, message):
        if message.author.id == 575252669443211264:  # other modmail bot
            return
        if ">close" in message.content or (
                type(message.content) is None and len(message.content) > 0 and message.content[
                0] == "="):
            return
        if message.content is not None and len(message.content) > 0 and message.content[0] == ">": return
        if not any(message.channel.id == i["channel"] for i in self.bot.db.execute("SElECT channel FROM modmail").fetchall()):
            return
        guild = self.bot.get_guild(self.bot.config["server"])
        userid = int(message.channel.topic)
        user = self.bot.get_user(userid)

        embed = await Helpers.create_embed(string=message.content, author=message.author, guild=guild, attachments=message.attachments, receive=True)

        files = [(await i.to_file()) for i in message.attachments]
        try:
            await user.send(embed=embed, files=files)
        except discord.errors.Forbidden:
            await message.channel.send(f"Unable to send message to user {str(user)}.")
            return

        embed.title = "Message Sent"
        embed.set_footer(text=str(user) + " | " + str(user.id), icon_url=user.display_avatar.url)
        files = [(await i.to_file()) for i in message.attachments]
        await message.channel.send(embed=embed, files=files)

    async def create_ticket(self, member: discord.Member, guild):
        name = "modmail-" + member.name + "-" + member.discriminator
        channel = await guild.create_text_channel(name, category=guild.get_channel(self.bot.config["ticket_category"]),
                                                  topic=member.id, nsfw=False)
        self.bot.db.execute("INSERT INTO modmail (id, channel) VALUES (?, ?)",
                            (member.id, channel.id))
        self.bot.connection.commit()
        embed = await Helpers.new_ticket_staff_embed(member)
        await channel.send(embed=embed)

        embed = await Helpers.new_ticket_mebers_embed(member)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            await channel.send(f"Unable to send message to {member.name}")
        return channel

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def close_modmail(self, context: commands.Context, *, reason=""):
        async with context.typing():
            if "modmail" not in context.channel.name:
                return
            await context.send("Closing...")
            userid = int(context.channel.topic)
            user = self.bot.get_user(userid)
            guild: discord.Guild = context.guild

            messages = [message async for message in context.channel.history(limit=None, oldest_first=True)]
            data = []
            headers = ["discord tag", "user id", "content", "timestamp"]
            # todo: add attachments
            for message in messages:
                if len(message.embeds) == 0 and (
                        len(message.content) != 0 and (message.content[0] == "=" or message.content == "Closing...")):
                    data.append([message.author, str(message.author.id), message.content,
                                 message.created_at.strftime("%a_%b_%d_at_%H_%M_%S")])
                    continue
                elif len(message.embeds) != 0:
                    embed = message.embeds[0]
                    try:
                        vals = embed.author.name.split(" | ")
                    except AttributeError:
                        vals = ["", ""]
                    try:
                        data.append(
                            [vals[0], vals[1], embed.description if embed.description is not None else "",
                             message.created_at.strftime("%a_%b_%d_at_%H_%M_%S")])
                    except IndexError:
                        pass
            table = columnar(data, headers, no_borders=True, terminal_width=200)
            # file = io.BytesIO(bytearray(table, "utf-8"))
            pathlib.Path("modmail/").mkdir(parents=True, exist_ok=True)
            file = open("modmail/" + context.channel.name + ".txt", "w")
            file.write(table)
            file.close()
            attach = discord.File(filename=context.channel.name + ".txt", fp="modmail/" + context.channel.name + ".txt")
            embed = discord.Embed(
                title="Ticket Closed",
                description=reason,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_author(name=str(context.author) + " | " + str(context.author.id),
                             icon_url=context.author.display_avatar.url)
            embed.set_footer(text=str(user) + " | " + str(user.id), icon_url=user.display_avatar.url)
            await self.bot.get_channel(self.bot.config["admin_logs"]).send(embed=embed, file=attach)

            embed.set_footer(text=str(guild) + " | " + str(guild.id), icon_url=guild.icon)
            try:
                await user.send(embed=embed)
            except discord.errors.Forbidden:
                await self.bot.get_channel(self.bot.config["admin_logs"]).send(
                    f"Unable to send closing message to user {str(user)}.")

        await context.channel.delete()
        self.bot.db.execute("DELETE FROM modmail WHERE id LIKE ?", (userid,))
        self.bot.connection.commit()

    @commands.command()
    async def clear_db(self, context):
        self.bot.db.execute("DELETE FROM modmail")
        self.bot.connection.commit()

    @commands.command()
    async def open_ticket(self, context, user: discord.Member, *, message="New Ticket"):
        channel = await self.create_ticket(user, context.guild)
        embed = await Helpers.create_embed(string=message, author=user, guild=context.guild, receive=True)
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            await channel.send(f"Unable to send message to {user.name}")
        embed.title = "Message Sent"
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Modmail(bot))
