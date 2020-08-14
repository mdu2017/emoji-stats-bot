import discord
from discord.ext import commands
import random
from const import *


class Emoji(commands.Cog):
    def __init__(self, client): # Add load emojis here (whenever initialized)
        self.client = client
        self._last_member = None

    # Event
    @commands.Cog.listener()
    async def on_ready(self):
        # print('Emoji Cog ready')
        print()
        # await loadEmotes(self.client) # Loaded once and stored into constants

    # Swap react to smart react
    @commands.command(brief='Adds dum reacts')
    async def swapdumb(self, ctx):
        count = 0
        async for message in ctx.channel.history(limit=3):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                # Add dumb reacts
                dmb = random.choice(dumbReacts)
                await message.add_reaction(dmb[0])
                await message.add_reaction(dmb[1])

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    # Swap react to dumb react
    @commands.command(brief='Add smart reacts')
    async def swapsmart(self, ctx):
        count = 0
        async for message in ctx.channel.history(limit=3):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                # Add smart reacts
                smt = random.choice(smartReacts)
                await message.add_reaction(smt[0])
                await message.add_reaction(smt[1])

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    # Swap react to red baboon reacts
    @commands.command(brief='Add red reacts')
    async def swapred(self, ctx):
        count = 0
        # Gets the last 3 messages
        async for message in ctx.channel.history(limit=3):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                await message.add_reaction(emojiList.get('red'))
                await message.add_reaction(emojiList.get('cowboy'))

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    # Swap react to blue baboon reacts
    @commands.command(brief='Add blue reacts')
    async def swapblue(self, ctx):
        count = 0
        async for message in ctx.channel.history(limit=3):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                await message.add_reaction(emojiList.get('blue'))
                await message.add_reaction(SIDEPIG)

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    # Swap react to dumb react
    @commands.command(brief='Plain baboon react')
    async def default(self, ctx):
        count = 0
        async for message in ctx.channel.history(limit=3):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                # default baboon react
                await message.add_reaction(emojiList.get('bb'))

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    # smartboon emote X times (.smtb <num>)
    @commands.command(brief='Print smartboon')
    async def smtb(self, ctx, amount=1):
        emoji = await getEmote(emotestring="smtb")
        await displayEmotes(ctx, amount, emoji)

    @commands.command(brief='Smart baboon blows away pig')
    async def blowpig(self, ctx):
        await ctx.channel.purge(limit=1)
        smtb = emojiList.get('smtb')
        await ctx.send(f'{smtb} {DASH} {DASH} {SIDEPIG}')

    @commands.command(brief='Smart pig blows away baboon')
    async def blowbb(self, ctx):
        await ctx.channel.purge(limit=1)
        smtpig = emojiList.get('smtpig')
        bb = emojiList.get('bb')
        await ctx.send(f'{smtpig} {DASH} {DASH} {bb}')

    @commands.command(brief='Good reacts')
    async def supersmart(self, ctx):
        smtb = emojiList.get('smtb')
        smtpig = emojiList.get('smtpig')
        rspig = emojiList.get('rspig')
        tbu = THUMBSUP
        somm = emojiList.get('somm')
        smug = emojiList.get('smug')

        count = 0
        # Gets the last 3 messages
        async for message in ctx.channel.history(limit=2):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                await message.add_reaction(smtb)
                await message.add_reaction(smtpig)
                await message.add_reaction(rspig)
                await message.add_reaction(tbu)
                await message.add_reaction(somm)
                await message.add_reaction(smug)

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    @commands.command(brief='Dumb reacts')
    async def superdumb(self, ctx):
        pb = emojiList.get('pb')
        pig = SIDEPIG
        bb = emojiList.get('bb')
        tbd = THUMBSDOWN
        knight = emojiList.get('kn')
        cf = emojiList.get('confused')

        count = 0
        # Gets the last 3 messages
        async for message in ctx.channel.history(limit=2):
            if count == 1:
                await message.clear_reactions()  # Clear all reactions

                await message.add_reaction(pb)
                await message.add_reaction(bb)
                await message.add_reaction(knight)
                await message.add_reaction(cf)
                await message.add_reaction(pig)
                await message.add_reaction(tbd)

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    @commands.command(brief='Add some random smart reacts')
    async def addsmart(self, ctx):

        count = 0
        # Gets the last 2 messages
        async for message in ctx.channel.history(limit=2):
            if count == 1: # This is the message to add reacts to

                # Add two random smart reacts
                smt = random.choice(smartReacts)
                await message.add_reaction(smt[0])
                await message.add_reaction(smt[1])

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    @commands.command(brief='Add some random dumb reacts')
    async def adddumb(self, ctx):

        count = 0
        # Gets the last 2 messages
        async for message in ctx.channel.history(limit=2):
            if count == 1:  # This is the message to add reacts to

                # Add two random smart reacts
                dmb = random.choice(dumbReacts)
                await message.add_reaction(dmb[0])
                await message.add_reaction(dmb[1])

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

    @commands.command(brief='Adds big news reacts')
    async def bignews(self, ctx):

        count = 0
        # Gets the last 2 messages
        async for message in ctx.channel.history(limit=2):
            if count == 1:  # This is the message to add reacts to

                await message.add_reaction(FISH)
                await message.add_reaction(FIRE)

                # remove the command
                await ctx.channel.purge(limit=1)
                return

            count += 1

        # Overrides inherited cog_check method

    async def cog_check(self, ctx):
        # Prevent any commands from occuring in serious or debate channel
        if ctx.channel.name == 'serious' or ctx.channel.name == 'baboons-of-pig-york':
            return False
        else:
            return True


# Global setup function
def setup(client):
    client.add_cog(Emoji(client))
