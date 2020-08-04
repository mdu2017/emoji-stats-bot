import discord
from discord.ext import commands
from discord.emoji import Emoji

token = open("token.txt", "r").read()  # read token from txt file

#Command prefix is .
client = commands.Bot(command_prefix='.')

# @bot.command()
# async def echo(ctx, arg):
# 	if arg == "baboon1":
# 		await ctx.send("B1")
# 	elif arg == "baboon2":
# 		await ctx.send("B2")

@client.event
async def on_ready():
    print('Bot ready')

@client.event
async def on_member_join(member):  # method expected by client. This runs once when connected
    print(f'{member} has joined the server')  # notification of login.

@client.event
async def on_member_remove(member):
    print(f'{member} has quit! Boo!')

@client.command()
async def ping(ctx):
    await ctx.send('Test')

#Type .joke for an "in your pants joke"
@client.command()
async def joke(ctx):
    await ctx.send('It\'s in your pants!')


client.run(token)  # token from text file
