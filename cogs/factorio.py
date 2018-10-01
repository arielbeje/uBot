import aiohttp
import bs4
import tomd
import re

import discord
from discord.ext import commands

from utils import assets

headerEx = re.compile(r"((^<br/>$)|(This (article|page)))")
referEx = re.compile(r".*? may refer to\:")
linkEx = re.compile(r"\((\/\S*)\)")
fontEx = re.compile(r"<h\d>(.*?)(<font.*>(.*?)</font>)?</h\d>")


async def get_response(url):
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            status = resp.status
            r = await resp.text()
    return (status, bs4.BeautifulSoup(r, "html.parser"))


def mod_embed(result):
    taglist = []
    fields = []
    title = result.find("div", class_="mod-card-info-container").find("h2", class_="mod-card-title").find("a")
    em = discord.Embed(title=title.get_text(),
                       url=f"https://mods.factorio.com{title['href'].replace(' ', '%20')}",
                       description=result.find("div", class_="mod-card-info-container").find("div", class_="mod-card-summary").get_text(),
                       colour=assets.Colors.success)
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
    return em


def get_wiki_description(soup):
    if soup.select("#mw-content-text > p"):
        pNum = 0
        if headerEx.search(str(soup.select("#mw-content-text > p")[0])):
            pNum = 1
        return tomd.convert(str(soup.select("#mw-content-text > p")[pNum])).strip().replace("<br/>", "\n")
    return ""


async def wiki_embed(url):
    soup = get_response(url)[1]
    description = await get_wiki_description()
    if "may refer to:" in description:
        url = soup.select("#mw-content-text > ul > li > a")[0]["href"]
        description = get_wiki_description(get_response(url)[1])

    em = discord.Embed(title=soup.find("h1", id="firstHeading").get_text(),
                       description=linkEx.sub(r"(https://wiki.factorio.com\1)", description),
                       url=url,
                       colour=assets.Colors.success)
    if soup.find("div", class_="factorio-icon"):
        em.set_thumbnail(url=f"https://wiki.factorio.com{soup.find('div', class_='factorio-icon').find('img')['src']}")
    return em


class FactorioCog():
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Factorio Commands"

    @commands.command(aliases=["mod"])
    async def linkmod(self, ctx, *, modname):
        """
        Search for a mod in [the Factorio mod portal](https://mods.factorio.com).
        """
        em = discord.Embed(title=f"Searching for \"{modname.title()}\" in mods.factorio.com...",
                           description="This may take a bit.",
                           colour=assets.Colors.listing)
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():
            try:
                soup = await get_response(f"https://mods.factorio.com/query/{modname.title()}")[1]

                if " 0 " in soup.find("span", class_="active-filters-bar-total-mods").get_text():
                    em = discord.Embed(title="Error",
                                       description=f"Could not find \"{modname.title()}\" in mod portal.",
                                       colour=assets.Colors.error)
                    await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
                    return

                if soup.find_all("div", class_="mod-card"):
                    if len(soup.find_all("div", class_="mod-card")) > 1:
                        em = discord.Embed(title=f"Search results for \"{modname}\"",
                                           colour=assets.Colors.listing)
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
                                   colour=assets.Colors.error)
                bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()

    @commands.command()
    async def wiki(self, ctx, *, searchterm):
        """
        Searches for a term in the [official Factorio wiki](https://wiki.factorio.com/).
        """
        em = discord.Embed(title=f"Searching for \"{searchterm.title()}\" in wiki.factorio.com...",
                           description="This shouldn't take long.",
                           colour=assets.Colors.listing)
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():
            url = f"https://wiki.factorio.com/index.php?search={searchterm.replace(' ', '%20')}"
            soup = get_response(url)[1]
            if soup.find("p", class_="mw-search-nonefound"):
                em = discord.Embed(title="Error",
                                   description=f"Could not find \"{searchterm.title()}\" in wiki.",
                                   colour=assets.Colors.error)
                await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
                return
            if soup.find_all("ul", class_="mw-search-results"):
                em = discord.Embed(title="Factorio Wiki",
                                   url=url,
                                   colour=assets.Colors.listing)
                for item in soup.find_all("ul", class_="mw-search-results")[0].find_all("li"):
                    item = item.find_next("div", class_="mw-search-result-heading").find("a")
                    itemLink = item["href"] if not item["href"].endswith(")") else item["href"].replace(")", "\)")
                    em.add_field(name=item["title"], value=f"[Read More](https://wiki.factorio.com{itemLink})", inline=True)
                await bufferMsg.edit(embed=em)
            else:
                await bufferMsg.edit(embed=await wiki_embed(url))

    @commands.command()
    async def fff(self, ctx, number):
        """Links an fff with the number provided."""
        try:
            number = int(number)
            link = f"https://factorio.com/blog/post/fff-{number}"
            response = await get_response(link)
            if response[0] == 200:
                soup = response[1]
                titleList = soup.find_all("h2")
                em = discord.Embed(title=titleList[0].string.strip(),
                                   url=link,
                                   colour=assets.Colors.success)
                titleList = titleList[1:]
                if len(titleList) == 0:
                    titleList = soup.find_all("h4")
                if len(titleList) == 0:
                    titleList = soup.find_all("h3")
                for title in titleList:
                    result = fontEx.search(str(title))
                    if len([group for group in result.groups() if group is not None]) == 1:
                        name = result.group(1)
                    else:
                        name = result.group(1) + result.group(3)
                    em.add_field(name=name,
                                 value=tomd.convert(str(title.next_sibling.next_sibling)).strip())
            else:
                em = discord.Embed(title="Error",
                                   description=f"Couldn't find FFF #{number}.",
                                   colour=assets.Colors.error)
        except ValueError:
            em = discord.Embed(title="Error",
                               desctiption="To use the command, you need to input a number.",
                               colour=assets.Colors.error)
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(FactorioCog(bot))
