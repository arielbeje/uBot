import asyncio
import os
import json

import discord
from discord.ext import commands

import utils.customchecks as customchecks

failedOps = 0

with open('variables.json', 'r') as f:
    variables = json.load(f)

if not variables["token"]:
    failedOps += 1
    print("No token inputted in variables.json."
          "The bot will not run without it.")

if not variables["modmail"]["guildID"]:
    failedOps += 1
    print("No guild ID for the modmail function was inputted in variables.json."
          "The modmail function will not run without it.")

else:
    guildID = int(variables["modmail"]["guildID"])

if os.path.exists('data/reminderdb.json'):
    with open('data/reminderdb.json', 'r') as f:
        reminderdb = json.load(f)
else:
    print(f"Reminder DB not found.")
    failedOps += 1

if not variables["joinleavechannelid"]:
    print("No channel ID for the leave/join events was inputted in variables.json."
          "The events will not run without it.")
    joinLeaveID = 0
    failedOps += 1
else:
    joinLeaveID = int(variables["joinleavechannelid"])

if not variables["myanimelist"]["login"] or variables["myanimelist"]["password"]:
    print("No username/password inputted in variables.json."
          "The MyAnimeList API requires them to function.")
    failedOps += 1


def get_prefix(bot, message):
    prefixes = variables["prefixes"]

    if message.guild is None:
        return variables["prefixes"][0]

    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix)
if joinLeaveID != 0:
    joinLeaveChannel = bot.get_channel(joinLeaveID)


@bot.event
async def on_command_error(ctx, error):
    origerror = getattr(error, 'original', error)
    if isinstance(origerror, customchecks.NoPermsError):
        em = discord.Embed(title="Error",
                           description=f"You do not have sufficient permissions to use the command `{ctx.command}`",
                           colour=0xDC143C)
        return await ctx.send(embed=em)
    else:
        raise error


@bot.event
async def on_ready():
    print(f"\n~-~-~-~-~-~-~-~-~\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}")
    servers = len(bot.guilds)
    users = len(bot.users)
    print(f"Serving {users} users in " + str(servers) + " server" + ("s" if servers > 1 else "") + ".")
    # Health log
    if failedOps != 0:
        print(f'{failedOps} operations failed.')
    print("~-~-~-~-~-~-~-~-~")


@bot.event
async def on_message(message):
    message.content = message.content.split(variables["comment"])[0]
    if message.guild is not None:
        await bot.process_commands(message)
    elif (message.guild is None and
            variables["modmail"]["enabled"].lower() == "true" and
            guildID):
        if bot.get_guild(guildID).get_member(message.author.id) is not None:
            modmailChannel = None
            for channel in bot.get_guild(guildID).channels:
                if channel.name == variables["modmail"]["channel"]:
                    modmailChannel = channel
            if modmailChannel:
                em = discord.Embed(title="New mod mail:",
                                   description=message.content,
                                   colour=0xDFDE6E)
                if message.author.avatar:
                    em.set_author(name=bot.get_guild(guildID).get_member(message.author.id).display_name,
                                  icon_url=f"https://cdn.discordapp.com/avatars/{message.author.id}/{message.author.avatar}.png?size=64")
                else:
                    em.set_author(name=bot.get_guild(guildID).get_member(message.author.id).display_name,
                                  icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
                # em.set_footer(text=bot.user.name, icon_url=f"https://cdn.discordapp.com/avatars/{bot.user.id}/{bot.user.avatar}.png?size=64")
                await modmailChannel.send(embed=em)
            else:
                # failedOps += 1  # Can't be used. Variable is not defined here.
                print(f"Could not find #{variables['modmail']['channel']} in {bot.get_guild(guildID).name}."
                      "Can not use modmail functionality.")


@bot.event
async def on_member_join(member):
    await joinLeaveChannel.send(f"Join - {member.mention}, account created at {member.created_at}."
                                f"ID {member.id}. {len(member.guild.members)} members.")


@bot.event
async def on_member_remove(member):
    await joinLeaveChannel.send(f"Leave - {member.name}. ID {member.id}."
                                f"{len(member.guild.members)} members.")


@bot.event
async def on_member_ban(guild, member):
    await joinLeaveChannel.send(f"Ban - {member.name}, ID {member.id}."
                                f"Joined at {member.joined_at}.")

if __name__ == '__main__':
    hadError = False
    coglist = []

    for root, directories, files in os.walk("cogs"):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filepath.endswith(".py"):
                coglist.append(filepath.split(".py")[0].replace("\\", "."))

    for cog in coglist:
        try:
            bot.load_extension(cog)
            print(f'Loaded {cog} successfully')
        except Exception:
            # raise Exception
            print(f"Failed to load cog: {cog}")
            failedOps += 1
            hadError = True
    if hadError:
        print("Error during cog loading.")
    else:
        print("Successfully loaded all cogs.")
    bot.run(variables["token"], bot=True, reconnect=True)
