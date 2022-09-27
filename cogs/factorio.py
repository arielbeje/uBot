import aiohttp
import bs4
import feedparser
import html
import re
import tomd

import discord
from discord.ext import commands

from typing import List, Tuple, Union

BASE_API_URL = "https://lua-api.factorio.com/latest/"
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
    downloads = infoCard.find("div", title="Downloads").contents[2].strip()
    createdAt = infoCard.find("div", title="Last updated").contents[2].strip()
    fields.extend([{"name": "Category", "value": "None" if len(taglist) == 0 else ", ".join(taglist)},
                   {"name": "Game Version(s)", "value": gameVersions},
                   {"name": "Downloads", "value": downloads},
                   {"name": "Updated", "value": createdAt}])
    for field in fields:
        em.add_field(**field, inline=True)
    return em


# def get_wiki_description(soup: bs4.BeautifulSoup) -> str:
#     """
#     Returns the first paragraph of a wiki page BeautifulSoup
#     """
#     if soup.select(".mw-parser-output > p"):
#         pNum = 0
#         if headerEx.search(str(soup.select(".mw-body-content > #mw-content-text > .mw-parser-output > p")[0])):
#             pNum = 1
#         return html.unescape(tomd.convert(str(soup.select(".mw-body-content > #mw-content-text > .mw-parser-output > p")[pNum]))).strip().replace("<br/>", "\n")
#     return ""


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

async def process_wiki(ctx: commands.Context, searchterm: str, stable: bool = False):
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
                title = results[0]["title"]
                url = f"https://{baseURL}/" + title.replace(" ", "_")
                paragraphs = str.split(await get_wiki_page_safe(client, WIKI_API_URL, title), "\n")
                intropar = [par for par in paragraphs if "'''" in par][0]
                formatted = linkEx.sub(
                    lambda m: f"[{m[2] or m[1]}](https://{baseURL})/{m[1]})",
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
            else: 
                engResults = []
                for result in results:
                    if langEx.search(result["title"]) is None:
                        engResults.append(result)
                if engResults != []:
                    em = discord.Embed(title="Factorio Wiki",
                                       url=f"https://{baseURL}/index.php?search={searchterm}",
                                       color=discord.Colour.gold())
                    for result in engResults:
                        url = f"https://{baseURL}/{result['title'].replace(' ', '_')}"
                        em.add_field(name = result["title"], value = f"[Read More]({url})")
                    await bufferMsg.edit(embed=em)

                else:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find English results for \"{searchterm.title()}\" in wiki.",
                                       color=discord.Colour.red())

def is_camel_case(query: str) -> bool:
    return query != query.lower() and query != query.upper() and "_" not in query


def process_query(query: str) -> Union[Tuple[str, List[str]], Tuple[str, str]]:
    if "::" in query:
        splitQuery = query.split("::")
        if query.startswith("Defines"):
            return ("define", splitQuery[1].split("."))
        else:
            return ("class+property", splitQuery)
    elif query.count(".") == 1 and is_camel_case(query.split(".")[0]):
        return ("class+property", query.split("."))
    elif is_camel_case(query):
        return ("class", query)
    elif query.startswith("defines."):
        return ("define", query.split(".")[1:])
    else:
        return ("event", query)


def define_tr_to_str(tr: bs4.element.Tag) -> str:
    for a in tr.find_all("a"):
        a["href"] = BASE_API_URL + a["href"]
    data = (tr.find("td", class_="header").string, tr.find("td", class_="description"))
    contents = data[1].contents
    if len(contents) > 0:
        if len(contents) > 1 and "\n" not in contents[0]:
            description = tomd.convert(f"<p>{''.join([str(item) for item in contents[:-1]])}</p>").strip()
        else:
            description = contents[0].split('\n')[0].strip()
        return f"`{data[0]}` - {description}"
    else:
        return f"`{data[0]}`"


def define_table_to_strs(table: bs4.element.Tag) -> List[str]:
    trs = table.find_all("tr", class_="element")
    return [define_tr_to_str(tr) for tr in trs]


def class_tr_to_str(tr: bs4.element.Tag) -> str:
    for a in tr.find_all("a"):
        a["href"] = BASE_API_URL + a["href"]
    data = (tr.find("td", class_="header"), tr.find("td", class_="description"))
    nameSpan = data[0].find("span", class_="element-name")
    if data[0].find("span", class_="attribute-type") is not None:
        accessType = "param"
        type_ = data[0].find("span", class_="param-type").text.strip()
    else:
        accessType = "func"
    if accessType == "param":
        attributeMode = data[0].find("span", class_="attribute-mode").text
        header = f"`{nameSpan.text} :: {type_}` {attributeMode}"
    else:
        header = f"`{nameSpan.text}`"

    contents = [item for item in data[1].contents if item != " "]
    if len(contents) > 0:
        if len(contents) > 1 and "\n" not in contents[0]:
            description = tomd.convert(f"<p>{''.join([str(item) for item in contents[:-1]])}</p>").strip()
        else:
            description = contents[0].strip()
        return f"{header} - {description}"
    else:
        return header


def class_table_to_strs(table: bs4.element.Tag) -> List[str]:
    return [class_tr_to_str(tr) for tr in table.find_all("tr")]


def get_class_description(soup: bs4.BeautifulSoup, class_: str) -> str:
    a = soup.select(f"tr > td.header > a[href=\"{class_}.html\"]")
    if len(a) == 1:
        descriptionTag = a[0].parent.parent.find("td", class_="description")
        descriptionRaw = "".join([str(content) for content in descriptionTag.contents])
        return tomd.convert(f"<p>{descriptionRaw}</p>").strip()
    return None


def get_event_description(div: bs4.element.Tag) -> str:
    for a in div.find_all("a"):
        a["href"] = BASE_API_URL + a["href"]
    data = (div.select("div.element-content > p"), div.find("div", class_="detail-content"))
    paragraphs = []
    for p in data[0]:
        contents = p.contents
        if not (len(contents) == 1 and len(contents[0].strip()) == 0):
            paragraphs.append(html.unescape(tomd.convert(str(p))))
    return "\n".join([p.strip().replace("\n", "") for p in paragraphs])


def get_event_contents(div: bs4.element.Tag) -> List[str]:
    contains = div.select("div.detail-content > div")
    props = []
    for prop in contains:
        text = prop.text.replace("  ", " ")
        searchResult = propEx.search(text).groups()
        if searchResult[2] is not None:
            props.append(f"`{searchResult[0]}` - {searchResult[2]}")
        else:
            props.append(f"`{searchResult[0]}`")
    return props


class FactorioCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Factorio Commands"

    @commands.command(aliases=["mod"])
    async def linkmod(self, ctx: commands.Context, *, modname: str = None):
        """
        Search for a mod in [the Factorio mod portal](https://mods.factorio.com).
        """
        if not modname:
            em = discord.Embed(title="Error",
                               description="To use the command, you need to enter a mod name to search.",
                               colour=discord.Colour.red())
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title=f"Searching for \"{modname.title()}\" in mods.factorio.com...",
                               description="This may take a bit.",
                               colour=discord.Colour.gold())
            bufferMsg = await ctx.send(embed=em)
            async with ctx.channel.typing():
                response = await get_soup(f"https://mods.factorio.com/query/{modname.title()}/downloaded/1?version=any")
                if response[0] == 200:
                    soup = response[1]
                    if " 0 " in soup.find("div", class_="grey").string:
                        em = discord.Embed(title="Error",
                                           description=f"Could not find \"{modname.title()}\" in mod portal.",
                                           colour=discord.Colour.red())
                        await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()

                    elif soup.find_all("div", class_="flex-column"):
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

                        else:
                            em = mod_embed(soup.find("div", class_="flex-column"))

                        await bufferMsg.edit(embed=em)
                else:
                    em = discord.Embed(title="Error",
                                       description="Couldn't reach mods.factorio.com.",
                                       colour=discord.Colour.red())
                    await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()

    @commands.command()
    async def wiki(self, ctx: commands.Context, *, searchterm: str = None):
        """
        Searches for a term in the [official Factorio wiki](https://wiki.factorio.com/).
        """
        await process_wiki(ctx, searchterm)

    @commands.command()
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

    @commands.command(name="0.17", aliases=[".17"])
    async def dot17(self, ctx: commands.Context):
        """
        Returns info about the release date of 0.17.
        """
        await ctx.invoke(self.bot.get_command("faq"), query="0.17")

    @commands.command()
    async def api(self, ctx: commands.Context, *, query: str = None):
        """
        Searches the [API documentation](https://lua-api.factorio.com/latest/) for the given query.
        If no query is given, gives a link to the documentation.
        """
        if query is None:
            em = discord.Embed(title="Latest API documentation",
                               url=BASE_API_URL,
                               colour=discord.Colour.gold())
            await ctx.send(embed=em)
            return
        em = discord.Embed(title="Retrieving latest API documentation",
                           description="This shouldn't take long.",
                           colour=discord.Colour.gold())
        bufferMsg = await ctx.send(embed=em)
        processResult = process_query(query)
        if processResult[0] == "define":
            response = await get_soup(BASE_API_URL + "defines.html")
            if response[0] == 200:
                fullName = f"defines.{'.'.join(processResult[1])}"
                tag = response[1].find(id=fullName)
                if tag is None:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find `{query}` in API",
                                       colour=discord.Colour.red())
                    await bufferMsg.edit(embed=em)
                    return
                tagType = str(tag).split(" ")[0][1:]  # For example, <div ....
                if tagType == "div":
                    contents = tag.find("div", class_="element-content").find("p").contents
                    description = ""
                    if len(contents) > 0:
                        if len(contents) > 1 and "\n" not in contents[0]:
                            for a in tag.find_all("a"):
                                a["href"] = BASE_API_URL + a["href"]
                            description = tomd.convert(f"<p>{''.join([str(item) for item in contents])}</p>").strip() + "\n"
                        else:
                            description = contents[0].split('\n')[0].strip() + "\n"
                    tables = tag.find_all("table", class_="brief-members")
                    for table in tables:
                        data = define_table_to_strs(table)
                        for tr in data:
                            description += tr + "\n"
                else:  # Since the tag can be only a div or a tr
                    description = define_tr_to_str(tag)
                if len(description) > 2048:
                    em = discord.Embed(title="Result too long for embedding",
                                       colour=discord.Colour.gold())
                else:
                    em = discord.Embed(title=fullName,
                                       description=description,
                                       colour=discord.Colour.gold())
                em.url = f"{BASE_API_URL}defines.html#{fullName}"
            else:
                em = discord.Embed(title="Error",
                                   description="Could not reach lua-api.factorio.com.",
                                   colour=discord.Colour.red())
        elif processResult[0] == "class":
            response = await get_soup(BASE_API_URL + "Classes.html")
            if response[0] == 200:
                tag = response[1].find("div", id=f"{processResult[1]}.brief")
                if tag is None:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find `{query}` in API",
                                       colour=discord.Colour.red())
                    await bufferMsg.edit(embed=em)
                    return
                table = tag.find("table", class_="brief-members")
                data = class_table_to_strs(table)
                description = get_class_description(response[1], processResult[1])
                if description is not None:
                    description += "\n"
                else:
                    description = ""
                description += "\n".join(data)
                if len(description) > 2048:
                    em = discord.Embed(title="Result too long for embedding",
                                       colour=discord.Colour.gold())
                else:
                    em = discord.Embed(title=query,
                                       description=description,
                                       colour=discord.Colour.gold())
                em.url = f"{BASE_API_URL}{query}.html"
            else:
                em = discord.Embed(title="Error",
                                   description="Could not reach lua-api.factorio.com.",
                                   colour=discord.Colour.red())
        elif processResult[0] == "class+property":
            response = await get_soup(BASE_API_URL + "Classes.html")
            if response[0] == 200:
                class_ = processResult[1][0]
                property_ = processResult[1][1]
                tag = response[1].find("a", href=f"{class_}.html#{class_}.{property_}")
                if tag is None:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find `{query}` in API",
                                       colour=discord.Colour.red())
                    await bufferMsg.edit(embed=em)
                    return
                tr = tag.parent.parent.parent
                description = class_tr_to_str(tr)
                em = discord.Embed(title=query,
                                   description=description,
                                   colour=discord.Colour.gold())
                em.url = f"{BASE_API_URL}{class_}.html#{class_}.{property_}"
            else:
                em = discord.Embed(title="Error",
                                   description="Could not reach lua-api.factorio.com.",
                                   colour=discord.Colour.red())
        else:  # event
            response = await get_soup(BASE_API_URL + "events.html")
            if response[0] == 200:
                tag = response[1].find("div", id=query)
                if tag is None:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find {query} in API",
                                       colour=discord.Colour.red())
                    await bufferMsg.edit(embed=em)
                    return
                em = discord.Embed(title=query,
                                   description=get_event_description(tag),
                                   url=f"{BASE_API_URL}events.html#{query}",
                                   colour=discord.Colour.gold())
                contents = get_event_contents(tag)
                if len(contents) > 0:
                    em.add_field(name="Contains", value="\n".join(contents), inline=False)
        await bufferMsg.edit(embed=em)


def setup(bot):
    bot.add_cog(FactorioCog(bot))
