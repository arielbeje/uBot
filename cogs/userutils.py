from ago import human
import aiohttp
import asyncio
import datetime
import re
import json
import os
import pytz
import html
import xml.etree.ElementTree as ET

import discord
from discord.ext import commands

'''if os.path.exists('data/reminderdb.json'):
    with open('data/reminderdb.json', 'r') as f:
        reminderdb = json.load(f)'''

with open('variables.json', 'r') as f:
    variables = json.load(f)

tagregex = re.compile(r"<.*?>")
ampregex = re.compile(r"&amp;#(\d*);")


def amp_repl(matchobj):
    return chr(int(matchobj.group(1)))


def clean_xml(inputdata):
    return tagregex.sub("", html.unescape(ampregex.sub(amp_repl, inputdata)))


'''async def reminder_check(bot, reminderdb=reminderdb):
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            with open('data/reminderdb.json', 'w') as f:
                reminderdb = json.load(f)
        except json.JSONDecodeError:
            await asyncio.sleep(1)
        for user in reminderdb:
            templist = list(reminderdb[user])  # Using list() to copy the list
            for reminder in templist:
                remindTime = int(datetime.datetime.utcfromtimestamp(reminder["time"]))
                if int(remindTime) <= int(time.time()):
                    channel = bot.get_channel(int(reminder["channel"]))
                    em = discord.Embed(title="Reminder",
                                       description=reminder["message"],
                                       colour=0x19B300)
                    # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
                    await channel.send(bot.get_user(int(user)).mention, embed=em)
                    templist.remove(reminder)
            reminderdb[user] = templist
        with open('data/reminderdb.json', 'w') as f:
            f.write(json.dumps(reminderdb, sort_keys=True, indent=4))
        await asyncio.sleep(1)'''


class UserUtils:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Utility Commands"

    '''@commands.command(name="reminder", aliases=["remindme"])
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

        if userID not in reminderdb:
            reminderdb[userID] = []
        reminderdb[userID].append({"message": content,
                                   "channel": ctx.message.channel.id,
                                   "time": remindTime.timestamp()})

        with open('data/reminderdb.json', 'w') as db:
            db.write(json.dumps(reminderdb, sort_keys=True, indent=4))

        em = discord.Embed(description=f"You will be reminded in {', '.join(timeString)} from now.",
                           colour=0x19B300)
        if len(timeString) > 1:
            em.description = f"You will be reminded in {', '.join(timeString[:-1])} and {timeString[-1]} from now."
        # em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)'''

    @commands.command(name='userinfo')
    async def user_info(self, ctx, user: discord.User=None):
        """Returns information about the given user"""
        if not user:
            user = ctx.message.author
        member = ctx.message.guild.get_member(user.id)
        em = discord.Embed(colour=0xDFDE6E)
        inlineFields = [
            {"name": "ID", "value": member.id},
            {"name": "Nickname", "value": member.nick if not None else "None"},
            {"name": "Status", "value": member.status},
            {"name": member.activity.state, "value": member.activity.name} if member.activity else
            {"name": "Activity", "value": "None"},
            {"name": "Mention", "value": member.mention}
        ]
        for field in inlineFields:
            em.add_field(**field, inline=True)
        avatar = user.avatar_url_as(size=64)  # if not None else discord.Embed.Empty
        registeredAt = pytz.utc.localize(member.created_at)
        joinedAt = pytz.utc.localize(member.joined_at)
        em.add_field(name="Joined", value=f"{human(joinedAt, precision=4)} ({joinedAt.strftime('%d-%m-%Y %H:%M:%S %Z')})")
        em.add_field(name="Roles", value=", ".join([role.name for role in member.roles]).replace("@everyone", "@\u200beveryone"))
        em.set_author(name=member.name, icon_url=avatar)
        em.set_thumbnail(url=avatar)
        em.set_footer(text=f"Created: {human(registeredAt, precision=4)} ({registeredAt.strftime('%d-%m-%Y %H:%M:%S %Z')})")
        await ctx.send(embed=em)

    @commands.command(name="anime")
    async def anime_search(self, ctx, *, query: str=""):
        """
        Searches MyAnimeList for given anime and returns some info.
        """
        if not query:
            em = discord.Embed(title="Error",
                               description="A search term is required.",
                               colour=0xDC143C)
            await ctx.send(embed=em)
            return
        em = discord.Embed(title=f"Searching for \"{query.title()}\" in myanimelist.net...",
                           description="This may take a bit.",
                           colour=0xDFDE6E)
        # em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():
            if variables["myanimelist"]["login"] and variables["myanimelist"]["password"]:
                try:
                    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(**variables["myanimelist"])) as client:
                        async with client.get(f"https://myanimelist.net/api/anime/search.xml?q={query.replace(' ', '+')}") as resp:
                            assert resp.status != 401
                            mal_data = ET.fromstring(await resp.text())
                except AssertionError:
                    print("Invalid myanimelist username/password.")
                    em = discord.Embed(title="Error",
                                       description="Invalid MyAnimeList login. Please contact the bot's owner.",
                                       colour=0xDC143C)
                    await bufferMsg.edit(embed=em)
                    return
            else:
                print("To use the anime command, a myanimelist login has to be inputted in variables.json.")
                em = discord.Embed(title="Error",
                                   description="Invalid MyAnimeList login. Please contact the bot's owner.",
                                   colour=0xDC143C)
                await bufferMsg.edit(embed=em)
                return

            choosingList = []
            messageToSend = "Please choose the correct show by entering its number.\n\n"
            i = 1
            for item in mal_data:
                if i <= 10:
                    choosingList.append(item)
                    messageToSend += f"[{i}] # {item[2].text}\n"
                    i += 1
                else:
                    break
            messageToSend += ("\n\nType \"exit\" to leave this menu.\n"
                              "# If no choice is made within 60 seconds, this message will be deleted.")
            await bufferMsg.edit(content=f"```python\n{messageToSend}```", embed=None)

            def check(message):
                content = message.content
                try:
                    int(content)
                    contentIsIndex = len(choosingList) >= int(content) - 1 and not int(content) < 1
                except ValueError:
                    contentIsIndex = False
                return message.author == ctx.message.author and contentIsIndex or content == "exit"

            try:
                if len(choosingList) > 1:
                    userMsg = await self.bot.wait_for("message", timeout=60.0, check=check)
                    botMember = ctx.message.guild.get_member(self.bot.user.id)
                    havePerm = botMember.permissions_in(ctx.message.channel).manage_messages
                    if userMsg.content == "exit":
                        await bufferMsg.delete()

                else:
                    data = choosingList[int(userMsg.content) - 1] if len(choosingList) > 1 else choosingList[0]
                    # If bot has manage messages perm, delete the message
                    em = discord.Embed(title=data[2].text,
                                       url=f"https://myanimelist.net/anime/{data[0].text}",
                                       description=clean_xml(data[10].text),
                                       colour=0x19B300)
                    em.set_thumbnail(url=data[11].text)
                    if data[2].text.lower() != data[1].text.lower():
                        em.description = f"**Alternative title:** {data[1].text}\n\n" + em.description
                    fields = []
                    start_date = datetime.datetime.strptime(data[8].text, "%Y-%m-%d")
                    if data[4].text == "0":
                        fields.append({"name": "Episodes", "value": "Unknown"})
                    else:
                        fields.append({"name": "Episodes", "value": data[4].text})
                    fields.extend([{"name": "Status", "value": data[7].text},
                                   {"name": "Start Date", "value": start_date.strftime("%d-%m-%Y")}])
                    if data[9].text != "0000-00-00":
                        end_date = datetime.datetime.strptime(data[9].text, "%Y-%m-%d")
                        fields.append({"name": "End Date", "value": end_date.strftime("%d-%m-%Y")})
                    if data[5].text != "0.00":
                        fields.append({"name": "Score", "value": f"{data[5].text} / 10"})
                    for field in fields:
                        em.add_field(**field, inline=True)
                    em.set_footer(text="Powered by myanimelist.net")

                    await bufferMsg.edit(embed=em, content=None)

                if havePerm:
                    await userMsg.delete()
            except asyncio.TimeoutError:
                await bufferMsg.delete()

    @anime_search.error
    async def mal_search_error_handler(self, ctx, error):
        origerror = getattr(error, 'original', error)
        if isinstance(origerror, aiohttp.http_exceptions.BadHttpMessage):
            em = discord.Embed(title="Error",
                               description="Couldn't find query in [My Anime List](https://myanimelist.net/) DB.",
                               colour=0xDC143C)
            await ctx.send(embed=em)


def setup(bot):
    # bot.loop.create_task(reminder_check(bot))
    bot.add_cog(UserUtils(bot))
