
import discord
# print(discord.__version__)  # check to make sure at least once you're on the right version!

token = open("token.txt", "r").read()  # read token from txt file

client = discord.Client()  # starts the discord client.


@client.event  # event decorator/wrapper. More on decorators here: https://pythonprogramming.net/decorators-intermediate-python-tutorial/
async def on_ready():  # method expected by client. This runs once when connected
    print(f'We have logged in as {client.user}')  # notification of login.


@client.event
async def on_message(message):  # event that happens per any message.

    # each message has a bunch of attributes. Here are a few.
    # check out more by print(dir(message)) for example.
    print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

    if len(message) != 0:
    	await message.channel.send("ok")

# @client.event
# async def on_message(message):  # event that happens per any message.
#     print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
#     if str(message.author) == "Sentdex#7777" and "hello" in message.content.lower():
#         await message.channel.send('Hi!')

client.run(token)  # token from text file
