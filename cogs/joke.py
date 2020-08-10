import discord
from discord.ext import commands
import const
from const import *
import random


class Joke(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Joke feature ready')

    # IQ memes (.iq)
    @commands.command(brief='IQ joke')
    async def iq(self, ctx):
        for guild in self.client.guilds:
            for member in guild.members:
                nickname = member.nick
                if nickname == 'Bull':
                    await ctx.send(f'{nickname} has IQ of a 160! {emojiList.get("smtb")}')
                if nickname == 'Pigboon':
                    await ctx.send(f'{nickname} has an IQ of 90 {emojiList.get("bb")}')
                    member.status = discord.Status.online

    # Enables bot to play Guess My Number
    @commands.command(brief='Guess a number between 1-10')
    async def guessgame(self, ctx):
        tries = 3
        num = random.randint(1, 10)
        print(num)
        await ctx.send(f'Welcome! I have a hidden number between 1-10. Make your best guess! You have {tries} tries.')

        while tries > 0:
            guess = None
            try:  # Need check for await b/c we only want to check messages from person who initiated the game
                guess = await self.client.wait_for('message', check=lambda message: message.author == ctx.author,
                                                   timeout=30)
                pass
            except Exception as e:
                await ctx.send(f'You took too long to respond. Game over.')

            guessedNum = int(guess.content)
            tries -= 1

            if guessedNum > num:
                await ctx.send(f'Your number is too high! {tries} tries left.')
            elif guessedNum < num:
                await ctx.send(f'Your number is too low! {tries} tries left.')
            else:
                await ctx.send('Well done... It seems I\'ve been guessed!')
                await ctx.send(f'{emojiList.get("smtpig")} {emojiList.get("smtb")}')
                return

        if tries == 0:
            await ctx.send('You failed to guess... Made!')
            await ctx.send(f'{emojiList.get("kn")} {DASH} {DASH} {SIDEPIG}')

    # Type .joke for an "in your pants joke"
    @commands.command(brief='Random canned response')
    async def joke(self, ctx):
        msg = random.choice(cannedResponses)
        await ctx.send(f'{msg}')

    @commands.command(brief='lazy response')
    async def lz(self, ctx):
        await ctx.send(f'Mmm... Sure Sure!')


def setup(client):
    client.add_cog(Joke(client))
