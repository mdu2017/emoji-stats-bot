import asyncio
import discord
from discord.ext import commands
from discord.emoji import Emoji

token = open("token.txt", "r").read()  # read token from txt file
emojiList = dict()  # dictionary, key-value pairs

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
    if emotestring == "pb":
        return emojiList.get("pigboon")
    if emotestring == "bb":
        return emojiList.get("baboon")
    if emotestring == "smtb":
        return emojiList.get("smartboon")


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


# Pigboon emote X times (.bb <num>)
@client.command()
async def bb(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="bb")
    await displayEmotes(ctx, amount, emoji)


# Pigboon emote X times (.bb <num>)
@client.command()
async def smtb(ctx, amount=1):
    emoji = await getEmote(ctx, emotestring="smtb")
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
    if amount < 1 or amount > 10:
        await ctx.send('Error: amount needs to be between 1-10')
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
