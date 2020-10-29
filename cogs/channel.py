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
                            (.chstats <channel_name> <option=message,react>)''')
    async def chstats(self, ctx, ch=''):

        channel_name, ch_id, valid_channel = processChName(self.client, ctx, ch)

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = str(ctx.guild.id)

        # Grab top 3 most used emojis and reactions in a channel
        cursor.execute("""
                SELECT emoji, SUM(cnt) FROM emojis
                WHERE emojis.guildid = %s AND chid = %s AND emojitype = 'message' 
                GROUP BY emoji ORDER BY SUM(cnt) DESC
                LIMIT 3""", (str(guild_id), str(ch_id)))
        emoji_record = cursor.fetchall()

        cursor.execute("""
                        SELECT emoji, SUM(cnt) FROM emojis
                        WHERE emojis.guildid = %s AND chid = %s AND emojitype = 'react' 
                        GROUP BY emoji ORDER BY SUM(cnt) DESC
                        LIMIT 3""", (str(guild_id), str(ch_id)))
        react_record = cursor.fetchall()

        # Set channel embed
        ch_embed = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        ch_embed.set_thumbnail(url=emoji_image_url)

        # Check for empty emoji data
        if len(emoji_record) == 0:
            ch_embed.add_field(name=f'No Emoji data available', value='-', inline=False)
        else:
            # Grab total count of used emojis
            emojiSum = getEmojiSumChn(cursor, ch_id, guild_id)
            if emojiSum == -1:
                ch_embed.add_field(name=f'No Emoji sum available', value='-', inline=False)

            # Get final emoji list
            finalList = processListChn(self.client, emoji_record, emojiSum, channel_name)
            emoji_result = getResult(finalList)
            ch_embed.add_field(name=f'Top 3 emojis used in #{channel_name}', value=f'{emoji_result}', inline=False)

        # Handle react portion of code
        if len(react_record) == 0:
            ch_embed.add_field(name=f'No reaction data available', value='-', inline=False)
        else:
            # Check emoji count
            emojiSum = getRctSumChn(cursor, ch_id, guild_id)
            if emojiSum == -1:
                ch_embed.add_field(name=f'No reaction sum available', value='-', inline=False)

            # Process reaction results
            finalList = processListChn(self.client, react_record, emojiSum, channel_name)
            react_result = getResult(finalList)
            ch_embed.add_field(name=f'Top 3 reactions used in #{channel_name}', value=f'{react_result}', inline=False)


        # Display final results
        await ctx.send(embed=ch_embed)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # TODO: Fix
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

        # TODO: add multi-page embeds

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

def getEmojiSumChn(cursor, ch_id, guild_id):
    cursor.execute("""
                SELECT SUM(cnt) FROM emojis 
                WHERE emojis.chid = %s AND emojitype = 'message'
                AND guildid = %s""", (str(ch_id), guild_id))
    emojiSum = cursor.fetchone()

    try:
        emojiSum = int(emojiSum[0])
    except Exception:
        return -1
    return emojiSum

def getRctSumChn(cursor, ch_id, guild_id):
    cursor.execute("""
                SELECT SUM(cnt) FROM emojis 
                WHERE emojis.chid = %s AND emojitype = 'react'
                AND guildid = %s""", (str(ch_id), guild_id))
    emojiSum = cursor.fetchone()
    try:
        emojiSum = int(emojiSum[0])
    except Exception:
        return -1
    return emojiSum
