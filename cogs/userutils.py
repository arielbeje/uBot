import asyncio
import datetime
import re
import json

import discord
from discord.ext import commands


with open('data/reminderdb.json', 'r') as f:
    reminderdb = json.load(f)


async def reminder_check(bot, reminderdb=reminderdb):
    await bot.wait_until_ready()
    while not bot.is_closed():
        tempdb = reminderdb.copy()
        for user in reminderdb:
            userdb = reminderdb[user]
            time = datetime.datetime.strptime(userdb["time"], "%Y-%m-%d %H:%M:%S %Z")
            if time < datetime.datetime.utcnow():
                channel = bot.get_channel(int(userdb["channel"]))
                em = discord.Embed(title="Reminder",
                                   description=userdb["message"],
                                   colour=0x19B300)
                # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
                await channel.send(bot.get_user(int(user)).mention, embed=em)
                del tempdb[user]
        reminderdb = tempdb
        with open('data/reminderdb.json', 'w') as f:
            f.write(json.dumps(reminderdb, sort_keys=True, indent=4))
        await asyncio.sleep(1)


class UserUtils:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Utility Commands"

    @commands.command(name="reminder")
    async def reminder(self, ctx, time: str="", *, content: str=""):
        """
        Sets a reminder with a message.
        """
        if not content:
            em = discord.Embed(title="Error",
                               description="To set a reminder, content is required.",
                               colour=0xDC143C)
            await ctx.send(embed=em)
            return

        userID = str(ctx.author.id)
        remindTime = datetime.datetime.utcnow()
        matchIter = re.finditer(r"(\d+)([dhmsDHMS])", time)
        timeString = []

        for match in matchIter:
            timeAmount = int(match.group(1))
            timeLetter = match.group(2).lower()
            if timeLetter == "d":
                remindTime += datetime.timedelta(days=timeAmount)
                toAppend = f"{timeAmount} day"
            elif timeLetter == "h":
                remindTime += datetime.timedelta(hours=timeAmount)
                toAppend = f"{timeAmount} hour"
            elif timeLetter == "m":
                remindTime += datetime.timedelta(minutes=timeAmount)
                toAppend = f"{timeAmount} minute"
            elif timeLetter == "s":
                remindTime += datetime.timedelta(seconds=timeAmount)
                toAppend = f"{timeAmount} second"
            if timeAmount > 1:
                toAppend += 's'
            timeString.append(toAppend)

        reminderdb[userID] = {}
        reminderdb[userID]["message"] = content
        reminderdb[userID]["channel"] = ctx.message.channel.id
        reminderdb[userID]["time"] = remindTime.strftime("%Y-%m-%d %H:%M:%S UTC")

        with open('data/reminderdb.json', 'w') as db:
            db.write(json.dumps(reminderdb, sort_keys=True, indent=4))

        em = discord.Embed(description=f"You will be reminded in {', '.join(timeString)} from now.",
                           colour=0x19B300)
        if len(timeString) > 1:
            em.description = f"You will be reminded in {', '.join(timeString[:-1])} and {timeString[-1]} from now."
        # em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)
    
    @commands.command(name='userinfo')
    async def user_info(self, ctx, user=discord.User=None):
        """Returns information about the given user"""
        if not user:
            user = ctx.message.author
        
        name = user.name
        
        if user.display_name != user.name:
            nickname = user.display_name

        userid = user.id
        avatar = user.avatar_url
        registeredAt = user.created_at
        joinedAt = ''
        #ariel pls make pretty embed

def setup(bot):
    bot.loop.create_task(reminder_check(bot))
    bot.add_cog(UserUtils(bot))
