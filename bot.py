import asyncio
import random
import re
import os
from const import *

import discord
from discord.ext import commands

# read token from txt file
token = open("token.txt", "r").read()

# Command prefix is .
client = commands.Bot(command_prefix='.')


@client.command(brief='(ex: .load <cogName>)')
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    print(f'{extension} LOADED')


@client.command(brief='(ex: .unload <cogName>)')
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print(f'{extension} unloaded')


@client.command(brief='(ex: .reload <cogName>)')
async def reload(ctx, extension):
    # client.unload_extension(f'cogs.{extension}')
    # client.load_extension(f'cogs.{extension}')
    client.reload_extension(f'cogs.{extension}')
    print(f'{extension} was reloaded')


# Loads all cogs in the cogs folder
for file in os.listdir('./cogs'):
    if file.endswith('.py'):
        client.load_extension(f'cogs.{file[:-3]}')  # Trim .py extension off of string
        print(f'{file} was loaded')

@client.event
async def on_ready():
    print('Main file ready')
    await client.change_presence(activity=discord.Game(f'Dominos! {PIZZA}'), status=discord.Status.online)

@client.event
async def on_member_join(member):  # method expected by client. This runs once when connected
    print(f'{member} has joined the server')  # notification of login.


@client.event
async def on_member_remove(member):
    print(f'{member} has quit! Boo!')


@client.event
async def on_message(message):
    ctx = await client.get_context(message)

    # Make sure bot doesn't respond its own message
    if message.author == client.user:
        return

    # If message is a command, process it and exit
    if ctx.valid:
        await client.process_commands(message)
        return

    # If bot receives a DM, handle separately and end
    if isinstance(ctx.channel, discord.channel.DMChannel):
        randResponse = random.choice(cannedResponses)
        await ctx.send(f'{randResponse}')
        return

    # Exit if in serious channel or debate channel
    if ctx.channel.name == 'serious' or ctx.channel.name == 'baboons-of-pig-york':
        return

    msg = message.content  # message string

    # if message contains some text, or if it's only emotes
    pattern = re.compile('[a-zA-Z0-9 .\\?]+')
    shouldReact = False
    if pattern.match(msg) and len(msg) > 35:
        # print('Contains text message')
        shouldReact = True
    else:
        # print('only emotes')
        shouldReact = False

    # Uses a weighted list to pick between smart/dumb reacts
    option = random.choice(weightedList)
    if option == 'True':
        tup = random.choice(smartReacts)
    else:
        tup = random.choice(dumbReacts)

    # Reacts if not all emotes
    if shouldReact:
        await message.add_reaction(tup[0])  # Calls add_reaction() on message
        await message.add_reaction(tup[1])


@client.command(brief='Put bot to sleep')
async def sleep(ctx):
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name='Sleeping'), status=discord.Status.idle, afk=True)
    await ctx.channel.purge(limit=1)


@client.command(brief='Wake up the bot')
async def awake(ctx):
    await client.change_presence(activity=discord.Game(f'Dominos {PIZZA}'), status=discord.Status.online, afk=False)
    await ctx.channel.purge(limit=1)


# Function name is the command name (ex: .ping)
@client.command(brief='Displays network latency')
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)}ms')


# Clears an X amount of messages from the channel (default 3) - (.cls or .clear)
@client.command(brief='Remove <X> amt of messages', aliases=['cls'])
async def clear(ctx, amount=3):
    if amount < 1 or amount > 25:
        await ctx.send('Error: amount needs to be between 1-25')
        return

    # remove clear command
    await ctx.channel.purge(limit=1)

    # remove <amount> of messages
    await ctx.channel.purge(limit=amount)

# Logs out and closes connection
@client.command(brief='Logs the bot out')
async def shutitoff(ctx):
    await ctx.channel.purge(limit=1)
    await client.logout()

client.run(token)  # token from text file
