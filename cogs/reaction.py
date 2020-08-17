import discord
from discord.ext import commands
from const import handleSpecialEmojis


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
        msg = reaction.message.content
        userid = str(user.id)
        emojiID = reaction.emoji

        value = str(emojiID)  # Stringify emoji for database

        # Handle user specific data table (both user and react have to exist)
        userData = await self.client.pg_con.fetch("""
                SELECT userid, reactid FROM users 
                WHERE userid = $1 AND reactid = $2 AND emojitype = 'react'""", userid, value)

        chData = await self.client.pg_con.fetch("""
                        SELECT chname, reactid FROM channel 
                        WHERE chname = $1 AND reactid = $2 AND emojitype = 'react'""", channel_name, value)

        # Process user data
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

        # Process channel data
        if not chData:
            await self.client.pg_con.execute("""
                INSERT INTO channel(chname, reactid, cnt, emojitype) 
                VALUES($1, $2, 1, 'react')""", channel_name, value)
        else:
            await self.client.pg_con.execute("""
                UPDATE channel SET cnt = cnt + 1
                WHERE chname = $1 AND reactid = $2 AND emojitype = 'react'""", channel_name, value)


    # Handles processing when reaction is removed from a message
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        channel_name = reaction.message.channel.name
        userid = str(user.id)
        emojiID = reaction.emoji
        value = str(emojiID)  # Stringify emoji for database

        # Handle user data
        userData = await self.client.pg_con.fetch("""
                SELECT userid, reactid FROM users 
                WHERE userid = $1 AND reactid = $2 AND emojitype = 'react'""", userid, value)
        if userData:
            await self.client.pg_con.execute("""UPDATE users SET cnt = cnt - 1 
                    WHERE users.userid = $1 
                    AND users.reactid = $2 
                    AND cnt > 0 AND users.emojitype = 'react'""", userid, value)
            # print(f'Successfully removed -- \n')

        # Handle channel data
        chData = await self.client.pg_con.fetch("""
                SELECT chname, reactid FROM channel 
                WHERE chname = $1 AND reactid = $2 AND emojitype = 'react'""", channel_name, value)
        if chData:
            await self.client.pg_con.execute("""
                UPDATE channel SET cnt = cnt - 1
                WHERE chname = $1 AND reactid = $2 AND emojitype = 'react' AND cnt > 0""", channel_name, value)

    # Gets the list of most used emojis for reactions
    @commands.command(brief="""Get list of top <N> most used reacts 
                            | Usage: .topreacts OR .topreacts <num> <mode> |
                             Modes include 'normal', 'custom', 'unicode' """)
    async def topreacts(self, ctx, amt=5, mode='normal'):
        # Handle invalid amount
        if amt < 1 or amt > 15:
            await ctx.send(f'Error: enter an amount between 1-20')
            return

        if mode == 'custom':
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
        else:
            # Grabs top X most used reacts by type
            if mode == 'normal':
                await ctx.send(f'Overall top {amt} most popular reacts!')
                record = await self.client.pg_con.fetch("""
                SELECT reactid, SUM(cnt) FROM users
                WHERE users.emojitype = 'react'
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC
                LIMIT $1""", amt)

        # Fetch single sum value
        emojiSum = await self.client.pg_con.fetchval(
            """SELECT SUM(cnt) FROM users WHERE users.emojitype = 'react'""")

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

    # Gets a list of reacts by user (Can use nickname or mention)
    @commands.command(brief='Get list of top 10 most used reacts by user')
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

        idValue = str(userID)

        # Leave off userid to fit into dictionary
        record = await self.client.pg_con.fetch("""
                SELECT reactid, cnt FROM users
                WHERE userid = $1
                AND users.emojitype = 'react'
                ORDER BY cnt DESC LIMIT 5;""", idValue)

        # Fetch single sum value
        emojiSum = await self.client.pg_con.fetchval("""
                SELECT SUM(cnt) FROM users 
                WHERE userid = $1 AND emojitype = 'react'""", idValue)

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

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'{username}\'s reaction list is empty!')
            return

        favoriteReact = finalList[0]
        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'{username}\'s top 5 reacts!')
        await ctx.send(f'{username}\'s favorite reaction: {favoriteReact}\n')
        await ctx.send(f'{result}')

    @commands.command(brief='Lists full stats for every react')
    async def fullreactstats(self, ctx):
        # Grabs all reactions
        record = await self.client.pg_con.fetch("""
                SELECT reactid, SUM(cnt) 
                FROM users WHERE users.emojitype = 'react'
                GROUP BY reactid
                ORDER BY SUM(cnt) DESC""")

        # Handle empty results
        if record is None:
            await ctx.send('No emoji data found.')
            return

        # Fetch single sum value
        emojiSum = await self.client.pg_con.fetchval("""SELECT SUM(cnt) FROM users WHERE emojitype = 'react'""")

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

        # If no reaction data from query, return empty
        if len(finalList) == 0:
            await ctx.send(f'No data available')
            return

        result = '\n\n'.join('#{} {}'.format(*item) for item in enumerate(finalList, start=1))

        # Display results
        await ctx.send(f'Full stats on overall usage of each react')
        await ctx.send(f'{result}')


def setup(client):
    client.add_cog(Reaction(client))
