import asyncio
import discord
import self
from discord.ext import commands
from discord.emoji import Emoji

token = open("token.txt", "r").read()  # read token from txt file
emojiList = dict()  # dictionary, key-value pairs

# TODO: filter emojiList string keys to shortened version in on_ready
# TODO: Add reactions based on messages
# TODO: Take in variable num of commands and display on same line
# TODO (separate): Add gamerBot to gg server (outputs links to different online games)

# Command prefix is .
client = commands.Bot(command_prefix='.')

# Helper function to print emotes
async def displayEmotes(ctx, amount, emoji):
    one = '{0}'.format(emoji)
    two = '{0} {1}'.format(emoji, emoji)
    three = '{0} {1} {2}'.format(emoji, emoji, emoji)

    # Remove the actual clear command
    await ctx.channel.purge(limit=1)

    # Print <amt> of emotes
    if amount == 1:
        await ctx.send(one)
    elif amount == 2:
        await ctx.send(two)
    elif amount == 3:
        await ctx.send(three)
    else:
        await ctx.send(one)


# Returns specific emoji based on which function has called it (helper function)
async def getEmote(ctx, emotestring):
    if emotestring == 'pb':
        return emojiList.get('pigboon')
    if emotestring == 'bb':
        return emojiList.get('baboon')
    if emotestring == 'smtb':
        return emojiList.get('smartboon')
    if emotestring == 'blue':
        return emojiList.get('bluebaboon')
    if emotestring == 'red':
        return emojiList.get('redbaboon')
    if emotestring == 'spook':
        return emojiList.get('spooked')
    if emotestring == 'cowboy':
        return emojiList.get('cowboybaboon')
    if emotestring == 'chef':
        return emojiList.get('chefboon')
    if emotestring == 'smug':
        return emojiList.get('smug')
    if emotestring == 'somm':
        return emojiList.get('sommelier')
    if emotestring == 'rspig':
        return emojiList.get('researchpig')
    if emotestring == 'smtpig':
        return emojiList.get('Pigsuit')


@client.event
async def on_ready():
    print('Bot ready')
    for guild in client.guilds:
        for emoji in guild.emojis:
            emojiList.setdefault(emoji.name, emoji)


@client.event
async def on_member_join(member):  # method expected by client. This runs once when connected
    print(f'{member} has joined the server')  # notification of login.


@client.event
async def on_member_remove(member):
    print(f'{member} has quit! Boo!')


# Function name is the command name (ex: .ping)
@client.command()
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)}ms')


# IQ memes (.iq)
@client.command()
async def iq(ctx):
    for guild in client.guilds:
        for member in guild.members:
            nickname = member.nick
            if nickname == 'Bull':
                await ctx.send(f'{nickname} has IQ of a 160!')
            if nickname == 'Pigboon':
                await ctx.send(f'{nickname} has an IQ of 90')

# Pigboon emote X times (.pb <num>)
@client.command()
async def pb(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="pb")
    await displayEmotes(ctx, amount, emoji)

# Baboon emote X times (.bb <num>)
@client.command()
async def bb(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="bb")
    await displayEmotes(ctx, amount, emoji)

# smartboon emote X times (.smtb <num>)
@client.command()
async def smtb(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="smtb")
    await displayEmotes(ctx, amount, emoji)

# bluebaboon emote X times (.blue <num>)
@client.command()
async def blue(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="blue")
    await displayEmotes(ctx, amount, emoji)

# redbaboon emote X times (.red <num>)
@client.command()
async def red(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="red")
    await displayEmotes(ctx, amount, emoji)

# spook emote X times (.spook <num>)
@client.command()
async def spook(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="spook")
    await displayEmotes(ctx, amount, emoji)

# Cowboy emote X times (.cowboy <num>)
@client.command()
async def cowboy(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="cowboy")
    await displayEmotes(ctx, amount, emoji)

# chef emote X times (.chef <num>)
@client.command()
async def chef(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="chef")
    await displayEmotes(ctx, amount, emoji)

# smug emote X times (.smug <num>)
@client.command()
async def smug(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="smug")
    await displayEmotes(ctx, amount, emoji)

# somm emote X times (.somm <num>)
@client.command()
async def somm(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="somm")
    await displayEmotes(ctx, amount, emoji)

# rspig emote X times (.rspig <num>)
@client.command()
async def rspig(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="rspig")
    await displayEmotes(ctx, amount, emoji)

# smtpig emote X times (.smtpig <num>)
@client.command()
async def smtpig(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="smtpig")
    await displayEmotes(ctx, amount, emoji)


# Print list of emojis (.em or .emotes)
@client.command(aliases=['em'])
async def emotes(ctx):
    for guild in client.guilds:
        for emoji in guild.emojis:
            await ctx.send(f'{emoji * 3}, {emoji.name}')


# Clears an X amount of messages from the channel (default 3) - (.cls or .clear)
@client.command(aliases=['cls'])
async def clear(ctx, amount=3):
    if amount < 1 or amount > 25:
        await ctx.send('Error: amount needs to be between 1-25')
        return

    # remove clear command
    await ctx.channel.purge(limit=1)

    # remove <amount> of messages
    await ctx.channel.purge(limit=amount)


# Type .joke for an "in your pants joke"
@client.command()
async def joke(ctx):
    await ctx.send('It\'s in your pants!')


# for guild in client.guilds:
#     for chan in guild.channels:
#         await ctx.send(f'{chan}')


client.run(token)  # token from text file
