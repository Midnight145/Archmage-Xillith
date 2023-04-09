import api
from discord.ext import commands
from discord.ext.buttons import Paginator


class Nodes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def search_nodes(self, context: commands.Context, *args):
        """
        Search for nodes
        :param context: the command context
        :param args: The arguments to search for, in the form of key=value. Generally aspects, but modifiers and types are also valid.
        :return:
        """
        kwargs = dict((k, v) for k, v in (pair.split('=') for pair in args))  # convert args to dict, assuming format key=value
        res = api.search_nodes(**kwargs)

        entries = []
        for i in res:
            entries.append(str(i))
        await Paginator(title="Results", color=0xce2029, entries=entries, length=1).start(context)


async def setup(bot):
    await bot.add_cog(Nodes(bot))
