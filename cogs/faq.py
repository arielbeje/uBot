import datetime
import os
import pytz
import re
import rethinkdb as r

import discord
from discord.ext import commands
from fuzzywuzzy import fuzz

import utils.customchecks as customchecks


def faqdb(ctx, keys=False):
    with r.connect(db="bot") as conn:
        returnDict = r.table("servers").get(
            ctx.message.guild.id).pluck("faq").run(conn)["faq"]
        if keys:
            return list(returnDict.keys())
        else:
            return returnDict


def embed_faq(ctx, bot, query, title=None, color=None):
    faquery = faqdb(ctx)[query]
    if "link" in faquery:
        faquery = faqdb(ctx)[faquery["link"]]
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
    em = discord.Embed(title=title,
                       description=content,
                       timestamp=timestamp,
                       colour=color)
    if image:
        em.set_image(url=image)
    em.set_author(name=authorName, icon_url=authorPic)
    # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
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
                           colour=0xDC143C)
        # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
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
            faqstr = faqdb(ctx, keys=True)
            faqstr.sort()
            em = discord.Embed(title="List of FAQ tags",
                               description=", ".join(faqstr).title(),
                               colour=0xDFDE6E)

        elif query in faqdb(ctx):
            em = embed_faq(ctx, self.bot, query)

        else:
            closeItems = []
            for item in faqdb(ctx, keys=True):
                if fuzz.ratio(query, item) >= 75:
                    closeItems.append(item.title())
            if len(closeItems) > 0:
                if len(closeItems) == 1:
                    em = embed_faq(ctx, self.bot, closeItems[0].lower(),
                                   title=f"Could not find \"{query.title()}\" in FAQ tags. Did you mean \"{closeItems[0]}\"?",
                                   color=0xFF8C00)
                else:
                    em = discord.Embed(title=f"Could not find \"{query.title()}\" in FAQ tags.",
                                       description=f"Did you mean {', '.join(closeItems)}?",
                                       colour=0xFF8C00)
            else:
                em = discord.Embed(title="Error",
                                   description=f"Could not find \"{query.title()}\" or any similarly named tags in FAQ tags.",
                                   colour=0xDC143C)
                em.set_footer(text=f"To see the list of all available FAQ tags, use {ctx.prefix}faq", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @faq_command.command(name="add", aliases=["edit"])
    @customchecks.has_mod_role()
    async def faq_add(self, ctx, title: str, *, content: str = ""):
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
                               colour=0xDC143C)
            await ctx.send(embed=em)
            return
        if (not content and
                not ctx.message.attachments and
                not imageURL):
            em = discord.Embed(title="Error",
                               description="Content is required to add an FAQ tag.",
                               colour=0xDC143C)
            # em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
            await ctx.send(embed=em)
            return

        else:
            creator = str(ctx.message.author.id)
            existed = False
            if title in faqdb(ctx):
                creator = faqdb(ctx)[title]["creator"]
                existed = True

            currentfaq = {}
            currentfaq["content"] = content
            currentfaq["image"] = ""
            currentfaq["timestamp"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            currentfaq["creator"] = creator

            if imageURL:
                if not await check_image(ctx, self.bot, title, imageURL):
                    updatebool = False
                else:
                    currentfaq["image"] = imageURL
            elif ctx.message.attachments:
                attachedFile = ctx.message.attachments[0]
                attachedFileName = attachedFile.filename.lower()
                if not await check_image(ctx, self.bot, title, attachedFileName, attachedFile.url):
                    updatebool = False
                else:
                    currentfaq["image"] = attachedFile.url

        if updatebool:
            with r.connect(db="bot") as conn:
                faq = r.table("servers").get(
                    ctx.message.guild.id).pluck("faq").run(conn)["faq"]
                faq[title] = currentfaq
                r.table("servers").get(ctx.message.guild.id).update(
                    {"faq": faq}).run(conn)
            embedTitle = f"Successfully added \"{title.title()}\" to database"
            if existed:
                embedTitle = f"Successfully edited \"{title.title()}\" in database"

            await ctx.send(embed=embed_faq(ctx, self.bot, title, embedTitle, 0x19B300))

    @faq_command.command(name="remove", aliases=["delete"])
    @customchecks.has_mod_role()
    async def faq_remove(self, ctx, *, title: str):
        """
        Remove a tag from the FAQ tags.
        """
        title = title.lower()
        if title in faqdb(ctx):
            em = embed_faq(ctx=ctx,
                           bot=self.bot,
                           query=title,
                           title=f"Successfully removed \"{title.title()}\" from FAQ tags.",
                           color=0xDC143C)
            with r.connect(db="bot") as conn:
                faq = r.table("servers").get(
                    ctx.message.guild.id).pluck("faq").run(conn)["faq"]
                del faq[title]
                r.table("servers").get(ctx.message.guild.id).update(
                    {"faq": r.literal(faq)}).run(conn)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Error",
                               description="Query not in FAQ tags.",
                               colour=0xDC143C)
            await ctx.send(embed=em)

    @faq_command.command(name="link")
    @customchecks.has_mod_role()
    async def faq_link(self, ctx, title: str, *, link: str):
        """
        Makes a shortcut tag in the list of FAQ tags.
        """
        if link in faqdb(ctx):
            if title in faqdb(ctx):
                em = embed_faq(ctx=ctx,
                               bot=self.bot,
                               query=title,
                               title=f"Successfully edited \"{title.title()}\" to be a link for \"{link.title()}\"")
            with r.connect(db="bot") as conn:
                faq = r.table("servers").get(
                    ctx.message.guild.id).pluck("faq").run(conn)["faq"]
                faq[title] = {"link": link}
                r.table("servers").get(ctx.message.guild.id).update(
                    {"faq": faq}).run(conn)
            em = discord.Embed(title=f"Successfully added tag \"{title}\" linking to \"{link}\"",
                               colour=0x19B300)
        else:
            em = discord.Embed(title="Error",
                               description="The tag to link to does not exist in the list of FAQ tags.",
                               colour=0xDC143C)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(FAQCog(bot))
