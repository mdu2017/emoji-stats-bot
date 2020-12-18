import asyncio

import discord
from discord.ext import commands
from emoji import UNICODE_EMOJI
import regex
import re
from const import *
from itertools import islice
import datetime


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

        # Don't count bot messages in statistics
        if message.author.bot:
            return

        msg = message.content

        ch_id = str(message.channel.id)
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        curr_time = datetime.datetime.now().strftime("%Y-%m-%d")

        # Get db connection and check
        conn, cursor = getConnection()

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
                cursor.execute("""
                    INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, chid)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(emoji, emojitype, userid, guildid, emojidate)
                    DO UPDATE SET cnt = emojis.cnt + 1
                """, (item, 'message', str(user_id), str(guild_id), 1, curr_time, ch_id))
                conn.commit()

        # Query unicode emojis into users db
        if len(unimojis) > 0:
            for item in unimojis:
                cursor.execute("""
                    INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, chid)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(emoji, emojitype, userid, guildid, emojidate)
                    DO UPDATE SET cnt = emojis.cnt + 1
                """, (item, 'message', str(user_id), str(guild_id), 1, curr_time, ch_id))
                conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Close connection

    # Returns the top 5 most used emojis in messages
    @commands.command(brief='Display overall stats for emojis used in messages')
    async def topemojis(self, ctx, amt=5):
        await ctx.channel.purge(limit=1)

        # Handle invalid amount
        if amt < 1 or amt > 20:
            await ctx.send(f'Error: enter an amount between 1-20')
            return

        # Get db connection and check
        conn, cursor = getConnection()
        guild_id = ctx.guild.id

        # Grabs top 5 most used reacts in messages
        record, emojiSum = get_top_emojis(cursor, guild_id, amt)

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

        # Check empty query
        if record is None:
            await ctx.send('No emoji data found')
            return

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
        em.set_thumbnail(url=emoji_image_url)
        em.add_field(name=f'The {len(finalList)} most used emojis in messages in the server',
                     value=f'{result}', inline=False)

        # Display results
        await ctx.send(embed=em)

    @commands.command(brief='Displays most used emojis in messages by user')
    async def useremojis(self, ctx, *args):
        await ctx.channel.purge(limit=1)

        usr_name = ' '.join(args)

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

        user, username, userID, valid = processName(self.client, ctx, usr_name)
        guild_id = str(ctx.guild.id)

        msg_author = ''
        async for message in ctx.channel.history(limit=1):
            msg_author = message.author

        # Check for empty user
        if not valid:
            await ctx.send(f'User {usr_name} was not found\nUsage: !e useremojis <@username>')
            return

        # Get db connection and check
        conn, cursor = getConnection()

        record, emojiSum = get_user_emojis(cursor, guild_id, mode, userID)

        if record is None:
            await ctx.send('No emoji data found')
            return

        # Fetch total emojis used
        finalList = processListMsg(self.client, record, emojiSum)

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'{username}\' has no emoji data')
            return

        page_content, final_pages = gen_embed_pages_emoji(finalList, username)

        if len(final_pages) == 1:
            em = discord.Embed(colour=discord.Colour.blurple(), title=f'Emoji stats for {username}', )
            em.add_field(name='Emojis used in server', value=f'{page_content[0]}', inline=False)
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

    @commands.command(brief='Lists user\'s favorite emote')
    async def favemoji(self, ctx, *args):
        await ctx.channel.purge(limit=1)
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
        record, emojiSum = get_fav_emoji(cursor, guild_id, userID)

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)


        # Check for empty records
        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

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
        # em.set_thumbnail(url=emoji_image_url)
        em.add_field(name=f'{username}\'s favorite emoji:', value=f'{favoriteEmoji}', inline=False)
        await ctx.send(embed=em)

    @commands.command(brief='Stat for every emoji used in messages')
    async def fullmsgstats(self, ctx, mode='normal'):
        await ctx.channel.purge(limit=1)
        guild_id = str(ctx.guild.id)
        msg_author = ''
        async for message in ctx.channel.history(limit=1):
            msg_author = message.author
            # print(f'msg author {msg_author}')

        # If last word is unicode or custom, it will grab specific types of reactions
        if mode == 'unicode' or mode == 'UNICODE':
            mode = 'unicode'
        elif mode == 'custom' or mode == 'CUSTOM':
            mode = 'custom'

        # Get db connection and check
        conn, cursor = getConnection()

        record, emojiSum = get_full_emoji_stats(cursor, guild_id, mode)
        if len(record) == 0:
            await ctx.send('No emoji data found')
            return

        # Get sum and final list
        finalList = processListMsg(self.client, record, emojiSum)

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'No data available')
            return

        # Close db stuff
        cursor.close()
        ps_pool.putconn(conn)

        # If only 1 page, then get the result and display
        page_content, final_pages = gen_embed_pages_emoji(finalList, user_name=ctx.guild.name)
        if len(final_pages) == 1:
            em = discord.Embed(colour=discord.Colour.blurple(), title=f'Full statistics for {ctx.guild.name} server',)
            em.add_field(name='Emojis used in server', value=f'{page_content[0]}', inline=False)
            await ctx.send(embed=em)
            return


        # TODO: multiple page embeds
        index = 0  # index keeps track of current item's index

        # Aggregate results into 5 results per page
        while index < len(finalList):
            # For the last page, get remaining results
            if index > len(finalList) - 5:
                res = getResult(finalList[index:len(finalList)], index+1)
                page_content.append(res)
                index += 5
            else:
                res = getResult(finalList[index:index+5], index+1)
                page_content.append(res)
                index += 5

        # Add embeds into final pages
        final_pages = []
        for i in range(len(page_content)):
            embed = discord.Embed(colour=discord.Colour.blurple(), title=f'Page {i+1}/{len(page_content)}',
                                  description=page_content[i],)
            final_pages.append(embed)

        curr_page = 0

        message = await ctx.send(embed=final_pages[curr_page])
        await message.add_reaction(arrow_start)
        await message.add_reaction(left_arrow)
        await message.add_reaction(right_arrow)
        await message.add_reaction(arrow_end)

        # Wait for the author to flip the page with a reaction
        def check(reaction, user):
            # return user == msg_author (toggle this to allow only the person who initiated the command to use)
            return not user.bot

        # Let user scroll between pages
        while True:
            try:
                # wait_for takes in the event to wait for and a check function that takes the arguments of the event
                reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=check)

                # next page, last page, prev page, first page
                if str(reaction.emoji) == right_arrow:
                    await message.remove_reaction(right_arrow, user)

                    # If already on last page, skip
                    if curr_page == len(final_pages)-1:
                        continue

                    curr_page += 1
                    await message.edit(embed=final_pages[curr_page])
                elif str(reaction.emoji) == arrow_end:
                    await message.remove_reaction(arrow_end, user)
                    if curr_page == len(final_pages)-1:
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
    @commands.command(brief='Get most used emojis today')
    async def emojistoday(self, ctx):
        await ctx.channel.purge(limit=1)
        conn, cursor = getConnection()

        today = datetime.datetime.now()
        last_24hr = today - datetime.timedelta(days=1)

        guild_id = str(ctx.guild.id)

        cursor.execute("""SELECT emoji, cnt FROM emojis 
            WHERE emojidate > (NOW() - INTERVAL '1 day') 
            AND guildid = %s AND emojitype = 'message'""", (str(guild_id),))


        record = cursor.fetchall()
        cursor.close()
        ps_pool.putconn(conn)

        finalList = getResult(processRecent(self.client, record))

        # Display results
        try:
            embed = discord.Embed(colour=discord.Colour.blurple())
            embed.set_thumbnail(url=emoji_image_url)
            embed.add_field(name=f'Emojis used within the past day', value=f'{finalList}', inline=False)
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("No data available")


def setup(client):
    client.add_cog(Message(client))

def gen_embed_pages_emoji(finalList, user_name):
    page_content = []

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
                          f'{user_name}\'s {len(finalList)} most used emojis'

        embed.set_thumbnail(url=emoji_image_url)
        final_pages.append(embed)

    return page_content, final_pages


def get_top_emojis(cursor, guild_id, amt):
    cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND emojis.guildid = %s
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        LIMIT (%s)""", (str(guild_id), amt))
    record = cursor.fetchall()

    if len(record) == 0:
        return None, None

    emojiSum = get_emoji_sum(cursor, guild_id)

    return record, emojiSum

def get_user_emojis(cursor, guild_id, mode, userID):
    if mode == 'unicode':
        cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND guildid = %s AND userid = %s AND emoji NOT LIKE '<%%'
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        """, (str(guild_id), str(userID)))
    elif mode == 'custom':
        cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND guildid = %s AND userid = %s AND emoji LIKE '<%%'
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        """, (str(guild_id), str(userID)))
    else:
        cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND guildid = %s AND userid = %s
        GROUP BY emoji ORDER BY SUM(cnt) DESC
        """, (str(guild_id), str(userID)))

    record = cursor.fetchall()

    if len(record) == 0:
        return None, None

    emojiSum = get_emoji_sum_usr(cursor, guild_id, userID)
    print(f'Emoji sum: {emojiSum}')

    return record, emojiSum

def get_fav_emoji(cursor, guild_id, user_id):
    cursor.execute("""
    SELECT emoji, SUM(cnt) FROM emojis
    WHERE emojis.emojitype = 'message' AND guildid = %s AND userid = %s
    GROUP BY emoji ORDER BY SUM(cnt) DESC LIMIT 1
    """, (str(guild_id), str(user_id)))

    record = cursor.fetchall()
    if len(record) == 0:
        return None, None
    emojiSum = get_emoji_sum_usr(cursor, guild_id, user_id)

    return record, emojiSum

def get_full_emoji_stats(cursor, guild_id, mode):
    if mode == 'unicode':
        cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND emojis.guildid = %s AND emoji NOT LIKE '<%%'
        GROUP BY emoji ORDER BY SUM(cnt) DESC """, (str(guild_id),))
    elif mode == 'custom':
        cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND emojis.guildid = %s AND emoji LIKE '<%%'
        GROUP BY emoji ORDER BY SUM(cnt) DESC """, (str(guild_id),))
    else:
        cursor.execute("""
        SELECT emoji, SUM(cnt) FROM emojis
        WHERE emojis.emojitype = 'message' AND emojis.guildid = %s
        GROUP BY emoji ORDER BY SUM(cnt) DESC """, (str(guild_id),))

    record = cursor.fetchall()
    if len(record) == 0:
        return None, None
    emojiSum = get_emoji_sum(cursor, guild_id)

    return record, emojiSum

# Gets sum of total emojis used in messages
def get_emoji_sum(cursor, guild_id):
    cursor.execute("""SELECT SUM(cnt) FROM emojis WHERE emojitype = 'message' AND guildid = %s""", (str(guild_id),))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])

    return emojiSum


# Get sum of total emojis used in user emoji commands
def get_emoji_sum_usr(cursor, guild_id, userID):
    cursor.execute("""
                SELECT SUM(cnt) FROM emojis WHERE userid = %s 
                AND emojitype = 'message' AND guildid = %s""", (str(userID), str(guild_id)))
    emojiSum = cursor.fetchone()
    emojiSum = int(emojiSum[0])
    return emojiSum
