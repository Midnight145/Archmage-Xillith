import typing
import re

from discord.ext import commands
from google.genai.errors import APIError
from pydantic import BaseModel

from modules import Errors
from modules.MessageInfo import MessageInfo


class VerificationResponse(BaseModel):
    status: str
    reason: str
    confidence: float


class AIUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini = bot.gemini
        self.gemini_config = bot.gemini_config


    def create_context(self, message_list: list[MessageInfo]) -> (str, bool):
        context = ""
        thread = False
        for message in message_list:
            # message.content = self.sanitize_input(message.content)

            # if message.content is None:
            #     continue
            if message.content.startswith(">start_conversation") or message.content.startswith(">sc"):
                thread = True
                message.content = re.sub(r'^>start_conversation\s*', '', message.content)
                message.content = re.sub(r'^>sc\s*', '', message.content)
            context = (str(message.author) if message.author != self.bot.user else self.bot.config[
                "name"]) + ": " + message.content + "\n" + context

        return context, thread

    def replace_mentions_with_usernames(self, message: typing.Union[MessageInfo, str]) -> str:
        if isinstance(message, MessageInfo):
            content = message.content
        else:
            content = message
        user_id_pattern = re.compile(r'<@!?(\d+)>')
        user_ids = user_id_pattern.findall(content)

        for user_id in user_ids:
            mention_pattern = f"<@!?{user_id}>"
            user = self.bot.get_user(int(user_id))
            if user == self.bot.user:
                content = re.sub(mention_pattern, self.bot.config["name"], content)
            if user:
                content = re.sub(mention_pattern, user.name, content)

        return content

    @staticmethod
    def split_messages(string: str) -> list[str]:
        """Splits a string into segments of 2000 characters or fewer,
        separating on the previous space instead of the middle of a word.

        Args:
            string: The string to split.

        Returns:
            A list of strings, where each string is a segment of the input string.
        """

        segments = []
        start = 0
        while start < len(string):
            end = min(start + 2000, len(string))
            if end < len(string):
                # Try to find a space to break at before the 2000-character limit
                break_point = string.rfind('\n', start, end)
                if break_point != -1:
                    end = break_point

            segments.append(string[start:end])
            start = end + 1 # start after the space, if there was one

        return segments

    @staticmethod
    def split_speakers(response: str) -> str:
        lines = response.split('\n')
        pattern = re.compile(r'^\w+\s*\w*:\s*')

        # Strip the pattern from the beginning of the first line
        if lines and pattern.match(lines[0]):
            lines[0] = pattern.sub('', lines[0])

        idx = 0
        for i, line in enumerate(lines[1:], start=1):
            if pattern.match(line):
                idx = i
                break

        # Keep only the lines up to but not including the first matching line
        if idx > 0:
            lines = lines[:idx]

        response = '\n'.join(lines)
        return response

    def truncate(self, string: str) -> str:
        """Ensures the input stays within configured message history length."""
        if not string:
            return ""  # Prevent errors from empty input

        lines = string.strip().splitlines()  # Strip whitespace before splitting
        history_limit = self.bot.config.get("history", 50)  # Use a default if missing
        if len(lines) <= history_limit:
            return string
        return "\n".join(lines[-history_limit:])  # Safely truncate to the last history_limit lines

    async def verify_prompt(self, prompt: str) -> typing.Union[int,  VerificationResponse]:
        config = self.gemini_config.model_copy()
        config.response_schema = VerificationResponse
        config.response_mime_type = "application/json"

        try:
            output = await self.gemini.aio.models.generate_content(
                    model="gemini-2.0-flash", contents=self.bot.config["security_filter"] + prompt,
                config=config
            )
        except APIError as e:
            return e.code
        # noinspection PyTypeChecker
        response: VerificationResponse = output.parsed
        return response

    async def generate_response(self, prompt: str) -> typing.Union[list[str], int]:
        prompt = self.truncate(prompt)
        try:
            output = await self.gemini.aio.models.generate_content(
                    model="gemini-2.0-flash", contents=self.bot.config["prompt"] + prompt, config=self.gemini_config
        )
        except APIError as e:
            print(e)
            return e.code
        text = self.sanitize_output(output.text)

        print("INPUT: " + self.bot.config["prompt"] + prompt)
        print("OUTPUT:" + text)
        return self.split_messages(text)

    def sanitize_output(self, string: str) -> str:
        text = re.sub(fr"^({self.bot.config['name']}:\s+)+", "", string)
        text = self.split_speakers(text)
        text = self.replace_mentions_with_usernames(text)
        return text.replace("@everyone", "`@everyone`").replace("@here", "`@here`")

    def sanitize_input(self, string: str, check_blocked: bool = True) -> str:
        if check_blocked:
            BLOCKED_PATTERNS: list[str] = self.bot.config["blocked_patterns"]
            for pattern in BLOCKED_PATTERNS:
                if re.search(re.compile(pattern, re.IGNORECASE), string):
                    return Errors.ERROR_UNSAFE
        string = self.replace_mentions_with_usernames(string)
        return string


async def setup(bot):
    await bot.add_cog(AIUtil(bot))
