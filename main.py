import asyncio
import datetime
import os
import pytz
import re

import logging
from logging.handlers import TimedRotatingFileHandler

import discord
from discord.ext import commands

from utils import customchecks, sql, punishmentshelper

workDir = os.getcwd()
logDir = os.path.join(workDir, "logs")
if not os.path.exists(logDir):
    os.makedirs(logDir)

fh = TimedRotatingFileHandler("logs/log", "midnight", encoding="utf-8", backupCount=7)
fh.setFormatter(logging.Formatter(fmt="[%(asctime)s] [%(name)-19s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
logging.basicConfig(handlers=[fh, ch],
                    level=logging.INFO)
logger = logging.getLogger('root')

intents = discord.Intents.none()
intents.bans = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.presences = True

if "UBOT" not in os.environ:
    logger.critical("Couldn't find a token. Please enter one in the UBOT environment variable. "
                    "The bot will not run without it")
    raise customchecks.NoTokenError()


async def initdb():
    """
    Initializes the database (makes sure that all tables are present)
    """
    tables = [table[0] for table in await sql.fetch("SELECT name FROM sqlite_master WHERE type='table'")]
    if any(table not in tables for table in ["servers", "faq", "prefixes", "modroles"]):
        if "servers" not in tables:
            await sql.execute("CREATE TABLE servers (serverid varchar(18) PRIMARY KEY, joinleavechannel varchar(18), comment text, muteroleid varchar(18))")
        if "faq" not in tables:
            await sql.execute("CREATE TABLE faq (serverid varchar(18), title text, content text, image text, creator varchar(18), timestamp timestamptz, link text)")
        if "prefixes" not in tables:
            await sql.execute("CREATE TABLE prefixes (serverid varchar(18), prefix text)")
        if "modroles" not in tables:
            await sql.execute("CREATE TABLE modroles (serverid varchar(18), roleid varchar(18))")
        if "mutes" not in tables:
            await sql.execute("CREATE TABLE mutes (serverid varchar(18), userid varchar(18), until timestamptz)")
        if "bans" not in tables:
            await sql.execute("CREATE TABLE bans (serverid varchar(18), userid varchar(18), until timestamptz)")


async def get_prefix(bot: commands.AutoShardedBot, message: discord.Message):
    """
    Returns the prefix(es) for the bot
    """
    prefixes = await sql.fetch("SELECT prefix FROM prefixes WHERE serverid=?", str(message.guild.id))
    prefixes = [prefix[0] for prefix in [prefix[0] for prefix in prefixes]]
    return commands.when_mentioned_or(*prefixes)(bot, message) if prefixes else commands.when_mentioned(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, intents=intents)


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    origerror = getattr(error, "original", error)
    if isinstance(origerror, commands.errors.CommandNotFound):
        pass
    elif isinstance(origerror, commands.MissingPermissions):
        description = origerror.args[0].replace('run command', f'use the command `{ctx.command}`')
        em = discord.Embed(title="Error",
                           description=description,
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
    elif isinstance(origerror, customchecks.NotAModError):
        em = discord.Embed(title="Error",
                           description=f"You are not a moderator on this server.\n" +
                                       f"For modifying moderator roles, see `{ctx.prefix}help modroles`",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
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
                           description=f"I've encountered an error ({type(origerror)}). Please contact my creator. ```{errorMsg}```",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
        raise error


@bot.event
async def on_ready():
    # In case the bot was off when leaving/joining a guild
    logger.info("Verifying guilds match DB")
    guilds = bot.guilds
    guildIds = [guild.id for guild in guilds]
    missingGuildIds = [guildId for guildId in guildIds if len(await sql.fetch("SELECT 1 FROM servers WHERE serverid=?", str(guildId))) == 0]
    for guildId in missingGuildIds:
        logger.debug(f"Added guild with id {guildId} to DB")
        await sql.initserver(guildId)
    undeletedGuildIds = [guildId[0] for guildId in await sql.fetch("SELECT serverid FROM servers") if int(guildId[0]) not in guildIds]
    for guildId in undeletedGuildIds:
        logger.debug(f"Removed guild with id {guildId} from DB")
        await sql.deleteserver(guildId)

    unfinishedMutes = await sql.fetch("SELECT * FROM mutes")
    utcnow = pytz.utc.localize(datetime.datetime.utcnow())
    for serverid, userid, until in unfinishedMutes:
        if until is None:
            continue
        until = datetime.datetime.strptime(until, "%Y-%m-%d %H:%M:%S%z")
        roleid = (await sql.fetch("SELECT muteroleid FROM servers WHERE serverid=?", serverid))[0][0]
        guild = bot.get_guild(int(serverid))
        if roleid is not None:
            role = guild.get_role(int(roleid))
        else:
            role = None
        member = guild.get_member(int(userid))
        if utcnow >= until:
            if member is not None and role is not None:
                await member.remove_roles(role, reason="Temporary mute ended.")
            await sql.execute("DELETE FROM mutes WHERE serverid=? AND userid=?", serverid, userid)
        else:
            duration = (until - utcnow).total_seconds()
            asyncio.ensure_future(punishmentshelper.ensure_unmute(guild, int(userid), duration, role, partialDuration=True))

    unfinishedBans = await sql.fetch("SELECT * FROM bans")
    for serverid, userid, until in unfinishedBans:
        until = datetime.datetime.strptime(until, "%Y-%m-%d %H:%M:%S%z")
        guild = bot.get_guild(int(serverid))
        guildBans = guild.bans()
        userid = int(userid)
        async for _, user in guildBans:
            if user.id == userid:
                break
        else:
            await sql.execute("DELETE FROM bans WHERE serverid=? AND userid=?", serverid, userid)
            continue
        if utcnow >= until:
            user = await guild.unban(user, reason="Temporary ban ended.")
            await sql.execute("DELETE FROM bans WHERE serverid=? AND userid=?", serverid, userid)
        else:
            duration = (until - utcnow).total_seconds()
            asyncio.ensure_future(punishmentshelper.ensure_unban(guild, user, duration, partialDuration=True))

    logger.info(f"Logged in as: {bot.user.name} - {bot.user.id}")
    logger.info(f"Serving {len(bot.users)} users in {len(guilds)} server{('s' if len(guilds) > 1 else '')}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Joined server \'{guild.name}\' - {guild.id}")
    await sql.initserver(guild.id)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    logger.info(f"Left server \'{guild.name}\' - {guild.id}")
    await sql.deleteserver(guild.id)

wikiEx = re.compile(r"\[\[(.*?)\]\]")
negativeWikiEx = re.compile(r"\`[\S\s]*?\[\[(.*?)\]\][\S\s]*?\`")
modEx = re.compile(r"\>\>(.*?)\<\<")
negativeModEx = re.compile(r"\`[\S\s]*?\>\>(.*?)\<\<[\S\s]*?\`")


@bot.event
async def on_message(message: discord.Message):
    if not isinstance(message.channel, discord.abc.GuildChannel) and not isinstance(message.channel, discord.Thread) and not isinstance(message.channel, discord.ForumChannel):
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
async def on_member_join(member: discord.Member):
    joinLeaveRow = await sql.fetch("SELECT joinleavechannel FROM servers WHERE serverid=?", str(member.guild.id))
    if len(joinLeaveRow) > 0:  # To avoid errors if the bot was the one removed
        joinLeaveID = joinLeaveRow[0][0]
        if joinLeaveID is not None:
            joinLeaveChannel = bot.get_channel(int(joinLeaveID))
            await joinLeaveChannel.send(f"**Join** - {member.mention}, account created at {member.created_at.isoformat()}.\n"
                                        f"ID {member.id}. {member.guild.member_count} members.")
    muteRow = await sql.fetch("SELECT * FROM mutes WHERE userid=?", str(member.id))
    if len(muteRow) > 0:
        muteRow = muteRow[0]
        roleRow = await sql.fetch("SELECT muteroleid FROM servers WHERE serverid=?",
                                  str(member.guild.id))
        if roleRow[0][0] is not None:
            role = member.guild.get_role(int(roleRow[0][0]))
        else:
            role = None
        if muteRow[2] is not None and role is not None:
            utcnow = pytz.utc.localize(datetime.datetime.utcnow())
            until = datetime.datetime.strptime(muteRow[2], "%Y-%m-%d %H:%M:%S%z")
            if utcnow < until:
                await member.add_roles(role)  # ensure_unmute is already running
        elif role is not None:
            await member.add_roles(role)


@bot.event
async def on_member_remove(member: discord.Member):
    joinLeaveRow = await sql.fetch("SELECT joinleavechannel FROM servers WHERE serverid=?", str(member.guild.id))
    if len(joinLeaveRow) > 0:
        joinLeaveID = joinLeaveRow[0][0]
        if joinLeaveID is not None:
            joinLeaveChannel = bot.get_channel(int(joinLeaveID))
            await joinLeaveChannel.send(f"**Leave** - {member.name}. ID {member.id}.\n"
                                        f"{member.guild.member_count} members.")


@bot.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
    joinLeaveRow = await sql.fetch("SELECT joinleavechannel FROM servers WHERE serverid=?", str(guild.id))
    if len(joinLeaveRow) > 0:
        joinLeaveID = joinLeaveRow[0][0]
        if joinLeaveID is not None:
            joinLeaveChannel = bot.get_channel(int(joinLeaveID))
            await joinLeaveChannel.send(f"**Ban** - {user.name}, ID {user.id}.\n")


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
            asyncio.get_event_loop().run_until_complete(bot.load_extension(cog))
            logger.debug(f"Loaded {cog} successfully")
        except Exception:
            logger.exception(f"Failed to load cog: {cog}")
            hadError = True
    if hadError:
        logger.warning("Error during cog loading")
    else:
        logger.info("Successfully loaded all cogs")
    bot.run(os.environ["UBOT"], reconnect=True)
