import json
import logging
import os
import re
import rethinkdb as r

import discord
from discord.ext import commands

from utils import customchecks

logging.basicConfig(level=logging.DEBUG,
                    format="[%(asctime)s] [%(name)-19s] %(levelname)-8s: %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S%z",
                    filename="log.log",
                    filemode="w+")
logger = logging.getLogger('root')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
logger.addHandler(ch)

with open("variables.json", "r") as f:
    variables = json.load(f)

if not variables["token"]:
    logger.critical("No token inputted in variables.json. "
                    "The bot will not run without it")
    raise customchecks.NoTokenError()

if not variables["joinleavechannelid"]:
    logger.warn("No channel ID for the leave/join events was inputted in variables.json. "
                "The events will not run without it")
    joinLeaveID = 0
else:
    joinLeaveID = int(variables["joinleavechannelid"])
    logger.info(f"Using channel with id {joinLeaveID} for join/leave events")


def get_prefix(bot, message):
    with r.connect(db="bot") as conn:
        prefixes = r.table("servers").get(
            message.guild.id).pluck("prefixes").run(conn)["prefixes"]

    if message.guild is None:
        return variables["prefixes"][0]

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix)

if joinLeaveID is not 0:
    joinLeaveChannel = bot.get_channel(joinLeaveID)


@bot.event
async def on_command_error(ctx, error):
    origerror = getattr(error, "original", error)
    if isinstance(origerror, customchecks.NoPermsError):
        em = discord.Embed(title="Error",
                           description=f"You do not have sufficient permissions to use the command `{ctx.command}`",
                           colour=0xDC143C)
        return await ctx.send(embed=em)
    else:
        raise error


@bot.event
async def on_ready():
    logger.info(f"Logged in as: {bot.user.name} - {bot.user.id}")
    logger.info(f"Serving {len(bot.users)} users in {len(bot.guilds)} server{('s' if len(bot.guilds) > 1 else '')}")


@bot.event
async def on_guild_join(guild):
    logger.info(f"Joined server \'{guild.name}\' - {guild.id}")
    with r.connect(db="bot") as conn:
        if not r.table("servers").get(guild.id).run(conn):
            r.table("servers").insert({"id": guild.id,
                                       "prefixes": ["+"],
                                       "faq": {},
                                       "modroles": ["Bot Commander"]
                                       }).run(conn)


@bot.event
async def on_guild_remove(guild):
    logger.info(f"Left server \'{guild.name}\' - {guild.id}")
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
        await joinLeaveChannel.send(f"Join - {member.mention}, account created at {member.created_at}.\n"
                                    f"ID {member.id}. {len(member.guild.members)} members.")


@bot.event
async def on_member_remove(member):
    if joinLeaveID is not 0:
        joinLeaveChannel = bot.get_channel(joinLeaveID)
        await joinLeaveChannel.send(f"Leave - {member.name}. ID {member.id}.\n"
                                    f"{len(member.guild.members)} members.")


@bot.event
async def on_member_ban(guild, member):
    if joinLeaveID is not 0:
        joinLeaveChannel = bot.get_channel(joinLeaveID)
        await joinLeaveChannel.send(f"Ban - {member.name}, ID {member.id}."
                                    f"Joined at {member.joined_at}.")


if __name__ == "__main__":
    hadError = False
    coglist = []

    for root, directories, files in os.walk("cogs"):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filepath.endswith(".py"):
                coglist.append(filepath.split(".py")[0].replace("\\", "."))

    logger.debug("Loading cogs")
    for cog in coglist:
        logger.debug(f"Loading {cog}")
        try:
            bot.load_extension(cog)
            logger.debug(f"Loaded {cog} successfully")
        except Exception:
            logger.exception(f"Failed to load cog: {cog}")
            hadError = True
    if hadError:
        logger.warning("Error during cog loading")
    else:
        logger.info("Successfully loaded all cogs")
    bot.run(variables["token"], bot=True, reconnect=True)
