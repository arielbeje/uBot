import aiohttp
import json
import os
import random

import discord
from discord.ext import commands

with open('data/dogdb.json', 'r') as dogdatabase:
    dogdb = json.load(dogdatabase)

with open('data/heresydb.json', 'r') as heresydatabase:
    heresydb = json.load(heresydatabase)


class FunCog():
    def __init__(self, bot):
        self.bot = bot
        type(self).__name__ = "Fun Commands"

    @commands.command(name="dog")
    async def random_dog(self, ctx):
        """
        Gives a random picture of a dog from [random.dog](https://random.dog).
        """
        dogpic = f"https://random.dog/{random.choice(dogdb)}"
        em = discord.Embed(title="Random Dog!",
                           colour=0x19B300)
        em.set_image(url=dogpic)
        em.set_footer(text=self.bot.user.name + " | Powered by random.dog", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="cat")
    async def random_cat(self, ctx):
        """
        Gives a random picture of a cat from [random.cat](http://random.cat).
        """
        async with aiohttp.ClientSession() as session:
            async with session.get("http://random.cat/meow") as r:
                if r.status == 200:
                    js = await r.json()
                    em = discord.Embed(title="Random Cat!",
                                       colour=0x19B300)
                    em.set_image(url=js['file'])
                    em.set_footer(text=f"{self.bot.user.name} | Powered by random.cat", icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
                    await ctx.send(embed=em)
                else:
                    em = discord.Embed(title="Error",
                                       description="Couldn't reach random.cat.\nTry again later.",
                                       colour=0xDC143C)
                    await ctx.send(embed=em)

    @commands.command(name="0.17")
    async def releaseDate(self, ctx):
        """
        Returns the release date of 0.17.
        """
        rndInt = random.randint(0, 20)
        if rndInt == 1:
            await ctx.send("0.17 has officially been cancelled.")
        elif rndInt == 2:
            await ctx.send(f"0.17 will be out for release in just {random.randint(1, 59)} minutes!")
        elif rndInt == 3:
            await ctx.send("0.17 will be released whenever Half-Life 3 comes out.")
        else:
            await ctx.send(f"0.17 is planned for release in {random.randint(1, 700)} days.")

    @commands.command(name="heresy")
    async def heresy(self, ctx, user: discord.User=None):
        """
        Declares heresy.
        Can also declare heresy on a user.
        """
        em = discord.Embed(colour=0x19B300)
        if user:
            em.description = f"{ctx.author.mention} declares heresy on {user.mention}!"
        else:
            em.description = f"{ctx.author.mention} declares heresy!"
        em.set_image(url=random.choice(heresydb))
        # em.set_footer(text=self.bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=64")
        await ctx.send(embed=em)

    @commands.command(name="blush", aliases=["bully","cuddle","hug","kiss","lewd","pat","pout","slap","smug"])
    async def imageMacros(self, ctx):
        """
        Various image commands
        """
        # Get which command was used
        usedCmd = ctx.message.content[1:]
        embed = discord.Embed()
        if usedCmd == "blush":
            embed.set_image(url=random.choice(blush))
        elif usedCmd == "bully":
            embed.set_image(url=random.choice(bully))
        elif usedCmd == "cuddle":
            embed.set_image(url=random.choice(cuddle))
        elif usedCmd == "hug":
            embed.set_image(url=random.choice(hug))
        elif usedCmd == "kiss":
            embed.set_image(url=random.choice(kiss))
        elif usedCmd == "lewd":
            embed.set_image(url=random.choice(lewd))
        elif usedCmd == "pat":
            embed.set_image(url=random.choice(pat))
        elif usedCmd == "pout":
            embed.set_image(url=random.choice(pout))
        elif usedCmd == "slap":
            embed.set_image(url=random.choice(slap))
        else:
            embed.set_image(url=random.choice(smug))
        await ctx.send(embed=embed)

    @commands.command(name="images")
    async def images(self, ctx):
        """
        Returns valid commands it can respond with images to
        """
        await ctx.send('blush|bully|cuddle|hug|kiss|lewd|pat|pout|slap|smug')

def setup(bot):
    bot.add_cog(FunCog(bot))



#beware - ugliness below - blush|bully|cuddle|hug|kiss|lewd|pat|pout|slap|smug
blush = [
    "http://i.imgur.com/iZebACb.gifv",
    "http://i.imgur.com/WPMPu6g.gifv",
    "http://i.imgur.com/PDE3u0P.png",
    "http://i.imgur.com/VyjPlIT.jpg",
    "http://i.imgur.com/yS1Dskt.png",
    "http://i.imgur.com/XgFxyQr.jpg",
    "http://i.imgur.com/qxgsHs8.jpg",
    "http://i.imgur.com/QI1zBfv.png",
    "http://i.imgur.com/QISeNMf.jpg",
    "http://i.imgur.com/fcwdNMi.jpg",
    "http://i.imgur.com/tQbfHoY.gifv",
    "http://i.imgur.com/GDn0hEd.gifv",
    "http://i.imgur.com/gr5CKX4.jpg",
    "http://i.imgur.com/Czxzev8.gifv",
    "http://i.imgur.com/BvGMMVj.png",
    "http://i.imgur.com/mFSr7XK.gifv",
    "http://i.imgur.com/rUdtjgA.gifv",
    "http://i.imgur.com/uqMyqyQ.png",
    "http://i.imgur.com/2DrPoiN.gifv",
    "http://i.imgur.com/zYL6dOM.gifv",
    "http://i.imgur.com/g2UdwJX.png",
    "http://i.imgur.com/vIsAEX6.png",
    "http://i.imgur.com/QoV0IBS.jpg",
    "http://i.imgur.com/53sDZje.png",
    "http://i.imgur.com/XHtu8fG.png",
    "http://i.imgur.com/N2KpNzA.gifv",
    "http://i.imgur.com/17cdshl.jpg",
    "http://i.imgur.com/eDjmeVP.gifv",
    "http://i.imgur.com/YsE5ErA.png",
    "http://i.imgur.com/DG6c1Jn.gifv",
    "http://i.imgur.com/LLGMSAn.gifv",
    "http://i.imgur.com/NBCR5pq.jpg",
    "http://i.imgur.com/miDyLGv.gifv",
    "http://i.imgur.com/J1Z77Z7.jpg",
    "http://i.imgur.com/cFOHb11.gifv",
    "http://i.imgur.com/BlU3Vs9.png",
    "http://i.imgur.com/acboyV8.jpg",
    "http://i.imgur.com/mapnOZK.png",
    "http://i.imgur.com/yfgzkJO.jpg",
    "http://i.imgur.com/1elHrBm.gifv",
    "http://i.imgur.com/VFtBzAL.png",
    "http://i.imgur.com/Xk53MAf.gifv",
    "http://i.imgur.com/pqQ1JZF.gifv",
    "http://i.imgur.com/cgSaX3M.png",
    "http://i.imgur.com/1ET6g6H.gifv",
    "http://i.imgur.com/gOV6Yxl.gifv",
    "http://i.imgur.com/QpdQ6Iq.gifv",
    "http://i.imgur.com/whihYV9.jpg",
    "http://i.imgur.com/3xwXRWU.png",
    "http://i.imgur.com/SvlNzH1.png",
    "http://i.imgur.com/OiGLLRV.gifv",
    "http://i.imgur.com/QfOQ3Er.png",
    "http://i.imgur.com/LCQwAAT.jpg",
    "http://i.imgur.com/FPe0KkG.png",
    "http://i.imgur.com/FaqOEpf.png",
    "http://i.imgur.com/RS08YgC.gifv",
    "http://i.imgur.com/jO2DlBy.gifv",
    "http://i.imgur.com/aWszM8e.gifv",
    "http://i.imgur.com/ycpGlN6.gifv",
    "http://i.imgur.com/FdxpMBy.gifv",
    "http://i.imgur.com/UglqMTh.png",
    "http://i.imgur.com/yMpjHWN.gifv",
    "http://i.imgur.com/ZiSuh7N.gifv",
    "http://i.imgur.com/dtyljYC.png",
    "http://i.imgur.com/v3VPI0n.gifv",
    "http://i.imgur.com/ksq3Yhl.jpg",
    "http://i.imgur.com/iNUfse3.jpg",
    "http://i.imgur.com/cPLG0G1.jpg"
]

bully = [
    "http://i.imgur.com/0bC1YSa.jpg",
    "http://i.imgur.com/BFhmsEn.png",
    "http://i.imgur.com/DdXzqOR.jpg",
    "http://i.imgur.com/G0qofeE.jpg",
    "http://i.imgur.com/TqqlRzb.jpg",
    "http://i.imgur.com/cSCRvPz.jpg",
    "http://i.imgur.com/cTPHfT4.png",
    "http://i.imgur.com/ivK9rpQ.jpg",
    "http://i.imgur.com/lUUbLhz.jpg",
    "http://i.imgur.com/q5pBikF.png",
    "http://i.imgur.com/qCqHvqb.png",
    "http://i.imgur.com/jt9IBFB.jpg",
    "http://i.imgur.com/dP4SK65.png",
    "http://i.imgur.com/2lcL3am.png",
    "http://i.imgur.com/rI6BqAh.png",
    "http://i.imgur.com/bYu7x69.jpg",
    "http://i.imgur.com/9hlu3Gc.jpg",
    "http://i.imgur.com/JtG4qXj.png",
    "http://i.imgur.com/j0C9bIR.png",
    "http://i.imgur.com/i0CkyjM.png",
    "http://i.imgur.com/C86qrrx.jpg",
    "http://i.imgur.com/eace8Km.jpg",
    "http://i.imgur.com/PweLmuH.jpg",
    "http://i.imgur.com/9Y5Rbct.png",
    "http://i.imgur.com/i7Y5HqV.jpg",
    "http://i.imgur.com/3sVgC2A.png",
    "http://i.imgur.com/0nkO2Hs.png",
    "http://i.imgur.com/d6CXd7L.jpg",
    "http://i.imgur.com/kVI9Aoh.gifv.",
    "http://i.imgur.com/8fZ2b6Z.png",
    "http://i.imgur.com/4T9qDPg.png",
    "http://i.imgur.com/n0kje5b.png",
    "http://i.imgur.com/wbZMAsO.jpg",
    "http://i.imgur.com/TKz6Ym4.png",
    "http://i.imgur.com/oe5opVt.png",
    "http://i.imgur.com/D0jU7vf.png"
]

cuddle = [
    "http://i.imgur.com/1fiKFCG.jpg",
    "http://i.imgur.com/1qcxXKV.jpg",
    "http://i.imgur.com/1tKUEmx.png",
    "http://i.imgur.com/9a6nU5l.png",
    "http://i.imgur.com/Krtnfra.jpg",
    "http://i.imgur.com/LSVeOSa.png",
    "http://i.imgur.com/S1XEsvM.png",
    "http://i.imgur.com/TmeN5zD.jpg",
    "http://i.imgur.com/Tq6ccqC.png",
    "http://i.imgur.com/YOrzSKE.jpg",
    "http://i.imgur.com/eGOlr4Z.gifv",
    "http://i.imgur.com/jqNjYIB.jpg",
    "http://i.imgur.com/jxTOrRz.jpg",
    "http://i.imgur.com/lWyWUDL.png",
    "http://i.imgur.com/pOjSF7X.jpg",
    "http://i.imgur.com/qD4gbHJ.jp",
    "http://i.imgur.com/tKlalnR.jpg",
    "http://i.imgur.com/xHAUoPk.jpg",
    "http://i.imgur.com/xsP7F9r.jpg",
    "http://i.imgur.com/GAyuaB7.gif",
    "http://i.imgur.com/OUL6iCT.jpg",
    "http://i.imgur.com/bsWrnOq.mp4",
    "http://i.imgur.com/biZdbT6.png",
    "http://i.imgur.com/Ccl5zsK.jpeg",
    "http://i.imgur.com/C034f1C.png"
]

hug = [
    "http://i.imgur.com/3UuGlxY.gif",
    "http://i.imgur.com/5ESIbtr.gif",
    "http://i.imgur.com/ByEMJlV.gif",
    "http://i.imgur.com/D7xqa1M.gif",
    "http://i.imgur.com/OUL6iCT.jpg",
    "http://i.imgur.com/RVydzN9.jpg",
    "http://i.imgur.com/TRAEPrG.jpg",
    "http://i.imgur.com/ajkjJhm.gif",
    "http://i.imgur.com/i5Cb4ZB.gif",
    "http://i.imgur.com/sIIfjyU.gif",
    "http://i.imgur.com/sLMSjgO.gif",
    "http://i.imgur.com/sOX8fzC.png",
    "http://i.imgur.com/tkbDOQL.jpg",
    "http://i.imgur.com/3YiNS3H.jpg",
    "http://i.imgur.com/4ChyZyt.jpg",
    "http://i.imgur.com/DwmBeGe.jpg",
    "http://i.imgur.com/FLj4khz.gif",
    "http://i.imgur.com/OlmhMzg.jpg",
    "http://i.imgur.com/QZLlbvC.gif",
    "http://i.imgur.com/T0WSvga.jpg",
    "http://i.imgur.com/WaVgODM.gif",
    "http://i.imgur.com/exIfNQ9.jpg",
    "http://i.imgur.com/q3sIWuJ.jpg",
    "http://i.imgur.com/z1dT2iR.jpg",
    "http://i.imgur.com/1h8jqu5.png",
    "http://i.imgur.com/iTn7QrY.png",
    "http://i.imgur.com/n5Kdwcl.jpg",
    "http://i.imgur.com/bDm2acY.jpg",
    "http://i.imgur.com/AtW9myk.jpg",
    "http://i.imgur.com/BEqNuVC.gif",
    "http://i.imgur.com/tZfW3GN.gif",
    "http://i.imgur.com/3ehaJ5b.gif",
    "http://i.imgur.com/EkSrgCa.png",
    "http://i.imgur.com/WOU75S5.gifv",
    "http://i.imgur.com/Kwel8RT.jpg",
    "http://i.imgur.com/DwIN6Ez.jpg",
    "http://i.imgur.com/De8qlhi.gif",
    "http://i.imgur.com/Zq4CxH1.jpg",
    "http://i.imgur.com/xTk7d57.png",
    "http://i.imgur.com/nlZcdE5.jpg",
    "http://i.imgur.com/3C4PdKO.gif",
    "http://i.imgur.com/TyhNG69.jpg",
    "http://i.imgur.com/KQPdet1.jpg",
    "http://i.imgur.com/5xuIiUg.jpg",
    "http://i.imgur.com/bzMSglR.gif",
    "http://i.imgur.com/vgOUnxB.png",
    "http://i.imgur.com/ClDX4qr.jpg",
    "http://i.imgur.com/zpbtWVE.gif",
    "http://i.imgur.com/ZQivdm1.gif",
    "http://i.imgur.com/gbEuIv2.jpg",
    "http://i.imgur.com/tj5KVy7.jpg",
    "http://i.imgur.com/ix8cZR4.jpg",
    "http://i.imgur.com/5FnZ4x7.jpg",
    "http://i.imgur.com/52eDoKB.jpg"
]

kiss = [
    "http://i.imgur.com/6piA8Bn.png",
    "http://i.imgur.com/9OvUVb7.gif",
    "http://i.imgur.com/BbV7nBm.png",
    "http://i.imgur.com/KvONLmo.png",
    "http://i.imgur.com/L0E9Jnu.png",
    "http://i.imgur.com/PuxakLo.png",
    "http://i.imgur.com/RVfAPXS.gif",
    "http://i.imgur.com/RXCT8Xu.jpg",
    "http://i.imgur.com/aRDQYHS.gif",
    "http://i.imgur.com/e87y1T0.png",
    "http://i.imgur.com/rrJXMLM.jpg",
    "http://i.imgur.com/vO7jPnC.png",
    "http://i.imgur.com/z8wsT3u.jpg",
    "http://i.imgur.com/5HCWeZi.jpg",
    "http://i.imgur.com/ZeqMVLT.jpg",
    "http://i.imgur.com/eMQES0X.jpg",
    "http://i.imgur.com/jv0zcn1.jpg",
    "http://i.imgur.com/mxheIpV.jpg",
    "http://i.imgur.com/64ARL67.png",
    "http://i.imgur.com/p5r7Wru.jpg",
    "http://i.imgur.com/BYSEn1d.gif",
    "http://i.imgur.com/byqfTq6.jpg",
    "http://i.imgur.com/TKQU3ce.jpg",
    "http://i.imgur.com/5DLhzsn.png",
    "http://i.imgur.com/IExRmme.jpg",
    "http://i.imgur.com/I743LVk.png",
    "http://i.imgur.com/WHVX5LA.jpg",
    "http://i.imgur.com/5QH0LRw.jpg",
    "http://i.imgur.com/u081Wh7.jpg"
]

lewd = [
    "http://i.imgur.com/0fmQEH9.gifv",
    "http://i.imgur.com/2hshUS8.png",
    "http://i.imgur.com/60Bw1H3.jpg",
    "http://i.imgur.com/7t2jr3l.jpg",
    "http://i.imgur.com/FdF3RVx.png",
    "http://i.imgur.com/OA3FpyR.jpg",
    "http://i.imgur.com/OHqDH95.png",
    "http://i.imgur.com/OniI7AN.jpg",
    "http://i.imgur.com/PNLAXHU.png",
    "http://i.imgur.com/XfdH2fM.png",
    "http://i.imgur.com/ZrDrYRq.jpg",
    "http://i.imgur.com/aqfjbQr.png",
    "http://i.imgur.com/bCtARvu.jpg",
    "http://i.imgur.com/czGynPQ.png",
    "http://i.imgur.com/enEenOJ.gifv",
    "http://i.imgur.com/i4yASS8.gifv",
    "http://i.imgur.com/j75dI3e.png",
    "http://i.imgur.com/kSBCm9O.jpg",
    "http://i.imgur.com/mKU4DD3.jpg",
    "http://i.imgur.com/pLe3uPH.jpg",
    "http://i.imgur.com/poaIulf.gifv",
    "http://i.imgur.com/rB021Oq.jpg",
    "http://i.imgur.com/rjdjlff.gifv",
    "http://i.imgur.com/zSVNE7f.png",
    "http://i.imgur.com/QqAOXmk.gif",
    "http://i.imgur.com/a34muR7.gifv",
    "http://i.imgur.com/Pi26Q1N.png",
    "http://i.imgur.com/DEw1wlC.png",
    "http://i.imgur.com/opF8yK7.jpg",
    "http://i.imgur.com/VuOSAfE.mp4",
    "http://i.imgur.com/2645QPF.png",
    "http://i.imgur.com/D3dO28e.png"
]

pat = [
    "http://i.imgur.com/8nBF6zB.jpg",
    "http://i.imgur.com/9VP1mt2.jpg",
    "http://i.imgur.com/45r3OMu.gif",
    "http://i.imgur.com/DovBeJA.jpg",
    "http://i.imgur.com/FWWsBBO.png",
    "http://i.imgur.com/H325x56.gif",
    "http://i.imgur.com/J2M2NwW.gif",
    "http://i.imgur.com/KclqOIS.png",
    "http://i.imgur.com/TWs8YeQ.gif",
    "http://i.imgur.com/VtSF0Bo.gif",
    "http://i.imgur.com/cXqETmD.jpg",
    "http://i.imgur.com/jAjhmZB.gif",
    "http://i.imgur.com/k1ccojT.jpg",
    "http://i.imgur.com/m6R9Gcs.gif",
    "http://i.imgur.com/mL555Kr.gif",
    "http://i.imgur.com/nJHxhTv.png",
    "http://i.imgur.com/tZbtYnJ.jpg",
    "http://i.imgur.com/YswZO81.gif",
    "http://i.imgur.com/yMYqtTc.gif",
    "http://i.imgur.com/W87G0pY.jpg",
    "http://i.imgur.com/KXily58.png",
    "http://i.imgur.com/upgYA1k.jpg",
    "http://i.imgur.com/JZTAFxn.gif",
    "http://i.imgur.com/nmqdk8b.gif",
    "http://i.imgur.com/Y8X8puQ.jpg",
    "http://i.imgur.com/HrqSHYP.gifv",
    "http://i.imgur.com/XypsXd1.png",
    "http://i.imgur.com/fHtlTVT.gif",
    "http://i.imgur.com/SurPnFI.png",
    "http://i.imgur.com/PXcUsO2.jpg",
    "http://i.imgur.com/ZBCfrfK.png",
    "http://i.imgur.com/D84uqqx.jpeg",
    "http://i.imgur.com/s6rX6Vm.jpeg",
    "http://i.imgur.com/BMm8q4m.jpeg",
    "http://i.imgur.com/ggsmEoT.png",
    "http://i.imgur.com/NBjnzzr.jpeg",
    "http://i.imgur.com/CSbLru9.png",
    "http://i.imgur.com/QFOoBs3.png"
]

pout = [
    "http://i.imgur.com/0kuOoWo.jpg",
    "http://i.imgur.com/3FeldbD.jpg",
    "http://i.imgur.com/6qsrPp3.png",
    "http://i.imgur.com/E6FUZ7U.gif",
    "http://i.imgur.com/GRQezS8.png",
    "http://i.imgur.com/QWuEy0c.png",
    "http://i.imgur.com/T1VYAq5.jpg",
    "http://i.imgur.com/dyHfYhX.png",
    "http://i.imgur.com/eryVYlJ.jpg",
    "http://i.imgur.com/s5sBPUx.jpg",
    "http://i.imgur.com/v2mhBJ1.png",
    "http://i.imgur.com/wZuH3Js.jpg",
    "http://i.imgur.com/y0rU7Md.jpg",
    "http://i.imgur.com/zkvidta.jpg",
    "http://i.imgur.com/8XvoUj8.png",
    "http://i.imgur.com/M5ym4tn.png",
    "http://i.imgur.com/C8n4jyI.jpg",
    "http://i.imgur.com/HohQynd.png",
    "http://i.imgur.com/6GXWRjg.png"
]

slap = [
    "http://i.imgur.com/CGyPnn9.gifv",
    "http://i.imgur.com/FQGN6Xw.gifv",
    "http://i.imgur.com/R5ABCpS.jpg",
    "http://i.imgur.com/XjDBzji.gif",
    "http://i.imgur.com/zcuWNX5.gifv",
    "http://i.imgur.com/LmhjQA8.gifv"
]

smug = [
    "http://i.imgur.com/4VUcsQw.jpg",
    "http://i.imgur.com/DGvxs2Y.png",
    "http://i.imgur.com/DImkyVx.jpg",
    "http://i.imgur.com/J3bVHDv.jpg",
    "http://i.imgur.com/NW150pB.png",
    "http://i.imgur.com/QBu545b.png",
    "http://i.imgur.com/bOTsU0K.png",
    "http://i.imgur.com/dKTcYRQ.jpg",
    "http://i.imgur.com/fPBTzZ5.jpg",
    "http://i.imgur.com/o5CgAHm.png",
    "http://i.imgur.com/qDoiBYn.png",
    "http://i.imgur.com/sCHlAiR.jpg",
    "http://i.imgur.com/tW381Ym.png",
    "http://i.imgur.com/lFeNwxW.jpg",
    "http://i.imgur.com/hGnhgMV.jpg",
    "http://i.imgur.com/1Enqr7e.jpg",
    "http://i.imgur.com/yNVFl4p.jpg"
]