#! /usr/bin/python3.10
import asyncio
import sqlite3
import json

from discord.ext.commands import Bot
import datetime
import discord
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from ticket_site import api

with open('config.json') as config_file:
    config = json.load(config_file)
with open('TOKEN.txt', 'r') as token:
    TOKEN = token.read().rstrip()

app = FastAPI()
app.include_router(api.router)

app.mount("/static", StaticFiles(directory="ticket_site/static"), name="static")
app.mount("/pfps", StaticFiles(directory="pfps"), name="pfps")
app.mount("/tickets/images", StaticFiles(directory="tickets/images"), name="images")


# noinspection PyUnusedLocal
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


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


connection = sqlite3.connect(config["database_file"], check_same_thread=False)
# connection.row_factory = sqlite3.Row

connection.row_factory = dict_factory
db = connection.cursor()
db.execute("CREATE TABLE IF NOT EXISTS warns (id INTEGER PRIMARY KEY, member INTEGER, reason TEXT)")
db.execute(
    "CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY,user_id INTEGER, channel INTEGER, "
    "time INTEGER, phrase TEXT, jump_url TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS modmail (id INTEGER PRIMARY KEY, channel INTEGER)")
connection.commit()
bot.db = db
bot.connection = connection
api.db = db


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


async def start():
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close()


asyncio.create_task(start())
