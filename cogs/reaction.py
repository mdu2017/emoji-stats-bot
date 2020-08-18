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
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

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
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

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
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        guild_id = ctx.guild.id

        if mode == 'custom':
            await ctx.send(f'Overall top {amt} most popular reacts in this server! (custom emojis)')
            cursor.execute("""
                SELECT reactid, SUM(cnt) FROM users
                WHERE users.emojitype = 'react' AND reactid LIKE '<%%' AND guildid = %s
                GROUP BY reactid ORDER BY SUM(cnt) DESC
                LIMIT (%s)""", (guild_id, amt))
            record = cursor.fetchall()
        elif mode == 'unicode':
            await ctx.send(f'Overall top {amt} most popular reacts in this server! (Unicode emojis)')
            cursor.execute("""
                SELECT reactid, SUM(cnt) FROM users
                WHERE users.emojitype = 'react' AND reactid NOT LIKE '<%%' AND guildid = %s
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC
                LIMIT (%s)""", (guild_id, amt))
            record = cursor.fetchall()
        else:
            # Grabs top X most used reacts by type
            if mode == 'normal':
                await ctx.send(f'Overall top {amt} most popular reacts in this server!')
                cursor.execute("""
                    SELECT reactid, SUM(cnt) FROM users
                    WHERE users.emojitype = 'react' AND guildid = %s
                    GROUP BY reactid
                    ORDER BY SUM(cnt) DESC
                    LIMIT %s""", (guild_id, amt))
                record = cursor.fetchall()

        if len(record) == 0:
            await ctx.send(f'No reaction data available')
            return

        # Fetch single sum value
        cursor.execute("""
            SELECT SUM(cnt) FROM users 
            WHERE users.emojitype = 'react' AND guildid = %s""", (guild_id, ))
        emojiSum = cursor.fetchone()
        emojiSum = int(emojiSum[0])

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
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of all reacts.')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some reacts won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of all reacts.')

        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))
        await ctx.send(f'{result}')

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Gets a list of reacts by user (Can use nickname or mention)
    @commands.command(brief='Get list of top 10 most used reacts by user (.userreacts <@username/nickname>')
    async def userreacts(self, ctx, arg1=''):
        user = None
        username = None
        userID = None

        # Check empty argument
        if arg1 == '':
            await ctx.send(f'Usage: .userreacts <@username> OR .userreacts <nickname>')
            return

        # If mentioned, get by id, otherwise search each member's nickname
        if '@' in arg1 and '!' in arg1:
            idStr = str(arg1)
            idStr = idStr[idStr.index('!') + 1: idStr.index('>')]
            userID = int(idStr)
            user = self.client.get_user(userID)
            username = user.name
        else:
            for guild in self.client.guilds:
                for member in guild.members:
                    nickname = member.nick
                    if str(arg1) == str(nickname):
                        user = member
                        username = user.name
                        userID = user.id
                        break

        # Check for empty user
        if user is None:
            await ctx.send(f'Error: user {arg1} was not found')
            return

        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

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
        sumSql = """SELECT SUM(cnt) FROM users WHERE userid = %s AND emojitype = 'react' AND guildid = %s"""
        cursor.execute(sumSql, (str(userID), guild_id))
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
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of reacts.')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some emojis won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of reacts.')

        favoriteReact = finalList[0]
        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'{username}\'s top 5 reacts in this server!')
        await ctx.send(f'{username}\'s favorite reaction: {favoriteReact}\n')
        await ctx.send(f'{result}')

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    @commands.command(brief='Lists full stats for every react (.fullreactstats)')
    async def fullreactstats(self, ctx):
        # Get db connection and check
        conn = ps_pool.getconn()
        if conn:
            cursor = conn.cursor()
        else:
            print('Error getting connection from pool')
            return

        guild_id = ctx.guild.id

        # Grabs all reactions
        cursor.execute("""
            SELECT reactid, SUM(cnt)
            FROM users WHERE users.emojitype = 'react' AND guildid = %s
            GROUP BY reactid
            ORDER BY SUM(cnt) DESC""", (guild_id, ))
        record = cursor.fetchall()

        # Handle empty results
        if len(record) == 0:
            await ctx.send('No reaction data found.')
            return

        # Fetch single sum value
        cursor.execute("""SELECT SUM(cnt) FROM users WHERE emojitype = 'react' AND guildid = %s""", (guild_id, ))
        emojiSum = cursor.fetchone()
        emojiSum = int(emojiSum[0])

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
                    f'{spacing}{currEmoji} - {name} used ({data[key]}) times | {percentage}% of all reacts.')

            else:
                temp = handleSpecialEmojis(key)  # TODO: Some emojis won't have a name so 'EMOJI' is by default
                finalList.append(f'{spacing}{key} - {temp} used ({data[key]}) times | {percentage}% of reacts.')

        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'Full stats of all reactions used in this server')
        await ctx.send(f'{result}')

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection


def setup(client):
    client.add_cog(Reaction(client))
