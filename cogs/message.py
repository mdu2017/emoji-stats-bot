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

        ctx = await self.client.get_context(message)
        channel_name = message.channel.name  # TODO: Add channel info to queries
        msg = message.content

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

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
                    WHERE userid = %s AND reactid = %s AND emojitype = 'message'""", (userid, item))
                existingData = cursor.fetchall()

                # Handle user data and commit
                if len(existingData) == 0:
                    # print('Successfully adding custom emoji in msg')
                    cursor.execute("""
                        INSERT INTO users(userid, reactid, cnt, emojitype)
                        VALUES (%s, %s, 1, 'message')""", (userid, item))
                else:
                    # print(f'Custom emoji exists, updating entry')
                    cursor.execute("""
                        UPDATE users SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND userid = %s AND reactid = %s""", (userid, item))
                conn.commit()

                # Handle channel data and commit
                cursor.execute("""
                        SELECT chname, reactid FROM channel
                        WHERE chname = %s AND reactid = %s AND emojitype = 'message'""", (channel_name, item))
                chData = cursor.fetchall()
                if len(chData) == 0:
                    cursor.execute("""
                        INSERT INTO channel(chname, reactid, cnt, emojitype)
                        VALUES (%s, %s, 1, 'message')""", (channel_name, item))
                else:
                    cursor.execute("""
                        UPDATE channel SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND chname = %s AND reactid = %s""", (channel_name, item))
                conn.commit()

        # Query unicode emojis into users db
        if len(unimojis) > 0:
            for item in unimojis:

                # Handle user data
                cursor.execute("""
                        SELECT userid, reactid FROM users
                        WHERE userid = %s AND reactid = %s AND emojitype = 'message'""", (userid, item))
                existingData = cursor.fetchall()
                if len(existingData) == 0:
                    # print('Successfully adding unicode emoji in msg')
                    cursor.execute("""
                        INSERT INTO users(userid, reactid, cnt, emojitype)
                        VALUES (%s, %s, 1, 'message')""", (userid, item))
                else:
                    # print('Unicode emoji exists, updating entry')
                    cursor.execute("""
                        UPDATE users SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND userid = %s AND reactid = %s""", (userid, item))
                conn.commit()

                # Handle channel data
                cursor.execute("""
                        SELECT chname, reactid FROM channel
                        WHERE chname = %s AND reactid = %s AND emojitype = 'message'""", (channel_name, item))
                chData = cursor.fetchall()

                if len(chData) == 0:
                    cursor.execute("""
                        INSERT INTO channel(chname, reactid, cnt, emojitype)
                        VALUES (%s, %s, 1, 'message')""", (channel_name, item))
                else:
                    cursor.execute("""
                        UPDATE channel SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND chname = %s AND reactid = %s""", (channel_name, item))
                conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)   # Close connection


    # Returns the top 5 most used emojis in messages
    @commands.command(brief='Display overall stats for emojis used in messages')
    async def topemojis(self, ctx, amt=5):
        # Handle invalid amount
        if amt < 1 or amt > 15:
            await ctx.send(f'Error: enter an amount between 1-20')
            return

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        # Grabs top 5 most used reacts in messages
        cursor.execute("""
            SELECT reactid, SUM(cnt) FROM users
            WHERE users.emojitype = 'message'
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC
            LIMIT %s""", [amt])
        record = cursor.fetchall()

        # Check empty query
        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

        # Fetch single sum value by message
        cursor.execute("""SELECT SUM(cnt) FROM users WHERE emojitype = 'message'""")
        emojiSum = cursor.fetchone()
        emojiSum = int(emojiSum[0])

        # TODO: Continue refactoring new psycopg2 library queries

        # Assuming that record gives rows of exactly 2 columns
        data = dict(record)  # convert record to dictionary
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
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of use.')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some emojis won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of use.')

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'Error: No emoji data found')
            return

        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'The {amt} most used emojis in messages!')
        await ctx.send(f'{result}')

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

    @commands.command(brief='Displays most used emojis in messages by user')
    async def useremojis(self, ctx, user_name=''):
        user = None
        username = None
        userID = None

        # If mentioned, get by id, otherwise search each member's nickname
        if '@' in user_name and '!' in user_name:
            idStr = str(user_name)
            idStr = idStr[idStr.index('!') + 1: idStr.index('>')]
            userID = int(idStr)
            user = self.client.get_user(userID)
            username = user.name
        else:
            for guild in self.client.guilds:
                for member in guild.members:
                    nickname = member.nick
                    if str(user_name) == str(nickname):
                        user = member
                        username = member.name
                        userID = member.id
                        break

        # Check for empty user
        if user is None:
            await ctx.send(f'User {user_name} was not found')
            return

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        idValue = str(userID)

        # Leave off userid to fit into dictionary
        cursor.execute("""
            SELECT reactid, cnt FROM users
            WHERE userid = %s AND users.emojitype = 'message'
            ORDER BY cnt DESC LIMIT 5;""", (str(idValue),))
        record = cursor.fetchall()

        # Fetch single sum value
        cursor.execute("""SELECT SUM(cnt) FROM users WHERE userid = %s AND emojitype = 'message'""", (str(idValue),))
        emojiSum = cursor.fetchone()
        emojiSum = int(emojiSum[0])

        data = dict(record)  # convert record to dictionary
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
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of use.')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some emojis won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of use.')

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'{username}\'s reaction list is empty!')
            return

        favoriteEmoji = finalList[0]
        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'{username}\'s top 5 reacts!')
        await ctx.send(f'{username}\'s favorite emoji: {favoriteEmoji}\n')
        await ctx.send(f'{result}')

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

    @commands.command(brief='Stat for every emoji used in messages')
    async def fullmsgstats(self, ctx):

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        cursor.execute("""
            SELECT reactid, SUM(cnt)
            FROM users WHERE users.emojitype = 'message'
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC""")
        record = cursor.fetchall()

        cursor.execute("""SELECT SUM(cnt) FROM users WHERE emojitype = 'message'""")
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
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of emojis.')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some emojis won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of emojis.')

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'No data available')
            return

        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'Full stats on overall usage of each emoji')
        await ctx.send(f'{result}')

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)


def setup(client):
    client.add_cog(Message(client))
