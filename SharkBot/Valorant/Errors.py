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
