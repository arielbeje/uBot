import datetime
import pytz

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from utils import customchecks, sql


async def faqdb(ctx, query=None, keys=False):
    if keys:
        return [result["title"] for result in await sql.fetch("SELECT title FROM faq WHERE serverid=$1 ORDER BY title", ctx.message.guild.id)]
    if query is None:
        return await sql.fetch("SELECT * FROM faq WHERE serverid=$1", ctx.message.guild.id)
    faqRow = await sql.fetch("SELECT * FROM faq WHERE serverid=$1 AND title=$2", ctx.message.guild.id, query)
    return faqRow[0]


async def embed_faq(ctx, bot, query, title=None, color=None):
    faquery = await faqdb(ctx, query)
    if faquery[6] is not None:  # link
        faquery = await faqdb(ctx, str(faquery[6]))
    if not title:
        title = str(faquery[1]).title()
    if not color:
        color = discord.Colour.gold()
    image = None if faquery[3] is None else str(faquery[3])
    author = bot.get_user(int(faquery["creator"]))
    authorName = ctx.guild.get_member(author.id).display_name
    if author.avatar:
        authorPic = f"https://cdn.discordapp.com/avatars/{author.id}/{author.avatar}.png?size=64"
    else:
        authorPic = "https://cdn.discordapp.com/embed/avatars/0.png"
    em = discord.Embed(title=title,
                       description="" if faquery[2] is None else str(faquery[2]),
                       timestamp=faquery[5],
                       colour=color)
    if image:
        em.set_image(url=image)
    em.set_author(name=authorName, icon_url=authorPic)
    return em


async def check_image(ctx, bot, title, name, link=""):
    if not link:
        link = name
    if (name[-3:] in ["png", "jpg", "gif"] or
            name[-4:] == "jpeg"):
        return True
    else:
        em = discord.Embed(title="Error",
                           description="An invalid image was used."
                                       "The supported formats are `png`, `jpg`, `jpeg` & `gif`",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
        return False


class FAQCog:
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Frequently Asked Questions"

    @commands.group(name="faq", aliases=["tag", "tags", "faw"], invoke_without_command=True)
    async def faq_command(self, ctx, *, query: str=""):
        """
        Shows the list of available FAQ tags.
        """
        query = query.lower()
        if not query:
            faqList = await faqdb(ctx, keys=True)
            if len(faqList) > 1:
                em = discord.Embed(title="List of FAQ tags",
                                   description=", ".join(faqList).title(),
                                   colour=discord.Colour.gold())
            else:
                em = discord.Embed(title="Error",
                                   description="This server does not have any defined FAQ tags.",
                                   colour=discord.Colour.red())

        elif query in await faqdb(ctx, keys=True):
            em = await embed_faq(ctx, self.bot, query)

        else:
            closeItems = []
            for item in await faqdb(ctx, keys=True):
                itemRatio = fuzz.ratio(query, item)
                if itemRatio >= 75:
                    closeItems.append((itemRatio, item.title()))
            if len(closeItems) > 0:
                if len(closeItems) == 1:
                    em = await embed_faq(ctx, self.bot, closeItems[0][1].lower(),
                                         title=f"Could not find \"{query.title()}\" in FAQ tags. Did you mean \"{closeItems[0][1]}\"?",
                                         color=discord.Colour.orange())
                else:
                    em = discord.Embed(title=f"Could not find \"{query.title()}\" in FAQ tags.",
                                       description=f"Did you mean {', '.join([item[1] for item in closeItems])}?",
                                       colour=discord.Colour.orange())
            else:
                em = discord.Embed(title="Error",
                                   description=f"Could not find \"{query.title()}\" or any similarly named tags in FAQ tags.",
                                   colour=discord.Colour.red())
                em.set_footer(text=f"To see the list of all available FAQ tags, use {ctx.prefix}faq", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @faq_command.command(name="add", aliases=["edit"])
    @customchecks.is_mod()
    async def faq_add(self, ctx, title: str, *, content: str=""):
        """
        Add a new tag to the FAQ tags.
        Can add an image by either attaching it to the message, or using ~~ imageurl at the end.
        """
        updatebool = True
        title = title.lower()
        try:
            content.split("~~")[1]
            content, imageURL = (content.split("~~")[0].strip(), content.split("~~")[1].strip())
        except IndexError:
            imageURL = ""
        if len(title) > 256:
            em = discord.Embed(title="Error",
                               description="The title inputted is too long.\nThe maximum title length is 256 characters.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)
            return
        if (not content and
                not ctx.message.attachments and
                not imageURL):
            em = discord.Embed(title="Error",
                               description="Content is required to add an FAQ tag.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)
            return

        else:
            creator = ctx.message.author.id
            existed = False
            if title in await faqdb(ctx, keys=True):
                curFAQ = await faqdb(ctx, title)
                creator = curFAQ["creator"]
                existed = True

            image = None
            timestamp = pytz.utc.localize(datetime.datetime.utcnow())

            if imageURL:
                if not await check_image(ctx, self.bot, title, imageURL):
                    updatebool = False
                else:
                    image = imageURL
            elif ctx.message.attachments:
                attachedFile = ctx.message.attachments[0]
                attachedFileName = attachedFile.filename.lower()
                if not await check_image(ctx, self.bot, title, attachedFileName, attachedFile.url):
                    updatebool = False
                else:
                    image = attachedFile.url

        if updatebool:
            if not existed:
                await sql.execute("INSERT INTO faq VALUES($1, $2, $3, $4, $5, $6, $7)",
                                  ctx.message.guild.id, title, content, image, creator, timestamp, None)
                embedTitle = f"Successfully added \"{title.title()}\" to database"
            else:
                await sql.execute("UPDATE faq SET content=$1, image=$2, timestamp=$3 WHERE serverid=$4 AND title=$5",
                                  content, image, timestamp, ctx.message.guild.id, title)
                embedTitle = f"Successfully edited \"{title.title()}\" in database"
            await ctx.send(embed=await embed_faq(ctx, self.bot, title, embedTitle, discord.Colour.dark_green()))

    @faq_command.command(name="remove", aliases=["delete"])
    @customchecks.is_mod()
    async def faq_remove(self, ctx, *, title: str):
        """
        Remove a tag from the FAQ tags.
        """
        title = title.lower()
        if title in await faqdb(ctx, keys=True):
            em = await embed_faq(ctx=ctx,
                                 bot=self.bot,
                                 query=title,
                                 title=f"Successfully removed \"{title.title()}\" from FAQ tags.",
                                 color=discord.Colour.red())
            await sql.execute("DELETE FROM faq WHERE serverid=$1 AND title=$2", ctx.message.guild.id, title)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="Query not in FAQ tags.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)

    @faq_command.command(name="link")
    @customchecks.is_mod()
    async def faq_link(self, ctx, title: str, *, link: str):
        """
        Makes a shortcut tag in the list of FAQ tags.
        """
        curDB = await faqdb(ctx, keys=True)
        if link in curDB:
            if title in curDB:
                em = await embed_faq(ctx=ctx,
                                     bot=self.bot,
                                     query=title,
                                     title=f"Successfully edited \"{title.title()}\" to be a link for \"{link.title()}\"")
            await sql.execute("INSERT INTO faq (serverid, title, link) VALUES ($1, $2, $3)", ctx.message.guild.id, title, link)
            em = discord.Embed(title=f"Successfully added tag \"{title}\" linking to \"{link}\"",
                               colour=discord.Colour.dark_green())
        else:
            em = discord.Embed(title="Error",
                               description="The tag to link to does not exist in the list of FAQ tags.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(FAQCog(bot))
