import asyncio
import json

import discord
from discord.ext import commands

with open('variables.json', 'r') as f:
    variables = json.load(f)

if variables["token"] == "":
    print("No token inputted. Please fill the variables.json file.")

if variables["modmail"]["guildID"] == "":
    print("No guild ID for the modmail function was inputted in variables.json.\nThe bot will run without it.")
else:
    guildID = int(variables["modmail"]["guildID"])


def get_prefix(bot, message):
    prefixes = variables["prefixes"]

    if message.guild is None:
        return variables["prefixes"][0]  # In DMs, use only a certain prefix.

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)


@bot.event
async def on_ready():
    print(f'\n~-~-~-~-~-~-~-~-~\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}')
    users = 0
    #servers = 0 # need to figure out how to iterate on all servers in rewrite.
    for user in bot.get_all_members():
        users += 1
    print(f'Serving ' + str(users) + ' users.')
    print(f'~-~-~-~-~-~-~-~-~')


@bot.event
async def on_message(message):
    message.content = message.content.split(variables["comment"])[0]
    if message.guild is not None:
        await bot.process_commands(message)
    elif message.guild is None and variables["modmail"]["enabled"].lower() == "true":
        if bot.get_guild(guildID).get_member(message.author.id) is not None:
            modmailChannel = None
            for channel in bot.get_guild(guildID).channels:
                if channel.name == variables["modmail"]["channel"]:
                    modmailChannel = channel
            if modmailChannel:
                em = discord.Embed(title=f"New mod mail:",
                                   description=message.content,
                                   colour=0xDFDE6E)
                if message.author.avatar:
                    em.set_author(name=bot.get_guild(guildID).get_member(message.author.id).display_name,
                                  icon_url=f"https://cdn.discordapp.com/avatars/{message.author.id}/{message.author.avatar}.png?size=64")
                else:
                    em.set_author(name=bot.get_guild(guildID).get_member(message.author.id).display_name,
                                  icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
                await modmailChannel.send(embed=em)
            else:
                print(f"Could not find #{variables['modmail']['channel']} in {bot.get_guild(guildID).name}. Can not use modmail functionality.")

if __name__ == '__main__':
    bot.load_extension("cogs.utils.help")
    bot.load_extension("cogs.utils.ownercog")
    bot.load_extension("cogs.faq")
    bot.load_extension("cogs.fun")
    bot.load_extension("cogs.admincommands")
    bot.load_extension("cogs.timezone")
    bot.load_extension("cogs.factorio")
    print(f'Successfully loaded extensions.')
    bot.run(variables["token"], bot=True, reconnect=True)
