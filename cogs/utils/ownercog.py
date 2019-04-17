import aiohttp
import inspect

import discord
from discord.ext import commands

from utils import customchecks


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Owner Commands"

    @commands.command(name="setavatar", aliases=["changeavatar", "setpic"])
    @customchecks.is_owner()
    async def set_avatar(self, ctx: commands.Context, url: str = ""):
        """
        Changes the bot's avatar.
        Can attach an image or use a URL.
        If no avatar is given, the avatar is reset.
        """
        async def avatar_from_link(location, file=False):
            name = location if not file else location.filename
            url = location if not file else location.url
            if name.lower()[-3:] in ['png', 'jpg', 'gif'] or name.lower()[-4:] in ['jpeg']:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        assert response.status == 200
                        r = await response.read()
                await self.bot.user.edit(avatar=r)
                em = discord.Embed(title="Successfully changed avatar to:",
                                   colour=discord.Colour.dark_green())
                em.set_image(url=url)
            else:
                em = discord.Embed(title="Error",
                                   description="Invalid file format",
                                   colour=discord.Colour.red())
            await ctx.send(embed=em)
        if not url and not ctx.message.attachments:
            await self.bot.user.edit(avatar=None)
            em = discord.Embed(title="Successfully reset avatar.",
                               colour=discord.Colour.dark_green())
            await ctx.send(embed=em)
        elif ctx.message.attachments:
            await avatar_from_link(ctx.message.attachments[0], file=True)
        elif url:
            await avatar_from_link(url)

    @commands.command(name="setname", aliases=["changename", "setusername", "changeusername"])
    @customchecks.is_owner()
    async def set_name(self, ctx: commands.Context, *, name: str):
        """
        Changes the bot's username.
        """
        if len(name) > 32:
            em = discord.Embed(title="Error",
                               description="The name inputted is too long.",
                               colour=discord.Colour.red())
            em.set_footer(text="The maximum name length is 32.")
            await ctx.send(embed=em)
        else:
            await self.bot.user.edit(username=name)
            em = discord.Embed(title=f"Successfully changed name to {name}.",
                               colour=discord.Colour.dark_green())
            await ctx.send(embed=em)

    @commands.command(name="eval", aliases=["debug"])
    @customchecks.is_owner()
    async def eval(self, ctx: commands.Context, *, code: str):
        """
        Evaluates code.
        """
        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

        env = {
            'bot': self.bot,
            'ctx': ctx
        }  # 'message': ctx.message, 'guild': ctx.message.guild, 'channel': ctx.message.channel, 'author': ctx.message.author

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            em = discord.Embed(title="Error",
                               description=python.format(type(e).__name__ + ': ' + str(e)),
                               colour=discord.Colour.red())
            await ctx.send(embed=em)
            return
        em = discord.Embed(title="Eval result",
                           description=python.format(result),
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @set_avatar.error
    async def set_avatar_error_handler(self, ctx, error):
        origerror = getattr(error, 'original', error)
        if isinstance(origerror, AssertionError):
            em = discord.Embed(title="Error",
                               description="The image/link inputted is invalid.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)

    @commands.command(name="setplaying")
    @customchecks.is_owner()
    async def set_playing(self, ctx: commands.Context, *, game: str = None):
        """
        Sets "currently playing" status.
        """
        em = discord.Embed(colour=discord.Colour.dark_green())
        if game is not None:
            await self.bot.change_presence(activity=discord.Game(name=game))
            em.title = f"Successfully set playing as {game}."
        else:
            await self.bot.change_presence(activity=None)
            em.title = "Successfully reset \"playing\"."
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(OwnerCog(bot))
