import datetime
import json
import os
import pytz
import re

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

if not os.path.isfile('data/tagdatabase.json'):
    faqdb = {}
else:
    with open('data/tagdatabase.json', 'r') as database:
        faqdb = json.load(database)

with open('variables.json', 'r') as f:
    variables = json.load(f)


def embedFAQ(ctx, bot, query, title=None, color=None):
    faquery = faqdb[query]
    if not title:
        title = query.title()
    if not color:
        color = 0xDFDE6E
    content = faquery["content"]
    image = faquery["image"]
    timestamp = datetime.datetime.strptime(faquery["timestamp"], "%Y-%m-%d %H:%M:%S %Z")
    author = bot.get_user(int(faquery["creator"]))
    authorName = ctx.guild.get_member(author.id).display_name
    if author.avatar:
        authorPic = f"https://cdn.discordapp.com/avatars/{author.id}/{author.avatar}.png?size=64"
    else:
        authorPic = "https://cdn.discordapp.com/embed/avatars/0.png"
    if content and not image:
        em = discord.Embed(title=title,
                           description=content,
                           timestamp=timestamp,
                           colour=color)

    elif not content and image:
        em = discord.Embed(title=title,
                           timestamp=timestamp,
                           colour=color)
        em.set_image(url=image)

    else:
        em = discord.Embed(title=title,
                           description=content,
                           timestamp=timestamp,
                           colour=color)
        em.set_image(url=image)
    em.set_author(name=authorName, icon_url=authorPic)
    em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
    return em


class faqCog:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Frequently Asked Questions"

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            em = discord.Embed(title="Error",
                               description=f"You do not have sufficient permissions to use the command `{ctx.command}`",
                               colour=0xDC143C)
            return await ctx.send(embed=em)
        else:
            raise error

    @commands.group(name="faq", aliases=["tag", "tags", "faw"], invoke_without_command=True)
    async def faqCommand(self, ctx, *, query: str=""):
        """
        Shows the list of available FAQ tags.
        """
        query = query.lower()
        if not query:
            faqstr = list(faqdb.keys())
            faqstr.sort()
            em = discord.Embed(title="List of FAQ tags",
                               description=', '.join(faqstr).title(),
                               colour=0xDFDE6E)

        elif query in faqdb:
            em = embedFAQ(ctx, self.bot, query)

        else:
            closeItems = []
            for item in list(faqdb.keys()):
                if fuzz.ratio(query, item) >= 75:
                    closeItems.append(item.title())
            if len(closeItems) > 0:
                em = discord.Embed(title=f"Could not find \"{query.title()}\" in FAQ tags.",
                                   description=f"Did you mean {', '.join(closeItems)}?",
                                   colour=0x19B300)
            else:
                em = discord.Embed(title="Error",
                                   description=f"Could not find \"{query.title()}\" or any similarly named tags in FAQ tags.",
                                   colour=0xDC143C)
                em.set_footer(text=f"To see the list of all available FAQ tags, use {ctx.prefix}faq", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @faqCommand.command(name="add", aliases=["edit"])
    @commands.has_any_role(*variables["botroles"])
    async def faqAdd(self, ctx, title: str, *, content: str = ""):
        """
        Add a new tag to the FAQ tags.
        """
        updatebool = True
        title = title.lower()
        if len(title) > 256:
            em = discord.Embed(title="Error",
                               description="The title inputted is too long.\nThe maximum title length is 256 characters.",
                               colour=0xDC143C)
            await ctx.send(embed=em)
            return 0
        if not content and not ctx.message.attachments:
            em = discord.Embed(title="Error",
                               description="Content is required to add an FAQ tag.",
                               colour=0xDC143C)
            em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
            await ctx.send(embed=em)
            updatebool = False

        elif content and not ctx.message.attachments:
            faqdb[title] = {}
            faqdb[title]["content"] = content
            faqdb[title]["image"] = ""
            faqdb[title]["timestamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " UTC"
            faqdb[title]["creator"] = str(ctx.message.author.id)

        elif not content and ctx.message.attachments:
            faqdb[title] = {}
            faqdb[title]["content"] = ""
            faqdb[title]["timestamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " UTC"
            faqdb[title]["creator"] = str(ctx.message.author.id)
            attachedFile = ctx.message.attachments[0]
            if attachedFile.filename.lower()[-3:] in ['png', 'jpg', 'gif'] or attachedFile.filename.lower()[-4:] in ['jpeg']:
                faqdb[title]["image"] = attachedFile.url
            else:
                em = discord.Embed(title="Error",
                                   description="An invalid image was used.\nThe supported formats are `png`, `jpg`, `jpeg` & `gif`",
                                   colour=0xDC143C)
                em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
                await ctx.send(embed=em)

        else:
            faqdb[title] = {}
            faqdb[title]["content"] = content
            faqdb[title]["timestamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + " UTC"
            faqdb[title]["creator"] = str(ctx.message.author.id)
            attachedFile = ctx.message.attachments[0]
            if attachedFile.filename.lower()[-3:] in ['png', 'jpg', 'gif'] or attachedFile.filename.lower()[-4:] in ['jpeg']:
                faqdb[title]["image"] = attachedFile.url
            else:
                em = discord.Embed(title="Error",
                                   description="An invalid image was used.\nThe supported formats are `png`, `jpg`, `jpeg` & `gif`",
                                   colour=0xDC143C)
                em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
                await ctx.send(embed=em)

        if updatebool:
            with open('data/tagdatabase.json', 'w') as database:
                database.write(json.dumps(faqdb, sort_keys=True, indent=4))
            try:
                faqdb[title]
                embedTitle = f"Successfully added \'{title.title()}\' to database"
            except KeyError:
                embedTitle = f"Successfully edited \"{title.title()}\" in database"

            await ctx.send(embed=embedFAQ(ctx, self.bot, title, embedTitle, 0x19B300))

    @faqCommand.command(name="remove")
    @commands.has_any_role(*variables["botroles"])
    async def faqRemove(self, ctx, *, title: str):
        """
        Remove a tag from the FAQ tags.
        """
        title = title.lower()
        if title in faqdb:
            del faqdb[title]
            with open('data/tagdatabase.json', 'w') as database:
                database.write(json.dumps(faqdb, sort_keys=True, indent=4))
            em = discord.Embed(title=f"Successfully removed \'{title.title()}\' from FAQ tags.",
                               description=f"To see the list of available tags, use {ctx.prefix}faq",
                               colour=0x19B300)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="Query not in FAQ tags.",
                               colour=0x19B300)
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(faqCog(bot))
