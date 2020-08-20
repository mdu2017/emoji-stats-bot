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
    async def chstats(self, ctx, ch='', option='message'):

        channel_name, typeStr, valid_channel, valid_option = processChName(self.client, ctx, ch, option)

        if not valid_channel:
            err_embed = discord.Embed(colour=discord.Colour.dark_orange(),
                    description=f'Text Channel #{ch} was not found\nUsage: .channelstats <channel_name> <option>')
            await ctx.send(embed=err_embed)
            return
        if not valid_option:
            err_embed = discord.Embed(colour=discord.Colour.dark_orange(),
                    description=f'<option>(s) are: \'react\' OR \'message\'\nUsage: .channelstats <channel_name> <option>')
            await ctx.send(embed=err_embed)
            return

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Grab top 3 most used emojis in a channel
        cursor.execute("""
            SELECT reactid, cnt FROM channel
            WHERE channel.chname = %s AND emojitype = %s AND guildid = %s
            ORDER BY cnt DESC LIMIT 3""", (channel_name, option, guild_id))
        record = cursor.fetchall()

        # Check for empty data
        if len(record) == 0:
            err_embed = discord.Embed(colour=discord.Colour.dark_orange(),
                    description=f'No emoji data available for #{channel_name}')
            await ctx.send(embed=err_embed)
            return

        # Grab total count of used emojis
        emojiSum = getEmojiSumChn(cursor, channel_name, option, guild_id)

        finalList = processListChn(self.client, record, emojiSum, typeStr, channel_name)
        result = getResult(finalList)

        em = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        em.add_field(name=f'Top 3 {typeStr} used in #{channel_name}', value=f'{result}', inline=False)

        await ctx.send(embed=em)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    @commands.command(brief='display most popular emojis/reaction for each channel if available (.fullchstats)')
    async def fullchstats(self, ctx):

        # Get db connection and check
        conn, cursor = getConnection()
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

        # Process two data lists and result string
        embed = fullChStatsResult(reactData, emojiData)
        await ctx.send(embed=embed)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # TODO (enhancement): Get most used emojis in the last week/month/day/year, etc.
    # @commands.command(brief='Most used emojis in the last <week/month/day/year>')
    # async def recentchstats(self, ctx):
    #     print()

def setup(client):
    client.add_cog(Channel(client))

def getEmojiSumChn(cursor, channel_name, option, guild_id):
    cursor.execute("""
                SELECT SUM(cnt) FROM channel 
                WHERE channel.chname = %s AND emojitype = %s
                AND guildid = %s""", (channel_name, option, guild_id))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])
    return emojiSum
