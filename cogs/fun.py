import random
import asyncio
from discord.ext import commands

class FunCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Fun Commands"

    @commands.hybrid_command(name="expansion", aliases=["1.2"])
    async def release_date(self, ctx: commands.Context):
        """
        Returns the release date of the expansion.
        """
        rndInt = random.randint(0, 20)
        if rndInt == 1:
            await ctx.reply("Expansion? There's an expansion?! Tell me everything!")
        elif rndInt == 2:
            await ctx.reply(f"The expansion will be out for release in just {random.randint(1, 59)} minutes!")
        elif rndInt == 3:
            await ctx.reply("The expansion will be released whenever Half-Life 3 comes out.")
        elif rndInt == 4:
            await ctx.reply("The expansion will be released when it's done.")
        elif rndInt == 5:
            await ctx.reply("The expansion was gets delayed by a month every time you ask.")
        else:
            msg = await ctx.reply(f"The expansion is planned for release in {random.randint(365, 1000)} days.")
            for i in range(4):
                await asyncio.sleep(random.randint(2, 8))
                await msg.edit(content=f"Wait no, actually it will release in {random.randint(365, 1000)} days.")
            await asyncio.sleep(random.randint(3, 10))
            await msg.edit(content=f"It will release in {random.randint(365, 1000)} days... I think.")



async def setup(bot):
    await bot.add_cog(FunCog(bot))
