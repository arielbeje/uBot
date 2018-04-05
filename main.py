import asyncio
import os
import json
import re
import rethinkdb as r

import discord
from discord.ext import commands

import utils.customchecks as customchecks

failedOps = 0

with open('variables.json', 'r') as f:
    variables = json.load(f)

if not variables["token"]:
    failedOps += 1
    print("No token inputted in variables.json."
          "The bot will not run without it.")

if os.path.exists('data/reminderdb.json'):
    with open('data/reminderdb.json', 'r') as f:
        reminderdb = json.load(f)
else:
    print(f"Reminder DB not found.")
    failedOps += 1

if not variables["joinleavechannelid"]:
    print("No channel ID for the leave/join events was inputted in variables.json."
          "The events will not run without it.")
    joinLeaveID = 0
    failedOps += 1
else:
    joinLeaveID = int(variables["joinleavechannelid"])
    print(joinLeaveID)

if not variables["myanimelist"]["login"] or variables["myanimelist"]["password"]:
    print("No username/password inputted in variables.json."
          "The MyAnimeList API requires them to function.")
    failedOps += 1


def get_prefix(bot, message):
    with r.connect(db="bot") as conn:
        prefixes = r.table("servers").get(
            message.guild.id).pluck("prefixes").run(conn)["prefixes"]

    if message.guild is None:
        return variables["prefixes"][0]

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)

if joinLeaveID is not 0:
    joinLeaveChannel = bot.get_channel(joinLeaveID)


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
    print(
        f"\n~-~-~-~-~-~-~-~-~\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}")
    servers = len(bot.guilds)
    users = len(bot.users)
    print(f"Serving {users} users in " + str(servers) +
          " server" + ("s" if servers > 1 else "") + ".")
    # Health log
    if failedOps != 0:
        print(f'{failedOps} operations failed.')
    print(joinLeaveID)
    print("~-~-~-~-~-~-~-~-~")


@bot.event
async def on_guild_join(guild):
    print("~-~-~-~-~-~-~-~-~\n" +
          f"Joined server {guild.id} - {guild.name}.\n" +
          "~-~-~-~-~-~-~-~-~")
    with r.connect(db="bot") as conn:
        if not r.table("servers").get(guild.id).run(conn):
            r.table("servers").insert({"id": guild.id,
                                       "prefixes": ["+"],
                                       "faq": {},
                                       "modroles": ["Bot Commander"]
                                       }).run(conn)


@bot.event
async def on_guild_remove(guild):
    print("~-~-~-~-~-~-~-~-~\n" +
          f"Left server {guild.id} - {guild.name}.\n" +
          "~-~-~-~-~-~-~-~-~")
    with r.connect(db="bot") as conn:
        r.table("servers").get(guild.id).delete().run(conn)

wikiEx = re.compile(r"\[\[(.*?)\]\]")
_wikiEx = re.compile(r"\`[\S\s]*?\[\[(.*?)\]\][\S\s]*?\`")
modEx = re.compile(r"\{\{(.*?)\}\}")
_modEx = re.compile(r"\`[\S\s]*?\{\{(.*?)\}\}[\S\s]*?\`")


@bot.event
async def on_message(message):
    msg = message.content
    wikiSearch = None if not wikiEx.search(msg) or _wikiEx.search(msg) else wikiEx.search(msg).group(1)
    modSearch = None if not modEx.search(msg) or _modEx.search(msg) else modEx.search(msg).group(1)
    if wikiSearch or modSearch:
        ctx = await bot.get_context(message)
        if wikiSearch:
            await ctx.invoke(bot.get_command("wiki"), searchterm=wikiSearch)
        elif modSearch:
            await ctx.invoke(bot.get_command("linkmod"), modname=modSearch)
    else:
        message.content = message.content.split(variables["comment"])[0]
        await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    if joinLeaveID is not 0:
        joinLeaveChannel = bot.get_channel(joinLeaveID)
    await joinLeaveChannel.send(f"Join - {member.mention}, account created at {member.created_at}."
                                f"ID {member.id}. {len(member.guild.members)} members.")


@bot.event
async def on_member_remove(member):
    print(joinLeaveID)
    if joinLeaveID is not 0:
        joinLeaveChannel = bot.get_channel(joinLeaveID)
    await joinLeaveChannel.send(f"Leave - {member.name}. ID {member.id}."
                                f"{len(member.guild.members)} members.")


@bot.event
async def on_member_ban(guild, member):
    if joinLeaveID is not 0:
        joinLeaveChannel = bot.get_channel(joinLeaveID)
    await joinLeaveChannel.send(f"Ban - {member.name}, ID {member.id}."
                                f"Joined at {member.joined_at}.")


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
            print(f'Loaded {cog} successfully')
        except Exception:
            # raise Exception
            print(f"Failed to load cog: {cog}")
            failedOps += 1
            hadError = True
    if hadError:
        print("Error during cog loading.")
    else:
        print("Successfully loaded all cogs.")
    bot.run(variables["token"], bot=True, reconnect=True)
