import aiohttp
import asyncio

import re

import requests

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks



JSON_LUA_API = "https://lua-api.factorio.com/latest/runtime-api.json"
BASE_API_URL = "https://lua-api.factorio.com/latest/"

# Get api json
# Decode json
# Flatten API
# Find entry

async def update_api():
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(JSON_LUA_API) as resp:
    #         if resp.ok == True:
    #             api = await resp.json()
    #             return api
    r = requests.get(JSON_LUA_API)
    api = r.json()

    return api

# asyncio.run(update_api())

def format_links(entry):
    description = re.sub(r"\[(.+)::(.+)\]\((\1)::(\2)\)", r"[\1::\2](https://lua-api.factorio.com/latest/\1.html#\1.\2)", entry["description"])
    description = re.sub(r"\[(.+)\]\((?!http)(.+)\)", r"[\1](https://lua-api.factorio.com/latest/\2.html)", description)
    return description

def make_event_table_field(em, concept_type):
    table_str = ""
    table_fields = []
    maxlen = 0
    for par in concept_type['parameters']:
        table_fields.append([par['name'], par['type']])
        if len(par['name']) > maxlen:
            maxlen = len(par['name'])
    for name, type in table_fields:
        table_str += f"{name.ljust(maxlen)}    :: {type}\n"
    em.add_field(name="Table fields", value = f"```{table_str}```")
    return em

def read_concept_types(em, concept_type):
    types_list = []
    for option in concept_type['options']:
        if type(option) == str:
            types_list.append(option)
        elif type(option) == dict:
            if option['complex_type'] == "table":
                em = make_event_table_field(em, option)
            types_list.append(option['complex_type'])
        else:
            em = read_concept_types(em, option)
    return [em, types_list]


def flattendefines(defines: list[dict], parents: list = [], output: list = []):
    for define in defines:
        parents.append(define["name"])
        if "subkeys" in define:
            output = flattendefines(define["subkeys"], parents, output)
            pass
        else:
            output.append(parents[:])
            del parents[-1]
            pass
    if len(parents)>0:
        del parents[-1]
    return output


class LuaAPIcog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = []
        self.update_api_cache.start()
    
    def cog_unload(self) -> None:
        self.update_api_cache.cancel()

    @tasks.loop(hours=2)
    async def update_api_cache(self):
        self.api = await update_api()
        flattened_defines = flattendefines(self.api["defines"])
        self.flattened_defines_strs = [".".join(f) for f in flattened_defines]
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(JSON_LUA_API) as resp:
        #         self.api = await resp.json()
        #         print("API UDPATED\n")

    api_search = app_commands.Group(name = "api", description = "...")
    
    @api_search.command(name="class")
    @app_commands.rename(cls="class")
    async def api_class(self, interaction: discord.Interaction, cls: str, member: str = ""):
        """
        Seaches for classes in the api documentation.
        """
        cls_entry = self.api["classes"][int(cls)]
        if not member:
            #Class referenced directly
            em = discord.Embed(color=0x206694)
            em.title = cls_entry["name"]
            em.url = f"{BASE_API_URL}{cls_entry['name']}.html"

            # Fix links in description.
            em.description = format_links(cls_entry)
            members = ""
            for member in cls_entry["methods"]:
                if len(members) < 900:
                    parameters = ""
                    if member['parameters']:
                        for par in member['parameters']:
                            parameters += f"{par['name']}, "
                        parameters = f"**{parameters[0:-2]}**"
                    if member['return_values']:
                        if 'complex_type' in member['return_values'][0]['type']:
                            return_values = f"-> {member['return_values'][0]['type']['complex_type']}"
                        else:
                            return_values = f"-> {member['return_values'][0]['type']}"
                    else:
                        return_values = ""
                    members += f"**{member['name']}({parameters})** {return_values}\n"
                else:
                    break
            for member in cls_entry["attributes"]:
                if len(members) < 900:
                    members += f"**{member['name']}**: {'R' if member['read'] else ''}{'W' if member['write'] else ''} :: {member['type']}\n"
                else:
                    break
            if len(members) > 1024:
                members = members[:1020] + "..."
            elif len(members) > 900:
                members += "..."
            em.add_field(name="Members:", value=members)
            await interaction.response.send_message(embed=em)
        else:
            # Specific member of class referenced
            em = discord.Embed(color=0x206694)
            em.title = f"{cls_entry['name']}::{member}"
            em.url = f"{BASE_API_URL}{cls_entry['name']}.html#{cls_entry['name']}.{member}"
            memberfound = False
            for method in cls_entry['methods']:
                if member == method['name']:
                    memberfound = True
                    em.description = method['description']
                    if method["parameters"]:
                        parameters = method["parameters"]
                        parameterstr = ""
                        for par in parameters:
                            parameterstr += f"**{par['name']}** :: {par['type']}{'?' if par['optional'] else ''}\n" # type may also be complex type
                        em.add_field(name="Parameters", value=parameterstr, inline=False)
                    if method["return_values"]:
                        returns = method["return_values"]
                        returnsstr = ""
                        for r in returns:
                            returnsstr += f"-> **{r['type']}** {r['description']}"
                        em.add_field(name="Return values", value=returnsstr, inline=False)
                    if "raises" in method:
                        raises = method["raises"]
                        raisesstr = ""
                        for r in raises:
                            raisesstr += f"**{r['name']}** {r['timeframe']}"
                        em.add_field(name="Raised events", value=raisesstr, inline=False)
                    break
            for attribute in cls_entry['attributes']:
                if memberfound:
                    break
                if member == attribute['name']:
                    memberfound = True
                    description = format_links(attribute)
                    # type may also be complex type
                    em.description = f"`{attribute['name']} :: {attribute['type']}{'?' if not attribute['optional'] else ''}` [{'R' if attribute['read'] else ''}{'W' if attribute['write'] else ''}]\n{description}"
            await interaction.response.send_message(embed=em)

            
    @api_class.autocomplete("cls")
    async def api_class_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=cls["name"], value=str(self.api["classes"].index(cls))) for cls in self.api["classes"] if current.lower() in cls["name"].lower()][0:25]
        return results

    @api_class.autocomplete("member")
    async def api_class_member_autocomplete(self, interaction: discord.Interaction, current: str):
        pass
        cls = int(interaction.namespace["class"])
        pass
        members = self.api["classes"][cls]["methods"] + self.api["classes"][cls]["attributes"] + self.api["classes"][cls]["operators"]
        results = [app_commands.Choice(name=member["name"], value=member["name"]) 
                for member in members
                if current.lower() in member["name"].lower()]
        return results[0:25]


    @api_search.command(name="event")
    async def api_event(self, interaction: discord.Interaction, event: str):
        """
        Seaches for events in the api documentation.
        """
        event_entry = self.api["events"][int(event)]
        em = discord.Embed(color=0x206694)
        em.title = event_entry["name"]
        em.url=f"{BASE_API_URL}events.html#{event_entry['name']}"
        em.description = format_links(event_entry)
        data_str = ""
        members = []
        maxlen = 0
        for data in event_entry["data"]:
            if len(data['name']) > maxlen:
                maxlen = len(data['name'])
            members.append([data['name'], data['type']])
        for name, type in members:
            data_str += f"{name.ljust(maxlen)}    :: {type}\n"
        em.add_field(name="Members", value=f"```{data_str}```")
        await interaction.response.send_message(embed=em)


    @api_event.autocomplete("event")
    async def api_event_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=event["name"], value=str(self.api["events"].index(event))) for event in self.api["events"] if current.lower() in event["name"].lower()][0:25]
        return results
    
    @api_search.command(name="concept")
    async def api_concept(self, interaction: discord.Interaction, concept: str):
        """
        Seaches for concepts in the api documentation.
        """
        concept_entry = self.api["concepts"][int(concept)]
        em = discord.Embed(color=0x206694)
        em.description = concept_entry['description']
        concept_type = concept_entry['type']
        types = ""

        if type(concept_type) == str:
            types = concept_type
        elif concept_type['complex_type'] == "table":
            types = concept_type['complex_type']
            em = make_event_table_field(em, concept_type)
        elif concept_type['complex_type'] == "union":
            em, types_list = read_concept_types(em, concept_type)
            types = " or ".join(types_list)
        else: 
            types = concept_type['complex_type']
        
        em.title = concept_entry['name']
        em.url=f"{BASE_API_URL}Concepts.html#{concept_entry['name']}"
        description_paragraphs = concept_entry['description'].split('\n\n')
        if len(description_paragraphs) > 1:
            description_paragraphs[0] += f"\n[[more]]({em.url})"
        description  = f"`{concept_entry['name']} :: {types}`\n\n{description_paragraphs[0]}"
        em.description = description
        await interaction.response.send_message(embed=em)

    @api_concept.autocomplete("concept")
    async def api_concept_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=concept["name"], value=str(self.api["concepts"].index(concept))) for concept in self.api["concepts"] if current.lower() in concept["name"].lower()][0:25]
        return results


    @api_search.command(name="defines")
    async def api_defines(self, interaction: discord.Interaction, defines: str):
        """
        Seaches for defines in the api documentation.
        """
        define_path = defines.split(".")
        defines_entry = self.api["defines"]
        for define in define_path:
            for d in defines_entry:
                if d['name'] == define:
                    if 'subkeys' in d:
                        defines_entry = d['subkeys']
                    else:
                        defines_entry = d
                    break
        em = discord.Embed(color=0x206694)
        em.title = defines
        em.url = f"{BASE_API_URL}defines.html#defines.{defines}"
        em.description = format_links(defines_entry)
        value_str = ""
        for value in defines_entry['values']:
            if len(value_str)<900:
                value_str += f"`{value['name']}` {format_links(value)}\n"
            else:
                value_str += "[...]"
                break
        em.add_field(name="values", value=value_str)
        await interaction.response.send_message(embed=em)
    
    @api_defines.autocomplete("defines")
    async def api_defines_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=f, value=f) for f in self.flattened_defines_strs if current.lower() in f.lower()][0:25]
        return results


    @api_search.command(name="builtin_types")
    async def api_builtin_types(self, interaction: discord.Interaction, builtin_type: str):
        type_entry = self.api["builtin_types"][int(builtin_type)]
        em = discord.Embed(color=0x206694)
        em.title = type_entry['name']
        em.url = f"{BASE_API_URL}Builtin-Types.html#{type_entry['name']}"
        em.description = format_links(type_entry)
        await interaction.response.send_message(embed=em)

    @api_builtin_types.autocomplete("builtin_type")
    async def api_builtin_types_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=builtin_type["name"], value=str(self.api["builtin_types"].index(builtin_type))) for builtin_type in self.api["builtin_types"] if current.lower() in builtin_type["name"].lower()][0:25]
        return results

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LuaAPIcog(bot))
