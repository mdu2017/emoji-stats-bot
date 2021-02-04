# Emoji Stats Discord Bot
Discord Bot that analyzes emoji usage and reactions in a Discord server.

Written in Python 3

Usage:

1. Open Discord application

2. git clone https://github.com/mdu2017/emoji-stats-bot.git

3. Navigate to directory you just cloned

4. Run python script using: 'python bot.py' (Will need python 3+)

# Commands

| Command        | Description  |
| ------------- |:-------------:|
| topemojis  | Shows the top 5 most popular emojis |
| useremojis \<username\> \<mode\>  | Shows user's most used emojis |
| fullmsgstats | Shows stats for all emojis used in messages |
| favemoji \<username\>  | Shows a user\'s favorite emoji |
| emojistoday | Show all emojis used in the past day |
| chstats \<channel_name\> | Shows a channel's top 3 most popular reactions/emojis |
| fullchstats | Shows the most popular reaction/emoji for every channel |
| topreacts  | Shows the top 5 most popular reactions |
| userreacts \<username\> \<mode\>  | Shows a user's most used reactions |
| favreact \<username\>  | Shows a user's favorite reaction |
| fullreactstats | Shows stats on all reactions used |
| reactstoday | Show all reactions used in the past day |

\<username\> - can use Discord nickname or mention user

\<channel_name\> - Discord Text Channel name (no # needed)

\<mode\> - unicode or custom (e.g "!e useremojis @user1 custom")
