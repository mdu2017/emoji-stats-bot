import unicodedata
from itertools import cycle
import psycopg2
from psycopg2 import pool

# Setup db connection at start
ps_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,
        user='tjazufgdgelrwg',
        password='52f31cc400aefb9dbb0dc7b88c71f8fb6ed9ffc515dc65617e9aad9dae92aa1d',
        host='ec2-54-158-122-162.compute-1.amazonaws.com',
        port='5432',
        database='d66tlan8f3srnu'
    )

if ps_pool:
    print('Connection successful')
else:
    print('error bad connection')

# Database credentials
# pswd = open('passwd.txt', 'r').read()

# read token from txt file
token = open("token.txt", "r").read()

# Various statuses for the bot
custom_status = cycle([f'Watching YouTube', f'Eating', f'Nap Time', f'.stats', 'Help'])

# Channels to disable bot commands for
rm_channels = []

def handleSpecialEmojis(key):
    name = 'EMOJI'
    try:
        name = unicodedata.name(key)
    except Exception as ex:
        print(f'Error: {ex}')

    return name
