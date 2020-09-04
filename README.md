# Emoji Stats Discord Bot
Discord Bot that analyzes emoji usage and reactions in a Discord server.

Written in Python 3 and connected with a PostgreSQL database.

Usage:

1. Open Discord application

2. git clone https://github.com/mdu2017/emoji-stats-bot.git

3. Navigate to directory you just cloned

4. Run python script using: 'python bot.py' (Will need python 3+)

# Commands
| Commands                        | Description |
| ------------- |:-------------:| 
| ping                            | Shows network ping |
| topreacts                       | Shows the 5 most popular reactions |
| userreacts (username) (mode)    | Shows a user's most used reactions - mode is optional (unicode or custom) |
| favreact (username)             | Shows a user's favorite reaction |
| fullreactstats (mode)           | Shows stats on all reactions used - mode is optional (unicode or custom) |
| topemojis                       | Shows the 5 most popular emojis |
| useremojis (username) (mode)    | Shows user's most used emojis - mode is optional (unicode or custom) |
| favemoji (username)             | Shows a user's favorite emoji |
| fullmsgstats (mode)             | Shows stats for all emojis used in messages - mode is optional (unicode or custom) |
| chstats (channel_name) (option) | Shows a channel's top 3 most popular reactions/emojis |
| fullchstats                     | Shows the most popular reaction/emoji for every channel |

(username) - can use Discord nickname or mention

(channel_name) - Discord Text Channel name (no # needed)

(option) -'react' or 'message'

Libraries used:

discord.py
psycopg2

