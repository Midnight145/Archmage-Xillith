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

async def setup(bot):
    await bot.add_cog(Wiki(bot))