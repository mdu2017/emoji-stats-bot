# Helper function to print emotes
async def displayEmotes(ctx, amount, emoji):
    one = '{0}'.format(emoji)
    two = '{0}{1}'.format(emoji, emoji)
    three = '{0}{1}{2}'.format(emoji, emoji, emoji)

    if amount == 1:
        await ctx.send(one)
    elif amount == 2:
        await ctx.send(two)
    elif amount == 3:
        await ctx.send(three)
    else:
        await ctx.send(one)

#Returns specific emoji based on which function has called it (helper function)
async def getEmote(ctx, emotestring):
    if emotestring == "pb":
        return emojiList.get("pigboon")
    if emotestring == "bb":
        return emojiList.get("baboon")
    if emotestring == "smtb":
        return emojiList.get("smartboon")