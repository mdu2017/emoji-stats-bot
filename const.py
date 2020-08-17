import unicodedata
from itertools import cycle

# Database credentials
pswd = open('passwd.txt', 'r').read()
# infoFile = open('db.txt', 'r')
# db_host = infoFile.readline()
# db = infoFile.readline()
# db_user = infoFile.readline()
# pswd = infoFile.readline()


# read token from txt file
token = open("token.txt", "r").read()

# map for list of custom emojis in your server
emoji_list = dict()

# fp1 = open('yourProfilePic.jpg/png', 'rb')
# pfp1 = fp1.read()

# Various statuses for the bot
custom_status = cycle([f'Watching YouTube', f'Eating', f'Nap Time', f'.stats', 'Help'])

# Channels to disable bot commands for
rm_channels = []


# Loads a list of custom emojis for use
# async def loadEmotes(client):
#     for guild in client.guilds:
#         for emoji in guild.emojis:
#             emoji_list.setdefault(emoji.name, emoji)

    # NOTE: to get your emojis, call emojiList.get('emojiname')

def handleSpecialEmojis(key):
    name = 'EMOJI'
    try:
        name = unicodedata.name(key)
    except Exception as ex:
        print(f'Error: {ex}')

    return name
