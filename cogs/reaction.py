import asyncio
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
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d")

        # Get db connection and check
        conn, cursor = getConnection()

        try:
            cursor.execute("""
                        INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, chid)
                        VALUES(%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT(emoji, emojitype, userid, guildid, emojidate) 
                        DO UPDATE SET cnt = emojis.cnt + 1""",
                           (value, 'react', user_id, str(guild_id), 1, curr_time, ch_id))
            conn.commit()
        except Exception:
            print('Error: database is full')
        finally:
            cursor.close()  # Close cursor
            ps_pool.putconn(conn)  # Close connection

    # Handles processing when reaction is removed from a message
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):

        channel_name = reaction.message.channel.name

        guild_id = str(reaction.message.guild.id)
        user_id = str(user.id)
        value = str(reaction.emoji)
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d")

        # Get db connection and check
        conn, cursor = getConnection()

        try:
            cursor.execute("""UPDATE emojis SET cnt = emojis.cnt - 1 WHERE emoji = %s AND userid = %s AND guildid = %s
                            AND emojitype = 'react' AND cnt > 0 and emojidate = %s""", (value, user_id, guild_id, curr_time))
            conn.commit()
        except Exception:
            print('Error: database full')
        finally:
            cursor.close()  # Close cursor
            ps_pool.putconn(conn)  # Close connection

    # Gets the list of most used emojis for reactions
    @commands.command(brief="""Get list of top <N> most used reacts 
        (.topreacts OR .topreacts <num> <mode=normal,custom,unicode>)""")
    async def topreacts(self, ctx, amt=5, mode='normal'):
        await ctx.channel.purge(limit=1)
        # Handle invalid amount
        if amt < 1 or amt > 20:
            await ctx.send(f'Error: enter an amount between 1-20')
            return

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Query records for top reactions
        record = None
        try:
            record, title, emojiSum = getTopReacts(cursor, guild_id, amt, mode)
        except Exception:
            await ctx.send('Error gathering top reaction data')
        finally:
            cursor.close()  # Close cursor
            ps_pool.putconn(conn)  # Close connection

        if record is None:
            await ctx.send(f'No reaction data available')
            return

        # Process final list and results
        finalList = processListRct(self.client, record, emojiSum)
        result = getResult(finalList)

        # Display results
        embed = discord.Embed(colour=discord.Colour.blurple())
        embed.set_thumbnail(url=emoji_image_url)
        embed.add_field(name=f'{title}', value=f'{result}', inline=False)
        await ctx.send(embed=embed)

    # Gets a list of reacts by user (Can use nickname or mention)
    @commands.command(brief='Get list of most used reacts by user (.userreacts <@username/nickname>')
    async def userreacts(self, ctx, *args):
        await ctx.channel.purge(limit=1)
        usr_name = ' '.join(args)
        guild_id = ctx.guild.id

        # If last word is unicode or custom, it will grab specific types of reactions
        lastNdx = usr_name.rfind(' ')
        mode = 'normal'
        if lastNdx != -1:
            lastWord = usr_name[lastNdx + 1:]
            if lastWord == 'unicode' or lastWord == 'UNICODE':
                mode = 'unicode'
                usr_name = usr_name[:lastNdx]
            elif lastWord == 'custom' or lastWord == 'CUSTOM':
                mode = 'custom'
                usr_name = usr_name[:lastNdx]

        user, username, userID, valid = processName(self.client, ctx, str(usr_name))

        msg_author = ''
        async for message in ctx.channel.history(limit=1):
            msg_author = message.author

        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e userreacts <@username> <option>')
            return

        # Get db connection and check
        conn, cursor = getConnection()

        # Fetch user records and reaction count
        record = None
        try:
            record, emojiSum = getUserReacts(cursor, guild_id, userID, mode)
        except Exception:
            await ctx.send('Error gathering user reaction data')
        finally:
            cursor.close()  # Close cursor
            ps_pool.putconn(conn)  # Close connection

        # Check for empty record
        if record is None:
            await ctx.send(f'{username}\'s reaction list is empty!')
            return

        # Process reaction list
        finalList = processListRct(self.client, record, emojiSum)

        # Generate final embed pages
        page_content, final_pages = gen_embed_pages(finalList, username)

        # If only 1 page, then get the result and display
        if len(final_pages) == 1:
            em = discord.Embed(colour=discord.Colour.blurple(), title=f'{username}\'s reaction stats', )
            em.add_field(name='Reactions used in server', value=f'{page_content[0]}', inline=False)
            await ctx.send(embed=em)
            return

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
        await ctx.channel.purge(limit=1)
        usr_name = ' '.join(args)

        # Get the user info from @mention or user's nickname
        user, username, userID, valid = processName(self.client, ctx, usr_name)
        guild_id = str(ctx.guild.id)

        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e favreact <@username>')
            return

        # Get db connection
        conn, cursor = getConnection()

        # Get the data
        record = None
        try:
            record, emojiSum = getFavoriteReact(cursor, userID, guild_id)
        except Exception:
            await ctx.send('Error getting favorite emoji')
        finally:
            cursor.close()
            ps_pool.putconn(conn)

        # Check for empty records
        if record is None:
            await ctx.send('No emoji data found')
            return

        # Convert records into list for display
        finalList = processListMsg(self.client, record, emojiSum)

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
        await ctx.channel.purge(limit=1)
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
        record = None
        try:
            record, emojiSum = getFullReactStats(cursor, guild_id, mode)
        except Exception:
            await ctx.send('Error gathering reaction stats')
        finally:
            cursor.close()  # Close cursor
            ps_pool.putconn(conn)  # Close connection

        # Handle empty results
        if record is None:
            await ctx.send('No reaction data found.')
            return

        # Process final list
        finalList = processListRct(self.client, record, emojiSum)
        page_content, final_pages = gen_embed_pages(finalList, user_name=ctx.guild.name)

        # If only 1 page, then get the result and display
        if len(final_pages) == 1:
            # page_content.append(getResult(finalList))
            em = discord.Embed(colour=discord.Colour.blurple(), title=f'{ctx.guild.name} reaction stats', )
            em.add_field(name='Reactions used in server', value=f'{page_content[0]}', inline=False)
            await ctx.send(embed=em)
            return

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

    # TODO: in progress
    @commands.command(brief='Get most used reaction today')
    async def reactstoday(self, ctx):
        await ctx.channel.purge(limit=1)

        today = datetime.datetime.now()
        last_24hr = today - datetime.timedelta(days=1)
        guild_id = str(ctx.guild.id)

        conn, cursor = getConnection()

        # Gather reactions used today
        record = None
        try:
            cursor.execute("""SELECT emoji, cnt FROM emojis 
                WHERE emojidate > (NOW() - INTERVAL '1 day') 
                AND guildid = %s AND emojitype = 'react'""", (str(guild_id), ))
            record = cursor.fetchall()
        except Exception:
            await ctx.send('Error gathering reactions today')
        finally:
            cursor.close()
            ps_pool.putconn(conn)

        if record is None:
            await ctx.send('No reaction data available')
            return

        finalList = getResult(processRecent(self.client, record))

        # Display results
        try:
            embed = discord.Embed(colour=discord.Colour.blurple())
            embed.set_thumbnail(url=emoji_image_url)
            embed.add_field(name=f'Reactions used within the past day', value=f'{finalList}', inline=False)
            await ctx.send(embed=embed)
        except Exception :
            await ctx.send(f'No data available')

    # TODO: in progress
    @commands.command(brief='Get top 5 most recently used reactions')
    async def recentreacts(self, ctx):
        print()


def setup(client):
    client.add_cog(Reaction(client))


# Generates pages for the embed
def gen_embed_pages(finalList, user_name):
    page_content = []
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
                          f'{user_name}\'s {len(finalList)} most used reactions'

        embed.set_thumbnail(url=emoji_image_url)
        final_pages.append(embed)

    return page_content, final_pages

def getTopReacts(cursor, guild_id, amt, mode):
    if mode == 'custom':
        cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND emojis.guildid = %s AND emoji LIKE '<%%'
            GROUP BY emoji
            ORDER BY SUM(cnt) DESC
            LIMIT (%s)""", (str(guild_id), amt))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server! (custom emojis)'
    elif mode == 'unicode':
        cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND emojis.guildid = %s AND emoji NOT LIKE '<%%'
            GROUP BY emoji
            ORDER BY SUM(cnt) DESC
            LIMIT (%s)""", (str(guild_id), amt))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server! (Unicode emojis)'
    else:
        cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND emojis.guildid = %s
            GROUP BY emoji
            ORDER BY SUM(cnt) DESC
            LIMIT (%s)""", (str(guild_id), amt))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server!'

    if len(record) == 0:
        return None, None

    # Get total reactions used in the server
    emojiSum = get_react_sum(cursor, guild_id)

    return record, title, emojiSum


# Get user reactions
def getUserReacts(cursor, guild_id, user_id, mode):
    sqlString = ''
    if mode == 'custom':
        sqlString = """
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'react' AND guildid = %s AND userid = %s AND emoji LIKE '<%%'
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        """

    elif mode == 'unicode':
        sqlString = """
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'react' AND guildid = %s AND userid = %s AND emoji NOT LIKE '<%%'
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        """
    else:
        sqlString = """
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'react' AND guildid = %s AND userid = %s
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        """

    cursor.execute(sqlString, (str(guild_id), str(user_id)))
    record = cursor.fetchall()

    if len(record) == 0:
        return None, None

    emojiSum = get_react_sum_user(cursor, user_id, guild_id)

    return record, emojiSum


# Get favorite react
def getFavoriteReact(cursor, user_id, guild_id):
    cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND userid = %s AND guildid = %s
            GROUP BY emoji ORDER BY SUM(cnt) DESC
            LIMIT 1""", (str(user_id), str(guild_id)))

    record = cursor.fetchall()

    if len(record) == 0:
        return None, None

    emojiSum = get_react_sum_user(cursor, str(user_id), str(guild_id))
    return record, emojiSum


def getFullReactStats(cursor, guild_id, mode):
    if mode == 'custom':
        cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND emojis.guildid = %s AND emoji LIKE '<%%'
            GROUP BY emoji
            ORDER BY SUM(cnt) DESC
            """, (str(guild_id),))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server! (custom emojis)'
    elif mode == 'unicode':
        cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND emojis.guildid = %s AND emoji NOT LIKE '<%%'
            GROUP BY emoji
            ORDER BY SUM(cnt) DESC
            """, (str(guild_id),))
        record = cursor.fetchall()
        title = f'Top {len(record)} most popular reacts in this server! (Unicode emojis)'
    else:
        cursor.execute("""
            SELECT emoji, SUM(cnt) FROM emojis
            WHERE emojis.emojitype = 'react' AND emojis.guildid = %s
            GROUP BY emoji
            ORDER BY SUM(cnt) DESC
            """, (str(guild_id),))

    record = cursor.fetchall()

    if len(record) == 0:
        return None, None

    emojiSum = get_react_sum(cursor, guild_id)

    return record, emojiSum


# Get total count of reactions by user in the server
def get_react_sum_user(cursor, user_id, guild_id):
    sumSql = """SELECT SUM(cnt) FROM emojis WHERE userid = %s AND emojitype = 'react' AND guildid = %s"""
    cursor.execute(sumSql, (str(user_id), str(guild_id)))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])

    return emojiSum


# Get total count of reactions in the server
def get_react_sum(cursor, guild_id):
    # Get total reactions used in the server
    cursor.execute("""
        SELECT SUM(cnt) FROM emojis 
        WHERE emojitype = 'react' AND guildid = %s""", (str(guild_id),))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])

    return emojiSum
