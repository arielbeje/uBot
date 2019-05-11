"""
Code stolen from https://github.com/Rapptz/discord.py
"""

import functools

import discord
from discord.ext import commands

from . import sql


class NotAModError(commands.CheckFailure):
    pass


class NoTokenError(Exception):
    pass


def is_mod():
    async def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        if permissions.administrator:
            return True
        msg = ctx.message
        if not msg.guild:
            raise NotAModError()
            return False

        getter = functools.partial(discord.utils.get, msg.author.roles)
        modroles = [int(result[0]) for result in await sql.fetch("SELECT roleid FROM modroles WHERE serverid=?", str(ctx.message.guild.id))]
        if not any(getter(id=role) is not None for role in modroles):
            raise NotAModError()
            return False
        return True
    return commands.check(predicate)
