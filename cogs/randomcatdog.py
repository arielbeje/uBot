import aiohttp
import json
import os
import random

import discord
from discord.ext import commands

if not os.path.isfile('data/dogdb.json'):
    dogdb = []
else:
    with open('data/dogdb.json', 'r') as dogdatabase:
        dogdb = json.load(dogdatabase)


class randomcatdog:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Random Dog & Cat"

    @commands.command(name="dog")
    async def randomDog(self, ctx):
        """
        Gives a random picture of a dog from random.dog.
        """
        dogpic = f"https://random.dog/{random.choice(dogdb)}"
        em = discord.Embed(title="Random Dog!",
                           colour=0x19B300)
        em.set_image(url=dogpic)
        em.set_footer(text=self.bot.user.name + " | Powered by random.dog", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="cat")
    async def randomCat(self, ctx):
        """
        Gives a random picture of a cat from random.cat.
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


def setup(bot):
    bot.add_cog(randomcatdog(bot))
