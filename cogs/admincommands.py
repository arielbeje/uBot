import discord
from discord.ext import commands

from utils import customchecks, sql


class AdminCommands:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Admin Commands"

    @commands.group(aliases=["modrole"], invoke_without_command=True)
    async def modroles(self, ctx):
        """
        Lists the moderator roles defined for this server.
        """
        roleIDs = await sql.fetch("SELECT roleid FROM modroles WHERE serverid=$1", ctx.message.guild.id)
        modroles = [ctx.message.guild.get_role(int(roleid)).name for roleid in [int(roleID["roleid"]) for roleID in roleIDs]]
        if modroles:
            em = discord.Embed(title=f"Defined mod roles for {ctx.message.guild.name}",
                               description=", ".join(modroles),
                               colour=discord.Colour.gold())
        else:
            em = discord.Embed(title="Error",
                               description="This server does not have any defined mod roles.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)

    @modroles.command(name="add")
    @customchecks.is_mod()
    async def add_mod_role(self, ctx, *, role: discord.Role):
        """
        Add a new moderator role to the defined ones.
        """
        roleIDs = [int(roleID["roleid"]) for roleID in await sql.fetch("SELECT roleid FROM modroles WHERE serverid=$1", ctx.message.guild.id)]
        if role.id not in roleIDs:
            await sql.execute("INSERT INTO modroles VALUES($1, $2)", ctx.message.guild.id, role.id)
            em = discord.Embed(title=f"Succesfully added \"{role.name}\" to mod roles list",
                               colour=discord.Colour.dark_green())
        else:
            em = discord.Embed(title="Error",
                               description=f"\"{role.name}\" is already in the defined mod roles.\n" +
                                           f"To list all mod roles, use `{ctx.prefix}modroles`.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)

    @modroles.command(name="remove", aliases=["delete"])
    @customchecks.is_mod()
    async def remove_mod_role(self, ctx, *, role: discord.Role):
        """
        Remove a moderator role from the defined list.
        """
        roleIDs = [int(roleID["roleid"]) for roleID in await sql.fetch("SELECT roleid FROM modroles WHERE serverid=$1", ctx.message.guild.id)]
        if role.id in roleIDs:
            await sql.execute("DELETE FROM modroles WHERE serverid=$1 AND roleid=$2", ctx.message.guild.id, role.id)
            em = discord.Embed(title=f"Succesfully removed \"{role.name}\" from mod roles list.",
                               colour=discord.Colour.dark_green())
        else:
            em = discord.Embed(title="Error",
                               description=f"\"{role.name}\" is not in the defined mod roles.\n" +
                                           f"To list all mod roles, use `{ctx.prefix}modroles`.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def prefixes(self, ctx):
        """
        List the available prefixes for this server.
        """
        prefixes = [result["prefix"] for result in await sql.fetch("SELECT prefix FROM prefixes WHERE serverid=$1", ctx.message.guild.id)]
        if prefixes:
            em = discord.Embed(title=f"Defined prefixes for {ctx.message.guild.name}",
                               description=f"`{'`, `'.join(prefixes)}",
                               colour=discord.Colour.gold())
        else:
            em = discord.Embed(title="Error",
                               description="This server does not have any defined prefixs.\n" +
                                           f"To define prefixes, use `{ctx.prefix}prefixes`.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)

    @prefixes.command(name="add")
    @customchecks.is_mod()
    async def add_prefix(self, ctx, *, prefix: str):
        """
        Adds a prefix to the list of defined ones.
        """
        prefixes = [result["prefix"] for result in await sql.fetch("SELECT prefix FROM prefixes WHERE serverid=$1", ctx.message.guild.id)]
        if prefix not in prefixes:
            await sql.execute("INSERT INTO prefixes VALUES($1, $2)", ctx.message.guild.id, prefix)
            em = discord.Embed(title=f"Added `{prefix}` to prefixes",
                               description=f"To see the list of all defined prefixes, use `{prefix}prefixes`",
                               colour=discord.Colour.dark_green())
        else:
            em = discord.Embed(title=f"Error",
                               description=f"`{prefix}` is already in the defined prefixes.\n" +
                                           f"To see the list of all defined prefixes, use `{ctx.prefix}prefixes`.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)

    @prefixes.command(name="remove")
    @customchecks.is_mod()
    async def remove_prefix(self, ctx, *, prefix: str):
        """
        Removes a prefix from the defined list.
        """
        prefixes = [result["prefix"] for result in await sql.fetch("SELECT prefix FROM prefixes WHERE serverid=$1", ctx.message.guild.id)]
        if prefix in prefixes:
            await sql.execute("DELETE FROM prefixes WHERE serverid=$1 AND prefix=$2", ctx.message.guild.id, prefix)
            em = discord.Embed(title=f"Removed `{prefix}` from prefixes",
                               description=f"To see the list of all defined prefixes, use {self.bot.user.mention} prefixes",
                               colour=discord.Colour.dark_green())
        else:
            em = discord.Embed(title=f"Error",
                               description=f"`{prefix}` is not in the defined prefixes.\n" +
                                           f"To see the list of all defined prefixes, use `{ctx.prefix}prefixes`.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)

    @commands.command()
    @customchecks.is_mod()
    async def reset(self, ctx):
        """
        Resets the bot's settings for this server.
        Careful! This doesn't have a confirmation message yet!
        """
        # TODO: Add confirmation message
        await sql.deleteserver(ctx.message.guild.id)
        await sql.initserver(ctx.message.guild.id)
        em = discord.Embed(title="Reset all data for this server",
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command(aliases=["purge"])
    @customchecks.has_permissions(manage_messages=True)
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
        origerror = getattr(error, "original", error)
        if isinstance(origerror, discord.errors.NotFound):  # Invalid prune number.
            em = discord.Embed(title="Error",
                               description="That message ID is invalid.",
                               colour=discord.Colour.red())
            return await ctx.send(embed=em)
        if isinstance(error, commands.errors.MissingRequiredArgument):
            em = discord.Embed(title="Error",
                               description=f"{ctx.prefix}prune requires a number of messages or a message ID.",
                               colour=discord.Colour.red())
            return await ctx.send(embed=em)

    @commands.command(name="setnick")
    @customchecks.is_mod()
    async def set_nick(self, ctx, *, nick=None):
        """
        Changes the bot's nickname in this server.
        If no nickname is inputted, the nickname is reset.
        """
        await ctx.guild.me.edit(nick=nick)
        em = discord.Embed(colour=discord.Colour.dark_green())
        if nick:
            em.title = f"Successfully changed nickname to \"{nick}\" in {ctx.guild.name}",
        else:
            em.title = f"Successfully reset nickname in {ctx.guild.name}"
        await ctx.send(embed=em)

    @commands.command(name="setcomment")
    @customchecks.is_mod()
    async def set_comment(self, ctx, *, comment=None):
        """
        Set the comment symbol for this server.
        When executing commands, text after the symbol message will be ignored.
        Use without a comment after the command to set no comment.
        """
        await sql.execute("UPDATE servers SET comment=$1 WHERE serverid=$2", comment, ctx.message.guild.id)
        em = discord.Embed(colour=discord.Colour.dark_green())
        if comment:
            em.title = f"Successfully changed comment symbol to `{comment}`."
        else:
            em.title = "Successfully removed comment symbol."
        await ctx.send(embed=em)

    @commands.command(name="setjoinleavechannel")
    @customchecks.is_mod()
    async def set_joinleave_channel(self, ctx, channel: discord.TextChannel=None):
        """
        Set the channel for join/leave events.
        Use without additional arguments to disable the functionality.
        """
        if channel is not None:
            await sql.execute("UPDATE servers SET joinleavechannel=$1 WHERE serverid=$2", channel.id, ctx.message.guild.id)
            em = discord.Embed(title=f"Successfully set join/leave events channel to {channel.mention}",
                               colour=discord.Colour.dark_green())
        else:
            await sql.execute("UPDATE servers SET joinleavechannel=$1 WHERE serverid=$2", None, ctx.message.guild.id)
            em = discord.Embed(title="Successfully disabled join/leave events",
                               colour=discord.Colour.dark_green())
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
