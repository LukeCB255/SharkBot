from discord.ext import commands
from SharkBot.Errors import SharkError


class ValorantError(SharkError):
    pass


class AgentNotFoundError(ValorantError):

    async def handler(self, ctx: commands.Context) -> bool:
        await ctx.reply(f"I'm afraid {self.args} is not a valid Agent!")
        return True


class MapNotFoundError(ValorantError):

    async def handler(self, ctx: commands.Context) -> bool:
        await ctx.reply(f"I'm afraid {self.args} is not a valid Map!")
        return True


class InvalidAgentValueError(ValorantError):

    async def handler(self, ctx: commands.Context) -> bool:
        await ctx.reply(f"I'm afraid {self.args} is not a valid Agent Value!")
        return True
