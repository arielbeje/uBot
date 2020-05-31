import datetime
import pytz

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

from utils import customchecks, sql

from typing import List


async def faqdb(ctx: commands.Context, query: str = None, keys: bool = False) -> List[str]:
    """
    Searches the database for FAQs according to parameters given
    """
    if keys:
        return [result[0] for result in await sql.fetch("SELECT title FROM faq WHERE serverid=? ORDER BY title", str(ctx.message.guild.id))]
    if query is None:
        return await sql.fetch("SELECT * FROM faq WHERE serverid=?", str(ctx.message.guild.id))
    faqRow = await sql.fetch("SELECT * FROM faq WHERE serverid=? AND title=?", str(ctx.message.guild.id), query)
    return faqRow[0]


async def embed_faq(ctx: commands.Context, bot: commands.AutoShardedBot, query: str, title: str = None, color: str = None) -> discord.Embed:
    """
    Returns a discord.Embed derived from the parameters given
    """
    queryRow = await faqdb(ctx, query)
    if queryRow[6] is not None:  # link
        queryRow = await faqdb(ctx, str(queryRow[6]))
    if not title:
        title = str(queryRow[1]).title()
    if not color:
        color = discord.Colour.gold()
    image = None if queryRow[3] is None else str(queryRow[3])
    author = bot.get_user(int(queryRow[4]))
    authorName = getattr(ctx.guild.get_member(author.id), "display_name", None)
    if authorName is not None and author.avatar:
        authorPic = "https://cdn.discordapp.com/avatars/{author.id}/{author.avatar}.png?size=64"
    else:
        authorPic = "https://cdn.discordapp.com/embed/avatars/0.png"
    em = discord.Embed(title=title,
                       description="" if queryRow[2] is None else str(queryRow[2]),
                       timestamp=datetime.datetime.strptime(queryRow[5], "%Y-%m-%d %H:%M:%S.%f%z"),
                       colour=color)
    if image:
        em.set_image(url=image)
    em.set_author(name=authorName or "Unknown", icon_url=authorPic)
    return em


async def check_image(ctx: commands.Context, bot: commands.AutoShardedBot, title: str, name: str, link: str = "") -> bool:
    """
    Checks wether a file is a supported image file
    """
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


class FAQCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Frequently Asked Questions"

    @commands.group(name="faq", aliases=["tag", "tags", "faw", "FAQ"], invoke_without_command=True)
    async def faq_command(self, ctx: commands.Context, *, query: str = ""):
        """
        Shows the list of available FAQ tags.
        """
        query = query.lower()
        if not query:
            faqList = await faqdb(ctx, keys=True)
            if len(faqList) > 0:
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
                                   description=f"Could not find \"{query.title()}\" or any similarly named tags in FAQ tags." + "\n" +
                                               f"Would you like to search [the wiki](https://wiki.factorio.com/index.php?search={query.replace(' ', '%20')})?",
                                   colour=discord.Colour.red())
                em.set_footer(text=f"To see the list of all available FAQ tags, use {ctx.prefix}faq", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @faq_command.command(name="add", aliases=["edit", "new"])
    @customchecks.is_mod()
    async def faq_add(self, ctx: commands.Context, title: str, *, content: str = ""):
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
                creator = curFAQ[4]
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
                await sql.execute("INSERT INTO faq VALUES(?, ?, ?, ?, ?, ?, ?)",
                                  str(ctx.message.guild.id), title, content, image, creator, timestamp, None)
                embedTitle = f"Successfully added \"{title.title()}\" to database"
            else:
                await sql.execute("UPDATE faq SET content=?, image=?, timestamp=? WHERE serverid=? AND title=?",
                                  content, image, timestamp, str(ctx.message.guild.id), title)
                embedTitle = f"Successfully edited \"{title.title()}\" in database"
            await ctx.send(embed=await embed_faq(ctx, self.bot, title, embedTitle, discord.Colour.dark_green()))

    @faq_command.command(name="remove", aliases=["delete"])
    @customchecks.is_mod()
    async def faq_remove(self, ctx: commands.Context, *, title: str):
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
            await sql.execute("DELETE FROM faq WHERE serverid=? AND title=?", str(ctx.message.guild.id), title)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="Query not in FAQ tags.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)

    @faq_command.command(name="link")
    @customchecks.is_mod()
    async def faq_link(self, ctx: commands.Context, title: str, *, link: str):
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
            await sql.execute("INSERT INTO faq (serverid, title, link) VALUES (?, ?, ?)", str(ctx.message.guild.id), title, link)
            em = discord.Embed(title=f"Successfully added tag \"{title}\" linking to \"{link}\"",
                               colour=discord.Colour.dark_green())
        else:
            em = discord.Embed(title="Error",
                               description="The tag to link to does not exist in the list of FAQ tags.",
                               colour=discord.Colour.red())
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(FAQCog(bot))
