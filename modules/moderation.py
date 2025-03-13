import discord
from discord.ext import commands
import re
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     regex = re.compile(r"(?:https?://)?discord(?:app)?.(?:com/invite|gg)/[a-zA-Z0-9]+/?")
    #     author: discord.Member = message.author
    #     try:
    #         perms: discord.Permissions = author.guild_permissions
    #     except AttributeError:
    #         return
    #     if perms.manage_messages:
    #         return
    #     if regex.search(message.content):
    #         await message.delete()
    #         await message.channel.send("No invites allowed! You have been muted for two minutes, please contact a moderator if you think this is a mistake.")
    #         await message.author.timeout(timedelta(minutes=2))
    #         await self.bot.get_channel(self.bot.config["automod"]).send(f"{message.author.mention} tried to post an invite link in {message.channel}. Message: {message.content}")

    # @commands.Cog.listener()
    # async def on_message_edit(self, before: discord.Message, after: discord.Message):
    #     regex = re.compile(r"(?:https?://)?discord(?:app)?.(?:com/invite|gg)/[a-zA-Z0-9]+/?")
    #     author: discord.Member = after.author
    #     perms: discord.Permissions = author.guild_permissions
    #     if perms.manage_messages:
    #         return
    #     if regex.search(after.content):
    #         await after.delete()
    #         await after.channel.send("No invites allowed! You have been muted for two minutes, please contact a moderator if you think this is a mistake.")
    #         await after.author.timeout(timedelta(minutes=2))
    #         await self.bot.get_channel(self.bot.config["automod"]).send(f"{after.author.mention} tried to post an invite link in {after.channel}. Message: {after.content}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
