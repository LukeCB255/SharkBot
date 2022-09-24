import discord
from discord.ext import tasks, commands
import SharkBot

	
class Valorant(commands.Cog):
	
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

		
async def setup(bot):
	await bot.add_cog(Valorant(bot))
	print("Valorant Cog loaded")


async def teardown(bot):
	print("Valorant Cog unloaded")
	await bot.remove_cog(Valorant(bot))
