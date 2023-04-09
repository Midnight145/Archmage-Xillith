import api
from discord.ext import commands
from discord.ext.buttons import Paginator


class Nodes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def search_nodes(self, context: commands.Context, *args):
        kwargs = dict((k, v) for k, v in (pair.split('=') for pair in args))
        res = api.search_nodes(**kwargs)

        entries = []
        for i in res:
            entries.append(str(i))
        await Paginator(title="Results", color=0xce2029, entries=entries, length=1).start(context)


async def setup(bot):
    await bot.add_cog(Nodes(bot))
