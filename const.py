import unicodedata
from itertools import cycle
import psycopg2
from psycopg2 import pool
import discord

# Emojis for turning page back/forward
right_arrow = '\U000025B6'
left_arrow = '\U000025C0'
# right_arrow = '\U000027A1'
# left_arrow = '\U00002B05'
arrow_end = '\U000023ED'
arrow_start = '\U000023EE'

file = open('dbcred.txt', 'r')
credList = file.read().splitlines()
usr = credList[0]
pwd = credList[1]
host = credList[2]
port = credList[3]
db = credList[4]

# Setup db connection at start
ps_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    user=usr,
    password=pwd,
    host=host,
    port=port,
    database=db
)

if ps_pool:
    print('Connection successful')
else:
    print('error bad connection')

# Database credentials
# pswd = open('passwd.txt', 'r').read()

emoji_image_url = 'https://images.emojiterra.com/google/android-10/512px/1f43c.png'

# read token from txt file
token = open("token.txt", "r").read()

# Various statuses for the bot
custom_status = cycle([f'!e help'])

# Channels to disable bot commands for
rm_channels = []


def getEmojiName(key):
    name = 'EMOJI'
    try:
        name = unicodedata.name(key)
    except Exception as ex:
        print(f'Error: {ex}')

    return name


# Used in all the commands to process data
def processListMsg(client, record, emojiSum):
    finalList = []
    data = dict(record)  # convert record to dictionary

    # Convert emoji into discord representation
    for key in data:
        keystr = str(key)
        percentage = round((data[key] / emojiSum) * 100, 2)
        spacing = ''
        if len(finalList) == 0:  # Spacing for first item
            spacing = ' '
        else:
            spacing = ''

        if '<' in keystr:  # If it's a custom emoji, parse ID
            startIndex = keystr.rindex(':') + 1
            endIndex = keystr.index('>')
            id = int(key[startIndex:endIndex])
            name = 'EMOJI'
            currEmoji = client.get_emoji(id)
            if currEmoji is not None:
                name = currEmoji.name
            finalList.append(
                f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of use.')

        else:
            temp = getEmojiName(key)  # TODO: Some emojis won't have a name so 'EMOJI' is by default
            finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of use.')

    return finalList


def processListChn(client, record, emojiSum, typeStr, channel_name):
    data = dict(record)
    finalList = []

    # Convert emoji into discord representation
    for key in data:
        keystr = str(key)
        percentage = round((data[key] / emojiSum) * 100, 2)
        spacing = ''
        if len(finalList) == 0:  # Spacing for first item
            spacing = ' '
        else:
            spacing = ''

        if '<' in keystr:  # If it's a custom emoji, parse ID
            startIndex = keystr.rindex(':') + 1
            endIndex = keystr.index('>')
            id = int(key[startIndex:endIndex])
            name = 'EMOJI'
            currEmoji = client.get_emoji(id)
            if currEmoji is not None:
                name = currEmoji.name
            finalList.append(
                f'{spacing}{currEmoji} - {name} used ({data[key]}) times '
                f'| {percentage}% of {typeStr} used in #{channel_name}')

        else:
            temp = getEmojiName(key)  # TODO: Some reacts won't have a name so 'EMOJI' is by default
            finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times '
                             f'| {percentage}% of {typeStr} used in #{channel_name}')

    return finalList


def processListRct(client, record, emojiSum):
    data = dict(record)  # convert record to dictionary
    finalList = []

    # Convert emoji into discord representation
    for key in data:
        keystr = str(key)
        percentage = round((data[key] / emojiSum) * 100, 2)
        spacing = ''
        if len(finalList) == 0:  # Spacing for first item
            spacing = ' '
        else:
            spacing = ''

        if '<' in keystr:  # If it's a custom emoji, parse ID
            startIndex = keystr.rindex(':') + 1
            endIndex = keystr.index('>')
            id = int(key[startIndex:endIndex])
            name = 'EMOJI'
            currEmoji = client.get_emoji(id)
            if currEmoji is not None:
                name = currEmoji.name
            finalList.append(
                f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of all reacts.')

        else:
            temp = getEmojiName(key)  # TODO: Some reacts won't have a name so 'EMOJI' is by default
            finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of all reacts.')

    return finalList


# Gets username info in commands involving usernames
def processName(client, ctx, user_name):
    user = None
    username = None
    userID = None
    valid = True

    if user_name == '':
        return None, None, None, False

    # If mentioned, get by id, otherwise search each member's nickname
    if '@' in user_name and '!' in user_name:
        idStr = str(user_name)
        idStr = idStr[idStr.index('!') + 1: idStr.index('>')]
        userID = int(idStr)
        user = client.get_user(userID)
        username = user.name
    else:
        for guild in client.guilds:
            for member in guild.members:
                nickname = member.nick
                if str(user_name) == str(nickname):
                    user = member
                    username = member.name
                    userID = member.id
                    break

    # Check for empty user
    if user is None:
        valid = False

    return user, username, userID, valid


def processChName(client, ctx, ch, option):
    valid_channel = True
    valid_option = True
    channel_name = ch

    # If no channel name specified, use current channel. If invalid channel name, exit
    if ch == '':
        channel_name = ctx.channel.name
    else:
        found = False
        for channel in ctx.guild.text_channels:
            if channel.name == ch:
                found = True
                channel_name = ch
                break
        if not found:
            valid_channel = False

    # handle invalid type
    if option != 'react' and option != 'message':
        valid_option = False

    # Used in formatted print
    if option == 'react':
        typeStr = 'reactions'
    else:
        typeStr = 'emojis'

    return channel_name, typeStr, valid_channel, valid_option


def fullChStatsResult(reactData, emojiData):
    filteredList = dict()  # Key to list of formatted strings (channel name -> f'emoji, cnt')

    # Add emoji data to filtered list
    for tup in emojiData:
        chname = tup[0]
        emoji = tup[1]
        cnt = tup[2]

        # If channel name exists, add the emoji
        if chname not in filteredList:
            filteredList[chname] = list()

        filteredList[chname].append(f'Most used emoji: {emoji} - used ({cnt}) times\n\n')

    # Add reaction data filtered list
    for tup in reactData:
        chname = tup[0]
        emoji = tup[1]
        cnt = tup[2]

        # If channel name exists, add the reaction
        if chname not in filteredList:
            filteredList[chname] = list()

        filteredList[chname].append(f'Most used reaction: {emoji} - used ({cnt}) times\n\n')

    embed = discord.Embed(colour=discord.Colour.blurple())
    embed.set_thumbnail(url=emoji_image_url)
    for key in filteredList:
        info = ''
        for tup in filteredList[key]:
            info += tup
        info += '\n'

        embed.add_field(name=f'#{key}', value=f'{info}', inline=False)


    return embed


# Gets database connection and cursor
def getConnection():
    # Get db connection and check
    conn = ps_pool.getconn()
    if conn:
        cursor = conn.cursor()
    else:
        print('Error getting connection from pool')
        return

    return conn, cursor


# Get the final results in a single message
def getResult(finalList, ndx=1):
    return '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=ndx))
