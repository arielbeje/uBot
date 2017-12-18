import aiohttp
import inspect
import io

import discord
from discord.ext import commands


class ownerCog():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setavatar", aliases=["changeavatar", "setpic"])
    @commands.is_owner()
    async def setAvatar(self, ctx, url: str=""):
        """
        Set the bot's avatar.
        Can attach an image or use a URL.
        """
        if not url and not ctx.message.attachments:
            await self.bot.user.edit(avatar=None)
            em = discord.Embed(title="Successfully reset avatar.",
                               colour=0x19B300)
        elif ctx.message.attachments:
            image = ctx.message.attachments[0]
            if image.filename.lower()[-3:] in ['png', 'jpg'] or image.filename.lower()[-4:] in ['jpeg']:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image.url) as response:
                        assert response.status == 200
                        r = await response.read()
                await self.bot.user.edit(avatar=r)
                em = discord.Embed(title="Successfully changed avatar to:",
                                   colour=0x19B300)
                em.set_image(url=image.url)
                em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        elif url:
            if url.lower()[-3:] in ['png', 'jpg'] or url.lower()[-4:] in ['jpeg']:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        assert response.status == 200
                        r = await response.read()
                await self.bot.user.edit(avatar=r)
                em = discord.Embed(title="Successfully changed avatar to:",
                                   colour=0x19B300)
                em.set_image(url=url)
                em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="setname", aliases=["changename", "setusername", "changeusername"])
    @commands.is_owner()
    async def setName(self, ctx, *, name: str):
        """
        Change the bot's username.
        """
        if len(name) > 32:
            em = discord.Embed(title="Error",
                               description="The name inputted is too long.",
                               colour=0xDC143C)
            em.set_footer(text="The maximum name length is 32.")
            await ctx.send(embed=em)
        else:
            await self.bot.user.edit(username=name)
            em = discord.Embed(title=f"Successfully changed name to {name}.",
                               colour=0x19B300)
            await ctx.send(embed=em)

    '''@commands.command(name="setnickname", aliases=["setnick", "editnick", "editnickname"])
    @commands.is_owner()
    async def setNickname(self, ctx, *, name: str):'''

    @commands.command(name="eval", aliases=["debug"])
    @commands.is_owner()
    async def eval(self, ctx, *, code: str):
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
                               colour=0xDC143C)
            await ctx.send(embed=em)
            return
        em = discord.Embed(title="Eval result",
                           description=python.format(result),
                           colour=0x19B300)
        await ctx.send(embed=em)

    @setAvatar.error
    async def setAvatarErrorHandler(self, ctx, error):
        origerror = getattr(error, 'original', error)
        if isinstance(origerror, AssertionError):
            em = discord.Embed(title="Error",
                               description="The image/link inputted is invalid.",
                               colour=0xDC143C)
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(ownerCog(bot))
