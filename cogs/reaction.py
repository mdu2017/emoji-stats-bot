import asyncio

import discord
from discord.ext import commands
from const import *
import datetime


class Reaction(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Reaction cog ready')

    # Handles when reactions are added to a message
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        # Ignore the reactions for the 4 arrows used to scroll pages
        emoji_str = str(reaction.emoji)
        if emoji_str == left_arrow or emoji_str == right_arrow or emoji_str == arrow_start or emoji_str == arrow_end:
            return

        # Ignore reaction if user is a bot
        if user.bot:
            return

        # Get channel id, user id, guild id, and emoji, and timestamp
        ch_id = str(reaction.message.channel.id)
        user_id = str(user.id)
        value = str(reaction.emoji)
        guild_id = str(reaction.message.guild.id)
        curr_time = datetime.datetime.now()

        # Get db connection and check
        conn, cursor = getConnection()

        # Add user to database list


        cursor.execute("""
            INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, chid)
            VALUES(%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(emoji, emojitype, userid, guildid)
            DO UPDATE SET cnt = emojis.cnt + 1, emojidate = %s
        """, (value, 'react', user_id, str(guild_id), 1, curr_time, ch_id, curr_time))
        conn.commit()

        print("Finished inserting data")

        # Handle user data if it exists
        # cursor.execute("""
        #     SELECT userid, reactid FROM users
        #     WHERE userid = %s AND reactid = %s
        #     AND emojitype = 'react' AND guildid = %s""", (userid, value, guild_id))
        # userData = cursor.fetchall()
        # if len(userData) == 0:
        #     cursor.execute("""
        #         INSERT INTO users(userid, reactid, cnt, emojitype, guildid)
        #         VALUES(%s, %s, 1, 'react', %s)""", (userid, value, guild_id))
        #     # print(f'successfully added -- \n')
        # else:
        #     cursor.execute("""
        #             UPDATE users SET cnt = cnt + 1
        #             WHERE users.userid = %s AND users.reactid = %s
        #             AND emojitype = 'react' AND guildid = %s""", (userid, value, guild_id))
            # print(f'successfully updated -- \n')
        # conn.commit()

        # Process channel data
        # cursor.execute("""
        #     SELECT chname, reactid FROM channel
        #     WHERE chname = %s AND reactid = %s
        #     AND emojitype = 'react' AND guildid = %s""", (channel_name, value, guild_id))
        # chData = cursor.fetchall()
        # if len(chData) == 0:
        #     cursor.execute("""
        #         INSERT INTO channel(chname, reactid, cnt, emojitype, guildid)
        #         VALUES(%s, %s, 1, 'react', %s)""", (channel_name, value, guild_id))
        #     # print('Channel reaction added')
        # else:
        #     cursor.execute("""
        #         UPDATE channel SET cnt = cnt + 1
        #         WHERE chname = %s AND reactid = %s
        #         AND emojitype = 'react' AND guildid = %s""", (channel_name, value, guild_id))
        #     # print('Channel reaction updated')
        # conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Handles processing when reaction is removed from a message
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        channel_name = reaction.message.channel.name
        userid = str(user.id)
        value = str(reaction.emoji)

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
    @commands.command(brief='Get list of most used reacts by user (.userreacts <@username/nickname>')
    async def userreacts(self, ctx, *args):
        usr_name = ' '.join(args)

        # If last word is unicode or custom, it will grab specific types of reactions
        lastNdx = usr_name.rfind(' ')
        mode = 'normal'
        if lastNdx != -1:
            lastWord = usr_name[lastNdx+1:]
            print(f'Last word: {lastWord}')
            if lastWord == 'unicode' or lastWord == 'UNICODE':
                mode = 'unicode'
                usr_name = usr_name[:lastNdx]
            elif lastWord == 'custom' or lastWord == 'CUSTOM':
                mode = 'custom'
                usr_name = usr_name[:lastNdx]

        user, username, userID, valid = processName(self.client, ctx, usr_name)

        msg_author = ''
        async for message in ctx.channel.history(limit=1):
            msg_author = message.author

        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e userreacts <@username>')
            return

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        record = getUserReacts(cursor, guild_id, userID, mode)

        # Check for empty record
        if len(record) == 0:
            await ctx.send(f'{username}\'s reaction list is empty!')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumRctUsr(cursor, userID, guild_id)
        finalList = processListRct(self.client, record, emojiSum)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

        # If only 1 page, then get the result and display
        page_content = []  # the final list of results for each page
        if len(finalList) <= 5:
            page_content.append(getResult(finalList))
            em = discord.Embed(colour=discord.Colour.blurple(), title=f'Full statistics for all reactions used', )
            em.add_field(name='Reactions used in server', value=f'{page_content[0]}', inline=False)
            await ctx.send(embed=em)
            return

        # TODO: multiple page embeds
        index = 0  # index keeps track of current item's index

        # Aggregate results into 5 results per page
        while index < len(finalList):
            # For the last page, get remaining results
            if index > len(finalList) - 5:
                res = getResult(finalList[index:len(finalList)], index + 1)
                page_content.append(res)
                index += 5
            else:
                res = getResult(finalList[index:index + 5], index + 1)
                page_content.append(res)
                index += 5

        # Add embeds into final pages
        final_pages = []
        for i in range(len(page_content)):
            embed = discord.Embed(colour=discord.Colour.blurple(), title=f'Page {i + 1}/{len(page_content)}',
                                  description=page_content[i], )
            if i == 0:
                embed.title = f'Page {i + 1}/{len(page_content)}\n' \
                              f'{username}\'s {len(finalList)} most used reactions in the server'

            embed.set_thumbnail(url=emoji_image_url)
            final_pages.append(embed)

        curr_page = 0

        # Display first page and add buttons
        message = await ctx.send(embed=final_pages[curr_page])
        await message.add_reaction(arrow_start)
        await message.add_reaction(left_arrow)
        await message.add_reaction(right_arrow)
        await message.add_reaction(arrow_end)

        # Wait for the author to flip the page with a reaction
        def check(reaction, user):
            # return user == msg_author (toggle this to allow only the person who initiated the command to use)
            return not user.bot and user == msg_author

        # Let user scroll between pages
        while True:
            try:
                # wait_for takes in the event to wait for and a check function that takes the arguments of the event
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)

                # next page, last page, prev page, first page
                if str(reaction.emoji) == right_arrow:
                    await message.remove_reaction(right_arrow, user)

                    # If already on last page, skip
                    if curr_page == len(final_pages) - 1:
                        continue

                    curr_page += 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == arrow_end:
                    await message.remove_reaction(arrow_end, user)
                    if curr_page == len(final_pages) - 1:
                        continue

                    curr_page = len(final_pages) - 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == left_arrow:
                    await message.remove_reaction(left_arrow, user)
                    if curr_page == 0:
                        continue

                    curr_page -= 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == arrow_start:
                    await message.remove_reaction(arrow_start, user)
                    if curr_page == 0:
                        continue

                    curr_page = 0
                    await message.edit(embed=final_pages[curr_page])

            except asyncio.TimeoutError:
                print('bad')
                break

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
        # em.set_thumbnail(url=emoji_image_url)
        em.add_field(name=f'{username}\'s favorite reaction:', value=f'{fav_react}', inline=False)
        await ctx.send(embed=em)

    @commands.command(brief='Lists full stats for every react (.fullreactstats)')
    async def fullreactstats(self, ctx, mode='normal'):
        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id
        msg_author = ''
        async for message in ctx.channel.history(limit=1):
            msg_author = message.author

        # If last word is unicode or custom, it will grab specific types of reactions
        if mode == 'unicode' or mode == 'UNICODE':
            mode = 'unicode'
        elif mode == 'custom' or mode == 'CUSTOM':
            mode = 'custom'

        # Grabs all reactions
        record = getFullReactStats(cursor, guild_id, mode)
        # cursor.execute("""
        #             SELECT reactid, SUM(cnt)
        #             FROM users WHERE users.emojitype = 'react' AND guildid = %s
        #             GROUP BY reactid
        #             ORDER BY SUM(cnt) DESC""", (guild_id,))
        # record = cursor.fetchall()

        # Handle empty results
        if len(record) == 0:
            await ctx.send('No reaction data found.')
            return

        # Fetch single sum value
        emojiSum = getEmojiSumRct(cursor, guild_id)
        finalList = processListRct(self.client, record, emojiSum)

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

        # TODO: multi-page embeds
        # If only 1 page, then get the result and display
        page_content = []  # the final list of results for each page
        if len(finalList) <= 5:
            page_content.append(getResult(finalList))
            em = discord.Embed(colour=discord.Colour.blurple(), title=f'Full statistics for all reactions used', )
            em.add_field(name='Reactions used in server', value=f'{page_content[0]}', inline=False)
            await ctx.send(embed=em)
            return

        # Aggregate results into 5 results per page
        index = 0
        while index < len(finalList):
            # For the last page, get remaining results
            if index > len(finalList) - 5:
                res = getResult(finalList[index:len(finalList)], index + 1)
                page_content.append(res)
                index += 5
            else:
                res = getResult(finalList[index:index + 5], index + 1)
                page_content.append(res)
                index += 5

        # Add embeds into final pages
        final_pages = []
        for i in range(len(page_content)):
            embed = discord.Embed(colour=discord.Colour.blurple(), title=f'Page {i + 1}/{len(page_content)}',
                                  description=page_content[i], )
            if i == 0:
                embed.title = f'Page {i + 1}/{len(page_content)} Full statistics for all reactions used'
            final_pages.append(embed)

        curr_page = 0

        message = await ctx.send(embed=final_pages[curr_page])
        await message.add_reaction(arrow_start)
        await message.add_reaction(left_arrow)
        await message.add_reaction(right_arrow)
        await message.add_reaction(arrow_end)

        # Wait for the author to flip the page with a reaction
        def check(reaction, user):
            return user == msg_author and not user.bot

        # Let user scroll between pages
        while True:
            try:
                # wait_for takes in the event to wait for and a check function that takes the arguments of the event
                reaction, user = await self.client.wait_for('reaction_add', timeout=45.0, check=check)

                # next page, last page, prev page, first page
                if str(reaction.emoji) == right_arrow:
                    await message.remove_reaction(right_arrow, user)

                    # If already on last page, skip
                    if curr_page == len(final_pages) - 1:
                        continue

                    curr_page += 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == arrow_end:
                    await message.remove_reaction(arrow_end, user)
                    if curr_page == len(final_pages) - 1:
                        continue

                    curr_page = len(final_pages) - 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == left_arrow:
                    await message.remove_reaction(left_arrow, user)
                    if curr_page == 0:
                        continue

                    curr_page -= 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == arrow_start:
                    await message.remove_reaction(arrow_start, user)
                    if curr_page == 0:
                        continue

                    curr_page = 0
                    await message.edit(embed=final_pages[curr_page])

            except asyncio.TimeoutError:
                print('bad')
                break


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


def getUserReacts(cursor, guild_id, user_id, mode):
    sqlString = ''
    if mode == 'custom':
        sqlString = """
        SELECT reactid, cnt FROM users
        WHERE userid = %s AND guildid = %s
        AND users.emojitype = 'react' AND reactid LIKE '<%%'
        ORDER BY cnt DESC;"""
        # print('Getting custom emojis')
    elif mode == 'unicode':
        sqlString = """
        SELECT reactid, cnt FROM users
        WHERE userid = %s AND guildid = %s
        AND users.emojitype = 'react' AND reactid NOT LIKE '<%%'
        ORDER BY cnt DESC;"""
        # print('Getting unicode emojis')
    else:
        sqlString = """
        SELECT reactid, cnt FROM users
        WHERE userid = %s AND guildid = %s
        AND users.emojitype = 'react'
        ORDER BY cnt DESC;"""
        # print('Normal')

    cursor.execute(sqlString, (str(user_id), guild_id))
    record = cursor.fetchall()

    return record

def getFullReactStats(cursor, guild_id, mode):
    if mode == 'unicode':
        cursor.execute("""
        SELECT reactid, SUM(cnt)
        FROM users WHERE users.emojitype = 'react' AND guildid = %s AND reactid NOT LIKE '<%%'
        GROUP BY reactid
        ORDER BY SUM(cnt) DESC""", (guild_id,))
    elif mode == 'custom':
        cursor.execute("""
        SELECT reactid, SUM(cnt)
        FROM users WHERE users.emojitype = 'react' AND guildid = %s AND reactid LIKE '<%%'
        GROUP BY reactid
        ORDER BY SUM(cnt) DESC""", (guild_id,))
    else:
        cursor.execute("""
        SELECT reactid, SUM(cnt)
        FROM users WHERE users.emojitype = 'react' AND guildid = %s
        GROUP BY reactid
        ORDER BY SUM(cnt) DESC""", (guild_id,))

    record = cursor.fetchall()
    return record


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
