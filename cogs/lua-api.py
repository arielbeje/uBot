import aiohttp
import asyncio

import re

import requests

from typing import Union, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks



JSON_LUA_API = "https://lua-api.factorio.com/latest/runtime-api.json"
BASE_API_URL = "https://lua-api.factorio.com/latest/"

flatten_exceptions = ["return_values", "options"]

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

def flatten_list(listname: str, input: list) -> Union[dict, list]:
    """
    Takes a list and returns a dictionary that indexes the list by names.
    """
    output = {}
    for item in input:
        if "name" in item and type(item) == dict:
            name = item["name"]
            del item["name"]
            output[name] = item
        else:
            name = listname
            output[name] = item
    return output

def list_contains_only_dicts(lst: list) -> bool:
    for item in lst:
        if not type(item) == dict:
            return False
    return True

def inspect_dict(mixed_dict: dict) -> dict:
    """
    Recursively iterates through dictionary and flattens every list it encounters
    """
    for key in mixed_dict:
        if type(mixed_dict[key]) == list and list_contains_only_dicts(mixed_dict[key]):
            if not key in flatten_exceptions:
                mixed_dict[key] = flatten_list(key, mixed_dict[key])
            else:
                for x, i in enumerate(mixed_dict[key]):
                    if type(x) == dict:
                        mixed_dict[key][i] = inspect_dict(x)
            if key in mixed_dict[key]:
                mixed_dict[key] = mixed_dict[key][key]

        if type(mixed_dict[key]) == dict:
            mixed_dict[key] = inspect_dict(mixed_dict[key])
    return mixed_dict

def format_links(entry):
    description = re.sub(r"\[(.+)::(.+)\]\((\1)::(\2)\)", r"[\1::\2](https://lua-api.factorio.com/latest/\1.html#\1.\2)", entry["description"])
    description = re.sub(r"\[(.+?)\]\((?!http)(.+?)\)", r"[\1](https://lua-api.factorio.com/latest/\2.html)", description)
    return description

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

def parse_types(input_type) -> Union[str, list[str, dict]]:
    if type(input_type) == str:
        return input_type
    else:
        complex_type = input_type["complex_type"]
        if complex_type == "type":
            return parse_types(input_type["value"])
        elif complex_type == "union":
            types = []
            for option in input_type["options"]:
                types.append(parse_types(option))
            return " or ".join(types)
        elif complex_type == "array":
            return f"array[{parse_types(input_type['value'])}]"
        elif complex_type == "dictionary" or complex_type == "LuaCustomTable":
            return f"{complex_type}[{parse_types(input_type['key'])} → {parse_types(input_type['value'])}]"
        elif complex_type == "function":
            parameters = []
            for par in input_type['parameters']:
                parameters.append(parse_types(par))
            return f"function({', '.join(parameters)})"
        elif complex_type == "literal":
            return str(input_type['value'])
        elif complex_type == "LuaLazyLoadedValue":
            return f"LuaLazyLoadedValue({parse_types(input_type['value'])})"
        elif complex_type == "struct":
            struct_str = parse_attributes(input_type['attributes'])
            return ["struct", {"name": "Attributes", "value": struct_str}]
        elif complex_type == "table" or complex_type == "tuple":
            return [complex_type, parse_table_parameters(input_type['parameters'])]

def parse_attributes(attributes: dict):
    output_str = ""
    for name, attr in attributes.items():
        output_str += f"**{name}**: {'R' if attr['read'] else ''}{'W' if attr['write'] else ''} :: {parse_types(attr['type'])}\n"
    return output_str

def parse_table_parameters(parameters: dict):
    table_str = ""
    table_fields = []
    maxlen = 0
    for name, par in parameters.items():
        table_fields.append([name, parse_types(par['type'])])
        if len(name) > maxlen:
            maxlen = len(name)
    for name, type in table_fields:
        table_str += f"{name.ljust(maxlen)}    :: {type}\n"
    return {"name": "Table fields", "value": f"```{table_str}```"}

class LuaAPIcog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = []
        self.update_api_cache.start()
    
    def cog_unload(self) -> None:
        self.update_api_cache.cancel()

    @tasks.loop(hours=2)
    async def update_api_cache(self):
        api = await update_api()
        flattened_defines = flattendefines(api["defines"])
        self.flattened_defines_strs = [".".join(f) for f in flattened_defines]
        self.api = inspect_dict(api)
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(JSON_LUA_API) as resp:
        #         self.api = await resp.json()
        #         print("API UDPATED\n")

    api_search = app_commands.Group(name = "api", description = "...")
    @api_search.command(name="page")
    @app_commands.choices(page=[
        app_commands.Choice(name="Home", value="index"),
        app_commands.Choice(name="Lifecycle", value="Data-Lifecycle"),
        app_commands.Choice(name="Classes", value="Classes"),
        app_commands.Choice(name="Events", value="events"),
        app_commands.Choice(name="Concepts", value="Concepts"),
        app_commands.Choice(name="Defines", value="defines"),
        app_commands.Choice(name="Builtin types", value="Builtin-Types"),
        app_commands.Choice(name="Libraries and functions", value="Libraries")
    ])
    async def api_page(self, interaction: discord.Interaction, page: app_commands.Choice[str]):
        """
        Direct links to the API or one of its main categories
        """
        em = discord.Embed(title=f"Factorio Runtime Docs: {page.name}", url=f"https://lua-api.factorio.com/latest/{page.value}.html", colour=discord.Colour.gold())
        if page.name == "Home":
            em.title = "Latest API Documentation"
            em.description = f"Latest version: {self.api['application_version']}"
        await interaction.response.send_message(embed=em)

    
    @api_search.command(name="class")
    @app_commands.rename(cls="class")
    async def api_class(self, interaction: discord.Interaction, cls: str, member: str = ""):
        """
        Seaches for classes in the api documentation.
        """
        #Support "ClassName.member" or :ClassName::member" format in class field
        if len(cls.split("."))>1:
            member = cls.split(".")[1]
            cls = cls.split(".")[0]
        elif len(cls.split("::"))>1:
            member = cls.split("::")[1]
            cls = cls.split("::")[0]

        if not cls in self.api["classes"]:
            em = discord.Embed(title="Error",
                description="No class with this name exists. Check your spelling and capitalization, or make sure to select an option from the autocomplete.",
                colour=discord.Colour.red())
            await interaction.response.send_message(embed=em)
            return
        cls_entry = self.api["classes"][cls]
        if not member:
            #Class referenced directly
            em = discord.Embed(colour=discord.Colour.gold())
            em.title = cls
            em.url = f"{BASE_API_URL}{cls}.html"

            em.description = format_links(cls_entry).split("\n\n")[0]
            members = ""
            for name, method in cls_entry["methods"].items():
                if len(members) < 900:
                    parameters = []
                    parameters_str = ""
                    if method['parameters']:
                        for par_name, par in method['parameters'].items():
                            parameters.append(f"{par_name}")
                        parameters_str = f"**{', '.join(parameters)}**"
                    if method['return_values']:
                        return_values = ", ".join([parse_types(value['type']) for value in method['return_values']])
                    else:
                        return_values = ""
                    members += f"**{name}({parameters_str})** {return_values}\n"
                else:
                    break
            for name, member in cls_entry["attributes"].items():
                if len(members) < 900:
                    members += f"**{name}**: {'R' if member['read'] else ''}{'W' if member['write'] else ''} :: {parse_types(member['type'])}\n"
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
            if not member in self.api["classes"][cls]["methods"] and member not in self.api["classes"][cls]["attributes"] and member not in self.api["classes"][cls]["operators"]:
                em = discord.Embed(title="Error",
                    description="Class has no member of the given name. Check your spelling and capitalization, or make sure to select an option from the autocomplete.",
                    colour=discord.Colour.red())
                await interaction.response.send_message(embed=em)
                return
            em = discord.Embed(colour=discord.Colour.gold())
            em.title = f"{cls}::{member}"
            em.url = f"{BASE_API_URL}{cls}.html#{cls}.{member}"
            memberfound = False
            for name, method in cls_entry['methods'].items():
                if member == name:
                    memberfound = True
                    em.description = method['description']
                    if method["parameters"]:
                        parameters = method["parameters"]
                        parameterstr = ""
                        for par_name, par in parameters.items():
                            parameterstr += f"**{par_name}** :: {parse_types(par['type'])}{'?' if par['optional'] else ''}\n"
                        em.add_field(name="Parameters", value=parameterstr, inline=False)
                    if method["return_values"]:
                        returns = method["return_values"]
                        returnsstr = ""
                        for ret in returns:
                            returnsstr += f"→ **{parse_types(ret['type'])}**{'?' if ret['optional'] else ''} {ret['description']}\n"
                        em.add_field(name="Return values", value=returnsstr, inline=False)
                    if "raises" in method:
                        raises = method["raises"]
                        raisesstr = ""
                        for rai_name, rai in raises.items():
                            raisesstr += f"**{rai_name}** {rai['timeframe']}"
                        em.add_field(name="Raised events", value=raisesstr, inline=False)
                    break
            for attr_name, attribute in cls_entry['attributes'].items():
                if memberfound:
                    break
                if member == attr_name:
                    memberfound = True
                    description = format_links(attribute)
                    attribute_type = parse_types(attribute['type'])
                    if type(attribute_type) == list:
                        em.add_field(name=attribute_type[1]["name"], value=attribute_type[1]["value"])
                        attribute_type = attribute_type[0]
                    em.description = f"`{attr_name} :: {attribute_type}{'?' if attribute['optional'] else ''}` [{'R' if attribute['read'] else ''}{'W' if attribute['write'] else ''}]\n{description}"
            await interaction.response.send_message(embed=em)

            
    @api_class.autocomplete("cls")
    async def api_class_autocomplete(self, interaction: discord.Interaction, current: str):
        if not "." in current and not "::" in current:
            results = [app_commands.Choice(name=cls, value=cls) for cls in list(self.api['classes']) if current.lower() in cls.lower()]
        else:
            if "." in current:
                cls = current.split(".")[0]
                sep = "."
                current = current.split(".")[1]
            elif "::" in current:
                cls = current.split("::")[0]
                sep = "::"
                current = current.split("::")[1]
            members = list(self.api["classes"][cls]["methods"]) + list(self.api["classes"][cls]["attributes"]) + list(self.api["classes"][cls]["operators"])
            results = [app_commands.Choice(name=cls+sep+member, value=cls+sep+member)
                    for member in members
                    if current.lower() in member.lower()]
        return results[0:25]

    @api_class.autocomplete("member")
    async def api_class_member_autocomplete(self, interaction: discord.Interaction, current: str):
        cls = interaction.namespace["class"]
        members = list(self.api["classes"][cls]["methods"]) + list(self.api["classes"][cls]["attributes"]) + list(self.api["classes"][cls]["operators"])
        results = [app_commands.Choice(name=member, value=member) 
                for member in members
                if current.lower() in member.lower()]
        return results[0:25]

    @api_search.command(name="event")
    async def api_event(self, interaction: discord.Interaction, event: str):
        """
        Seaches for events in the api documentation.
        """
        event_entry = self.api["events"][event]
        em = discord.Embed(colour=discord.Colour.gold())
        em.title = event
        em.url=f"{BASE_API_URL}events.html#{event}"
        em.description = format_links(event_entry)
        data_str = ""
        members = []
        maxlen = 0
        for data_name, data in event_entry["data"].items():
            if len(data_name) > maxlen:
                maxlen = len(data_name)
            members.append([data_name, parse_types(data['type'])])
        for name, type in members:
            data_str += f"{name.ljust(maxlen)}    :: {type}\n"
        em.add_field(name="Members", value=f"```{data_str}```")
        await interaction.response.send_message(embed=em)


    @api_event.autocomplete("event")
    async def api_event_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=event, value=event) for event in list(self.api["events"]) if current.lower() in event.lower()][0:25]
        return results
    
    @api_search.command(name="concept")
    async def api_concept(self, interaction: discord.Interaction, concept: str):
        """
        Seaches for concepts in the api documentation.
        """
        concept_entry = self.api["concepts"][concept]
        em = discord.Embed(colour=discord.Colour.gold())
        em.description = concept_entry['description']
        concept_type = parse_types(concept_entry['type'])
        if type(concept_type) == list:
            em.add_field(name=concept_type[1]["name"], value=concept_type[1]["value"])
            concept_type = concept_type[0]
        
        em.title = concept
        em.url=f"{BASE_API_URL}Concepts.html#{concept}"
        description_paragraphs = concept_entry['description'].split('\n\n')
        if len(description_paragraphs) > 1:
            description_paragraphs[0] += f"\n[[more]]({em.url})"
        description  = f"`{concept} :: {concept_type}`\n\n{description_paragraphs[0]}"
        em.description = description
        await interaction.response.send_message(embed=em)

    @api_concept.autocomplete("concept")
    async def api_concept_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=concept, value=concept) for concept in list(self.api["concepts"]) if current.lower() in concept.lower()][0:25]
        return results


    @api_search.command(name="defines")
    async def api_defines(self, interaction: discord.Interaction, defines: str):
        """
        Seaches for defines in the api documentation.
        """
        define_path = defines.split(".")
        defines_entry = self.api["defines"][define_path[0]]
        if len(define_path) > 1:
            for d in define_path[1:]:
                defines_entry = defines_entry["subkeys"][d]
                pass
        em = discord.Embed(colour=discord.Colour.gold())
        em.title = defines
        em.url = f"{BASE_API_URL}defines.html#defines.{defines}"
        em.description = format_links(defines_entry)
        value_str = ""
        for name, value in defines_entry['values'].items():
            if len(value_str)<900:
                value_str += f"`{name}` {format_links(value)}\n"
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
        """
        Seaches for builtin types in the api documentation.
        """
        type_entry = self.api["builtin_types"][builtin_type]
        em = discord.Embed(colour=discord.Colour.gold())
        em.title = builtin_type
        em.url = f"{BASE_API_URL}Builtin-Types.html#{builtin_type}"
        em.description = format_links(type_entry)
        await interaction.response.send_message(embed=em)

    @api_builtin_types.autocomplete("builtin_type")
    async def api_builtin_types_autocomplete(self, interaction: discord.Interaction, current: str):
        results = [app_commands.Choice(name=builtin_type, value=builtin_type) for builtin_type in list(self.api["builtin_types"]) if current.lower() in builtin_type.lower()][0:25]
        return results

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LuaAPIcog(bot))
