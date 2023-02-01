import traceback

import discord
from discord.ext import commands

import SharkBot


class Errors(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.HybridCommandError):
            error = error.original
        if isinstance(error, commands.errors.ConversionError):
            if isinstance(error.original, SharkBot.Errors.SharkError):
                error = error.original
        if isinstance(error, commands.CommandInvokeError) or isinstance(error, discord.app_commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Sorry, I don't know that command!")
            return
        if isinstance(error, commands.CheckAnyFailure):
            await ctx.send("Sorry, you can't do that!")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("I think you're missing an argument there!")
            return
        if isinstance(error, commands.ChannelNotFound):
            await ctx.send("Please enter a valid channel!")
            return
        if isinstance(error, commands.errors.BadArgument):
            await ctx.send("Please enter a valid argument!")
            return
        if isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("Extension not loaded!")
            return
        if isinstance(error, commands.ExtensionNotFound):
            await ctx.send("Extension not found!")
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can only be used inside a server!")
            return
        if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm afraid you don't have permission to do that!")
            return

        if isinstance(error, SharkBot.Errors.SharkError):
            if await error.handler(ctx):
                return

        error_type = type(error)
        print(f"{error_type.__module__}.{error_type.__name__}{error.args}")
        error_name = f"{error_type.__module__}.{error_type.__name__}{error.args}"

        embed = discord.Embed()
        embed.title = "Something went wrong!"
        embed.colour = discord.Color.red()
        embed.description = "Oh no! An error occurred! I've let James know, and they'll do what they can to fix it!"
        embed.set_footer(text=error_name)
        await ctx.send(embed=embed)

        dev = await self.bot.fetch_user(SharkBot.IDs.dev)
        embed = discord.Embed()
        embed.title = "Error Report"
        embed.description = "Oopsie Woopsie"
        embed.add_field(name="Type", value=error_name, inline=False)
        embed.add_field(name="Args", value=error.args, inline=False)
        embed.add_field(name="Traceback", value="\n".join(traceback.format_tb(error.__traceback__)))
        await dev.send(embed=embed)

        raise error


async def setup(bot):
    await bot.add_cog(Errors(bot))
    print("Errors Cog loaded")


async def teardown(bot):
    print("Errors Cog unloaded")
    await bot.remove_cog(Errors(bot))
