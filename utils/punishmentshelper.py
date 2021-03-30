import asyncio
import datetime
import humanfriendly
from . import sql

import discord

from typing import Union


async def lazily_fetch_member(guild: discord.Guild, user_id: int):
    return guild.get_member(user_id) or await guild.fetch_member(user_id)


async def ensure_unmute(server: discord.Guild, member_id: int, duration: int,
                        role: discord.Role, partialDuration: bool = False):
    """
    Sleeps for the given duration, then unmutes the member.
    Also removes the mute row from the db.
    """
    await asyncio.sleep(duration)
    reason = "Temporary mute " + (f"of {humanfriendly.format_timespan(duration)} " if not partialDuration else "") + "ended."
    member = await lazily_fetch_member(server, member_id)
    if member is not None:
        try:
            await member.remove_roles(role, reason=reason)
        except discord.HTTPException:
            pass
    await sql.execute("DELETE FROM mutes WHERE serverid=? AND userid=?",
                      str(server.id), str(member_id))


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


async def notify(member: discord.Member, punisher: discord.Member, title: str,
                 reason: str, duration: int = None, until: datetime.datetime = None):
    """
    Sends a private message to the member (if allowed) with the details of the punishment.
    """
    em = discord.Embed(title=title + " notification",
                       colour=discord.Colour.red())
    em.add_field(name="Server", value=f"{member.guild.name} (ID {member.guild.id})", inline=False)
    if duration and until:
        em.add_field(name="Duration", value=humanfriendly.format_timespan(duration), inline=False)
        em.timestamp = until
        em.set_footer(text="Will last until")  # Footer will be `Will last until • {until}`
    if reason is not None:
        em.add_field(name="Reason", value=reason, inline=False)
    em.add_field(name="Punished/modified by", value=f"{punisher.display_name} - {punisher.mention}")
    try:
        await member.send(embed=em)
    except discord.errors.Forbidden:
        pass
