import unicodedata
from itertools import cycle

# Database password
pswd = open('passwd.txt', 'r').read()

# read token from txt file
token = open("token.txt", "r").read()

# map for list of emojis + random reactList
emojiList = dict()
randReactList = list()

# Tuples with reacts that are usually paired together
smartReacts = list(tuple())
dumbReacts = list(tuple())

weightedList = ['True', 'False', 'True', 'True', 'False']
cannedResponses = ['Mmm...', 'Yeah Yeah', 'Sure Sure',
                   'Perhaps...', 'It\'s in your pants!',
                   'Mangos!', 'Yu\'s!', 'Dominos!',
                   'Low Crack!', 'Guessed!', 'Made!']

# List of unicode emojis
THUMBSUP = '\U0001F44D'
THUMBSDOWN = '\U0001F44E'
ROFL = '\U0001F923'
DEVIL = '\U0001F608'
IMP = '\U0001F47F'
DASH = '\U0001F4A8'
TROLL = '\U0001F47A'
SIDEPIG = '\U0001F416'
TORNADO = '\U0001F32A'
FIRE = '\U0001F525'
FISH = '\U0001F3A3'
PIZZA = '\U0001F355'
HOTPEPPER = '\U0001F336'

fpdefault = open('plain.png', 'rb')
fp1 = open('smartboon.jpg', 'rb')
fp2 = open('pigboon.jpg', 'rb')
fp3 = open('redhat.jpg', 'rb')
fp4 = open('knightboon.jpg', 'rb')
fp5 = open('spook.jpg', 'rb')
fp6 = open('dart.jpg', 'rb')

pfpdefault = fpdefault.read()
pfp1 = fp1.read()
pfp2 = fp2.read()
pfp3 = fp3.read()
pfp4 = fp4.read()
pfp5 = fp5.read()
pfp6 = fp6.read()

# customProfPics = cycle([pfp1, pfp2, pfp3, pfp4, pfp5, pfp6])

customStatus = cycle([f'Dominos {PIZZA}', f'Eating Mangos! {TROLL}', f'Nap Time {FISH}', f'Idle', 'Memes'])


async def loadEmotes(client):
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
    emojiList['confused'] = emojiList.pop('confusedbb')

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
async def getEmote(emotestring):
    return emojiList.get(emotestring)

