import aiohttp
import json
import random

import discord
from discord.ext import commands

with open("data/imagedb.json", "r") as imgdatabase:
    imagedb = json.load(imgdatabase)

dogdb = imagedb["dogs"]
animedb = imagedb["anime"]
heresydb = imagedb["heresy"]


async def send_reaction_image(ctx: commands.Context, category: str):
    """
    Sends an image randomly pulled from the category given
    """
    em = discord.Embed()
    em.set_image(url=random.choice(animedb[category]))
    await ctx.send(embed=em)


class FunCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Fun Commands"

    @commands.command(name="dog")
    async def random_dog(self, ctx: commands.Context):
        """
        Gives a random picture of a dog from [random.dog](https://random.dog).
        """
        dogpic = f"https://random.dog/{random.choice(dogdb)}"
        em = discord.Embed(title="Random Dog!",
                           colour=discord.Colour.dark_green())
        em.set_image(url=dogpic)
        em.set_footer(text="Powered by random.dog", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="cat")
    async def random_cat(self, ctx: commands.Context):
        """
        Gives a random picture of a cat from [random.cat](http://random.cat).
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("http://aws.random.cat/meow") as r:
                if r.status == 200:
                    js = await r.json()
                    em = discord.Embed(title="Random Cat!",
                                       colour=discord.Colour.dark_green())
                    em.set_image(url=js["file"])
                    em.set_footer(text="Powered by aws.random.cat", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
                    await ctx.send(embed=em)
                else:
                    em = discord.Embed(title="Error",
                                       description="Couldn't reach random.cat.\nTry again later.",
                                       colour=discord.Colour.red())
                    await ctx.send(embed=em)

    @commands.command(name="0.18", aliases=[".18"])
    async def release_date(self, ctx: commands.Context):
        """
        Returns the release date of 0.18.
        """
        rndInt = random.randint(0, 20)
        if rndInt == 1:
            await ctx.send("0.18 has officially been cancelled.")
        elif rndInt == 2:
            await ctx.send(f"0.18 will be out for release in just {random.randint(1, 59)} minutes!")
        elif rndInt == 3:
            await ctx.send("0.18 will be released whenever Half-Life 3 comes out.")
        else:
            await ctx.send(f"0.18 is planned for release in {random.randint(1, 700)} days.")

    @commands.command(name="heresy")
    async def heresy(self, ctx: commands.Context, user: discord.User = None):
        """
        Declares heresy.
        Can also declare heresy on a user.
        """
        em = discord.Embed(colour=discord.Colour.dark_green())
        if user:
            em.description = f"{ctx.author.mention} declares heresy on {user.mention}!"
        else:
            em.description = f"{ctx.author.mention} declares heresy!"
        em.set_image(url=random.choice(heresydb))
        await ctx.send(embed=em)

    @heresy.error
    async def heresy_error_handler(self, ctx: commands.Context, error):
        origerror = getattr(error, "original", error)
        if isinstance(origerror, commands.errors.BadArgument):
            em = discord.Embed(title="Error",
                               description="Couldn't find user.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def reactions(self, ctx: commands.Context):
        """
        Sends reaction images.
        """
        em = discord.Embed(title="Wrong command",
                           description=(f"To use reaction images, use {ctx.prefix}reactions and then one of these commands:\n" +
                                        "blush, bully, cuddle, hug, kiss, lewd, pat, pout, slap"),
                           colour=discord.Colour.red())
        await ctx.send(embed=em)

    @reactions.command()
    async def blush(self, ctx: commands.Context):
        """Sends a blushing image."""
        await send_reaction_image(ctx, "blush")

    @reactions.command()
    async def bully(self, ctx: commands.Context):
        """Sends a bullying image."""
        await send_reaction_image(ctx, "bully")

    @reactions.command()
    async def cuddle(self, ctx: commands.Context):
        """Sends a cuddling image."""
        await send_reaction_image(ctx, "cuddle")

    @reactions.command()
    async def hug(self, ctx: commands.Context):
        """Sends a hugging image."""
        await send_reaction_image(ctx, "hug")

    @reactions.command()
    async def kiss(self, ctx: commands.Context):
        """Sends a kissing image."""
        await send_reaction_image(ctx, "kiss")

    @reactions.command()
    async def lewd(self, ctx: commands.Context):
        """Send a "lewd" image."""
        await send_reaction_image(ctx, "lewd")

    @reactions.command()
    async def pat(self, ctx: commands.Context):
        """Sends a patting image."""
        await send_reaction_image(ctx, "pat")

    @reactions.command()
    async def pout(self, ctx: commands.Context):
        """Sends a pouting image."""
        await send_reaction_image(ctx, "pout")

    @reactions.command()
    async def slap(self, ctx: commands.Context):
        """Sends a slapping image."""
        await send_reaction_image(ctx, "slap")

    @reactions.command()
    async def smug(self, ctx: commands.Context):
        """Sends a smug image."""
        await send_reaction_image(ctx, "smug")


def setup(bot):
    bot.add_cog(FunCog(bot))
