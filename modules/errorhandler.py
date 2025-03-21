from discord.ext import commands
import traceback
from discord.ext.buttons import Paginator


class TracebackHandler:
    def __init__(self, _id: int, _error: str, _tb: traceback.TracebackException):
        self.id = _id
        self.error = _error
        self.traceback = _tb

    def __str__(self):
        return "**" + self.error + "**" + "\n" + ''.join(traceback.format_tb(self.traceback)).replace("ryan", "midnight")


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["show_error"])
    @commands.is_owner()
    async def get_error(self, context: commands.Context, errcode: str):
        try:
            await context.send(str(self.bot.traceback[int(errcode)]))
        except KeyError:
            await context.send("Error code does not exist, returning.")

    @commands.Cog.listener()
    async def on_command_error(self, context: commands.Context, error: commands.errors.CommandError):
        if type(error) == commands.CommandNotFound:
            return
        elif type(error) == commands.MissingRequiredArgument:
            error: commands.MissingRequiredArgument
            await context.send(f"Missing required argument: {error.param}")
            return
        err_code = 255
        for i in range(len(self.bot.traceback) + 1):
            if i in self.bot.traceback:
                continue
            err_code = i
        await context.send(f"""{error}\nError code {err_code}""")
        original = getattr(error, 'original', error)
        handler = TracebackHandler(err_code, f"{error.__class__.__name__}: {str(error)}", original.__traceback__)
        self.bot.traceback[err_code] = handler

    @commands.command()
    @commands.is_owner()
    async def throw(self, context: commands.Context):
        raise ZeroDivisionError

    @commands.command()
    @commands.is_owner()
    async def del_error(self, context: commands.Context, errcode: str):
        try:
            temp = self.bot.traceback[int(errcode)]
            del self.bot.traceback[int(errcode)]
        except KeyError:
            await context.send(f"Error {errcode} does not exist.")
            return
        await context.send(f"Traceback {errcode} deleted. Contents:\n{str(temp)}")

    @commands.command()
    @commands.is_owner()
    async def clear_errors(self, context: commands.Context):
        self.bot.traceback = {}
        await context.send("Traceback cache cleared.")

    @commands.command()
    @commands.is_owner()
    async def show_errors(self, context):
        pages = []
        items = []
        for key, item in self.bot.traceback.items():
            items.append(item)
        items.sort(key=lambda x: x.id)
        for item in items:
            pages.append(f"**Error Code {item.id}:**\n{str(item)}")

        await Paginator(title="Tracebacks", color=0xce2029, entries=pages, length=1).start(context)


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
