import datetime
import os
import re

import requests
from discord.ext import commands
import discord
import json

from requests.exceptions import InvalidSchema


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.config_file = './config.json'

        def update_config():
            data = json.JSONEncoder().encode(self.bot.config)
            obj = json.loads(data)
            with open(self.bot.config_file, 'w') as conf:
                print("Writing config to file...")
                print(json.dumps(obj, ensure_ascii=True, indent=2))
                conf.write(json.dumps(obj, ensure_ascii=True, indent=2))

        self.bot.update_config = update_config

    BOT_PREFIX = '='

    @commands.command()
    @commands.is_owner()
    async def status(self, context, *, status=""):
        game = discord.Game(status)
        await self.bot.change_presence(status=discord.Status.online, activity=game)
        await context.send(f"Status changed to: {status}" if status != "" else "Reset status")
        self.bot.config["status"] = status
        self.bot.update_config()

    @commands.command(aliases=["kill"], help="Kills the bot")
    @commands.is_owner()
    async def die(self, context):
        await context.send("Bot shutting down...")
        await self.bot.close()

    @commands.command(help=f"Will unload a cog.\nUsage: {BOT_PREFIX}unload cogname", brief="Will unload a cog.",
                      aliases=['ul'])
    @commands.is_owner()
    async def unload(self, context, arg):
        if arg not in self.bot.all_cogs:
            arg = "modules." + arg
        if arg not in self.bot.all_cogs:
            await context.send(f"Error: cog {arg} doesn't exist. Check spelling or capitalization.")
            return
        if arg in self.bot.unloaded_cogs:
            await context.send(f"Cog {arg} already unloaded! Try loading it first.")
            return
        await self.bot.unload_extension(arg)
        await context.send(f"Cog {arg} successfully unloaded!")
        self.bot.loaded_cogs.remove(arg)
        self.bot.unloaded_cogs.append(arg)

    @commands.command(help=f"Will load a cog.\nUsage: {BOT_PREFIX}load cogname", brief="Will load a cog.",
                      aliases=['l'])
    @commands.is_owner()
    async def load(self, context, arg):
        if arg not in self.bot.all_cogs:
            arg = "modules." + arg
        if arg not in self.bot.all_cogs:
            await context.send(f"Error: cog {arg} doesn't exist. Check spelling or capitalization.")
            return
        if arg in self.bot.loaded_cogs:
            await context.send(f"Cog {arg} already loaded! Try unloading it first.")
            return
        await self.bot.load_extension(arg)
        await context.send(f"Cog {arg} successfully loaded!")
        self.bot.unloaded_cogs.remove(arg)
        self.bot.loaded_cogs.append(arg)

    @commands.command(help=f"Will reload a cog.\nUsage: {BOT_PREFIX}reload cogname", brief="Will reload a cog.",
                      aliases=['rl'])
    @commands.is_owner()
    async def reload_cog(self, context, arg):
        if arg not in self.bot.all_cogs:
            arg = "modules." + arg
        if arg not in self.bot.all_cogs:
            await context.send(f"Error: cog {arg} doesn't exist. Check spelling or capitalization.")
            return
        if arg in self.bot.unloaded_cogs:
            await context.send(f"Cog {arg} is unloaded, loading instead.")
            await self.bot.load_extension(arg)
            await context.send(f"Cog {arg} successfully loaded!")
            self.bot.unloaded_cogs.remove(arg)
            self.bot.loaded_cogs.append(arg)
            return
        await self.bot.reload_extension(arg)
        await context.send(f"Cog {arg} successfully reloaded!")

    @commands.command(name="reload", aliases=["r"], hidden=True)
    async def reload_all(self, ctx: commands.Context):
        """Reloads all cogs"""
        for cog in self.bot.all_cogs:
            try:
                self.bot.unload_extension(cog)
                self.bot.load_extension(cog)
                self.bot.loaded_cogs.append(cog)
                self.bot.unloaded_cogs.remove(cog)
            except Exception as e:
                self.bot.traceback[cog] = e
                self.bot.unloaded_cogs.append(cog)
                self.bot.loaded_cogs.remove(cog)
        await ctx.send("Reloaded all cogs")

    @commands.command()
    @commands.is_owner()
    async def rename(self, context, *, name):
        await self.bot.user.edit(username=name)
        await context.send("Username successfully changed!")

    @commands.command()
    async def botinfo(self, context):
        creator = await self.bot.fetch_user(self.bot.owner_id)
        embed = discord.Embed(
            title="Bot Info",
            description="",
            color=discord.Color.gold()
        )
        embed.set_author(name="Created by " + str(creator), icon_url=creator.display_avatar.url)
        embed.set_thumbnail(url=creator.display_avatar.url)
        embed.set_image(url=self.bot.user.display_avatar.url)
        embed.add_field(name="User ID", value=self.bot.user.id, inline=False)
        embed.add_field(name="Join Date",
                        value=context.guild.get_member(self.bot.user.id).joined_at.strftime("%Y-%m-%d %H:%M.%S"),
                        inline=False)
        embed.add_field(name="Other Info", value="Created with discord.py", inline=False)
        await context.send(embed=embed)

    @commands.is_owner()
    @commands.command(aliases=['rlconfig'])
    async def reload_config(self, context):
        with open('./config.json') as config_file:
            config = json.load(config_file)
            self.bot.config = config
            await context.send("Config reloaded!")

    @commands.is_owner()
    @commands.command()
    async def write_config(self, context, key, *, value):
        if all(i.isdigit() for i in value):
            value = int(value)
        self.bot.config[key] = value
        self.bot.update_config()
        await self.reload_config(context)
        await context.send(f"Config Updated! Key {key} updated with value {value}")

    @commands.command()
    @commands.is_owner()
    async def get_config(self, context, key):
        await context.send(self.bot.config[key])

    @commands.command()
    @commands.is_owner()
    async def dump_config(self, context):
        data = json.JSONEncoder().encode(self.bot.config)
        obj = json.loads(data)
        string = json.dumps(obj, ensure_ascii=True, indent=2)
        await context.send(
            f"""```json
{string}
```""")

    @commands.command()
    @commands.is_owner()
    async def execute(self, context, *, query):
        resp = self.bot.db.execute(query).fetchall()
        self.bot.connection.commit()
        await context.send(f"Query processed. Rows found: {len(resp)}")

    @commands.command(aliases=['ac'])
    @commands.is_owner()
    async def add_cog(self, context: commands.Context, arg):
        if arg not in self.bot.all_cogs:
            self.bot.all_cogs.append(arg)
            with open(self.bot.COG_FILE, "a") as cogs:
                cogs.write(arg + "\n")
            await context.send(f"Cog {arg} successfully added!")
        else:
            await context.send(f"Cog {arg} already seems to exist, not adding.")

    @commands.command(aliases=['dc'])
    @commands.is_owner()
    async def delete_cog(self, context: commands.Context, arg):
        if arg in self.bot.all_cogs:
            self.bot.all_cogs.remove(arg)

            with open(self.bot.COG_FILE, "w") as cogs:
                cogs.writelines([i + "\n" for i in self.bot.all_cogs])
            await context.send(f"Cog {arg} successfully deleted!")
        else:
            await context.send(f"Cog {arg} does not exist, not deleting.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, context: commands.Context, limit=None):
        await context.message.delete()

        def is_me(message):
            return message.author == self.bot.user

        if limit is None:
            check = is_me
        else:
            check = lambda x: True
        await context.channel.purge(limit=int(limit) if limit is not None else 100, check=check)

    @commands.command()
    @commands.is_owner()
    async def message(self, context, member: discord.Member, *, contents: str):
        files = [(await i.to_file()) for i in context.message.attachments]

        embed = discord.Embed(
            title=f"New Message",
            description=contents,
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )

        await context.send("Message sent!")
        try:
            await member.send(embed=embed, files=files)
        except discord.Forbidden:
            await context.send(f"Error in sending message to {member.mention}: Forbidden")

    @commands.command()
    async def id(self, context: commands.Context, member: discord.Member = None):
        if member is None:
            member = context.author
        await context.send(str(member.id))

    @commands.command()
    @commands.is_owner()
    async def log(self, context: commands.Context, member: discord.Member):
        await context.send("Going...")
        guild: discord.Guild = context.guild
        for channel in guild.channels:
            await context.send("Logging in channel: " + channel.mention)
            strs = []
            if not isinstance(channel, discord.TextChannel):
                continue
            channel: discord.TextChannel
            filename = f"{member.id}-{channel.name}.txt"
            if os.path.exists(filename):
                continue
            async for message in channel.history(limit=None, oldest_first=True):
                if message.author.id == member.id:
                    str_ = f"{message.created_at} {str(message.author)}: {message.content}\n"
                    strs.append(str_)
                    for i in message.attachments:
                        str_ = f"{message.created_at} {str(message.author)}: {i.proxy_url}\n"
                        strs.append(str_)
            if len(strs) == 0:
                continue
            with open(filename, "w") as f:
                f.writelines(strs)
            file = discord.File(filename)
            await context.send(f"Logged {member.mention} in {channel.mention}", file=file)
            os.remove(filename)

    @commands.command(aliases=["addemote", "ae"])
    @commands.has_permissions(manage_emojis=True)
    async def add_emote(self, context: commands.Context, name, image=None):
        if image is None:
            if context.message.attachments:
                await context.guild.create_custom_emoji(name=name, image=(
                    await context.message.attachments[0].to_file()).fp.read())
                await context.send("Emote " + name + " added")
                return
            else:
                await context.send("Image is a require argument that is missing")
                return
        try:
            emote = requests.get(image).content
        except InvalidSchema:
            image = self.bot.get_emoji(int(list(
                (re.search("<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>", image)).groups())[
                                               -1])).url
            emote = requests.get(image).content
        await context.guild.create_custom_emoji(name=name, image=emote)
        await context.send("Emote " + name + " added")


async def setup(bot):
    await bot.add_cog(Utilities(bot))
