from ago import human

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

    @commands.hybrid_command(name="userinfo")
    async def user_info(self, ctx: commands.Context, member: discord.Member = None):
        """Returns information about the given member"""
        member = member or ctx.author
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
        avatar = member.avatar.replace(size=64)
        em.add_field(name="Joined", value=f"{human(member.joined_at, precision=4)} ({member.joined_at.replace(microsecond=0).isoformat()})")
        em.add_field(name="Roles", value=", ".join([role.name for role in member.roles]).replace("@everyone", "@\u200beveryone"))
        em.set_author(name=member.name, icon_url=avatar)
        em.set_thumbnail(url=avatar)
        em.set_footer(text=f"Created: {human(member.created_at, precision=4)} ({member.created_at.replace(microsecond=0).isoformat()})")
        await ctx.send(embed=em)

    @commands.hybrid_command()
    async def info(self, ctx: commands.Context):
        """Shows info about the bot"""
        em = discord.Embed(title="uBot",
                           colour=discord.Colour.gold())
        em.add_field(name="Creator", value="arielbeje - <@114814850621898755>")
        em.add_field(name="Source", value="[GitHub](https://github.com/arielbeje/uBot)")
        em.add_field(name="Invite link", value="[Link](https://discordapp.com/oauth2/authorize?&client_id=334003132583510016&scope=bot&permissions=0)")
        await ctx.send(embed=em)


async def setup(bot):
    await bot.add_cog(UserUtils(bot))
