import api
from discord.ext import commands
from discord.ext.buttons import Paginator


class Aspects(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def search(self, context: commands.Context, *args):
        """
        Will show the aspects of items that match the given search parameters.
        :param context: command context
        :param args: search arguments, given in the form of key=value. Valid keys are: mod, name, itemid, metadata.
        :return:
        """
        kwargs = dict((k, v) for k, v in (pair.split('=') for pair in args))
        res = api.search_aspects(**kwargs)
        entries = []
        for i in res:
            entries.append(str(i))
        await Paginator(title="Results", color=0xce2029, entries=entries, length=10).start(context)

    @commands.command()
    async def aspects(self, context: commands.Context, *, args: str):
        """
        Will show the items that have all the given aspects.
        :param context: command context
        :param args: the aspects to search for, separated by spaces.
        :return:
        """
        args = [i.rstrip() for i in args.split(" ")]
        res = api.search_aspect(*args)
        entries = []
        for i in res:
            entries.append(str(i))
        await Paginator(title="Results", color=0xce2029, entries=entries, length=10).start(context)


async def setup(bot):
    await bot.add_cog(Aspects(bot))
