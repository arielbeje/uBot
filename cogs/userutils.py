from ago import human
import pytz

import discord
from discord.ext import commands

from typing import Tuple, Union


def activity_info(activity: Union[discord.Spotify, discord.Game, discord.Streaming, discord.Activity]) -> Tuple[str, str]:
    """
    Returns the proper title and name for the activity given
    """
    if activity.type == discord.ActivityType.listening:
        return ("Listening to", activity.title)
    elif activity.type == discord.ActivityType.playing:
        return ("Playing", activity.name)
    elif activity.type == discord.ActivityType.streaming:
        return ("Streaming", activity.name)
    elif activity.type == discord.ActivityType.watching:
        return ("Watching", activity.name)
    return (activity.state, activity.name)


class UserUtils(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Utility Commands"

    @commands.command(name="userinfo")
    async def user_info(self, ctx: commands.Context, user: discord.User = None):
        """Returns information about the given user"""
        if not user:
            user = ctx.message.author
        member = ctx.message.guild.get_member(user.id)
        em = discord.Embed(colour=discord.Colour.gold())
        activityInfo = activity_info(member.activity) if member.activity else None
        inlineFields = [
            {"name": "ID", "value": member.id},
            {"name": "Nickname", "value": str(member.nick)},
            {"name": "Status", "value": member.status},
            {"name": activityInfo[0], "value": activityInfo[1]} if activityInfo is not None else
            {"name": "Activity", "value": "None"},
            {"name": "Mention", "value": member.mention}
        ]
        for field in inlineFields:
            em.add_field(**field, inline=True)
        avatar = user.avatar_url_as(size=64)  # if not None else discord.Embed.Empty
        registeredAt = pytz.utc.localize(member.created_at)
        joinedAt = pytz.utc.localize(member.joined_at)
        em.add_field(name="Joined", value=f"{human(joinedAt, precision=4)} ({joinedAt.strftime('%d-%m-%Y %H:%M:%s %Z')})")
        em.add_field(name="Roles", value=", ".join([role.name for role in member.roles]).replace("@everyone", "@\u200beveryone"))
        em.set_author(name=member.name, icon_url=avatar)
        em.set_thumbnail(url=avatar)
        em.set_footer(text=f"Created: {human(registeredAt, precision=4)} ({registeredAt.strftime('%d-%m-%Y %H:%M:%s %Z')})")
        await ctx.send(embed=em)

    @commands.command()
    async def info(self, ctx: commands.Context):
        """Shows info about the bot"""
        em = discord.Embed(title="uBot",
                           colour=discord.Colour.gold())
        em.add_field(name="Creator", value="arielbeje - <@114814850621898755>")
        em.add_field(name="Source", value="[GitHub](https://github.com/arielbeje/uBot)")
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(UserUtils(bot))
