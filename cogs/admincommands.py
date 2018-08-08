import rethinkdb as r
import discord
from discord.ext import commands
from utils import customchecks


class AdminCommands:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Admin Commands"

    @commands.group(aliases=["modrole"], invoke_without_command=True)
    async def modroles(self, ctx):
        """
        Lists the moderator roles defined for this server.
        """
        with r.connect(db="bot") as conn:
            modroles = r.table("servers").get(
                ctx.message.guild.id).pluck("modroles").run(conn)["modroles"]
        if modroles:
            await ctx.send(f"Defined mod roles for {ctx.message.guild.name}: `{'`, `'.join(modroles)}`\n" +
                           f"To add more, use `{ctx.prefix}modroles add/remove [role]`.")
        else:
            await ctx.send(f"This server does not have any defind mod roles.")

    @modroles.command(name="add")
    @customchecks.has_mod_role()
    async def add_mod_role(self, ctx, *, modrole: str):
        """
        Add a new moderator role to the defined ones.
        """
        with r.connect(db="bot") as conn:
            modroles = r.table("servers").get(
                ctx.message.guild.id).pluck("modroles").run(conn)["modroles"]
            if modrole not in modroles:
                modroles.append(modrole)
                r.table("servers").get(ctx.message.guild.id).get().update(
                    {"modroles": modroles}).run(conn)
                await ctx.send(f"Successfully added \"{modrole}\" to mod roles list.")
            else:
                await ctx.send(f"\"{modrole}\" is already in the defined mod roles.\n" +
                               f"To list all mod roles, use `{ctx.prefix}modroles`.")

    @modroles.command(name="remove", aliases=["delete"])
    @customchecks.has_mod_role()
    async def remove_mod_role(self, ctx, *, modrole: str):
        """
        Remove a moderator role from the defined list.
        """
        with r.connect(db="bot") as conn:
            modroles = r.table("servers").get(
                ctx.message.guild.id).pluck("modroles").run(conn)["modroles"]
            if modrole in modroles:
                modroles.remove(modrole)
                r.table("servers").get(ctx.message.guild.id).update(
                    {"modroles": modroles}).run(conn)
                await ctx.send(f"Successfully added \"{modrole}\" to mod roles list.")
            else:
                await ctx.send(f"\"{modrole}\" is not in the defined mod roles.\n" +
                               f"To list all mod roles, use `{ctx.prefix}modroles`.")

    @commands.group(invoke_without_command=True)
    async def prefixes(self, ctx):
        """
        List the available prefixes for this server.
        """
        with r.connect(db="bot") as conn:
            prefixes = r.table("servers").get(
                ctx.message.guild.id).pluck("prefixes").run(conn)["prefixes"]
            if prefixes:
                await ctx.send(f"Defined prefixes for {ctx.message.guild.name}: `{'`, `'.join(prefixes)}`.")
            else:
                await ctx.send(f"This server does not have any defined prefixes.\n" +
                               f"To define prefixes, use `{ctx.prefix}prefixes`.")

    @prefixes.command(name="add")
    @customchecks.has_mod_role()
    async def add_prefix(self, ctx, *, prefix: str):
        """
        Adds a prefix to the list of defined ones.
        """
        with r.connect(db="bot") as conn:
            prefixes = r.table("servers").get(
                ctx.message.guild.id).pluck("prefixes").run(conn)["prefixes"]
            if prefixes:
                if prefix not in prefixes:
                    prefixes.append(prefix)
                    r.table("servers").get(ctx.message.guild.id).update(
                        {"prefixes": prefixes}).run(conn)
                    await ctx.send(f"Added `{prefix}` to prefixes.\n" +
                                   f"To see see the list of all prefixes, use `{ctx.prefix}prefixes`")
                else:
                    await ctx.send(f"`{prefix}` is already in the defined prefixes.\n" +
                                   f"To list all prefixes, use `{ctx.prefix}prefixes`.")
            else:
                r.table("servers").get(ctx.message.guild.id).update(
                    {"prefixes": [prefix]}).run(conn)
                await ctx.send(f"Added `{prefix}` to prefixes.\n" +
                               f"To see see the list of all prefixes, use `{ctx.prefix}prefixes`")

    @prefixes.command(name="remove")
    @customchecks.has_mod_role()
    async def remove_prefix(self, ctx, *, prefix: str):
        """
        Removes a prefix from the defined list.
        """
        with r.connect(db="bot") as conn:
            prefixes = r.table("servers").get(
                ctx.message.guild.id).pluck("prefixes").run(conn)["prefixes"]
            if prefix in prefixes:
                prefixes.remove(prefix)
                r.table("servers").get(ctx.message.guild.id).update(
                    {"prefixes": prefixes}).run(conn)
                await ctx.send(f"Removed `{prefix}` from prefixes.\n" +
                               f"To see see the list of all prefixes, use `{ctx.prefix}prefixes`")
            else:
                await ctx.send(f"`{prefix}` is not in the defined prefixes.\n" +
                               f"To list all prefixes, use `{ctx.prefix}prefixes`.")

    @commands.command()
    @customchecks.has_mod_role()
    async def reset(self, ctx):
        """
        Resets the bot's settings for this server.
        Careful! This doesn't have a confirmation message yet!
        """
        with r.connect(db="bot") as conn:
            r.table("servers").get(
                ctx.message.guild.id).update({"id": ctx.message.guild.id,
                                              "prefixes": ["+"],
                                              "faq": {},
                                              "modroles": ["Bot Commander"]
                                              }).run(conn)
        await ctx.send("Reset all data for this server.")

    @commands.command(name="prune", aliases=["purge"])
    @customchecks.has_mod_role()
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
    @customchecks.has_mod_role()
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
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
