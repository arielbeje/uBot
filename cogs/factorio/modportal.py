from ago import human
import aiohttp
import datetime
import json
import re

import discord
from discord.ext import commands


def mod_embed(r, bot, modlink):
    taglist = []
    em = discord.Embed(title=r["title"],
                       url=f"https://mods.factorio.com/mods/{r['owner']}/{modlink.replace(' ', '%20')}",
                       description=r["summary"],
                       colour=0x19B300)
    if r["media_files"]:
        em.set_thumbnail(url=r["media_files"][0]["urls"]["thumb"])
    em.add_field(name="Owner", value=r["owner"], inline=True)
    for tag in r["tags"]:
        taglist.append(tag["title"])
    em.add_field(name="Tags", value=', '.join(taglist), inline=True)
    em.add_field(name="Version", value=r["releases"][0]["version"], inline=True)
    em.add_field(name="Game Version", value=r["releases"][0]["game_version"], inline=True)
    em.add_field(name="License", value=f"[{r['license_name']}]({r['license_url']})", inline=True)
    em.add_field(name="Downloads", value=str(r["downloads_count"]), inline=True)
    for item in ["created_at", "updated_at"]:
        r[item] = re.sub(r"(?P<before>[+-]\d{2})(:)(?P<after>\d{2})", r"\g<before>\g<after>", r[item])
        r[item] = datetime.datetime.strptime(r[item], "%Y-%m-%d %H:%M:%S.%f%z")
        r[item] = human(r[item], precision=1)
    em.add_field(name="Released", value=r["created_at"], inline=True)
    em.add_field(name="Updated", value=r["updated_at"], inline=True)
    em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
    return em


class ModPortal():
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Factorio Mod Portal"

    @commands.command(name="linkmod", aliases=["mod"])
    async def linkmod(self, ctx, *, modname):
        """
        Search for a mod in [mods.factorio.com](https://mods.factorio.com).
        """
        em = discord.Embed(title=f"Searching for \"{modname.title()}\" in mods.factorio.com...",
                           description="This may take a bit.",
                           colour=0xDFDE6E)
        em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        bufferMsg = await ctx.send(embed=em)
        async with ctx.channel.typing():
            for modlink in [modname, modname.replace(' ', '%20'), modname.replace(' ', '_'), modname.replace(' ', '-')]:
                modlink = modlink.title()
                async with aiohttp.ClientSession().get(f"https://mods.factorio.com/api/mods/{modlink}") as response:
                    r = await response.read()
                r = json.loads(r)
                try:
                    r["detail"]
                    pass
                except KeyError:
                    break
            try:
                r["detail"]
                async with aiohttp.ClientSession().get(f"https://mods.factorio.com/api/mods?q={modname.title()}&order=updated&page_size=4") as response:
                    r = await response.read()
                r = json.loads(r)
                if len(r["results"]) > 1:
                    em = discord.Embed(title=f"Search results for \"{modname}\"",
                                       colour=0xDFDE6E)
                    for result in r["results"]:
                        em.add_field(name=result["title"], inline=False, value=f"{result['summary']} [_Read More_](https://mods.factorio.com/mods/{result['owner']}/{result['name']})")
                elif len(r["results"]) == 1:
                    async with aiohttp.ClientSession().get(f"https://mods.factorio.com/api/mods/{r['results'][0]['name']}") as response:
                        r2 = await response.read()
                    r2 = json.loads(r2)
                    em = mod_embed(r2, self.bot, f"https://mods.factorio.com/api/{r['results'][0]['name']}")
                else:
                    em = discord.Embed(title="Error",
                                       description=f"Could not find \"{modname.title()}\" in mod portal.",
                                       colour=0xDC143C)
                await bufferMsg.edit(embed=em)
                return
            except KeyError:
                await bufferMsg.edit(embed=mod_embed(r, self.bot, modlink))


def setup(bot):
    bot.add_cog(modPortal(bot))
