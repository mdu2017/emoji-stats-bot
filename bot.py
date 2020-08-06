import asyncio
import random
import re

import discord
import self
from discord.ext import commands
from discord.emoji import Emoji
from discord.utils import get

token = open("token.txt", "r").read()  # read token from txt file
emojiList = dict()  # dictionary, key-value pairs
randReactList = list()  # List of random emotes

# Tuples with reacts that are usually paired together
smartReacts = list(tuple())
dumbReacts = list(tuple())  # Pairs of reacts

# List of unicode emojis
THUMBSUP = '\U0001F44D'
THUMBSDOWN = '\U0001F44E'
ROFL = '\U0001F923'
DEVIL = '\U0001F608'
IMP = '\U0001F47F'
DASH = '\U0001F4A8'
TROLL = '\U0001F47A'
SIDEPIG = '\U0001F416'

cannedResponses = ['Mmm...', 'Yeah Yeah', 'Sure Sure',
                   'Perhaps...', 'It\'s in your pants!',
                   'Mangos!', 'Yu\'s!', 'Dominos!',
                   'Low Crack!', 'Guessed!', 'Made!']

# TODO: Add reactions based on messages
# TODO: Take in variable num of commands and display on same line
# TODO (separate): Add gamerBot to gg server (outputs links to different online games)
# TODO: Add random response to jokes...

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
    return emojiList.get(emotestring)


# Loads and populates emojiList
@client.event
async def on_ready():
    print('Bot ready')
    for guild in client.guilds:
        for emoji in guild.emojis:
            emojiList.setdefault(emoji.name, emoji)

    # Shorten string key
    emojiList['pb'] = emojiList.pop('pigboon')
    emojiList['bb'] = emojiList.pop('baboon')
    emojiList['smtb'] = emojiList.pop('smartboon')
    emojiList['blue'] = emojiList.pop('bluebaboon')
    emojiList['red'] = emojiList.pop('redbaboon')
    emojiList['spook'] = emojiList.pop('spooked')
    emojiList['cowboy'] = emojiList.pop('cowboybaboon')
    emojiList['chef'] = emojiList.pop('chefboon')
    emojiList['smug'] = emojiList.pop('smug')
    emojiList['somm'] = emojiList.pop('sommelier')
    emojiList['rspig'] = emojiList.pop('researchpig')
    emojiList['smtpig'] = emojiList.pop('Pigsuit')
    emojiList['kn'] = emojiList.pop('knightboon')

    # Add list of emotes for random react (basic
    randReactList.append(emojiList.get('pb'))
    randReactList.append(emojiList.get('bb'))
    randReactList.append(emojiList.get('smtb'))
    randReactList.append(emojiList.get('rspig'))
    randReactList.append(emojiList.get('somm'))
    randReactList.append(emojiList.get('smtpig'))

    # Add list of tuples (smart reacts)
    smartReacts.append((THUMBSUP, emojiList.get('smtb')))
    smartReacts.append((emojiList.get('rspig'), emojiList.get('smtpig')))
    smartReacts.append((emojiList.get('somm'), emojiList.get('smtb')))
    smartReacts.append((emojiList.get('smtb'), emojiList.get('rspig')))
    smartReacts.append((emojiList.get('smtpig'), emojiList.get('smtb')))

    # Add list of tuples (dumb reacts)
    dumbReacts.append((emojiList.get('pb'), emojiList.get('bb')))
    dumbReacts.append((emojiList.get('bb'), TROLL))
    dumbReacts.append((emojiList.get('pb'), THUMBSDOWN))
    dumbReacts.append((emojiList.get('bb'), THUMBSDOWN))
    dumbReacts.append((emojiList.get('chef'), emojiList.get('bb')))
    dumbReacts.append((emojiList.get('kn'), emojiList.get('bb')))


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
    if pattern.match(msg) and len(msg) > 40:
        # print('Contains text message')
        shouldReact = True
    else:
        # print('only emotes')
        shouldReact = False

    # TODO: Currently uses reacts from smart list
    listDiff = ['True', 'False', 'True', 'True', 'False']
    option = random.choice(listDiff)
    if option == 'True':
        tup = random.choice(smartReacts)
        emoji1 = tup[0]
        emoji2 = tup[1]
    else:
        tup = random.choice(dumbReacts)
        emoji1 = tup[0]
        emoji2 = tup[1]

    # Reacts if not all emotes
    if shouldReact:
        await message.add_reaction(emoji1)  # Calls add_reaction() on message
        await message.add_reaction(emoji2)


# Swap react to smart react
@client.command()
async def swapdumb(ctx):
    count = 0
    async for message in ctx.channel.history(limit=3):
        if count == 1:
            await message.clear_reactions()  # Clear all reactions

            # Add dumb reacts
            dmb = random.choice(dumbReacts)
            await message.add_reaction(dmb[0])
            await message.add_reaction(dmb[1])

            # remove the command
            await ctx.channel.purge(limit=1)
            return

        count += 1


# Swap react to dumb react
@client.command()
async def swapsmart(ctx):
    count = 0
    async for message in ctx.channel.history(limit=3):
        if count == 1:
            await message.clear_reactions()  # Clear all reactions

            # Add dumb reacts
            smt = random.choice(smartReacts)
            await message.add_reaction(smt[0])
            await message.add_reaction(smt[1])

            # remove the command
            await ctx.channel.purge(limit=1)
            return

        count += 1

# Swap react to red baboon reacts
@client.command()
async def swapred(ctx):
    count = 0
    # Gets the last 3 messages
    async for message in ctx.channel.history(limit=3):
        if count == 1:
            await message.clear_reactions()  # Clear all reactions

            await message.add_reaction(emojiList.get('red'))
            await message.add_reaction(emojiList.get('cowboy'))

            # remove the command
            await ctx.channel.purge(limit=1)
            return

        count += 1

# Swap react to blue baboon reacts
@client.command()
async def swapblue(ctx):
    count = 0
    async for message in ctx.channel.history(limit=3):
        if count == 1:
            await message.clear_reactions()  # Clear all reactions

            await message.add_reaction(emojiList.get('blue'))
            await message.add_reaction(SIDEPIG)

            # remove the command
            await ctx.channel.purge(limit=1)
            return

        count += 1

# Swap react to dumb react
@client.command()
async def default(ctx):
    count = 0
    async for message in ctx.channel.history(limit=3):
        if count == 1:
            await message.clear_reactions()  # Clear all reactions

            # default baboon react
            await message.add_reaction(emojiList.get('bb'))

            # remove the command
            await ctx.channel.purge(limit=1)
            return

        count += 1

@client.command()
async def blowpig(ctx):
    await ctx.channel.purge(limit=1)
    smtb = emojiList.get('smtb')
    await ctx.send(f'{smtb} {DASH} {DASH} {SIDEPIG}')

@client.command()
async def blowbb(ctx):
    await ctx.channel.purge(limit=1)
    smtpig = emojiList.get('smtpig')
    bb = emojiList.get('bb')
    await ctx.send(f'{smtpig} {DASH} {DASH} {bb}')


# Enables bot to play Guess My Number
@client.command(brief='Guess a number between 1-10')
async def guessgame(ctx):
    tries = 3
    num = random.randint(1, 10)
    print(num)
    await ctx.send(f'Welcome! I have a hidden number between 1-10. Make your best guess! You have {tries} tries.')

    while tries > 0:
        # guess = None
        try: # Need check for await b/c we only want to check messages from person who initiated the game
            guess = await client.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
            pass
        except Exception as e:
            await ctx.send(f'You took too long to respond. Game over.')

        guessedNum = int(guess.content)
        tries -= 1

        if guessedNum > num:
            await ctx.send(f'Your number is too high! {tries} tries left.')
        elif guessedNum < num:
            await ctx.send(f'Your number is too low! {tries} tries left.')
        else:
            await ctx.send('Well done... It seems I\'ve been guessed!')
            await ctx.send(f'{emojiList.get("smtpig")} {emojiList.get("smtb")}')
            return

    if tries == 0:
        await ctx.send('You failed to guess... Made!')
        await ctx.send(f'{emojiList.get("kn")} {DASH} {DASH} {SIDEPIG}')


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
                await ctx.send(f'{nickname} has IQ of a 160! {emojiList.get("smtb")}')
            if nickname == 'Pigboon':
                await ctx.send(f'{nickname} has an IQ of 90 {emojiList.get("bb")}')


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



client.run(token)  # token from text file
