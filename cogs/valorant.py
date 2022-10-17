import discord
from discord.ext import tasks, commands
import SharkBot

	
class Valorant(commands.Cog):
	
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@commands.hybrid_group()
	async def val(self, ctx: commands.Context):
		await ctx.send("Valorant Command")

	@val.command()
	async def upload(self, ctx: commands.Context):
		if len(ctx.message.attachments) == 0:
			await ctx.send("You didn't attach any files...")
			return
		for file in ctx.message.attachments:
			with open(f"data/live/valorant/{file.filename}", "wb+") as outfile:
				outfile.write(await file.read())
		await ctx.send(f"Saved {len(ctx.message.attachments)} files to `data/live/valorant`")

		
async def setup(bot):
	await bot.add_cog(Valorant(bot))
	print("Valorant Cog loaded")


async def teardown(bot):
	print("Valorant Cog unloaded")
	await bot.remove_cog(Valorant(bot))
