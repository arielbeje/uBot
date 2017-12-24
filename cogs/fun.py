import aiohttp
import json
import os
import random

import discord
from discord.ext import commands

with open('data/dogdb.json', 'r') as dogdatabase:
    dogdb = json.load(dogdatabase)

with open('data/heresydb.json', 'r') as heresydatabase:
    heresydb = json.load(heresydatabase)


class FunCog():
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Fun Commands"

    @commands.command(name="dog")
    async def random_dog(self, ctx):
        """
        Gives a random picture of a dog from [random.dog](https://random.dog).
        """
        dogpic = f"https://random.dog/{random.choice(dogdb)}"
        em = discord.Embed(title="Random Dog!",
                           colour=0x19B300)
        em.set_image(url=dogpic)
        em.set_footer(text=self.bot.user.name + " | Powered by random.dog", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="cat")
    async def random_cat(self, ctx):
        """
        Gives a random picture of a cat from [random.cat](http://random.cat).
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("http://random.cat/meow") as r:
                if r.status == 200:
                    js = await r.json()
                    em = discord.Embed(title="Random Cat!",
                                       colour=0x19B300)
                    em.set_image(url=js['file'])
                    em.set_footer(text=self.bot.user.name + " | Powered by random.cat", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
                    await ctx.send(embed=em)
                else:
                    em = discord.Embed(title="Error",
                                       description="Couldn't reach random.cat.\nTry again later.",
                                       colour=0xDC143C)
                    await ctx.send(embed=em)

    @commands.command(name="heresy")
    async def heresy(self, ctx, user: discord.User=None):
        """
        Declares heresy.
        Can also declare heresy on a user.
        """
        if user:
            em = discord.Embed(description=f"{ctx.author.mention} declares heresy on {user.mention}!",
                               colour=0x19B300)
        else:
            em = discord.Embed(description=f"{ctx.author.mention} declares heresy!",
                               colour=0x19B300)
        em.set_image(url=random.choice(heresydb))
        em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(FunCog(bot))