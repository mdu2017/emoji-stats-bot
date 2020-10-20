import discord
from discord.ext import commands, tasks
import const
import datetime
from const import getConnection
from const import ps_pool

class General(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        # self.change_status.start()  # Changes status periodically
        print('General Cog Ready')

        activity = discord.Activity(type=discord.ActivityType.watching, name='!e help')
        await self.client.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_member_join(self, member):  # method expected by client. This runs once when connected
        server_name = member.guild.name
        print(f'{member} has joined the server {server_name}')  # notification of login.

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        server_name = member.guild.name
        print(f'{member} has left the server {server_name}')

    # TODO: delete unused emoji data after 3 weeks (clear stuff every 3 days)
    # Change bot status every hour
    # @tasks.loop(hours=72)
    # async def change_status(self):
    #     activity = discord.Activity(type=discord.ActivityType.watching, name='!e help')
    #     await self.client.change_presence(activity=activity)

    @commands.command()
    async def getservers(self, ctx):
        guilds = list(self.client.guilds)
        print(f"Connected on {str(len(guilds))} servers:")
        print('\n'.join(guild.name for guild in guilds))

    # Overrides inherited cog_check method (Check before executing any commands)
    async def cog_check(self, ctx):
        # If bot is disabled in the specified channel, don't execute command
        if ctx.channel.name in const.rm_channels:
            return False

        return True

    @commands.command(pass_context=True)
    async def help(self, ctx):
        author = ctx.message.author  # Used to send DM when calling help

        # Set ember and header
        em = discord.Embed(
            colour=discord.Colour.blurple(),
            title='Command Help',
            description='Below are the list of commands for the bot',
        )

        # Set author
        em.set_author(name='Bot prefix is !e  (Example command: !e topemojis)')

        # Message commands
        em.add_field(name='useremojis <user>',
                     value='''Displays user\'s top 5 emojis 
                     <user> can be nickname or mention''', inline=False)
        em.add_field(name='topemojis <num>',
                     value='''Display <num> most used emojis in the server 
                     <num> = number between 1-15''', inline=False)
        em.add_field(name='favemoji <@username>',
                     value='Display user\'s favorite emoji in the server', inline=False)
        em.add_field(name='fullmsgstats', value='Display stats for all emojis used in the server', inline=False)
        em.add_field(name='emojistoday', value='Display all emojis used in the last 24 hours', inline=False)

        # Reaction commands
        em.add_field(name='userreacts <user>', value='''Displays user\'s top 5 reactions
                                                    <user> can be nickname or mention''', inline=False)
        em.add_field(name='topreacts <num> <mode>', value='''Display <num> most used reactions in the server
                                                   <num> - number between 1-15
                                                   <mode> - "custom" or "unicode" -- mode is an optional argument''', inline=False)
        em.add_field(name='favreact <@username>',
                     value='''Display user\'s favorite reaction in the server 
                     <@username> - can use mention or nickname''', inline=False)
        em.add_field(name='fullreactstats', value='Display stats for all reactions used in the server', inline=False)
        em.add_field(name='reactstoday', value='Display all reactions used in the last 24 hours', inline=False)

        # Channel commands
        em.add_field(name='.chstats <channel_name>',
                     value='''Display top 3 emojis and reactions for a specified channel. 
                     <channel_name> - name of the channel (no # needed)''',
                     inline=False)
        em.add_field(name='fullchstats (currently under work)', value='Shows the most popular emoji and react for each channel if possible',
                     inline=False)

        await author.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        conn, cursor = getConnection()
        guild_id = str(guild.id)
        guild_name = guild.name

        # Add to list of guilds
        cursor.execute("""
        INSERT INTO guild(guildid, guildname)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """, (guild_id, guild_name))
        conn.commit()

        # Read channel data
        for channel in guild.text_channels:
            ch_id = channel.id
            ch_name = channel.name

            cursor.execute("""
                            INSERT INTO channel(chid, chname, guildid)
                            VALUES (%s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """, (ch_id, ch_name, guild_id))
        conn.commit()

        # Read user list
        for member in guild.members:
            user_id = str(member.id)

            # Skip adding bot ids
            if member.bot:
                continue

            cursor.execute("""
                INSERT INTO users(userid, guildid, enabled)
                VALUES (%s, %s, True)
                ON CONFLICT DO NOTHING""", (user_id, guild_id))
        conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Return connection to pool

    @commands.command(brief='refresh the database')
    async def refreshData(self, ctx):
        conn, cursor = getConnection()

        for guild in self.client.guilds:
            guild_id = str(guild.id)
            guild_name = guild.name

            # Add to list of guilds
            cursor.execute("""
                    INSERT INTO guild(guildid, guildname)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """, (guild_id, guild_name))
            conn.commit()

            # Read channel data
            for channel in guild.text_channels:
                ch_id = channel.id
                ch_name = channel.name

                cursor.execute("""
                    INSERT INTO channel(chid, chname, guildid)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """, (ch_id, ch_name, guild_id))
            conn.commit()

            # Read user list
            for member in guild.members:
                user_id = str(member.id)

                # Skip adding bot ids
                if member.bot:
                    continue

                cursor.execute("""
                    INSERT INTO users(userid, guildid)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING""", (user_id, guild_id))
            conn.commit()

        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Return connection to pool

    @commands.command(brief='refresh the database')
    async def testtimestamp(self, ctx):
        conn, cursor = getConnection()

        today = datetime.datetime.today()
        three_weeks_ago = today - datetime.timedelta(weeks=3)
        really_old = today - datetime.timedelta(weeks=4)

        # cursor.execute("""
        #     INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, chid)
        #     VALUES(%s, %s, %s, %s, %s, %s, %s)
        #     ON CONFLICT(emoji, emojitype, userid, guildid)
        #     DO UPDATE SET cnt = emojis.cnt + 1, emojidate = %s
        # """, ('BADDATA', 'react', '353037475016474637', '689284514886844446', 1, really_old, '739569231112437935', really_old))
        #
        # cursor.execute("""
        #             INSERT INTO emojis(emoji, emojitype, userid, guildid, cnt, emojidate, chid)
        #             VALUES(%s, %s, %s, %s, %s, %s, %s)
        #             ON CONFLICT(emoji, emojitype, userid, guildid)
        #             DO UPDATE SET cnt = emojis.cnt + 1, emojidate = %s
        #         """, (
        # 'bad2', 'react', '353037475016474637', '689284514886844446', 1, really_old, '739569231112437935', really_old))
        # conn.commit()

        # cursor.execute("""DELETE FROM emojis where emojidate < (NOW() - INTERVAL '21 days')""")
        # conn.commit()
        # record = cursor.fetchall()
        #
        # print(f'Record of old entries: {record}')


        cursor.close()  # Close cursor
        ps_pool.putconn(conn)  # Return connection to pool

def setup(client):
    client.add_cog(General(client))
