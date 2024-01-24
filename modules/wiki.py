import re
from discord.ext import commands


class Wiki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        newline = "\n"
        result = re.findall('\[\[(.*?)\]\]', message.content)
        if not result:
            return
        links = [f"<https://ftbwiki.org/index.php?&search={(i.replace(' ', '+') if ' ' in i else i)}>" for i in result]
        await message.channel.send(f"Fetched {', '.join(result) if len(result) > 1 else ''.join(result)} for you:\n{newline.join(links)}")

    @commands.command()
    async def src(self, context):
        file = open(__file__)
        await context.send("\u0060\u0060\u0060python\n" + file.read() + "\u0060\u0060\u0060")
        file.close()


async def setup(bot):
    await bot.add_cog(Wiki(bot))