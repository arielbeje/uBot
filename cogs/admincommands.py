import json

import discord
from discord.ext import commands

import utils.checks as customchecks

with open('variables.json', 'r') as f:
    variables = json.load(f)


class AdminCommands:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Admin Commands"

    @commands.command(name="prune", aliases="purge")
    @customchecks.has_any_role(*variables["modroles"])
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
    async def prune_error_handler(self, ctx, error):
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
    @customchecks.has_any_role(*variables["modroles"])
    async def set_nick(self, ctx, *, nick: str=None):
        """
        Changes the bot's nickname in this server.
        If no nickname is inputted, the nickname is reset.
        """
        await ctx.guild.me.edit(nick=nick)
        em = discord.Embed(colour=0x19B300)
        if nick:
            em.title = f"Successfully changed nickname to \"{nick}\" in {ctx.guild.name}",
        else:
            em.title = f"Successfully reset nickname in {ctx.guild.name}"
        em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
