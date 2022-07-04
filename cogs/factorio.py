import aiohttp
import bs4
import feedparser
import html
import re
import tomd

import discord
from discord.ext import commands

from typing import List, Tuple, Union, Any

BASE_API_URL = "https://lua-api.factorio.com/latest/"

headerEx = re.compile(r"((^<br/>$)|(This (article|page)))")
referEx = re.compile(r".*? may refer to\:")
linkEx = re.compile(r"\((\/\S*)\)")
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

async def get_json(url: str) -> Tuple[int, Any]:  # TODO not sure what the type of the JSON should be
    """
    Returns a list with the response code (as int) and a JSON object of the URL
    """
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            status = resp.status
            r = await resp.json()
    return (status, r)


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


def get_wiki_description(soup: bs4.BeautifulSoup) -> str:
    """
    Returns the first paragraph of a wiki page BeautifulSoup
    """
    if soup.select(".mw-parser-output > p"):
        pNum = 0
        if headerEx.search(str(soup.select(".mw-body-content > #mw-content-text > .mw-parser-output > p")[0])):
            pNum = 1
        return html.unescape(tomd.convert(str(soup.select(".mw-body-content > #mw-content-text > .mw-parser-output > p")[pNum]))).strip().replace("<br/>", "\n")
    return ""


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


async def wiki_embed(url: str) -> discord.Embed:
    """
    Returns a discord.Embed object from a wiki URL
    """
    soup = (await get_soup(url))[1]
    description = get_wiki_description(soup)
    baseURL = "wiki.factorio.com" if not url.startswith('stable.') else "stable.wiki.factorio.com"
    templateURL = r"(https://stable.wiki.factorio.com\1)" if url.startswith('stable.') else r"(https://wiki.factorio.com\1)"
    if "may refer to:" in description:
        title = soup.find("h1", id="firstHeading").get_text()
        em = discord.Embed(title="Multiple pages share the title or description of " +
                                 "\"{}\"".format(title),
                           url = f"https://{baseURL}/{title}",
                           colour=discord.Colour.red())
        for item in soup.select(".mw-parser-output > ul")[0].find_all("li"):
            item = item.find("a")
            itemLink = item["href"] if not item["href"].endswith(")") else item["href"].replace(")", "\\)")
            em.add_field(name=item["title"], value=f"[Read More](https://{baseURL}{itemLink})", inline=True)
    else:
        em = discord.Embed(title=soup.find("h1", id="firstHeading").get_text(),
                           description=linkEx.sub(templateURL, description),
                           url=url,
                           colour=discord.Colour.dark_green())
        if soup.find("div", class_="factorio-icon"):
            em.set_thumbnail(url=f"https://{baseURL}{soup.find('div', class_='factorio-icon').find('img')['src']}")
    return em


async def process_wiki(ctx: commands.Context, searchterm: str, stable: bool = False):
    """
    Sends a message according to parameters given
    """
    if not searchterm:
        em = discord.Embed(title="Error",
                           description="To use this command, you have to enter a term to search for.",
                           colour=discord.Colour.red())
        await ctx.send(embed=em)
        return
    baseURL = "wiki.factorio.com" if not stable else "stable.wiki.factorio.com"
    em = discord.Embed(title=f"Searching for \"{searchterm.title()}\" in {baseURL}...",
                       description="This shouldn't take long.",
                       colour=discord.Colour.gold())
    bufferMsg = await ctx.send(embed=em)
    async with ctx.channel.typing():
        url = f"https://{baseURL}/index.php?search={searchterm.replace(' ', '%20')}"
        soup = (await get_soup(url))[1]
        if soup.find("p", class_="mw-search-nonefound"):
            em = discord.Embed(title="Error",
                               description=f"Could not find \"{searchterm.title()}\" in {'' if not stable else 'stable '}wiki.",
                               colour=discord.Colour.red())
            await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
        else:
            if soup.find_all("ul", class_="mw-search-results"):
                engResults = []
                em = discord.Embed(title=f"Factorio {'' if not stable else 'Stable '}Wiki",
                                   url=url,
                                   colour=discord.Colour.gold())
                for item in soup.find_all("ul", class_="mw-search-results")[0].find_all("li"):
                    item = item.find_next("div", class_="mw-search-result-heading").find("a")
                    if langEx.search(item["title"]) is None:
                        engResults.append(item)
                if len(engResults) == 1:
                    item = engResults[0]
                    await bufferMsg.edit(embed=await wiki_embed(f"https://{baseURL}{item['href']}"))
                elif len(engResults) > 1:
                    for item in engResults:
                        em.add_field(name=item["title"], value=f"[Read More](https://{baseURL}{item['href']})", inline=True)
                    await bufferMsg.edit(embed=em)
                else:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find English results for \"{searchterm.title()}\" in {'' if not stable else 'stable '}wiki.",
                                       colour=discord.Colour.red())
                    await bufferMsg.edit(embed=em) if ctx.prefix is not None else await bufferMsg.delete()
            else:
                await bufferMsg.edit(embed=await wiki_embed(url))


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


async def find_api_member(json: Any, query: str, bufferMsg: Any) -> Any:  # TODO types?
    for member in json:
        if member["name"] == query:
            return member
    # If it gets to here, no matching member was found
    em = discord.Embed(title="Error", description=f"Could not find {query} in API", colour=discord.Colour.red())
    await bufferMsg.edit(embed=em)
    return None


async def find_class_member(allClasses, childClass, memberName, bufferMsg) -> Tuple[Any, str]:  # TODO types?
    relevantClasses = [childClass]
    if "base_classes" in childClass:  # make sure parent classes are searched too
        for baseClass in childClass["base_classes"]:
            parentClass = await find_api_member(allClasses, baseClass, bufferMsg)  # always finds something
            relevantClasses.append(parentClass)
    for class_ in relevantClasses:
        for category in {"methods", "attributes"}:  # operators not supported
            member = await find_api_member(class_[category], memberName, bufferMsg)
            if member is not None:
                return member, category


async def guarded_embed(title: str, description: str, url: str, colour: Any, bufferMsg: Any) -> None:  # TODO types?
    title = "Result too long to embed." if len(description) > 2048 else title
    description = "" if len(description) > 2048 else description
    em = discord.Embed(title=title, description=description, url=url, colour=colour)
    await bufferMsg.edit(embed=em)


def render_api_type(type_: Any) -> str:  # TODO types?
    if type(type_) == str:
        return type_
    else:
        complexType = type_["complex_type"]
        if complexType == "variant":
            inner_types = [render_api_type(inner) for inner in type_["options"]]
            return " or ".join(inner_types)
        elif complexType == "array":
            return f"array[{render_api_type(type_['value'])}]"
        elif complexType in {'dictionary', 'LuaCustomTable'}:
            key, value = render_api_type(type_["key"]), render_api_type(type_["value"])
            return f"{complexType}[{key} → {value}]"
        elif complexType == "table":
            return "table"
        elif complexType == "function":
            parameters = [render_api_type(param) for param in type_["parameters"]]
            return f"function({', '.join(parameters)})"
        elif complexType == "LuaLazyLoadedValue":
            return str(type_["value"])


def render_class_member(member: Any, category: str) -> str:  # TODO types?
    if category == "methods":  # doesn't take variant and variadic parameters into account
        params = ", ".join([param["name"] for param in member["parameters"]])
        parameters = f"{{{params}}}" if member["takes_table"] else f"({params})"
        rvalues = [render_api_type(rvalue["type"]) for rvalue in member["return_values"]]
        return_values = f" → {', '.join(rvalues)}" if len(rvalues) > 0 else ""
        return f"\n**{member['name']}**{parameters}{return_values}"
    elif category == "attributes":
        type = render_api_type(member["type"])
        access = ""  # at least one of read or write will always be available
        if member["read"]: access += "R"
        if member["write"]: access += "W"
        return f"\n**{member['name']}** :: {type} *[{access}]*"
    else:
        return ""  # no support for operators


async def render_define(define: Any, subtypes: List[str], bufferMsg: Any) -> Union[str, None]:  # TODO types?
    if len(subtypes) != 0:
        subtype = await find_api_member(define["subkeys"], subtypes[0], bufferMsg)
        if subtype is not None:  # go deeper if a subtype is requested
            return await render_define(subtype, subtypes[1:], bufferMsg)
    else:
        description = f"{define['description']}\n" if define['description'] != "" else ""
        if "subkeys" in define:
            for subkey in define["subkeys"]:
                description += f"\n**{subkey['name']}:**"
                description += await render_define(subkey, [], bufferMsg) or ""
                # TODO should be indented for visual clarity, but it seems to auto-strip leading whitespace
        if "values" in define:
            for value in define["values"]:
                desc = f": {value['description']}" if value['description'] else ""
                description += f"\n{value['name']}{desc}"
        return description + "\n"


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
    async def stablewiki(self, ctx: commands.Context, *, searchterm: str = None):
        """
        Searches for a term in the [official Stable Factorio wiki](https://stable.wiki.factorio.com/).
        """
        await process_wiki(ctx, searchterm, stable=True)

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
        if query in ["classes", "events", "concepts", "defines"]:
            pagename = query.capitalize() if query in ["classes", "concepts"] else query
            em = discord.Embed(title=query.capitalize(),
                               url=f"{BASE_API_URL}{pagename}.html",
                               colour=discord.Colour.gold())
            await bufferMsg.edit(embed=em)
            return
        processResult = process_query(query)
        response = await get_json(BASE_API_URL + "runtime-api.json")
        if response[0] != 200:
            em = discord.Embed(title="Error",
                               description="Could not reach lua-api.factorio.com.",
                               colour=discord.Colour.red())
            await bufferMsg.edit(embed=em)
            return
        json = response[1]
        if processResult[0] == "class":  # could also be a concept
            class_ = await find_api_member(json["classes"], query, bufferMsg)
            if class_ is not None:
                description = class_['description'] + "\n"
                for category in ["methods", "attributes"]:
                    for member in class_[category]:
                        member_desc = f": {member['description'].split('.')[0]}." if member["description"] else ""
                        description += render_class_member(member, category) + member_desc
                url = f"{BASE_API_URL}{query}.html"
                await guarded_embed(query, description, url, discord.Colour.gold(), bufferMsg)
            else:  # if it's not a class, check if it's a concept
                concept = await find_api_member(json["concepts"], query, bufferMsg)
                if concept is not None:
                    # With much more effort, one could add more detail to concepts
                    url = f"{BASE_API_URL}Concepts.html#{query}"
                    await guarded_embed(query, concept["description"], url, discord.Colour.gold(), bufferMsg)
        elif processResult[0] == "class+property":
            className = processResult[1][0]
            class_ = await find_api_member(json["classes"], className, bufferMsg)
            if class_ is not None:
                memberName = processResult[1][1]
                member, category = await find_class_member(json["classes"], class_, memberName, bufferMsg)
                if member is not None:
                    description = render_class_member(member, category)
                    description += f"\n\n{member['description']}\n" if member['description'] != "" else ""
                    if category == "methods":
                        for parameter in member["parameters"]:
                            type = render_api_type(parameter["type"])
                            optional = " (optional)" if parameter["optional"] else ""
                            paramDesc = f": {parameter['description']}" if parameter["description"] else ""
                            description += f"\n**{parameter['name']}** :: {type}{optional}{paramDesc}"
                    url = f"{BASE_API_URL}{className}.html#{className}.{memberName}"
                    await guarded_embed(query, description, url, discord.Colour.gold(), bufferMsg)
        elif processResult[0] == "define":
            splitName = processResult[1]
            define = await find_api_member(json["defines"], splitName[0], bufferMsg)
            if define is not None:
                description = await render_define(define, list(splitName[1:]), bufferMsg)
                if description is not None:
                    fullName = f"defines.{'.'.join(splitName)}"
                    await guarded_embed(fullName, description, f"{BASE_API_URL}defines.html#{fullName}",
                      discord.Colour.gold(), bufferMsg)
        else:  # event
            event = await find_api_member(json["events"], query, bufferMsg)
            if event is not None:
                em = discord.Embed(title=query,
                                   description=event["description"],
                                   url=f"{BASE_API_URL}events.html#{query}",
                                   colour=discord.Colour.gold())
                contents = []
                for dataset in event["data"]:
                    type = render_api_type(dataset["type"])
                    optional = " (optional)" if dataset["optional"] else ""
                    dataDesc = f": {dataset['description']}" if dataset["description"] else ""
                    contents.append(f"**{dataset['name']}** :: {type}{optional}{dataDesc}")
                if len(contents) > 0:
                    em.add_field(name="Contains", value="\n".join(contents), inline=False)
                await bufferMsg.edit(embed=em)


def setup(bot):
    bot.add_cog(FactorioCog(bot))
