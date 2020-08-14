import discord
from discord.ext import commands, tasks
from const import *
import random
import re
import regex
import string
import unicodedata
from emoji import UNICODE_EMOJI
import emoji


class General(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()  # Changes status every hour
        print('general file ready')

    @commands.Cog.listener()
    async def on_member_join(self, member):  # method expected by client. This runs once when connected
        print(f'{member} has joined the server')  # notification of login.

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} has quit! Boo!')

    # Change bot status every 10 mins
    @tasks.loop(seconds=600)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(next(customStatus)))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        channel = reaction.message.channel
        msg = reaction.message.content
        userid = str(user.id)
        emojiID = reaction.emoji

        value = str(emojiID)  # Stringify emoji for database

        # Handle user specific data table (both user and react have to exist)
        userData = await self.client.pg_con.fetch("""
            SELECT userid, reactid FROM users 
            WHERE userid = $1 AND reactid = $2 AND emojitype = 'react'""", userid, value)

        if not userData:
            await self.client.pg_con.execute("""
                INSERT INTO users(userid, reactid, cnt, emojitype) 
                VALUES($1, $2, 1, 'react')""", userid, value)
            # print(f'successfully added -- \n')
        else:
            await self.client.pg_con.execute("""
                UPDATE users SET cnt = cnt + 1 
                WHERE users.userid = $1 AND users.reactid = $2 AND emojitype = 'react'""", userid, value)
            # print(f'successfully updated -- \n')

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user): # TODO: Note -- calling swap command doesn't trigger this...
        channel = reaction.message.channel
        userid = str(user.id)
        emojiID = reaction.emoji
        value = str(emojiID)  # Stringify emoji for database

        # record = await self.client.pg_con.fetch("SELECT * FROM react WHERE react.reactid = $1", value)
        # if record:
        #     await self.client.pg_con.execute("""UPDATE react SET cnt = cnt - 1 WHERE react.reactid = $1 AND cnt > 0""", value)

        userData = await self.client.pg_con.fetch("""
            SELECT userid, reactid FROM users 
            WHERE userid = $1 AND reactid = $2 AND emojitype = 'react'""", userid, value)
        if userData:
            await self.client.pg_con.execute("""UPDATE users SET cnt = cnt - 1 
                WHERE users.userid = $1 
                AND users.reactid = $2 
                AND cnt > 0 AND users.emojitype = 'react'""", userid, value)
            print(f'Successfully removed -- \n')

    @commands.command(brief='Get list of top <N> most used reacts')
    async def topreacts(self, ctx, amt=8, mode='normal'):
        # Grabs top X most used reacts by type
        if mode == 'normal':
            await ctx.send(f'Overall top {amt} most popular reacts!')
            record = await self.client.pg_con.fetch("""
                SELECT reactid, SUM(cnt) FROM users
                WHERE users.emojitype = 'react'
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC
                LIMIT $1""", amt)
        elif mode == 'custom':
            await ctx.send(f'Overall top {amt} most popular reacts! (custom emojis)')
            record = await self.client.pg_con.fetch("""
                SELECT reactid, SUM(cnt) FROM users
                WHERE users.emojitype = 'react' AND reactid LIKE '<%'
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC
                LIMIT $1""", amt)
        elif mode == 'unicode':
            await ctx.send(f'Overall top {amt} most popular reacts! (Unicode emojis)')
            record = await self.client.pg_con.fetch("""
                SELECT reactid, SUM(cnt) FROM users
                WHERE users.emojitype = 'react' AND reactid NOT LIKE '<%'
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC
                LIMIT $1""", amt)

        # Fetch single sum value
        emojiSum = await self.client.pg_con.fetchval("""SELECT SUM(cnt) FROM users WHERE users.emojitype = 'react'""")

        # Assuming that record gives rows of exactly 2 columns
        data = dict(record)  # convert record to dictionary
        converted = list(tuple())  # Convert into tuples (emoji, name, count)
        finalList = []

        # Convert emoji into discord representation
        for key in data:
            keystr = str(key)
            percentage = round((data[key] / emojiSum) * 100, 2)
            if '<' in keystr:  # If it's a custom emoji, parse ID
                startIndex = keystr.rindex(':') + 1
                endIndex = keystr.index('>')
                id = int(key[startIndex:endIndex])
                name = 'EMOJI'
                currEmoji = self.client.get_emoji(id)
                if currEmoji is not None:
                    name = currEmoji.name
                # converted.append((currEmoji, name, data[key], percentage))  # Emoji name, emoji, frequency
                finalList.append(f'{currEmoji}: ({data[key]}) - {name} - {percentage}%')
            else:
                temp = handleSpecialEmojis(key)  # TODO: Some reacts won't have a mapping so 'EMOJI' is by default
                # converted.append((key, temp, data[key], percentage))
                finalList.append(f'{key}: ({data[key]})  {temp} - {percentage}%')

        # for item in converted:  # 0 is emoji, 1 is name, 2 is count, 3 is percentage
        #     finalList.append(f'{item[0]} - {item[2]}: {item[1]} - {item[3]}%')

        await ctx.send('\n'.join('{}: {}'.format(*k) for k in enumerate(finalList)))
        # await ctx.send(f'{finalList}')

    @commands.command(brief='Lists full stats for every react')
    async def fullstats(self, ctx):
        await ctx.send(f'Full stats on overall usage of each react')

        # Grabs top 8 most used reacts
        record = await self.client.pg_con.fetch("""
                SELECT reactid, SUM(cnt) FROM users
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC""")

        # Fetch single sum value
        emojiSum = await self.client.pg_con.fetchval("""SELECT SUM(cnt) FROM users""")

        # Assuming that record gives rows of exactly 2 columns
        data = dict(record)  # convert record to dictionary
        converted = list(tuple())  # Convert into tuples (emoji, name, count)

        # Convert emoji into discord representation
        for key in data:
            keystr = str(key)
            percentage = round((data[key] / emojiSum) * 100, 2)
            if '<' in keystr:  # If it's a custom emoji, parse ID
                startIndex = keystr.rindex(':') + 1
                endIndex = keystr.index('>')
                id = int(key[startIndex:endIndex])
                emoji = self.client.get_emoji(id)
                converted.append((emoji, emoji.name, data[key], percentage))  # Emoji name, emoji, frequency
            else:
                temp = handleSpecialEmojis(key)  # TODO: Some reacts won't have a mapping so 'EMOJI' is by default
                converted.append((key, temp, data[key], percentage))

        # Display statistics
        for item in converted:
            await ctx.send(f'{item[0]} - {item[2]}: {item[1]} - {item[3]}%')

    @commands.command(brief='Get list of top 10 most used reacts by user')
    async def emojistats(self, ctx, arg1='Pigboon'):
        user = None
        username = None
        userID = None

        # If mentioned, get by id
        if '@' in arg1 and '!' in arg1:
            idStr = str(arg1)
            idStr = idStr[idStr.index('!') + 1: idStr.index('>')]
            userID = int(idStr)
            user = self.client.get_user(userID)
            username = user.name
        else:
            # If by nickname, go through each member and search nickname
            for guild in self.client.guilds:
                for member in guild.members:
                    nickname = member.nick
                    if str(arg1) == str(nickname):
                        user = member
                        username = user.name
                        userID = user.id
                        break

        idValue = str(userID)

        if user is not None:
            await ctx.send(f'{username}\'s top 8 reacts!')

            # Leave off userid to fit into dictionary
            record = await self.client.pg_con.fetch("""
                SELECT reactid, cnt FROM users
                WHERE userid = $1
                AND users.emojitype = 'react'
                ORDER BY cnt DESC LIMIT 8;""", idValue)

            # Fetch single sum value
            emojiSum = await self.client.pg_con.fetchval("""
                SELECT SUM(cnt) FROM users 
                WHERE userid = $1 AND emojitype = 'react'""", idValue)

            data = dict(record)  # convert record to dictionary
            converted = list(tuple())  # Convert into tuples (emoji, name, count)

            # Convert emoji into discord representation and add percentages
            for key in data:
                keystr = str(key)
                percentage = round((data[key] / emojiSum) * 100, 2)
                if '<' in keystr:  # If it's a custom emoji, parse ID
                    startIndex = keystr.rindex(':') + 1
                    endIndex = keystr.index('>')
                    id = int(key[startIndex:endIndex])
                    emoji = self.client.get_emoji(id)
                    converted.append((emoji, emoji.name, data[key], percentage))  # Emoji name, emoji, frequency
                else:
                    temp = handleSpecialEmojis(key) # TODO: Some reacts won't have a mapping so 'EMOJI' is by default
                    converted.append((key, temp, data[key], percentage))

            # Display statistics
            for item in converted:
                await ctx.send(f'{item[0]} - {item[2]}: {item[1]} - {item[3]}%')

    # Overrides inherited cog_check method (Check before executing any commands)
    async def cog_check(self, ctx):
        # Prevent any commands from occuring in serious or debate channel
        if ctx.channel.name == 'serious' or ctx.channel.name == 'baboons-of-pig-york':
            return False
        else:
            return True

    # TODO: fill here
    @commands.command(brief='Display overall stats for emojis used in messages')
    async def topemojis(self, ctx, amt=8):
        await ctx.send(f'The {amt} most used emojis in messages!')


        # Grabs top 8 most used reacts in messages
        record = await self.client.pg_con.fetch("""
                    SELECT reactid, SUM(cnt) FROM users
                    WHERE users.emojitype = 'message'
                    GROUP BY reactid
                    ORDER BY SUM(cnt) DESC
                    LIMIT $1""", amt)

        # Fetch single sum value by message
        emojiSum = await self.client.pg_con.fetchval("""
                        SELECT SUM(cnt) FROM users WHERE emojitype = 'message'""")

        # Assuming that record gives rows of exactly 2 columns
        data = dict(record)  # convert record to dictionary
        converted = list(tuple())  # Convert into tuples (emoji, name, count)

        # Convert emoji into discord representation
        for key in data:
            keystr = str(key)
            percentage = round((data[key] / emojiSum) * 100, 2)
            if '<' in keystr:  # If it's a custom emoji, parse ID
                startIndex = keystr.rindex(':') + 1
                endIndex = keystr.index('>')
                id = int(key[startIndex:endIndex])
                emoji = self.client.get_emoji(id)
                converted.append((emoji, emoji.name, data[key], percentage))  # Emoji name, emoji, frequency
            else:
                temp = handleSpecialEmojis(key)  # TODO: Some reacts won't have a mapping so 'EMOJI' is by default
                converted.append((key, temp, data[key], percentage))

        # Display statistics
        for item in converted:
            await ctx.send(f'{item[0]} - {item[2]}: {item[1]} - {item[3]}%')


    @commands.Cog.listener() # Cog on_message automatically runs comands once
    async def on_message(self, message):

        # Make sure bot doesn't respond its own message
        if message.author == self.client.user:
            return

        ctx = await self.client.get_context(message)
        msg = message.content

        userid = str(message.author.id) # Store as string in DB

        # If bot receives a DM, handle separately and end TODO: can remove later
        # if isinstance(ctx.channel, discord.channel.DMChannel):
        #     randResponse = random.choice(cannedResponses)
        #     await ctx.send(f'{randResponse}')
        #     return

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
                existingData = await self.client.pg_con.fetch("""
                    SELECT userid, reactid FROM users
                    WHERE userid = $1 AND reactid = $2 AND emojitype = 'message'""", userid, item)

                if not existingData:
                    # print('Successfully adding custom emoji in msg')
                    await self.client.pg_con.execute("""
                        INSERT INTO users(userid, reactid, cnt, emojitype)
                        VALUES ($1, $2, 1, 'message')""", userid, item)
                else:
                    # print(f'Custom emoji exists, updating entry')
                    await self.client.pg_con.execute("""
                        UPDATE users SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND userid = $1 AND reactid = $2""", userid, item)

        # Query unicode emojis into users db
        if len(unimojis) > 0:
            for item in unimojis:
                existingData = await self.client.pg_con.fetch("""
                    SELECT userid, reactid FROM users 
                    WHERE userid = $1 AND reactid = $2 AND emojitype = 'message'""", userid, item)

                if not existingData:
                    # print('Successfully adding unicode emoji in msg')
                    await self.client.pg_con.execute("""
                        INSERT INTO users(userid, reactid, cnt, emojitype)
                        VALUES ($1, $2, 1, 'message')""", userid, item)
                else:
                    # print('Unicode emoji exists, updating entry')
                    await self.client.pg_con.execute("""
                        UPDATE users SET cnt = cnt + 1
                        WHERE emojitype = 'message' AND userid = $1 AND reactid = $2""", userid, item)

    @commands.command(brief='Put bot to sleep')
    async def sleep(self, ctx):
        await self.client.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='Sleeping'),
            status=discord.Status.idle, afk=True)
        await ctx.channel.purge(limit=1)

    @commands.command(pass_context=True)
    async def deletethis(self, ctx):
        await self.client.say('Command received')
        await self.client.delete_message(ctx.message)
        await self.client.say('Message deleted')

    @commands.command(brief='Wake up the bot')
    async def awake(self, ctx):
        await self.client.change_presence(activity=discord.Game(f'Dominos {PIZZA}'), status=discord.Status.online,
                                          afk=False)
        await ctx.channel.purge(limit=1)

    @commands.command()
    async def watching(self, ctx):
        act = discord.Activity(type=discord.ActivityType.watching, name="YouTube")
        on = discord.Status.online

        await self.client.change_presence(activity=act, status=on)
        await ctx.channel.purge(limit=1)

    # Function name is the command name (ex: .ping)
    @commands.command(brief='Displays network latency')
    async def ping(self, ctx):
        await ctx.send(f'{round(self.client.latency * 1000)}ms')

    # Clears an X amount of messages from the channel (default 3) - (.cls or .clear)
    @commands.command(brief='Remove <X> amt of messages', aliases=['cls'], pass_context=True)
    async def clear(self, ctx, amount=3):

        # Disable feature for serious/news channel
        if ctx.channel.name == 'serious' or ctx.channel.name == 'baboons-of-pig-york':
            return

        if amount < 1 or amount > 25:
            await ctx.send('Error: amount needs to be between 1-25')
            return

        # remove clear command
        await ctx.channel.purge(limit=1)

        # remove <amount> of messages
        await ctx.channel.purge(limit=amount)

    # Logs out and closes connection
    @commands.command(brief='Logs the bot out')
    async def shutitoff(self, ctx):
        await ctx.channel.purge(limit=1)
        await self.client.logout()


def setup(client):
    client.add_cog(General(client))


def handleSpecialEmojis(key):
    name = 'EMOJI'
    try:
        name = unicodedata.name(key)
    except Exception as ex:
        print(f'Error: {ex}')

    return name
