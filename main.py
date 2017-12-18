import asyncio
import json

import discord
from discord.ext import commands

with open('variables.json', 'r') as f:
    variables = json.load(f)

if variables["token"] == "":
    print("No token inputted. Please fill the variables.json file.")


def get_prefix(bot, message):
    prefixes = variables["prefixes"]

    if message.guild.id is None:
        return variables["prefixes"][0]  # In DMs, use only a certain prefix.

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)


@bot.event
async def on_ready():
    print(f'\n~-~-~-~-~-~-~-~-~\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n~-~-~-~-~-~-~-~-~')


@bot.event
async def on_message(message):
    message.content = message.content.split(variables["comment"])[0]
    await bot.process_commands(message)

if __name__ == '__main__':
    bot.load_extension("cogs.utils.help")
    bot.load_extension("cogs.utils.ownercog")
    bot.load_extension("cogs.faq")
    bot.load_extension("cogs.randomcatdog")
    bot.load_extension("cogs.admincommands")
    bot.load_extension("cogs.timezone")
    bot.load_extension("cogs.factorio.modportal")
    bot.load_extension("cogs.factorio.wiki")
    bot.run(variables["token"], bot=True, reconnect=True)
