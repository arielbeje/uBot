import datetime
from dateutil import parser
import json
import pytz
import os
import re

import discord
from discord.ext import commands

if not os.path.isfile('data/timezonedb.json'):
    timezonedb = {}
else:
    with open('data/timezonedb.json', 'r') as database:
        timezonedb = json.load(database)

with open('variables.json', 'r') as f:
    variables = json.load(f)


class timezoneConverter:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Timezone Converter"

    @commands.group(name="timezone", aliases=["convertime", "converttime"], invoke_without_command=True)
    @commands.has_any_role(*variables["timezoneroles"])
    async def timezone(self, ctx, *, time: str=None):
        """
        Converts a certain time from a user's timezone to everyone's timezone.
        If no time is inputted, convert current time.
        """
        authorID = str(ctx.message.author.id)
        authorName = ctx.message.author.name
        addList = []
        if authorID in timezonedb:
            authorZone = pytz.timezone(timezonedb[authorID])
            if time is not None:
                timep = parser.parse(time)
            else:
                timep = datetime.datetime.now(authorZone)
            for userID in timezonedb:
                if userID != authorID and "d&d" in [x.name.lower() for x in ctx.guild.get_member(int(userID)).roles]:
                    user = self.bot.get_user(int(userID))
                    userZone = pytz.timezone(timezonedb[userID])
                    if time is not None:
                        addList.append("{1} - {0}".format(user.name, authorZone.localize(timep).astimezone(userZone).strftime("%H:%M %d-%m")))
                    else:
                        addList.append("{1} - {0}".format(user.name, timep.astimezone(userZone).strftime("%H:%M %d-%m")))
                elif userID == authorID:
                    if time is not None:
                        invokerTime = "{1} - {0} *".format(authorName, authorZone.localize(timep).strftime("%H:%M %d-%m"))
                    else:
                        invokerTime = "{1} - {0} *".format(authorName, timep.strftime("%H:%M %d-%m"))
            addList.insert(0, invokerTime)
            em = discord.Embed(title=f"Converted times:",
                               description="```" + re.sub("[\['\]]", '', str(addList).replace(", ", "\n")) + "```",
                               colour=0x19B300)
            if time is not None:
                em.set_footer(text="The format used to display date/time is hh:mm dd-mm.")
            else:
                em.set_footer(text='''The format used to display date/time is hh:mm dd-mm.
If you meant to add yourself to the timezone database, use {0}timezone add <your timezone>.'''.format(ctx.prefix))
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description=f'''You are not in the timezone database.
To add yourself, use `{ctx.prefix}timezone add <your timezone>`''',
                               colour=0xDC143C)
            em.set_footer(text="The list of available timezones is located at en.wikipedia.org/wiki/List_of_tz_database_time_zones")
            await ctx.send(embed=em)

    @timezone.command(name="add", aliases=["edit"])
    @commands.has_any_role(*variables["timezoneroles"])
    async def timezoneJoin(self, ctx, *, timezone: str=None):
        """
        Add yourself to the timezone database.
        Use with `timezone add timezone', using a timezone from en.wikipedia.org/wiki/List_of_tz_database_time_zones.
        """
        pytz.timezone(timezone)  # To catch errors
        timezonedb[str(ctx.message.author.id)] = timezone
        with open('data/timezonedb.json', 'w') as database:
            database.write(json.dumps(timezonedb, sort_keys=True, indent=4))
        em = discord.Embed(title="Successfully added you to timezone database.",
                           colour=0x19B300)
        await ctx.send(embed=em)

    @timezone.command(name="remove", aliases=["delete"])
    @commands.has_any_role(*variables["timezoneroles"])
    async def timezoneRemove(self, ctx):
        """
        Remove yourself from the timezone database.
        """
        del timezonedb[str(ctx.message.author.id)]
        with open('data/timezonedb.json', 'w') as database:
            database.write(json.dumps(timezonedb, sort_keys=True, indent=4))
        em = discord.Embed(title="Successfully removed you from timezone database.",
                           colour=0x19B300)
        await ctx.send(embed=em)

    @timezone.command(name="adduser", aliases=["edituser"])
    @commands.has_permissions(manage_roles=True)
    @commands.has_any_role(*variables["timezoneroles"])
    async def timezoneJoinUser(self, ctx, user: discord.User, *, timezone: str=None):
        """
        Add a user to the timezone database.
        Use with `timezone adduser <user> <timezone>', using a timezone from en.wikipedia.org/wiki/List_of_tz_database_time_zones.
        """
        pytz.timezone(timezone)  # To catch errors
        if user is not None:
            timezonedb[str(user.id)] = timezone
            with open('data/timezonedb.json', 'w') as database:
                database.write(json.dumps(timezonedb, sort_keys=True, indent=4))
            em = discord.Embed(title="Successfully added {0} to timezone database.".format(user.name),
                               colour=0x19B300)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="An invalid user was inputted.",
                               colour=0xDC143C)
            await ctx.send(embed=em)

    @timezone.command(name="removeuser")
    @commands.has_permissions(manage_roles=True)
    @commands.has_any_role(*variables["timezoneroles"])
    async def timezoneRemoveUser(self, ctx, user: discord.User):
        """
        Remove a user from the timezone database.
        """
        if user is not None and str(user.id) in timezonedb:
            del timezonedb[str(user.id)]
            with open('data/timezonedb.json', 'w') as database:
                database.write(json.dumps(timezonedb, sort_keys=True, indent=4))
            em = discord.Embed(title="Successfully removed {0} from timezone database.".format(user.name),
                               colour=0x19B300)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="An invalid user was inputted.",
                               colour=0xDC143C)
            await ctx.send(embed=em)

    @timezone.error
    async def timezoneErrorHandler(self, ctx, error):
        origerror = getattr(error, 'original', error)
        if isinstance(origerror, pytz.exceptions.UnknownTimeZoneError):
            em = discord.Embed(title="Error",
                               description="An invalid timezone was inputted. Please use a timezone from [this list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).",
                               colour=0xDC143C)
            await ctx.send(embed=em)

    @timezoneJoin.error
    async def timezoneJoinErrorHandler(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            em = discord.Embed(title="Error",
                               description="A timezone/date/time is required.",
                               colour=0xDC143C)
            await ctx.send(embed=em)

    @timezoneJoinUser.error
    async def timezoneJoinUserErrorHandler(self, ctx, error):
        origerror = getattr(error, 'original', error)
        if isinstance(origerror, pytz.exceptions.UnknownTimeZoneError):
            em = discord.Embed(title="Error",
                               description="An invalid timezone was inputted. Please use a timezone from [this list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).",
                               colour=0xDC143C)
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(timezoneConverter(bot))
