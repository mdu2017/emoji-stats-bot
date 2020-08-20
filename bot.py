import os
from const import *
from discord.ext import commands
import discord

# Command prefix is .
client = commands.Bot(command_prefix='!e ')
client.remove_command('help')

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


# Loads all custom emojis into list
@client.event
async def on_ready():
    conn = ps_pool.getconn()

    if conn:
        cursor = conn.cursor()
        try:
            # Create initial tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channel (
                chname    VARCHAR(50),
                reactid   TEXT, 
                cnt       int,
                emojitype VARCHAR(20),
                guildid   BIGINT,
                PRIMARY KEY(chname, reactid, emojitype, guildid)
            )""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                userid VARCHAR(100) NOT NULL,
                reactid TEXT,
                cnt		INT,
                emojitype VARCHAR(20),
                guildid   BIGINT,
                PRIMARY KEY(userid, reactid, emojitype, guildid)
            )""" )
            print(f'Tables created successfully')
            conn.commit()
        except Exception as e:
            print('Error creating tables')

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Return connection to pool


# client.loop.run_until_complete(create_db_pool())  # Keep db pool open
client.run(token)  # token from text file
