import asyncio
import os
import json

import discord
from discord.ext import commands

import utils.customchecks as customchecks

with open('variables.json', 'r') as f:
    variables = json.load(f)

if not variables["token"]:
    print("No token inputted in variables.json."
          "The bot will not run without it.")

if not variables["modmail"]["guildID"]:
    print("No guild ID for the modmail function was inputted in variables.json."
          "The modmail function will not run without it.")

else:
    guildID = int(variables["modmail"]["guildID"])

with open('data/reminderdb.json', 'r') as f:
    reminderdb = json.load(f)


def get_prefix(bot, message):
    prefixes = variables["prefixes"]

    if message.guild is None:
        return variables["prefixes"][0]

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)


@bot.event
async def on_command_error(ctx, error):
    origerror = getattr(error, 'original', error)
    if isinstance(origerror, customchecks.NoPermsError):
        em = discord.Embed(title="Error",
                           description=f"You do not have sufficient permissions to use the command `{ctx.command}`",
                           colour=0xDC143C)
        return await ctx.send(embed=em)
    else:
        raise error


@bot.event
async def on_ready():
    print(f"\n~-~-~-~-~-~-~-~-~\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}")
    servers = len(bot.guilds)
    users = len(bot.users)
    print(f"Serving {users} users in "+str(servers)+" server"+("s" if servers > 1 else "")+".")
    print("~-~-~-~-~-~-~-~-~")


@bot.event
async def on_message(message):
    message.content = message.content.split(variables["comment"])[0]
    if message.guild is not None:
        await bot.process_commands(message)
    elif (message.guild is None and
            variables["modmail"]["enabled"].lower() == "true" and
            guildID):
        if bot.get_guild(guildID).get_member(message.author.id) is not None:
            modmailChannel = None
            for channel in bot.get_guild(guildID).channels:
                if channel.name == variables["modmail"]["channel"]:
                    modmailChannel = channel
            if modmailChannel:
                em = discord.Embed(title="New mod mail:",
                                   description=message.content,
                                   colour=0xDFDE6E)
                if message.author.avatar:
                    em.set_author(name=bot.get_guild(guildID).get_member(message.author.id).display_name,
                                  icon_url=f"https://cdn.discordapp.com/avatars/{message.author.id}/{message.author.avatar}.png?size=64")
                else:
                    em.set_author(name=bot.get_guild(guildID).get_member(message.author.id).display_name,
                                  icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
                await modmailChannel.send(embed=em)
            else:
                print(f"Could not find #{variables['modmail']['channel']} in {bot.get_guild(guildID).name}."
                      "Can not use modmail functionality.")


if __name__ == '__main__':
    hadError = False
    coglist = []

    for root, directories, files in os.walk("cogs"):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filepath.endswith(".py"):
                coglist.append(filepath.split(".py")[0].replace("\\", "."))

    for cog in coglist:
        try:
            bot.load_extension(cog)
        except Exception:
            raise Exception
            print(f"Failed to load cog: {cog}")
            hadError = True
    if hadError:
        print("Error during cog loading.")
    else:
        print("Successfully loaded all cogs.")
    bot.run(variables["token"], bot=True, reconnect=True)
