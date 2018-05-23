import aiohttp
import json
import os
import random

import discord
from discord.ext import commands

with open('data/imagedb.json', 'r') as imgdatabase:
    imagedb = json.load(imgdatabase)

dogdb = imagedb["dogs"]
animedb = imagedb["anime"]

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
        em.set_footer(text="Powered by random.dog", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="cat")
    async def random_cat(self, ctx):
        """
        Gives a random picture of a cat from [random.cat](http://random.cat).
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("http://aws.random.cat/meow") as r:
                if r.status == 200:
                    js = await r.json()
                    em = discord.Embed(title="Random Cat!",
                                       colour=0x19B300)
                    em.set_image(url=js["file"])
                    em.set_footer(text="Powered by aws.random.cat", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
                    await ctx.send(embed=em)
                else:
                    em = discord.Embed(title="Error",
                                       description="Couldn't reach random.cat.\nTry again later.",
                                       colour=0xDC143C)
                    await ctx.send(embed=em)

    @commands.command(name="0.17")
    async def releaseDate(self, ctx):
        """
        Returns the release date of 0.17.
        """
        rndInt = random.randint(0, 20)
        if rndInt == 1:
            await ctx.send("0.17 has officially been cancelled.")
        elif rndInt == 2:
            await ctx.send(f"0.17 will be out for release in just {random.randint(1, 59)} minutes!")
        elif rndInt == 3:
            await ctx.send("0.17 will be released whenever Half-Life 3 comes out.")
        else:
            await ctx.send(f"0.17 is planned for release in {random.randint(1, 700)} days.")

    @commands.command(name="heresy")
    async def heresy(self, ctx, user: discord.User=None):
        """
        Declares heresy.
        Can also declare heresy on a user.
        """
        em = discord.Embed(colour=0x19B300)
        if user:
            em.description = f"{ctx.author.mention} declares heresy on {user.mention}!"
        else:
            em.description = f"{ctx.author.mention} declares heresy!"
        em.set_image(url=random.choice(heresydb))
        # em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="images", aliases=["blush", "bully", "cuddle", "hug", "kiss", "lewd", "pat", "pout", "slap", "smug"])
    async def image_macros(self, ctx, user: discord.User=None):
        """
        Various image commands - blush, bully, cuddle, hug, kiss, lewd, pat, pout, slap, smug
        """
        usedCmd = ctx.invoked_with
        author = ctx.message.author.mention
        em = discord.Embed()
        if usedCmd == "blush":
            em.set_image(url=random.choice(animedb["blush"]))
        elif usedCmd == "bully":
            if not user:
                em.description = f"{author} is a bully!"
            else:
                em.description = f"{author} is bullying {user.mention}!"
            em.set_image(url=random.choice(animedb["bully"]))
        elif usedCmd == "cuddle":
            if not user:
                em.description = f"Come here, {author}"
            else:
                em.description = f"{author} cuddles with {user.mention}"
            em.set_image(url=random.choice(animedb["cuddle"]))
        elif usedCmd == "hug":
            em.set_image(url=random.choice(animedb["hug"]))
        elif usedCmd == "kiss":
            em.set_image(url=random.choice(animedb["kiss"]))
        elif usedCmd == "lewd":
            em.set_image(url=random.choice(animedb["lewd"]))
        elif usedCmd == "pat":
            if user:
                em.description = f"{author} pats {user.mention}"
            em.set_image(url=random.choice(animedb["pat"]))
        elif usedCmd == "pout":
            em.set_image(url=random.choice(animedb["pout"]))
        elif usedCmd == "slap":
            em.set_image(url=random.choice(animedb["slap"]))
        else:
            em.set_image(url=random.choice(animedb["smug"]))
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(FunCog(bot))
