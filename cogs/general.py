import discord
from discord.ext import commands, tasks
from const import *


class General(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        self.change_status.start()  # Changes status periodically
        print('General Cog Ready')

    @commands.Cog.listener()
    async def on_member_join(self, member):  # method expected by client. This runs once when connected
        print(f'{member} has joined the server')  # notification of login.

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} has left the server')

    # Change bot status every hour
    @tasks.loop(seconds=3600)
    async def change_status(self):
        activity = discord.Activity(type=discord.ActivityType.watching, name='!e help')
        await self.client.change_presence(activity=activity)

    # Overrides inherited cog_check method (Check before executing any commands)
    async def cog_check(self, ctx):
        # If bot is disabled in the specified channel, don't execute command
        if ctx.channel.name in rm_channels:
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

        # Channel commands
        em.add_field(name='channelstats <channel_name> <option>',
                     value='''Display top 3 emojis or reactions for a specified channel. 
                     <channel_name> - name of the channel (no # needed)
                     <channel_name> and <option> are optional arguments. 
                     <option> is either "react" or "message"''',
                     inline=False)
        em.add_field(name='fullchstats', value='Shows the most popular emoji and react for each channel if possible',
                     inline=False)

        # Add descriptions for General commands
        em.add_field(name='ping', value='Display network latency', inline=False)

        await author.send(embed=em)

    # Displays network ping
    @commands.command(brief='Displays network latency')
    async def ping(self, ctx):
        await ctx.send(f'{round(self.client.latency * 1000)}ms')


def setup(client):
    client.add_cog(General(client))
