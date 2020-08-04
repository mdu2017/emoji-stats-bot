
import discord
import os
import random

# print(discord.__version__)  # check to make sure at least once you're on the right version!
from discord.ext import commands

token = open("token.txt", "r").read()  # read token from txt file

client = discord.Client()  # starts the discord client.

#Command prefix is !bbn or !Bbn
bot = commands.Bot(command_prefix=("!bbn", "!Bbn"), case_insensitive=True)

@bot.command()
async def echo(ctx, arg):
	if arg == "baboon1":
		await ctx.send("B1")
	elif arg == "baboon2":
		await ctx.send("B2")


@client.event  # event decorator/wrapper. More on decorators here: https://pythonprogramming.net/decorators-intermediate-python-tutorial/
async def on_ready():  # method expected by client. This runs once when connected
    print(f'We have logged in as {client.user}')  # notification of login.


@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, ARE YOU READY TO FEED YOUR ASS OFF?'
    )
    await member.channel.send(
        f'Hi {member.name}, ARE YOU READY TO FEED YOUR ASS OFF?'
    )

@client.event
async def on_message(message):  # event that happens per any message.

	# This prevents the bot from recursively printing its own message
	if message.author == client.user:
		return

	funny_quotes = ['ARE YOU READY TO FEED YOUR ASS OFF?', 'hi neighbor', 'got2gitgud kid', 'hi']

	if message.content != ' ':
		response = random.choice(funny_quotes)
		await message.channel.send(response)
	elif message.content == '!hi':
		await message.channel.send('hi' + {message.name})

client.run(token)  # token from text file
