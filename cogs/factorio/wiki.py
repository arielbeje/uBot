import bs4
import requests

import discord
from discord.ext import commands


class wiki():
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Factorio Wiki"

    @commands.command(name="wiki")
    async def wikiCommand(self, ctx, *, searchterm):
        """
        Search for a term in the [official Factorio wiki](https://wiki.factorio.com/).
        """
        r = requests.get(f"https://wiki.factorio.com/index.php?search={searchterm.title().replace(' ', '%20')}")
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        if soup.find('p', class_='mw-search-nonefound'):
            em = discord.Embed(title="Error",
                               description=f"Could not find \"{searchterm.title()}\" in wiki.",
                               colour=0xDC143C)
            em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
            await ctx.send(embed=em)
            return
        if soup.find_all('ul', class_="mw-search-results"):
            em = discord.Embed(title="Factorio Wiki",
                               url=r.url,
                               colour=0xDFDE6E)
            for item in soup.find_all('ul', class_="mw-search-results")[0].find_all("li"):
                item = item.find_next('div', class_="mw-search-result-heading").find('a')
                em.add_field(title=item['title'], value=f"[Read More](https://wiki.factorio.com{item['href']})", inline=True)
            em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title=soup.find("h1", id='firstHeading').get_text(),
                               description=soup.select("#mw-content-text > p")[0].get_text(),
                               url=r.url,
                               colour=0x19B300)
            if soup.find('div', class_="factorio-icon"):
                print(f"https://wiki.factorio.com{soup.find('div', class_='factorio-icon').find('img')['src']}")
                em.set_thumbnail(url=f"https://wiki.factorio.com{soup.find('div', class_='factorio-icon').find('img')['src']}")
            em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(wiki(bot))
