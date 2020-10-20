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

    @commands.command()
    async def getservers(self, ctx):
        guilds = list(self.client.guilds)
        print(f"Connected on {str(len(guilds))} servers:")
        # print('\n'.join(guild.name for guild in guilds))

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
        em.add_field(name='topemojis', value='Shows the 5 most popular emojis', inline=True)
        em.add_field(name='useremojis <username> <mode>', value='Shows user\'s most used emojis', inline=True)
        em.add_field(name='favemoji <username>', value='Shows a user\'s favorite emoji', inline=True)
        em.add_field(name='fullmsgstats', value='Shows stats for all emojis used in messages', inline=True)
        em.add_field(name='emojistoday', value='Shows all emojis used in the past day', inline=True)

        # Reaction commands
        em.add_field(name='topreacts', value='Shows the 5 most popular reactions', inline=True)
        em.add_field(name='userreacts <username> <mode>', value='Shows a user\'s most used reactions', inline=True)
        em.add_field(name='favreact <@username>', value='Shows a user\'s favorite reaction', inline=True)
        em.add_field(name='fullreactstats', value='Shows stats for all reactions used', inline=True)
        em.add_field(name='reactstoday', value='Show all reactions used in the past day', inline=True)

        # Channel commands
        em.add_field(name='chstats <channel_name>',
                     value='Shows a channel\'s top 3 most popular reactions and emojis', inline=True)
        em.add_field(name='fullchstats (*under work*)',
                     value='Shows the most popular reaction/emoji for every channel', inline=True)

        # Notes
        em.add_field(name='<mode> - optional argument (use "unicode" or "custom" to filer type)', value='-', inline=False)
        em.add_field(name='<username> - Can use discord nickname or mention user', value='-', inline=False)
        em.add_field(name='<channel_name> - Discord text channel name (no # needed)', value='-', inline=False)

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
