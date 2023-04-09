#! /usr/bin/python3.6
import json

from discord.ext.commands import Bot
import datetime
import discord

with open('config.json') as config_file:
    config = json.load(config_file)
with open('TOKEN.txt', 'r') as token:
    TOKEN = token.read().rstrip()


async def get_prefix(bot_, message):
    return config["prefix"]

GUILD_ID = config["server"]
READY_CHANNEL = config["staff_botspam"]

COG_FILE = "COGS.txt"
intents = discord.Intents.all()

bot = Bot(command_prefix=get_prefix, intents=intents)

with open(COG_FILE, "r") as cogs:
    bot.all_cogs = [i.rstrip() for i in cogs.readlines()]

bot.config = config
bot.COG_FILE = COG_FILE
bot.current_invite = None
bot.loaded_cogs, bot.unloaded_cogs = [], []
bot.owner_id = 613371584295469084
bot.traceback = {}

@bot.event
async def on_ready():
    bot.guild = None

    while bot.guild is None:
        bot.guild = bot.get_guild(GUILD_ID)

    for i in bot.all_cogs:
        if i not in bot.loaded_cogs:
            await bot.load_extension(i)
            bot.loaded_cogs.append(i)

    await bot.change_presence(status=discord.Status.online, activity=discord.Game(bot.config["status"]))

    print("Bot is ready!")
    print("Logged in as:")
    print(bot.user)

    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M.%S"))
    print()


@bot.event
async def on_disconnect():
    print("Bot disconnected")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M.%S"))
    print()


@bot.event
async def on_connect():
    print("Bot connected")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M.%S"))
    print()


bot.run(TOKEN)
