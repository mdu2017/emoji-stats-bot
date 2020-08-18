import discord
from discord.ext import commands
from const import *


class Channel(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Channel cog ready')

    # Top 3 most popular emojis for reactions/messages for a channel (optional type)
    @commands.command(brief='''Top 3 emojis for reactions/messages 
                            (.channelstats OR.channelstats <channel_name> <option=message,react>)''')
    async def channelstats(self, ctx, ch='', option='message'):
        channel_name = None

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
                await ctx.send(f'Text Channel #{ch} was not found\nUsage: .channelstats <channel_name> <option>')
                return

        # handle invalid type
        if option != 'react' and option != 'message':
            await ctx.send(f'<option>(s) are: \'react\' OR \'message\'\nUsage: .channelstats <channel_name> <option>')
            return

        # Used in formatted print
        if option == 'react':
            typeStr = 'reactions'
        else:
            typeStr = 'emojis'

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        guild_id = ctx.guild.id

        # Grab top 3 most used emojis in a channel
        cursor.execute("""
            SELECT reactid, cnt FROM channel
            WHERE channel.chname = %s AND emojitype = %s AND guildid = %s
            ORDER BY cnt DESC LIMIT 3""", (channel_name, option, guild_id))
        record = cursor.fetchall()

        # Check for empty data
        if len(record) == 0:
            await ctx.send(f'No emoji data available for [#{channel_name}]')
            return

        # Grab total count of used emojis
        cursor.execute("""
            SELECT SUM(cnt) FROM channel 
            WHERE channel.chname = %s AND emojitype = %s
            AND guildid = %s""", (channel_name, option, guild_id))
        emojiSum = cursor.fetchone()
        emojiSum = int(emojiSum[0])

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
                currEmoji = self.client.get_emoji(id)
                if currEmoji is not None:
                    name = currEmoji.name
                finalList.append(
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times in [#{channel_name}] '
                    f'| {percentage}% of {typeStr} used in [#{channel_name}]')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some reacts won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times in [#{channel_name}] '
                                 f'| {percentage}% of {typeStr} used in [#{channel_name}]')


        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        await ctx.send(f'Top 3 {typeStr} used in [#{channel_name}]: \n {result}')

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # TODO (enhancement): Get most used emojis in the last week/month/day/year, etc.
    # @commands.command(brief='Most used emojis in the last <week/month/day/year>')
    # async def recentchstats(self, ctx):
    #     print()

    @commands.command(brief='display most popular emojis/reaction for each channel if available (.fullchstats)')
    async def fullchstats(self, ctx):

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        guild_id = ctx.guild.id

        sqlReacts = """SELECT c1.chname, c1.reactid, c1.cnt
            FROM channel as c1, (SELECT chname, MAX(cnt) FROM channel
                WHERE emojitype = 'react' AND guildid = %s GROUP BY chname) AS c2
            WHERE c1.chname = c2.chname AND c1.cnt = c2.max AND c1.emojitype = 'react' AND c1.guildid = %s
            ORDER BY c1.cnt DESC;"""
        sqlEmojis = """SELECT c1.chname, c1.reactid, c1.cnt
            FROM channel as c1, (SELECT chname, MAX(cnt) FROM channel
                WHERE emojitype = 'message' AND guildid = %s GROUP BY chname) AS c2
            WHERE c1.chname = c2.chname AND c1.cnt = c2.max AND c1.emojitype = 'message' AND c1.guildid = %s
            ORDER BY c1.cnt DESC;"""

        # Gather reaction data
        cursor.execute(sqlReacts, (guild_id, guild_id))
        reactData = cursor.fetchall()

        # Gather emoji data
        cursor.execute(sqlEmojis, (guild_id, guild_id))
        emojiData = cursor.fetchall()

        if len(reactData) == 0 and len(emojiData) == 0:
            await ctx.send('No reaction or emoji data available')
            return

        filteredList = dict()   #Key to list of formatted strings (channel name -> f'emoji, cnt')

        # Add reaction data filtered list
        for tup in reactData:
            chname = tup[0]
            emoji = tup[1]
            cnt = tup[2]

            # If channel name exists, add the reaction
            if chname not in filteredList:
                filteredList[chname] = list()

            filteredList[chname].append(f'Most used reaction: {emoji} - used ({cnt}) times\n\n')

        # Add emoji data to filtered list
        for tup in emojiData:
            chname = tup[0]
            emoji = tup[1]
            cnt = tup[2]

            # If channel name exists, add the emoji
            if chname not in filteredList:
                filteredList[chname] = list()

            filteredList[chname].append(f'Most used emoji: {emoji} - used ({cnt}) times\n\n')

        info = ''
        for key in filteredList:
            info += 'Channel ' + '#' + key + '\n'
            for tup in filteredList[key]:
                info += tup
            info += '\n'

        await ctx.send(f'{info}')

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

def setup(client):
    client.add_cog(Channel(client))
