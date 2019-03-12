"""
Code stolen from https://github.com/Rapptz/discord.py
"""

import functools

import discord
from discord.ext import commands

from . import sql


class NoPermsError(commands.CheckFailure):
    pass


class NoTokenError(Exception):
    pass


def has_any_role(*names):
    def predicate(ctx):
        msg = ctx.message
        if not msg.guild:
            raise NoPermsError()
            return False

        getter = functools.partial(discord.utils.get, msg.author.roles)
        if not any(getter(name=name) is not None for name in names):
            raise NoPermsError()
        return any(getter(name=name) is not None for name in names)
    return commands.check(predicate)


def has_permissions(**perms):
    def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not missing:
            return True
        raise commands.MissingPermissions(missing)
    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        if permissions.administrator:
            return True
        msg = ctx.message
        if not msg.guild:
            raise NoPermsError()
            return False

        getter = functools.partial(discord.utils.get, msg.author.roles)
        modroles = [int(result[0]) for result in await sql.fetch("SELECT roleid FROM modroles WHERE serverid=?", str(ctx.message.guild.id))]
        if not any(getter(id=role) is not None for role in modroles):
            raise NoPermsError()
            return False
        return True
    return commands.check(predicate)


def is_mod_or_has_permissions(**perms):
    async def predicate(ctx):
        msg = ctx.message
        if not msg.guild:
            raise NoPermsError()
            return False
        if msg.author.permissions_in(msg.channel).administrator:
            return True

        getter = functools.partial(discord.utils.get, msg.author.roles)
        modroles = [int(result[0]) for result in await sql.fetch("SELECT roleid FROM modroles WHERE serverid=?", str(ctx.message.guild.id))]

        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not any(getter(id=role) is not None for role in modroles) and missing:
            raise commands.MissingPermissions(missing)
            return False
        return True
    return commands.check(predicate)


def is_owner():
    async def predicate(ctx):
        if not (await ctx.bot.is_owner(ctx.author)):
            raise NoPermsError()
        return True

    return commands.check(predicate)
