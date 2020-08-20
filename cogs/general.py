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
                     value='Displays user\'s top 5 emojis | <user> can be nickname or mention', inline=True)
        em.add_field(name='topemojis <num>',
                     value='Display <num> most used emojis in the server | <num> = number between 1-15', inline=True)
        em.add_field(name='fullmsgstats', value='Display stats for all emojis used in the server', inline=True)

        # Reaction commands
        em.add_field(name='userreacts <user>', value='Displays user\'s top 5 reactions | '
                                                     '<user> can be nickname or mention', inline=True)
        em.add_field(name='topreacts <num>', value='Display <num> most used reactions in the server | '
                                                   '<num> = number between 1-15', inline=True)
        em.add_field(name='fullreactstats', value='Display stats for all reactions used in the server', inline=True)

        # Channel commands
        em.add_field(name='channelstats <channel_name> <option>',
                     value='Display top 3 emojis or reactions for a specified channel. '
                           '<channel_name> and <option> are optional arguments. <option> is either react or message',
                     inline=True)
        em.add_field(name='fullchstats', value='Shows the most popular emoji and react for each channel if possible',
                     inline=True)

        # Add descriptions for General commands
        em.add_field(name='ping', value='Display network latency', inline=True)

        await author.send(embed=em)

    # Disable bot commands in specified channel
    # @commands.command(brief='Disable bot command usage in a specific channel')
    # async def rmbotch(self, ctx, chan):
    #     found = False
    #     for channel in ctx.guild.text_channels:
    #         if channel.name == chan:
    #             rm_channels.append(chan)
    #             print(f'Bot commands disabled for #{chan}')
    #             found = True
    #             break
    #
    #     if not found:
    #         await ctx.send(f'Text Channel #{chan} was not found')

    # Enable bot commands in specified channel
    # @commands.command(brief='Enable bot command usage in a specific channel')
    # async def addbotch(self, ctx, chan):
    #     found = False
    #     for channel in ctx.guild.text_channels:
    #         if channel.name == chan:
    #             found = True
    #             break
    #
    #
    #     if chan in rm_channels:
    #         rm_channels.remove(chan)
    #         print(f'Bot commands re-enabled for #{chan}')
    #     else:
    #         if not found:
    #             await ctx.send(f'Text Channel #{chan} was not found')
    #         else:
    #             await ctx.send(f'{chan} is already enabled!')

    # Make bot parrot a message
    # @commands.command(brief='Parrot message back with bot')
    # async def parrot(self, ctx, *args):
    #     msg = ' '.join(args)
    #
    #     await ctx.channel.purge(limit=1)
    #     await ctx.send(f'{msg}')

    # @commands.command(brief='Put bot to Idle status')
    # async def sleep(self, ctx):
    #     await self.client.change_presence(
    #         activity=discord.Activity(type=discord.ActivityType.listening, name='Sleeping'),
    #         status=discord.Status.idle, afk=True)
    #     await ctx.channel.purge(limit=1)

    # Displays network ping
    @commands.command(brief='Displays network latency')
    async def ping(self, ctx):
        await ctx.send(f'{round(self.client.latency * 1000)}ms')

    # Clears an X amount of messages from the channe
    # @commands.command(brief='Remove <X> amt of messages', aliases=['cls'], pass_context=True)
    # async def clear(self, ctx, amount=3):
    #
    #     # Disable feature for serious/news channel
    #     if ctx.channel.name == 'serious' or ctx.channel.name == 'baboons-of-pig-york':
    #         return
    #
    #     if amount < 1 or amount > 25:
    #         await ctx.send('Error: amount needs to be between 1-25')
    #         return
    #
    #     # remove clear command
    #     await ctx.channel.purge(limit=1)
    #
    #     # remove <amount> of messages
    #     await ctx.channel.purge(limit=amount)


def setup(client):
    client.add_cog(General(client))
