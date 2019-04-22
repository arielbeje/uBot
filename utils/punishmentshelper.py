import asyncio
import humanfriendly
from . import sql

import discord

from typing import Union


async def ensure_unmute(server: discord.Guild, member: discord.Member, duration: int,
                        role: discord.Role, partialDuration: bool = False):
    """
    Sleeps for the given duration, then unmutes the member.
    Also removes the mute row from the db.
    """
    await asyncio.sleep(duration)
    reason = "Temporary mute " + (f"of {humanfriendly.format_timespan(duration)} " if not partialDuration else "") + "ended."
    await member.remove_roles(role, reason=reason)
    await sql.execute("DELETE FROM mutes WHERE serverid=? AND userid=?",
                      str(server.id), str(member.id))


async def ensure_unban(server: discord.Guild, member: Union[discord.Member, discord.User],
                       duration: int, partialDuration: bool = False):
    """
    Sleeps for the given duration, then unbans the member.
    Also removes the ban row from the db.
    """
    await asyncio.sleep(duration)
    reason = "Temporary ban " + (f"of {humanfriendly.format_timespan(duration)} " if not partialDuration else "") + "ended."
    await server.unban(member, reason=reason)
    await sql.execute("DELETE FROM bans WHERE serverid=? AND userid=?",
                      str(server.id), str(member.id))
