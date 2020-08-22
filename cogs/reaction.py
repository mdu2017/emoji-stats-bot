import discord
from discord.ext import commands
from const import *


class Reaction(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Reaction cog ready')

    # Handles when reactions are added to a message
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        channel_name = reaction.message.channel.name  # TODO: Add channel info to queries
        userid = str(user.id)
        emojiID = reaction.emoji
        value = str(emojiID)  # Stringify emoji for database

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = reaction.message.guild.id

        # Handle user data if it exists
        cursor.execute("""
            SELECT userid, reactid FROM users
            WHERE userid = %s AND reactid = %s 
            AND emojitype = 'react' AND guildid = %s""", (userid, value, guild_id))
        userData = cursor.fetchall()
        if len(userData) == 0:
            cursor.execute("""
                INSERT INTO users(userid, reactid, cnt, emojitype, guildid) 
                VALUES(%s, %s, 1, 'react', %s)""", (userid, value, guild_id))
            # print(f'successfully added -- \n')
        else:
            cursor.execute("""
                    UPDATE users SET cnt = cnt + 1
                    WHERE users.userid = %s AND users.reactid = %s 
                    AND emojitype = 'react' AND guildid = %s""", (userid, value, guild_id))
            # print(f'successfully updated -- \n')
        conn.commit()

        # Process channel data
        cursor.execute("""
            SELECT chname, reactid FROM channel
            WHERE chname = %s AND reactid = %s 
            AND emojitype = 'react' AND guildid = %s""", (channel_name, value, guild_id))
        chData = cursor.fetchall()
        if len(chData) == 0:
            cursor.execute("""
                INSERT INTO channel(chname, reactid, cnt, emojitype, guildid)
                VALUES(%s, %s, 1, 'react', %s)""", (channel_name, value, guild_id))
            # print('Channel reaction added')
        else:
            cursor.execute("""
                UPDATE channel SET cnt = cnt + 1
                WHERE chname = %s AND reactid = %s 
                AND emojitype = 'react' AND guildid = %s""", (channel_name, value, guild_id))
            # print('Channel reaction updated')
        conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Handles processing when reaction is removed from a message
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        channel_name = reaction.message.channel.name
        userid = str(user.id)
        emojiID = reaction.emoji
        value = str(emojiID)  # Stringify emoji for database

        # Get db connection and check
        conn, cursor = getConnection()

        guild_id = reaction.message.guild.id

        # Handle user data if it exists
        cursor.execute("""
                SELECT userid, reactid FROM users
                WHERE userid = %s AND reactid = %s 
                AND emojitype = 'react' AND guildid = %s""", (userid, value, guild_id))
        userData = cursor.fetchall()
        if len(userData) > 0:
            cursor.execute("""
                UPDATE users SET cnt = cnt - 1
                WHERE users.userid = %s AND users.reactid = %s 
                AND emojitype = 'react' AND cnt > 0 AND guildid = %s""", (userid, value, guild_id))
            # print(f'successfully updated (remove) -- \n')
        conn.commit()

        # Process channel data
        cursor.execute("""
                SELECT chname, reactid FROM channel
                WHERE chname = %s AND reactid = %s 
                AND emojitype = 'react' AND guildid = %s""", (channel_name, value, guild_id))
        chData = cursor.fetchall()
        if len(chData) > 0:
            cursor.execute("""
                UPDATE channel SET cnt = cnt - 1
                WHERE chname = %s AND reactid = %s 
                AND emojitype = 'react' AND cnt > 0 AND guildid = %s""", (channel_name, value, guild_id))
        conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Gets the list of most used emojis for reactions
    @commands.command(brief="""Get list of top <N> most used reacts 
        (.topreacts OR .topreacts <num> <mode=normal,custom,unicode>)""")
    async def topreacts(self, ctx, amt=5, mode='normal'):
        # Handle invalid amount
        if amt < 1 or amt > 15:
            await ctx.send(f'Error: enter an amount between 1-20')
            return

        record = None

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Query records for top reactions
        record, title = getTopReacts(cursor, guild_id, amt, mode)

        if len(record) == 0:
            await ctx.send(f'No reaction data available')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumRct(cursor, guild_id)
        finalList = processListRct(self.client, record, emojiSum)

        # Display results
        result = getResult(finalList)
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_thumbnail(url=emoji_image_url)
        embed.add_field(name=f'{title}', value=f'{result}', inline=False)
        await ctx.send(embed=embed)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Gets a list of reacts by user (Can use nickname or mention)
    @commands.command(brief='Get list of top 10 most used reacts by user (.userreacts <@username/nickname>')
    async def userreacts(self, ctx, *args):
        usr_name = ' '.join(args)
        user, username, userID, valid = processName(self.client, ctx, usr_name)

        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e userreacts <@username>')
            return

        # Get db connection and check
        conn, cursor = getConnection()

        guild_id = ctx.guild.id

        sqlString = """
            SELECT reactid, cnt FROM users
            WHERE userid = %s AND guildid = %s
            AND users.emojitype = 'react'
            ORDER BY cnt DESC LIMIT 5;"""

        cursor.execute(sqlString, (str(userID), guild_id))
        record = cursor.fetchall()

        # Check for empty record
        if len(record) == 0:
            await ctx.send(f'{username}\'s reaction list is empty!')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumRctUsr(cursor, userID, guild_id)
        finalList = processListRct(self.client, record, emojiSum)
        result = getResult(finalList)

        # Display results
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_thumbnail(url=emoji_image_url)
        embed.add_field(name=f'{username}\'s top 5 reacts in this server!', value=f'{result}', inline=False)
        await ctx.send(embed=embed)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    @commands.command(brief='Lists user\'s favorite reaction')
    async def favreact(self, ctx, *args):
        usr_name = ' '.join(args)

        # Get the user info from @mention or user's nickname
        user, username, userID, valid = processName(self.client, ctx, usr_name)
        guild_id = ctx.guild.id

        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e favreact <@username>')
            return

        # Get db connection
        conn, cursor = getConnection()

        # Get the data
        cursor.execute("""
            SELECT reactid, cnt FROM users
            WHERE userid = %s AND users.emojitype = 'react' AND guildid = %s
            ORDER BY cnt DESC LIMIT 1;""", (str(userID), guild_id))
        record = cursor.fetchall()

        # Check for empty records
        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumRctUsr(cursor, userID, guild_id)

        # Convert records into list for display
        finalList = processListMsg(self.client, record, emojiSum)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'{username}\' has no emoji data')
            return

        fav_react = finalList[0]

        # Create embed and display results
        em = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        em.set_thumbnail(url=emoji_image_url)
        em.add_field(name=f'{username}\'s favorite reaction:', value=f'{fav_react}', inline=False)
        await ctx.send(embed=em)

    @commands.command(brief='Lists full stats for every react (.fullreactstats)')
    async def fullreactstats(self, ctx):
        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Grabs all reactions
        cursor.execute("""
            SELECT reactid, SUM(cnt)
            FROM users WHERE users.emojitype = 'react' AND guildid = %s
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC""", (guild_id,))
        record = cursor.fetchall()

        # Handle empty results
        if len(record) == 0:
            await ctx.send('No reaction data found.')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumRct(cursor, guild_id)
        finalList = processListRct(self.client, record, emojiSum)
        result = getResult(finalList)

        # TODO: multi-page embeds
        
        # Display results
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_thumbnail(url=emoji_image_url)
        embed.add_field(name=f'Full stats of all reactions used in this server', value=f'{result}', inline=False)
        await ctx.send(embed=embed)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection


def setup(client):
    client.add_cog(Reaction(client))


def getTopReacts(cursor, guild_id, amt, mode):
    if mode == 'custom':
        cursor.execute("""
            SELECT reactid, SUM(cnt) FROM users
            WHERE users.emojitype = 'react' AND reactid LIKE '<%%' AND guildid = %s
            GROUP BY reactid ORDER BY SUM(cnt) DESC
            LIMIT (%s)""", (guild_id, amt))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server! (custom emojis)'
    elif mode == 'unicode':
        cursor.execute("""
            SELECT reactid, SUM(cnt) FROM users
            WHERE users.emojitype = 'react' AND reactid NOT LIKE '<%%' AND guildid = %s
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC
            LIMIT (%s)""", (guild_id, amt))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server! (Unicode emojis)'
    else:
        cursor.execute("""
            SELECT reactid, SUM(cnt) FROM users
            WHERE users.emojitype = 'react' AND guildid = %s
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC
            LIMIT %s""", (guild_id, amt))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server!'

    return record, title

def getEmojiSumRct(cursor, guild_id):
    cursor.execute("""
                SELECT SUM(cnt) FROM users 
                WHERE users.emojitype = 'react' AND guildid = %s""", (guild_id,))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])
    return emojiSum

def getEmojiSumRctUsr(cursor, userID, guild_id):
    sumSql = """SELECT SUM(cnt) FROM users WHERE userid = %s AND emojitype = 'react' AND guildid = %s"""
    cursor.execute(sumSql, (str(userID), guild_id))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])
    return emojiSum
