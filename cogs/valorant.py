import discord
from discord.ext import tasks, commands
from SharkBot import Member, IDs, Valorant as V


class Valorant(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group()
    async def val(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=V.valorantRed)
        embed.title = "Val Commands"
        baseCommands = ""
        baseCommands += f"agents: view and modify your agent preferences\n"
        embed.add_field(name="Commands", value=baseCommands)
        if ctx.author.get_role(IDs.roles["Mod"]) != None:
            adminCommands = ""
            adminCommands += f"upload: replace analysis.json\n"
            embed.add_field(name="Admin commands", value=adminCommands, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @val.command()
    @commands.has_role(IDs.roles["Mod"])
    async def upload(self, ctx: commands.Context) -> None:
        if len(ctx.message.attachments) == 0:
            await ctx.send("You didn't attach any files...")
            return
        for file in ctx.message.attachments:
            with open(f"data/live/valorant/{file.filename}", "wb+") as outfile:
                outfile.write(await file.read())
        await ctx.send(f"Saved {len(ctx.message.attachments)} files to `data/live/valorant`")

    @val.command()
    async def agents(self, ctx: commands.Context) -> None:
        member = Member.get(ctx.author.id)
        memval = member.valorant
        data = memval.raw_data
        embed = discord.Embed(colour=V.valorantRed)
        embed.title = "Select a map to view/modify"
        view = V.Views.AgentsView(member.id, embed)
        await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Valorant(bot))
    print("Valorant Cog loaded")


async def teardown(bot):
    print("Valorant Cog unloaded")
    await bot.remove_cog(Valorant(bot))
