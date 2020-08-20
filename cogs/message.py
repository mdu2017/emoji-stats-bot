import discord
from discord.ext import commands
from emoji import UNICODE_EMOJI
import regex
import re
from const import *


class Message(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Message cog ready')

    # Handles when messages are sent in the channel
    @commands.Cog.listener()  # Cog on_message automatically runs comands once
    async def on_message(self, message):

        # Make sure bot doesn't respond its own message
        if message.author == self.client.user:
            return

        # ctx = await self.client.get_context(message)
        guild_id = message.guild.id
        channel_name = message.channel.name  # TODO: Add channel info to queries
        msg = message.content

        # Get db connection and check
        conn, cursor = getConnection()

        userid = str(message.author.id)  # Store as string in DB

        # FIND ALL CUSTOM EMOJIS
        custom_emojis = re.findall(r'<:\w*:\d*>', msg)

        # FIND ALL UNICODE EMOJIS
        unimojis = []
        data = regex.findall(r'\X', msg)  # Used to get all single characters
        for ch in data:
            if any(char in UNICODE_EMOJI for char in ch):
                unimojis.append(ch)

        # Query custom emojis into database if not empty
        if len(custom_emojis) > 0:
            for item in custom_emojis:
                # Check if data exists
                cursor.execute("""
                    SELECT userid, reactid FROM users
                    WHERE userid = %s AND reactid = %s 
                    AND emojitype = 'message' AND guildid = %s""", (userid, item, guild_id))
                existingData = cursor.fetchall()

                # Handle user data and commit
                if len(existingData) == 0:
                    # print('Successfully adding custom emoji in msg')
                    cursor.execute("""
                        INSERT INTO users(userid, reactid, cnt, emojitype, guildid)
                        VALUES (%s, %s, 1, 'message', %s)""", (userid, item, guild_id))
                else:
                    # print(f'Custom emoji exists, updating entry')
                    cursor.execute("""
                        UPDATE users SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND userid = %s 
                        AND reactid = %s AND guildid = %s""", (userid, item, guild_id))
                conn.commit()

                # Handle channel data and commit
                cursor.execute("""
                        SELECT chname, reactid FROM channel
                        WHERE chname = %s AND reactid = %s 
                        AND emojitype = 'message' AND guildid = %s""", (channel_name, item, guild_id))
                chData = cursor.fetchall()
                if len(chData) == 0:
                    cursor.execute("""
                        INSERT INTO channel(chname, reactid, cnt, emojitype, guildid)
                        VALUES (%s, %s, 1, 'message', %s)""", (channel_name, item, guild_id))
                else:
                    cursor.execute("""
                        UPDATE channel SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND chname = %s 
                        AND reactid = %s AND guildid = %s""", (channel_name, item, guild_id))
                conn.commit()

        # Query unicode emojis into users db
        if len(unimojis) > 0:
            for item in unimojis:

                # Handle user data
                cursor.execute("""
                        SELECT userid, reactid FROM users
                        WHERE userid = %s AND reactid = %s 
                        AND emojitype = 'message' AND guildid = %s""", (userid, item, guild_id))
                existingData = cursor.fetchall()
                if len(existingData) == 0:
                    # print('Successfully adding unicode emoji in msg')
                    cursor.execute("""
                        INSERT INTO users(userid, reactid, cnt, emojitype, guildid)
                        VALUES (%s, %s, 1, 'message', %s)""", (userid, item, guild_id))
                else:
                    # print('Unicode emoji exists, updating entry')
                    cursor.execute("""
                        UPDATE users SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND userid = %s 
                        AND reactid = %s AND guildid = %s""", (userid, item, guild_id))
                conn.commit()

                # Handle channel data
                cursor.execute("""
                        SELECT chname, reactid FROM channel
                        WHERE chname = %s AND reactid = %s 
                        AND emojitype = 'message' AND guildid = %s""", (channel_name, item, guild_id))
                chData = cursor.fetchall()

                if len(chData) == 0:
                    cursor.execute("""
                        INSERT INTO channel(chname, reactid, cnt, emojitype, guildid)
                        VALUES (%s, %s, 1, 'message', %s)""", (channel_name, item, guild_id))
                else:
                    cursor.execute("""
                        UPDATE channel SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND chname = %s 
                        AND reactid = %s AND guildid = %s""", (channel_name, item, guild_id))
                conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Returns the top 5 most used emojis in messages
    @commands.command(brief='Display overall stats for emojis used in messages')
    async def topemojis(self, ctx, amt=5):
        # Handle invalid amount
        if amt < 1 or amt > 15:
            await ctx.send(f'Error: enter an amount between 1-20')
            return

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Grabs top 5 most used reacts in messages
        cursor.execute("""
            SELECT reactid, SUM(cnt) FROM users
            WHERE users.emojitype = 'message' AND guildid = %s
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC
            LIMIT %s""", (guild_id, amt))
        record = cursor.fetchall()

        # Check empty query
        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

        # Fetch total emojis used
        emojiSum = getEmojiSumMsg(cursor, guild_id)

        # Process final list for displaying
        finalList = processListMsg(self.client, record, emojiSum)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'Error: No emoji data found in this server')
            return

        result = getResult(finalList)

        # Create customized embed
        em = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        em.add_field(name=f'The {len(finalList)} most used emojis in messages in the server',
                     value=f'{result}', inline=False)

        # Display results
        await ctx.send(embed=em)

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

    @commands.command(brief='Displays most used emojis in messages by user')
    async def useremojis(self, ctx, *args):
        usr_name = ' '.join(args)
        user, username, userID, valid = processName(self.client, ctx, usr_name)

        # Check for empty user
        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e useremojis <@username>')
            return

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Leave off userid to fit into dictionary
        cursor.execute("""
            SELECT reactid, cnt FROM users
            WHERE userid = %s AND users.emojitype = 'message' AND guildid = %s
            ORDER BY cnt DESC LIMIT 5;""", (str(userID), guild_id))
        record = cursor.fetchall()

        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

        # Fetch total emojis used
        emojiSum = getEmojiSumUsrMsg(cursor, guild_id, userID)

        # Process final list for displaying
        finalList = processListMsg(self.client, record, emojiSum)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'{username}\' has no emoji data')
            return

        favoriteEmoji = finalList[0]
        result = getResult(finalList)

        # Create customized embed
        em = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        em.add_field(name=f'{username}\'s {len(finalList)} most used emojis in the server',
                     value=f'{result}', inline=False)

        # Display results
        await ctx.send(embed=em)

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

    @commands.command(brief='Lists user\'s favorite emote')
    async def favemoji(self, ctx, *args):
        usr_name = ' '.join(args)

        # Get the user info from @mention or user's nickname
        user, username, userID, valid = processName(self.client, ctx, usr_name)
        guild_id = ctx.guild.id

        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e favemoji <@username>')
            return

        # Get db connection
        conn, cursor = getConnection()

        # Get the data
        cursor.execute("""
                    SELECT reactid, cnt FROM users
                    WHERE userid = %s AND users.emojitype = 'message' AND guildid = %s
                    ORDER BY cnt DESC LIMIT 1;""", (str(userID), guild_id))
        record = cursor.fetchall()

        # Check for empty records
        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumUsrMsg(cursor, guild_id, userID)

        # Convert records into list for display
        finalList = processListMsg(self.client, record, emojiSum)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'{username}\' has no emoji data')
            return

        favoriteEmoji = finalList[0]

        # Create embed and display results
        em = discord.Embed(
            colour=discord.Colour.blurple(),
        )
        em.add_field(name=f'{username}\'s favorite emoji:', value=f'{favoriteEmoji}', inline=False)
        await ctx.send(embed=em)

    @commands.command(brief='Stat for every emoji used in messages')
    async def fullmsgstats(self, ctx):
        guild_id = ctx.guild.id

        # Get db connection and check
        conn, cursor = getConnection()

        cursor.execute("""
            SELECT reactid, SUM(cnt)
            FROM users WHERE users.emojitype = 'message' AND guildid = %s
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC""", (guild_id,))
        record = cursor.fetchall()

        # Get sum and final list
        emojiSum = getEmojiSumMsg(cursor, guild_id)
        finalList = processListMsg(self.client, record, emojiSum)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'No data available')
            return

        # Join results into one message string
        result = getResult(finalList)

        # Display results
        # Create embed and display results
        em = discord.Embed(
            colour=discord.Colour.blurple(),
            title=f'Full statistics for all emojis used',
        )
        em.add_field(name='Emojis used in server', value=f'{result}', inline=False)
        await ctx.send(embed=em)

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)


def setup(client):
    client.add_cog(Message(client))


# Gets sum of total emojis used in messages
def getEmojiSumMsg(cursor, guild_id):
    cursor.execute("""SELECT SUM(cnt) FROM users WHERE emojitype = 'message' AND guildid = %s""", (guild_id,))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])

    return emojiSum


# Get sum of total emojis used in user emoji commands
def getEmojiSumUsrMsg(cursor, guild_id, userID):
    cursor.execute("""
                SELECT SUM(cnt) FROM users WHERE userid = %s 
                AND emojitype = 'message' AND guildid = %s""", (str(userID), guild_id))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])
    return emojiSum
