"""" shit's broken but the general idea is there

import discord

client = discord.Client()

class Logger:
    @client.event
    async def on_message_edit(before, after):
        result = '''
        Edited message with ID: {}
        Before: {}
        After: {}'''.format(after.id, before.content, after.content)
        await client.send_message("should be configurable by admins - todo", result)

def setup(bot):
    bot.add_cog(Logger(bot))

"""
