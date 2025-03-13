import asyncio
import typing
from io import BytesIO

import discord
from discord.ext import commands
from google import genai
from google.genai.types import GenerateContentConfig

from modules import Errors
from modules.MessageInfo import MessageInfo

message_cache = {}
channel_cache = {}


class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini: genai.Client = bot.gemini
        self.gemini_config: GenerateContentConfig = bot.gemini_config
        self.util = bot.get_cog("AIUtil")

    @commands.command(aliases=["sc"], name="start_conversation", description="Start a conversation with the AI")
    async def start_conversation(self, context: commands.Context, *, prompt: str):
        if not self.check_whitelist(context.channel):
            return
        await self.possibly_send(context.message, prompt)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.check_whitelist(message.channel) or message.author.bot or message.reference is None:
            return

        message.content = self.util.split_speakers(message.content)
        if message.content.startswith(">start_conversation") or message.content.startswith(">sc"):
            return
        if message.reference.resolved.author != self.bot.user:
            return

        await self.populate_database(message)  # populate the database with the message and its references
        message_list = self.recur_db(message.id, message.channel.id, [])
        context, is_thread = self.util.create_context(message_list)
        if is_thread:
            await self.possibly_send(message, "\n\n" + context)


    def check_whitelist(self, channel: discord.TextChannel) -> bool:
        if isinstance(channel, discord.Thread):
            return channel.parent_id in self.bot.config["whitelist"]
        return channel.id in self.bot.config["whitelist"]


    async def possibly_send(self, message: discord.Message, prompt: str):
        channel = message.channel
        if message.author.id == 613371584295469084 and "--override" in message.content:
            message.content.replace("--override", "")
        else:
            check = self.util.sanitize_input(message.content)
            channel = message.channel
            if check == Errors.ERROR_UNSAFE:
                to_delete = await channel.send(check)
                await asyncio.sleep(2)
                await message.delete()
                await asyncio.sleep(1)
                await to_delete.delete()
                return
            response = await self.util.verify_prompt(check)
            if isinstance(response, int):
                await channel.send(Errors.ERROR_GENERIC + str(response))
                return
            if response.status != "safe" and response.confidence > self.bot.config["confidence_threshold"]:
                await channel.send(
                    f"The following message was blocked as potentially unsafe: \n{message.content}\n\n{response.reason}\nConfidence Threshold: {response.confidence}\n\nIf you think this is a mistake, please contact Ruby.")
                await message.delete()
                return
        prompt = self.util.sanitize_input(prompt, check_blocked = False)
        async with channel.typing():
            output_list = await self.util.generate_response(prompt)
            if output_list is None:
                await channel.send(Errors.ERROR_NORESPONSE)
                return
            if isinstance(output_list, int):
                await channel.send(Errors.ERROR_GENERIC + str(output_list))
                return
            await self.send_messages(channel, output_list, message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        self.bot.db.execute("DELETE FROM ai_messages WHERE id = ?", (message.id,))
        self.bot.connection.commit()

    @commands.command()
    async def export_context(self, context: commands.Context, message_id: int, channel_id: int = None):
        if channel_id is None:
            channel_id = context.channel.id
        message = await self.bot.get_channel(channel_id).fetch_message(message_id)
        await self.populate_database(message)
        message_list = self.recur_db(message_id, channel_id, [])
        _context, is_thread = self.util.create_context(message_list)
        memory_file = BytesIO()
        memory_file.write(_context.encode())
        memory_file.seek(0)
        await context.send(file=discord.File(memory_file, filename="context.txt"))

    @staticmethod
    async def send_messages(messageable: discord.abc.Messageable, output_list: list[str], message: discord.Message):
        for output in output_list:
            new_message = await messageable.send(output, reference=message)
            message = new_message

    async def resolve_message(self, message: discord.Message):
        if message.reference is None:
            return
        if message.reference.resolved is not None:
            return
        if message.reference.channel_id in channel_cache:
            channel = channel_cache[message.reference.channel_id]
        else:
            try:
                channel = await self.bot.fetch_channel(message.reference.channel_id)
                channel_cache[message.reference.channel_id] = channel
            except discord.errors.NotFound:
                print("Failed to fetch channel")
                return
        try:
            message.reference.resolved = await channel.fetch_message(message.reference.message_id)
            message_cache[message.reference.message_id] = message.reference.resolved
        except discord.errors.NotFound:
            print("Failed to fetch message")
            return

    async def populate_database(self, message: typing.Union[discord.Message, int], channel: int = None):
        if isinstance(message, discord.Message):
            result = self.bot.db.execute("SELECT parent, channel FROM ai_messages WHERE id = ?", (message.id,)).fetchone()
            if result is None:
                message_cache[message.id] = message
                if message.reference is None:
                    self.bot.db.execute("INSERT OR IGNORE INTO ai_messages (id, parent, channel, author, content) VALUES (?, ?, ?, ?, ?)", (message.id, 0, message.channel.id, message.author.id, message.content))
                    self.bot.connection.commit()
                    return
                else:
                    self.bot.db.execute("INSERT OR IGNORE INTO ai_messages (id, parent, channel, author, content) VALUES (?, ?, ?, ?, ?)", (message.id, message.reference.message_id, message.channel.id, message.author.id, message.content))
                    self.bot.connection.commit()

                    await self.resolve_message(message.reference.resolved)

                    await self.populate_database(message.reference.resolved)
            else:

                await self.populate_database(result["parent"], result["channel"])
        else:
            result = self.bot.db.execute("SELECT parent, channel FROM ai_messages WHERE id = ?", (message,)).fetchone()
            if result is None:
                try:

                    message = await self.bot.get_channel(channel).fetch_message(message)
                    message_cache[message.id] = message
                    await self.populate_database(message)
                except discord.errors.NotFound:
                    print("Failed to fetch message")
            else:
                if result["parent"] == 0:
                    return
                await self.populate_database(result["parent"], result["channel"])

    def recur_db(self, message_id: int, channel_id: int, message_list: list[MessageInfo]) -> list[MessageInfo]:
        result = self.bot.db.execute("SELECT parent, author, content FROM ai_messages WHERE id = ? AND channel = ?", (message_id, channel_id)).fetchone()
        if result is None:
            return message_list
        message_list.append(MessageInfo(message_id, result["parent"], channel_id, self.bot.get_user(result["author"]), result["content"]))
        if result["parent"] == 0:
            return message_list
        else:
            return self.recur_db(result["parent"], channel_id, message_list)


async def setup(bot):
    await bot.add_cog(Gemini(bot))


