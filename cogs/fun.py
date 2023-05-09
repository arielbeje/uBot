import random
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
            await ctx.send("The expansion has officially been cancelled.")
        elif rndInt == 2:
            await ctx.send(f"The expansion will be out for release in just {random.randint(1, 59)} minutes!")
        elif rndInt == 3:
            await ctx.send("The expansion will be released whenever Half-Life 3 comes out.")
        else:
            await ctx.send(f"The expansion is planned for release in {random.randint(365, 1000)} days.")

async def setup(bot):
    await bot.add_cog(FunCog(bot))
