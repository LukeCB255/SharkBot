import discord
from discord.ext import tasks, commands
import SharkBot

	
class Valorant(commands.Cog):
	
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@commands.hybrid_group()
	async def val(self, ctx: commands.Context):
		await ctx.send("Valorant Command")

		
async def setup(bot):
	await bot.add_cog(Valorant(bot))
	print("Valorant Cog loaded")


async def teardown(bot):
	print("Valorant Cog unloaded")
	await bot.remove_cog(Valorant(bot))
