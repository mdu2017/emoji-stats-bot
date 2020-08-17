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
    async def channelstats(self, ctx, ch='', option='react'):
        print('todo')

        # If no channel name specified, use current channel. If invalid channel name, exit
        if ch == '':
            channel_name = ctx.channel.name
        else:
            found = False
            for channel in ctx.guild.text_channels:
                if channel.name == ch:
                    found = True
                    break
            if not found:
                await ctx.send(f'Text Channel #{ch} was not found\nUsage: .channelstats <channel_name> <option>')
                return

        # handle invalid type
        if option != 'react' and option != 'message':
            await ctx.send(f'<option>(s) are: \'react\' OR \'message\'\nUsage: .channelstats <channel_name> <option>')
            return

        channel_name = ctx.channel.name

        # TODO: queries here
        # TODO: Handle cases where channel has no reactions/emojis (maybe query for valid channel names, query for null channel names)

    # TODO (enhancement): Get most used emojis in the last week/month/day/year, etc.
    @commands.command(brief='Most used emojis in the last <week/month/day/year>')
    async def recentchstats(self, ctx):
        print()

    @commands.command(brief='display most popular emojis/reactions for every channel, if possible')
    async def fullchstats(self, ctx):
        print('todo')
        # TODO: Handle cases where channel has no reactions/emojis (maybe query for valid channel names, query for null channel names)


def setup(client):
    client.add_cog(Channel(client))
