from ago import human
import re
import pytz
import html

import discord
from discord.ext import commands

tagregex = re.compile(r"<.*?>")
ampregex = re.compile(r"&amp;#(\d*);")


def amp_repl(matchobj):
    return chr(int(matchobj.group(1)))


def clean_xml(inputdata):
    return tagregex.sub("", html.unescape(ampregex.sub(amp_repl, inputdata)))


class UserUtils(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Utility Commands"

    @commands.command(name="userinfo")
    async def user_info(self, ctx, user: discord.User = None):
        """Returns information about the given user"""
        if not user:
            user = ctx.message.author
        member = ctx.message.guild.get_member(user.id)
        em = discord.Embed(colour=discord.Colour.gold())
        activity = member.activity
        inlineFields = [
            {"name": "ID", "value": member.id},
            {"name": "Nickname", "value": member.nick if not None else "None"},
            {"name": "Status", "value": member.status},
            {"name": activity.state if type(activity) is not discord.Spotify else activity.title, "value": activity.name} if activity else
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
    async def info(self, ctx):
        """Shows info about the bot"""
        em = discord.Embed(title="uBot",
                           colour=discord.Colour.gold())
        em.add_field(name="Creator", value="arielbeje - <@114814850621898755>")
        em.add_field(name="Source", value="[GitHub](https://github.com/arielbeje/uBot)")
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(UserUtils(bot))
