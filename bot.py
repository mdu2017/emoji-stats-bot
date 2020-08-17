import os
from const import *
import asyncpg
from discord.ext import commands, tasks

# Command prefix is .
client = commands.Bot(command_prefix='.')


# Create connection pool
async def create_db_pool():
    client.pg_con = await asyncpg.create_pool(database='emojistats', user='postgres', password=pswd)


@client.command(brief='(ex: .load <cogName>)')
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    print(f'{extension} LOADED')


@client.command(brief='(ex: .unload <cogName>)')
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(f'{extension} unloaded')


# Reload command for cog
@client.command(brief='(ex: .reload <cogName>)')
async def reload(ctx, extension):
    client.reload_extension(f'cogs.{extension}')
    print(f'{extension} was reloaded')


# Loads all cogs in the cogs folder
for file in os.listdir('./cogs'):
    if file.endswith('.py'):
        client.load_extension(f'cogs.{file[:-3]}')  # Trim .py extension off of string
        # print(f'{file} was loaded')


# Loads all custom emojis into list
@client.event
async def on_ready():
    print('Main file ready, loading emotes')
    # await loadEmotes(client)


client.loop.run_until_complete(create_db_pool())  # Keep db pool open
client.run(token)  # token from text file
