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

    # Change bot status every 10 mins
    @tasks.loop(seconds=600)
    async def change_status(self):
        await self.client.change_presence(activity=discord.Game(next(custom_status)))

    # Overrides inherited cog_check method (Check before executing any commands)
    async def cog_check(self, ctx):

        # If bot is disabled in the specified channel, don't execute command
        if ctx.channel.name in rm_channels:
            return False

        return True

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
