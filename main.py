import asyncio
import os
import re

import logging
from logging.handlers import TimedRotatingFileHandler

import discord
from discord.ext import commands

from utils import customchecks, sql

workDir = os.getcwd()
logDir = os.path.join(workDir, "logs")
if not os.path.exists(logDir):
    os.makedirs(logDir)

fh = TimedRotatingFileHandler("logs/log", "midnight", encoding="utf-8", backupCount=7)
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(fmt="[%(asctime)s] [%(name)-19s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
logging.basicConfig(handlers=[fh, ch],
                    level=logging.DEBUG)
logger = logging.getLogger('root')

if "UBOT" not in os.environ:
    logger.critical("Couldn't find a token. Please enter one in the UBOT environment variable. "
                    "The bot will not run without it")
    raise customchecks.NoTokenError()


async def initdb():
    tables = [table[0] for table in await sql.fetch("SELECT name FROM sqlite_master WHERE type='table'")]
    if any(table not in tables for table in ["servers", "faq", "prefixes", "modroles"]):
        if "servers" not in tables:
            await sql.execute("CREATE TABLE servers (serverid varchar(20) PRIMARY KEY, joinleavechannel varchar(20), comment text)")
        if "faq" not in tables:
            await sql.execute("CREATE TABLE faq (serverid varchar(20), title text, content text, image text, creator varchar(20), timestamp timestamptz, link text)")
        if "prefixes" not in tables:
            await sql.execute("CREATE TABLE prefixes (serverid varchar(20), prefix text)")
        if "modroles" not in tables:
            await sql.execute("CREATE TABLE modroles (serverid varchar(20), roleid varchar(20))")


async def get_prefix(bot, message):
    prefixes = await sql.fetch("SELECT prefix FROM prefixes WHERE serverid=?", str(message.guild.id))
    prefixes = [prefix[0] for prefix in [prefix[0] for prefix in prefixes]]
    return commands.when_mentioned_or(*prefixes)(bot, message) if prefixes else commands.when_mentioned(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix)


@bot.event
async def on_command_error(ctx, error):
    origerror = getattr(error, "original", error)
    if isinstance(origerror, customchecks.NoPermsError):
        em = discord.Embed(title="Error",
                           description=f"You do not have sufficient permissions to use the command `{ctx.command}`",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(origerror, commands.MissingPermissions):
        description = origerror.args[0].replace('run command', f'use the command `{ctx.command}`')
        em = discord.Embed(title="Error",
                           description=description,
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(origerror, discord.ext.commands.errors.CommandNotFound):
        pass
    elif isinstance(origerror, discord.errors.Forbidden):
        em = discord.Embed(title="Error",
                           description="I don't have sufficient permissions to do that.",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
    else:
        try:
            errorMsg = origerror.message
        except AttributeError:
            errorMsg = str(origerror)
        em = discord.Embed(title="Error",
                           description="I've encountered an error. Please contact my creator.\n" +
                                       f"```{errorMsg}```",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
        raise error


@bot.event
async def on_ready():
    logger.info(f"Logged in as: {bot.user.name} - {bot.user.id}")
    logger.info(f"Serving {len(bot.users)} users in {len(bot.guilds)} server{('s' if len(bot.guilds) > 1 else '')}")


@bot.event
async def on_guild_join(guild):
    logger.info(f"Joined server \'{guild.name}\' - {guild.id}")
    await sql.initserver(guild.id)


@bot.event
async def on_guild_remove(guild):
    logger.info(f"Left server \'{guild.name}\' - {guild.id}")
    await sql.deleteserver(guild.id)

wikiEx = re.compile(r"\[\[(.*?)\]\]")
negativeWikiEx = re.compile(r"\`[\S\s]*?\[\[(.*?)\]\][\S\s]*?\`")
modEx = re.compile(r"\>\>(.*?)\<\<")
negativeModEx = re.compile(r"\`[\S\s]*?\>\>(.*?)\<\<[\S\s]*?\`")


@bot.event
async def on_message(message):
    if not isinstance(message.channel, discord.abc.GuildChannel):
        return
    msg = message.content
    comment = await sql.fetch("SELECT comment FROM servers WHERE serverid=?", str(message.guild.id))
    comment = comment[0][0] if len(comment) > 0 and str(comment[0]) != "None" else None
    wikiSearch = None if not wikiEx.search(msg) or negativeWikiEx.search(msg) else wikiEx.search(msg).group(1)
    modSearch = None if not modEx.search(msg) or negativeModEx.search(msg) else modEx.search(msg).group(1)
    if wikiSearch or modSearch:
        ctx = await bot.get_context(message)
        if wikiSearch:
            await ctx.invoke(bot.get_command("wiki"), searchterm=wikiSearch)
        elif modSearch:
            await ctx.invoke(bot.get_command("linkmod"), modname=modSearch)
    else:
        if comment is not None:
            message.content = message.content.split(comment)[0]
        await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    joinLeaveRow = await sql.fetch("SELECT joinleavechannel FROM servers WHERE serverid=?", str(member.guild.id))
    if len(joinLeaveRow) > 0:  # To avoid errors if the bot was the one removed
        joinLeaveID = joinLeaveRow[0][0]
        if joinLeaveID is not None:
            joinLeaveChannel = bot.get_channel(int(joinLeaveID))
            await joinLeaveChannel.send(f"**Join** - {member.mention}, account created at {member.created_at.isoformat()}.\n"
                                        f"ID {member.id}. {len(member.guild.members)} members.")


@bot.event
async def on_member_remove(member):
    joinLeaveRow = await sql.fetch("SELECT joinleavechannel FROM servers WHERE serverid=?", str(member.guild.id))
    if len(joinLeaveRow) > 0:
        joinLeaveID = joinLeaveRow[0][0]
        if joinLeaveID is not None:
            joinLeaveChannel = bot.get_channel(int(joinLeaveID))
            await joinLeaveChannel.send(f"**Leave** - {member.name}. ID {member.id}.\n"
                                        f"{len(member.guild.members)} members.")


@bot.event
async def on_member_ban(guild, member):
    joinLeaveRow = await sql.fetch("SELECT joinleavechannel FROM servers WHERE serverid=?", str(member.guild.id))
    if len(joinLeaveRow) > 0:
        joinLeaveID = joinLeaveRow[0][0]
        if joinLeaveID is not None:
            joinLeaveChannel = bot.get_channel(int(joinLeaveID))
            await joinLeaveChannel.send(f"**Ban** - {member.name}, ID {member.id}.\n"
                                        f"Joined at {member.joined_at.isoformat()}.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(initdb())

    hadError = False
    coglist = []

    for root, directories, files in os.walk("cogs"):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filepath.endswith(".py"):
                coglist.append(filepath.split(".py")[0].replace(os.sep, "."))

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
    bot.run(os.environ["UBOT"], bot=True, reconnect=True)
