import aiohttp
import bs4
import tomd
import re

import discord
from discord.ext import commands


def mod_embed(result):
    taglist = []
    fields = []
    title = result.find("div", class_="mod-card-info-container").find("h2", class_="mod-card-title").find("a")
    em = discord.Embed(title=title.get_text(),
                       url=f"https://mods.factorio.com{title['href'].replace(' ', '%20')}",
                       description=result.find("div", class_="mod-card-info-container").find("div", class_="mod-card-summary").get_text(),
                       colour=0x19B300)
    thumbnail = result.find("div", class_="mod-card-thumbnail")
    if "no-picture" not in thumbnail.attrs["class"]:
        em.set_thumbnail(url=thumbnail.find("a").find("img")["src"])
    owner = result.find("div", class_="mod-card-info-container").find("div", class_="mod-card-author").find("a")
    fields.append({"name": "Owner", "value": f"[{owner.get_text()}]({owner['href']})"})
    for tag in result.find("div", class_="mod-card-footer").find("ul").find_all("li", class_="tag"):
        tag = tag.find("span").find("a")
        taglist.append(f"[{tag.get_text()}]({tag['href']})")
    gameVersions = result.find("div", class_="mod-card-info").find("span", title="Available for these Factorio versions")
    downloads = result.find("div", class_="mod-card-info").find("span", title="Downloads")
    createdAt = result.find("div", class_="mod-card-info").find("span", title="Last updated")
    fields.extend([{"name": "Tags", "value": ', '.join(taglist)},
                   {"name": "Game Version(s)", "value": gameVersions.find("div", class_="mod-card-info-tag-label").get_text()},
                   {"name": "Downloads", "value": downloads.find("div", class_="mod-card-info-tag-label").get_text()},
                   {"name": "Updated", "value": createdAt.find("div", class_="mod-card-info-tag-label").get_text()}])
    for field in fields:
        em.add_field(**field, inline=True)
    # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
    return em


class FactorioCog():
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Factorio Commands"

    @commands.command(name="linkmod", aliases=["mod"])
    async def linkmod(self, ctx, *, modname):
        """
        Search for a mod in [mods.factorio.com](https://mods.factorio.com).
        """
        em = discord.Embed(title=f"Searching for \"{modname.title()}\" in mods.factorio.com...",
                           description="This may take a bit.",
                           colour=0xDFDE6E)
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    modname = modname.title()
                    async with session.get(f"https://mods.factorio.com/query/{modname}") as response:
                        soup = bs4.BeautifulSoup(await response.text(), 'html.parser')

                if " 0 " in soup.find("span", class_="active-filters-bar-total-mods").get_text():
                    em = discord.Embed(title="Error",
                                       description=f"Could not find \"{modname.title()}\" in mod portal.",
                                       colour=0xDC143C)
                    await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
                    return

                if soup.find_all("div", class_="mod-card"):
                    if len(soup.find_all("div", class_="mod-card")) > 1:
                        em = discord.Embed(title=f"Search results for \"{modname}\"",
                                           colour=0xDFDE6E)
                        i = 0
                        for result in soup.find_all("div", class_="mod-card"):
                            if i <= 4:
                                title = result.find("h2", class_="mod-card-title").find("a")
                                if title.get_text().title() == modname.title():
                                    em = mod_embed(result)
                                    break
                                em.add_field(name=title.get_text(),
                                             value=f"{result.find('div', class_='mod-card-summary').get_text()} [_Read More_](https://mods.factorio.com/mods{title['href']})")
                                i += 1

                    else:
                        em = mod_embed(soup.find("div", class_="mod-card"))

                    await bufferMsg.edit(embed=em)
                    return

            except (aiohttp.client_exceptions.ContentTypeError, KeyError):
                em = discord.Embed(title="Error",
                                   description="Couldn't reach mods.factorio.com.",
                                   colour=0xDC143C)
                bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()

    @commands.command(name="wiki")
    async def wiki(self, ctx, *, searchterm):
        """
        Searches for a term in the [official Factorio wiki](https://wiki.factorio.com/).
        """
        em = discord.Embed(title=f"Searching for \"{searchterm.title()}\" in wiki.factorio.com...",
                           description="This shouldn't take long.",
                           colour=0xDFDE6E)
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as client:
                async with client.get(f"https://wiki.factorio.com/index.php?search={searchterm.replace(' ', '%20')}") as resp:
                    r = await resp.text()
                    url = str(resp.url)
            soup = bs4.BeautifulSoup(r, "html.parser")
            if soup.find("p", class_="mw-search-nonefound"):
                em = discord.Embed(title="Error",
                                   description=f"Could not find \"{searchterm.title()}\" in wiki.",
                                   colour=0xDC143C)
                await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
                return
            if soup.find_all("ul", class_="mw-search-results"):
                em = discord.Embed(title="Factorio Wiki",
                                   url=url,
                                   colour=0xDFDE6E)
                for item in soup.find_all("ul", class_="mw-search-results")[0].find_all("li"):
                    item = item.find_next("div", class_="mw-search-result-heading").find("a")
                    itemlink = item["href"] if not item["href"].endswith(")") else item["href"].replace(")", "\)")
                    em.add_field(name=item["title"], value=f"[Read More](https://wiki.factorio.com{itemlink})", inline=True)
                await bufferMsg.edit(embed=em)
            else:
                description_ = ""
                if soup.select("#mw-content-text > p"):
                    pNum = 0
                    if re.search(r"((^<br/>$)|(This (article|page)))", str(soup.select("#mw-content-text > p")[0])):
                        pNum = 1
                    description_ = tomd.convert(str(soup.select("#mw-content-text > p")[pNum])).strip().replace("<br/>", "\n")
                em = discord.Embed(title=soup.find("h1", id="firstHeading").get_text(),
                                   description=re.sub(r"\((\/\S*)\)", r"(https://wiki.factorio.com\1)", description_),
                                   url=url,
                                   colour=0x19B300)
                if soup.find("div", class_="factorio-icon"):
                    em.set_thumbnail(url=f"https://wiki.factorio.com{soup.find('div', class_='factorio-icon').find('img')['src']}")
                await bufferMsg.edit(embed=em)


def setup(bot):
    bot.add_cog(FactorioCog(bot))
