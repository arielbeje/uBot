import discord
from discord.ext import commands


class testCog():
    def __init__(self, bot):
        self.bot = bot

    @commands.command("test")
    async def testCommand(self, ctx):
        author = self.bot.get_user(ctx.message.author.id)
        if ctx.guild.get_member(author.id).nick:
            authorName = ctx.guild.get_membeR(author.id).nick
        else:
            authorName = author.name
        em = discord.Embed(title="Embed with direct name.")
        em.set_author(name=author.name)
        await ctx.send(embed=em)
        em = discord.Embed(title="Embed with indirect name.")
        em.set_author(name=authorName)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(testCog(bot))
