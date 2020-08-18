# Channel Stats (Most popular reaction for each channel. Most popular emoji for each channel)
import discord
from discord.ext import commands
import re
from const import handleSpecialEmojis


class Channel(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Channel cog ready')

    # Top 3 most popular emojis for reactions/messages for a channel (optional type)
    @commands.command(brief='Top 3 emojis for reactions/messages')
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

        if option == 'react':
            typeStr = 'reactions'
        else:
            typeStr = 'emojis'

        # Grab top 3 most used emojis in a channel
        record = await self.client.pg_con.fetch("""
            SELECT reactid, cnt FROM channel
            WHERE channel.chname = $1 AND emojitype = $2
            ORDER BY cnt DESC LIMIT 3""", channel_name, option)
        emojiSum = await self.client.pg_con.fetchval("""
            SELECT SUM(cnt) FROM channel
            WHERE channel.chname = $1 AND emojitype = $2""", channel_name, option)

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

        # Check for empty data
        if len(finalList) == 0:
            await ctx.send(f'No emoji data available for [#{channel_name}]')
            return

        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        await ctx.send(f'Top 3 {typeStr} used in [#{channel_name}]: \n {result}')

    # TODO (enhancement): Get most used emojis in the last week/month/day/year, etc.
    @commands.command(brief='Most used emojis in the last <week/month/day/year>')
    async def recentchstats(self, ctx):
        print()

    @commands.command(brief='display most popular emojis/reactions for every channel, if possible')
    async def fullchstats(self, ctx):
        print('todo')


def setup(client):
    client.add_cog(Channel(client))
