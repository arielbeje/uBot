import aiohttp
import bs4
import feedparser
import re
import tomd

import discord
from discord.ext import commands

from typing import List, Tuple, Union

WIKI_API_URL = "https://wiki.factorio.com/api.php"

headerEx = re.compile(r"((^<br/>$)|(This (article|page)))")
referEx = re.compile(r".*? may refer to\:")
linkEx = re.compile(r"\[\[(.*?)(?:\|(.*?))?\]\]", re.X)
fontEx = re.compile(r"<h\d>(.*?)(<font.*>(.*?)</font>)?</h\d>")
langEx = re.compile(r"/(cs|de|es|fr|it|ja|nl|pl|pt-br|ru|sv|uk|zh|tr|ko|ms|da|hu|vi|pt-pt)$")
fffEx = re.compile(r"Friday Facts #(\d*)")
propEx = re.compile(r"^(\w+ :: [^:]+)(: (.+))?$")
markdownEx = re.compile(r"([~*_`])")


async def get_soup(url: str) -> Tuple[int, bs4.BeautifulSoup]:
    """
    Returns a list with the response code (as int) and a BeautifulSoup object of the URL
    """
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            status = resp.status
            r = await resp.text()
    return (status, bs4.BeautifulSoup(r, "html.parser"))


def mod_embed(result: bs4.BeautifulSoup) -> discord.Embed:
    """
    Returns a discord.Embed object derived from a mod page BeautifulSoup
    """
    taglist = []
    fields = []
    headerAndSummaryDiv = result.find("div", class_="w100p")
    infoCard = result.find("div", class_="mod-card-info")
    footer = result.find("div", class_="panel-inset")

    title = headerAndSummaryDiv.find("h2", class_="mb0").find("a")
    summary = headerAndSummaryDiv.find("p", class_="pre-line").string
    em = discord.Embed(title=title.string,
                       url=f"https://mods.factorio.com{title['href'].replace(' ', '%20')}",
                       description=markdownEx.sub(r"\\\1", summary),
                       colour=discord.Colour.dark_green())
    thumbnail = result.find("div", class_="mod-thumbnail").find("img")
    if thumbnail is not None:
        em.set_thumbnail(url=thumbnail["src"])
    owner = headerAndSummaryDiv.find("div").find("a", class_="orange")
    fields.append({"name": "Owner", "value": f"[{owner.string}](https://mods.factorio.com{owner['href']})"})
    for tag in footer.find_all("a", class_="slot-button-inline"):
        taglist.append(f"[{tag.string.strip()}](https://mods.factorio.com{tag['href']})")
    gameVersions = infoCard.find("div", title="Available for these Factorio versions").contents[2].strip()
    downloads = infoCard.find("div", title="Downloads, updated daily").contents[2].strip()
    createdAtDiv = infoCard.find("div", title="Last updated")
    createdAt = createdAtDiv.find("span").contents[0].strip()
    fields.extend([{"name": "Category", "value": "None" if len(taglist) == 0 else ", ".join(taglist)},
                   {"name": "Game Version(s)", "value": gameVersions},
                   {"name": "Downloads", "value": downloads},
                   {"name": "Updated", "value": createdAt}])
    for field in fields:
        em.add_field(**field, inline=True)
    return em


async def embed_fff(number: int) -> discord.Embed:
    """
    Returns a discord.Embed object derived from an fff number
    """
    link = f"https://factorio.com/blog/post/fff-{number}"
    response = await get_soup(link)
    if response[0] == 200:
        soup = response[1]
        titleList = soup.find_all("h2")
        em = discord.Embed(title=titleList[0].string.strip(),
                           url=link,
                           colour=discord.Colour.dark_green())
        titleList = titleList[1:]
        if len(titleList) == 0:
            titleList = soup.find_all("h4")
        if len(titleList) == 0:
            titleList = soup.find_all("h3")
        for title in titleList:
            # Check for smaller font tag and append it to the title
            result = fontEx.search(str(title))
            if len([group for group in result.groups() if group is not None]) == 1:
                name = result.group(1)
            else:
                name = result.group(1) + result.group(3)
            content = str(title.next_sibling.next_sibling)
            if "<p>" not in content:
                continue
            if "<ol>" in content:
                itemCount = 1
                while "<li>" in content:
                    content = content.replace("<li>", f"{itemCount}. ", 1)
                    itemCount += 1
            if "<ul>" in content:
                content = content.replace("<li>", "- ")
            for item in ["<ol>", "</ol>", "<ul>", "</ul>", "</li>", "<br/>"]:
                content = content.replace(item, "")
            # Escape Discord formatting characters
            for item in ["*", "_"]:
                content = content.replace(item, "\\" + item)
            content = content.replace("\n\n", "\n")
            em.add_field(name=name.replace("amp;", ""),
                         value=tomd.convert(content).strip())
    else:
        em = discord.Embed(title="Error",
                           description=f"Couldn't find FFF #{number}.",
                           colour=discord.Colour.red())
    return em

async def get_wiki_page_safe(client, api_url, title):
    async with client.get(api_url, params={
        "action": "parse",
        "format": "json",
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content"
    }) as page_info:
        pagejson = await page_info.json()
        page = pagejson["query"]["pages"]
        if "revisions" in list(page.values())[0]:
            revisions = list(page.values())[0]["revisions"][0]
            title = list(page.values())[0]["title"]
            content = list(revisions.values())[2]
            return content
        return ""

async def search_wiki_page(client, api_url, title):
    async with client.get(api_url, params={
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": title,
        "srnamespace": "0|3000"
    }) as page_info:
        pagejson = await page_info.json()
        totalhits = pagejson["query"]["searchinfo"]["totalhits"]
        results = pagejson["query"]["search"]
        return totalhits, results

async def process_wiki(ctx: commands.Context, searchterm: str):
    """
    Sends a message according to parameters given
    """
    #Error when no search term is given
    if not searchterm:
        em = discord.Embed(title="Error",
                           description="To use this command, you have to enter a term to search for.",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
        return
    baseURL = "wiki.factorio.com"

    #Buffer message
    em = discord.Embed(title=f"Searching for \"{searchterm.title()}\" in {baseURL}...",
                       description="This shouldn't take long.",
                       colour=discord.Colour.gold())
    bufferMsg = await ctx.send(embed=em)
    async with ctx.channel.typing():
        async with aiohttp.ClientSession() as client:
            totalhits, results = await search_wiki_page(client, WIKI_API_URL, searchterm)
            if totalhits == 0:
                em = discord.Embed(title="Error",
                    description=f"Could not find \"{searchterm.title()}\" in wiki.",
                    colour=discord.Colour.red())
                await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()

            elif results[0]["title"].lower() == searchterm.lower():
                await wiki_page_embed(baseURL, bufferMsg, client, results[0])
            else: 
                engResults = []
                for result in results:
                    if langEx.search(result["title"]) is None:
                        engResults.append(result)
                if engResults != []:
                    if len(engResults) == 1:
                        await wiki_page_embed(baseURL, bufferMsg, client, engResults[0])
                    else:
                        em = discord.Embed(title="Factorio Wiki",
                                        url=f"https://{baseURL}/index.php?search={searchterm}".replace(' ', '_'),
                                        color=discord.Colour.gold())
                        for result in engResults:
                            url = f"https://{baseURL}/{result['title'].replace(' ', '_')}"
                            em.add_field(name = result["title"], value = f"[Read More]({url})")
                        await bufferMsg.edit(embed=em)

                else:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find English results for \"{searchterm.title()}\" in wiki.",
                                       color=discord.Colour.red())
                    await bufferMsg.edit(embed=em)

async def wiki_page_embed(baseURL, bufferMsg, client, result):
    title = result["title"]
    url = f"https://{baseURL}/" + title.replace(" ", "_")
    paragraphs = str.split(await get_wiki_page_safe(client, WIKI_API_URL, title), "\n")
    try: intropar = [par for par in paragraphs if par != '' and par[0] != "{" and par[0] != "<"][0]
    except IndexError: intropar = paragraphs[1]
    formatted = linkEx.sub(
                    lambda m: f"[{m[2] or m[1]}](https://{baseURL}/{m[1].replace(' ', '_')})",
                    intropar)
    formatted = formatted.replace("'", "")
    em = discord.Embed(title=title,
                    url=url,
                    description=formatted,
                    color=discord.Colour.green())
    if "Infobox" in paragraphs[0]:
        image_url = f"https://{baseURL}/images/{title.replace(' ', '_')}.png"
        em.set_thumbnail(url=image_url)
    await bufferMsg.edit(embed=em)


class FactorioCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Factorio Commands"

    @commands.hybrid_command(aliases=["linkmod"])
    async def mod(self, ctx: commands.Context, *, modname: str = None):
        """
        Search for a mod in [the Factorio mod portal](https://mods.factorio.com).
        """
        #Error: no mod name provided
        if not modname:
            em = discord.Embed(title="Error",
                               description="To use the command, you need to enter a mod name to search.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)
            return
        
        #Create and send search in progress embed
        em = discord.Embed(title=f"Searching for \"{modname.title()}\" in mods.factorio.com...",
                            description="This may take a bit.",
                            colour=discord.Colour.gold())
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():

            #Get mod search results page
            response = await get_soup(f"https://mods.factorio.com/?version=1.1&search_order=updated&query={modname.title()}")

            #Error: bad response
            if response[0] != 200:
                em = discord.Embed(title="Error",
                                    description="Couldn't reach mods.factorio.com.",
                                    colour=discord.Colour.red())
                await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
                return
        
            soup = response[1]

            #Error: no results
            if " 0 " in soup.find("div", class_="grey").string:
                em = discord.Embed(title="Error",
                                    description=f"Could not find \"{modname.title()}\" in mod portal.",
                                    colour=discord.Colour.red())
                await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
                return

            #Multiple results
            if len(soup.find_all("div", class_="flex-column")) > 1:
                em = discord.Embed(title=f"Search results for \"{modname}\"",
                                    colour=discord.Colour.gold())
                i = 0
                for result in soup.find_all("div", class_="flex-column"):
                    if i <= 4:
                        title = result.find("h2", class_="mb0").find("a")
                        if title.string.title() == modname.title():
                            em = mod_embed(result)
                            break
                        author = result.find("a", class_="orange").string
                        summary = markdownEx.sub(r"\\\1", result.find("p", class_="pre-line").string)
                        em.add_field(name=f"{title.string} (by {author})",
                                        value=f"{summary} [*Read More*](https://mods.factorio.com/mods{title['href']})")
                        i += 1
            #Single result
            else:
                em = mod_embed(soup.find("div", class_="flex-column"))

            await bufferMsg.edit(embed=em)

    @commands.hybrid_command()
    async def wiki(self, ctx: commands.Context, *, searchterm: str = None):
        """
        Searches for a term in the [official Factorio wiki](https://wiki.factorio.com/).
        """
        await process_wiki(ctx, searchterm)

    @commands.hybrid_command()
    async def fff(self, ctx: commands.Context, number: str = None):
        """
        Links an fff with the number provided.
        """
        bufferMsg = None
        if number is not None:
            try:
                number = int(number)
                em = await embed_fff(number)
            except ValueError:
                em = discord.Embed(title="Error",
                                   description="To use the command, you need to input a number.",
                                   colour=discord.Colour.red())
        else:
            em = discord.Embed(title=f"Searching for latest FFF...",
                               description="This may take a bit.",
                               colour=discord.Colour.gold())
            bufferMsg = await ctx.send(embed=em)
            async with ctx.channel.typing():
                async with aiohttp.ClientSession() as client:
                    async with client.get("https://www.factorio.com/blog/rss") as resp:
                        status = resp.status
                        r = await resp.text()
                if status == 200:
                    rss = feedparser.parse(r)
                    i = 0
                    entry = rss.entries[i]
                    while "friday facts" not in entry.title.lower():
                        i += 1
                        entry = rss.entries[i]
                    em = await embed_fff(fffEx.search(entry.title).group(1))
        if not bufferMsg:
            await ctx.send(embed=em)
        else:
            await bufferMsg.edit(embed=em)


async def setup(bot):
    await bot.add_cog(FactorioCog(bot))
