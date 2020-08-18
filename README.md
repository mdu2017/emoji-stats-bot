# Emoji Stats Discord Bot
Discord Bot that analyzes emoji usage and reactions in a Discord server.

Written in Python 3 and connected with a PostgreSQL database.

Usage:

1. Open Discord application

2. git clone https://github.com/mdu2017/emoji-stats-bot.git

3. Navigate to directory you just cloned

4. Run python script using: 'python bot.py' (Will need python 3+)

# Commands

| Command        | Description  |
| ------------- |:-------------:| 
| .ping       | shows network ping |
| .cls \<num\>      | Deletes the <num> most recent messages  | 
| .topreacts \<amt\>  | Shows the X most popular reactions | 
| .userreacts \<username\>  | Shows a user's most used reactions| 
| .fullreactstats | Shows stats on all reactions used| 
| .topemojis \<amt\>  | Shows the X most popular emojis | 
| .useremojis \<username\>  | Shows user's most used emojis | 
| .fullmsgstats \<amt\>  | Shows stats for all emojis used in messages | 
| .channelstats \<channel_name\> \<option\>  | Shows a channel's top 3 most popular reactions/emojis |
| .fullchstats | Shows the most popular reaction/emoji for every channel | 

\<amt\> - is any number between 1-20 

\<username\> - can use Discord nickname or mention

\<channel_name\> - Discord Text Channel name (no # needed)

\<option\> -'react' or 'message'

Libraries used:
discord.py
psycopg2
