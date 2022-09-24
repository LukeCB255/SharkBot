import discord
from discord.ext import commands
from SharkBot.Errors import SharkError


class ValorantError(SharkError):
    pass


class AgentNotFoundError(ValorantError):
    pass


class MapNotFoundError(ValorantError):
    pass


class InvalidAgentValueError(ValorantError):
    pass


async def handler(ctx: commands.Context, error: Exception) -> bool:

    if isinstance(error, AgentNotFoundError):
        await ctx.reply(f"I'm afraid {error.args} is not a valid Agent!")
        return True

    if isinstance(error, MapNotFoundError):
        await ctx.reply(f"I'm afraid {error.args} is not a valid Map!")
        return True

    if isinstance(error, InvalidAgentValueError):
        await ctx.reply(f"I'm afraid {error.args} is not a valid Agent Value!")
        return True

    return False
