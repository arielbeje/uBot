import datetime
import pytz

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from fuzzywuzzy import fuzz

from utils import customchecks, sql
from utils.punishmentshelper import lazily_fetch_member

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
    em = discord.Embed(title=title,
                       description="" if queryRow[2] is None else str(queryRow[2]),
                       colour=color)
    if image:
        em.set_image(url=image)
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
    
async def list_all_tags(ctx: commands.Context, bot: commands.AutoShardedBot):
    faqList = await faqdb(ctx, keys=True)
    if len(faqList) > 0:
        em = discord.Embed(title="List of FAQ tags",
                            description=", ".join(faqList).title(),
                            colour=discord.Colour.gold())
    else:
        em = discord.Embed(title="Error",
                            description="This server does not have any defined FAQ tags.",
                            colour=discord.Colour.red())
    
    await ctx.send(embed=em)


async def send_faq_entry(ctx: commands.Context, bot: commands.AutoShardedBot, query: str):
    if query in await faqdb(ctx, keys=True):
        em = await embed_faq(ctx, bot, query)

    else:
        closeItems = []
        for item in await faqdb(ctx, keys=True):
            itemRatio = fuzz.ratio(query, item)
            if itemRatio >= 75:
                closeItems.append((itemRatio, item.title()))
        if len(closeItems) == 0:
            em = discord.Embed(title="Error",
                                description=f"Could not find \"{query.title()}\" or any similarly named tags in FAQ tags." + "\n" +
                                            f"Would you like to search [the wiki](https://wiki.factorio.com/index.php?search={query.replace(' ', '%20')})?",
                                colour=discord.Colour.red())
            em.set_footer(text=f"To see the list of all available FAQ tags, use {ctx.prefix}faq", icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
        elif len(closeItems) == 1:
            em = await embed_faq(ctx, bot, closeItems[0][1].lower(),
                                    title=f"Could not find \"{query.title()}\" in FAQ tags. Did you mean \"{closeItems[0][1]}\"?",
                                    color=discord.Colour.orange())
        else:
            em = discord.Embed(title=f"Could not find \"{query.title()}\" in FAQ tags.",
                                description=f"Did you mean {', '.join([item[1] for item in closeItems])}?",
                                colour=discord.Colour.orange())
    await ctx.send(embed=em)

class FAQCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.update_faq_cache.start()
        type(self).__name__ = "Frequently Asked Questions"
    
    def cog_unload(self) -> None:
        self.update_faq_cache.cancel()

    @tasks.loop(hours=3)
    async def update_faq_cache(self):
        self.tags = {}
        servers = [int(result[0]) for result in await sql.fetch("SELECT serverid FROM servers")]
        for server in servers:
            self.tags[server] = [result[0] for result in await sql.fetch("SELECT title FROM faq WHERE serverid=? ORDER BY title", str(server))]

    @commands.hybrid_group(name="faq", aliases=["tag", "tags", "faw", "FAQ"], fallback="list", with_app_command=True)
    async def faq_command(self, ctx: commands.Context, *, query: str = ""):
        """
        Shows the list of available FAQ tags or returns the tag with the given name.
        """
        query = query.lower()
        if not query:
            await list_all_tags(ctx, self.bot)
        
        else: 
            await send_faq_entry(ctx, self.bot, query)

    @faq_command.command(name="tag")
    async def faq_tag(self, ctx: commands.Context, *, query: str):
        """
        Shows the list of available FAQ tags or returns the tag with the given name.
        """
        query = query.lower()
        await send_faq_entry(ctx, self.bot, query)

    @faq_command.command(name="add", aliases=["edit", "new"])
    @customchecks.is_mod()
    async def faq_add(self, ctx: commands.Context, title: str, *, content: str = "", image: discord.Attachment = None):
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
        await self.update_faq_cache()

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
            await sql.execute("DELETE FROM faq WHERE serverid=? and link=?", str(ctx.message.guild.id), title)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="Query not in FAQ tags.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)
        await self.update_faq_cache()

    @faq_command.command(name="link")
    @customchecks.is_mod()
    @app_commands.rename(title="new_title", link="link_to")
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
        await self.update_faq_cache()
    
    @faq_tag.autocomplete("query")
    @faq_command.autocomplete("query")
    @faq_remove.autocomplete("title")
    @faq_link.autocomplete("link")
    async def faq_tag_autocomplete(self, ctx: commands.Context, current: str):
        server = ctx.guild.id
        return [app_commands.Choice(name=tag, value=tag) for tag in self.tags[server] if current.lower() in tag.lower()][0:25]


async def setup(bot):
    await bot.add_cog(FAQCog(bot))
