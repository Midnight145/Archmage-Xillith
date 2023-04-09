from discord.ext import commands
import json
import os


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = {}
        if not os.path.exists("commands.json"):
            open("commands.json", "w+").close()

        with open("commands.json") as f:
            self.custom_commands = json.load(f)

    @commands.Cog.listener()
    async def on_message(self, message):
        for command, response in self.custom_commands.items():
            if message.content.startswith(">" + command) or message.content == ">" + command:
                await message.channel.send(response)

    @commands.command(aliases=["add_command"])
    async def add_custom_command(self, context, command, *, response):
        self.custom_commands[command] = response
        self.save_commands()
        await context.send(f"Command {command} added with response {self.custom_commands[command]}")

    def save_commands(self):
        with open("commands.json", "w+") as f:
            json.dump(self.custom_commands, f)

    @commands.command(aliases=["delete_command", "remove_command"])
    async def remove_custom_command(self, context, command):
        if command not in self.custom_commands:
            await context.send(f"Error: Command {command} does not exist")
            return

        del self.custom_commands[command]
        self.save_commands()
        await context.send(f"Command {command} deleted.")


async def setup(bot):
    await bot.add_cog(CustomCommands(bot))