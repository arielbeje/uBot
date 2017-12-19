import json

import discord
from discord.ext import commands


with open('variables.json', 'r') as f:
    variables = json.load(f)


class adminCommands:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Admin Commands"

    @commands.command(name="prune", aliases="purge")
    @commands.has_any_role(*variables["modroles"])
    async def prune(self, ctx, prunenum: int):
        """
        Prunes a certain amount of messages. Can also use message ID.
        Maximum amount of messages to prune is 300.
        """
        if prunenum < 300:
            await ctx.channel.purge(limit=prunenum + 1)

        else:
            message = await ctx.get_message(prunenum)
            await ctx.channel.purge(after=message)

    @prune.error
    async def pruneErrorHandler(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):  # Invalid prune number.
            em = discord.Embed(title="Error",
                               description="That message ID is invalid.",
                               colour=0xDC143C)
            await ctx.send(embed=em)
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            em = discord.Embed(title="Error",
                               description=f"{ctx.prefix}prune requires a number of messages or a message ID.",
                               colour=0xDC143C)
            await ctx.send(embed=em)

    @commands.command(name="setnick")
    @commands.has_any_role(*variables["modroles"])
    async def setNick(self, ctx, *, nick: str=None):
        """
        Changes the bot's nickname in this server.
        If no nickname is inputted, the nickname is reset.
        """
        await ctx.guild.me.edit(nick=nick)
        if nick:
            em = discord.Embed(title=f"Successfully changed nickname to \"{nick}\" in {ctx.guild.name}",
                               colour=0x19B300)
        else:
            em = discord.Embed(title=f"Successfully reset nickname in {ctx.guild.name}",
                               colour=0x19B300)
        em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="setplaying")
    @commands.has_any_role(*variables["modroles"])
    async def setPlaying(self, ctx, *, game: str=None):
        """
        Sets "currently playing" status.
        """
        await self.bot.change_presence(game=discord.Game(name=game))
        if game:
            em = discord.Embed(title=f"Successfully set playing as {game}.",
                               colour=0x19B300)
        else:
            em = discord.Embed(title="Successfully reset \"playing\".",
                               colour=0x19B300)
        em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(adminCommands(bot))
