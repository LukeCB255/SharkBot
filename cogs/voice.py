import discord
from discord.ext import tasks, commands

import secret

if secret.testBot:
    import testids as ids
else:
    import ids


class Voice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    @commands.has_role(ids.roles["Mod"])
    async def migrate(self, ctx, *, newchannel: discord.VoiceChannel):
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel!")
            return
        currentChannel = ctx.author.voice.channel
        members = list(currentChannel.members)
        for member in members:
            await member.move_to(newchannel)
        await ctx.send(f"Moved *{len(members)}* members from {currentChannel.mention} to {newchannel.mention}.")

    @commands.hybrid_command()
    @commands.has_role(ids.roles["Mod"])
    async def summon(self, ctx, *, targetchannel: discord.VoiceChannel):
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel!")
            return
        members = list(targetchannel.members)
        currentChannel = ctx.author.voice.channel
        for member in members:
            await member.move_to(currentChannel)
        await ctx.send(f"Moved *{len(members)}* members from {targetchannel.mention} to {currentChannel.mention}.")


async def setup(bot):
    await bot.add_cog(Voice(bot))
    print("Voice Cog loaded")


async def teardown(bot):
    print("Voice Cog unloaded")
    await bot.remove_cog(Voice(bot))
