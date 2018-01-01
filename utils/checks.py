"""
Code stolen from https://github.com/Rapptz/discord.py
"""

import asyncio
import functools

import discord
from discord.ext import commands


class NoPermsError(commands.CheckFailure):
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


def is_owner():
    @asyncio.coroutine
    def predicate(ctx):
        if not (yield from ctx.bot.is_owner(ctx.author)):
            raise NoPermsError()
        return True

    return commands.check(predicate)


def has_permissions(**perms):
    def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]

        if not missing:
            return True

        print(missing)
        raise NoPermsError(missing)
    return commands.check(predicate)
