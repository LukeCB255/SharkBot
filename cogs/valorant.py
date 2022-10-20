import discord
from discord.ext import tasks, commands
from SharkBot import Member, IDs, Valorant as Val


class Valorant(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group()
    async def val(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=Val.valorantRed)
        embed.title = "Val Commands"
        base_commands = ""
        base_commands += f"agents: view and modify your agent preferences\n"
        base_commands += f"match: get comp recommendations for your match.\n"
        embed.add_field(name="Commands", value=base_commands)
        if ctx.author.get_role(IDs.roles["Mod"]) is not None:
            admin_commands = ""
            admin_commands += f"upload: replace analysis.json\n"
            admin_commands += f"m_agents: view and modify other people's preferences\n"
            embed.add_field(name="Admin commands", value=admin_commands, inline=False)
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
        embed = discord.Embed(colour=Val.valorantRed)
        embed.title = "Select a map to view/modify"
        view = Val.Views.AgentsView(ctx.author.id, ctx.author.id, embed)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @val.command()
    @commands.has_role(IDs.roles["Mod"])
    async def m_agents(self, ctx: commands.Context, target: discord.Member) -> None:
        embed = discord.Embed(colour=Val.valorantRed)
        embed.title = "Map"
        view = Val.Views.AgentsView(ctx.author.id, target.id, embed)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @val.command()
    async def match(self, ctx: commands.Context,
                    player1: discord.Member = None,
                    player2: discord.Member = None,
                    player3: discord.Member = None,
                    player4: discord.Member = None,
                    player5: discord.Member = None) -> None:

        player_list = [player1, player2, player3, player4, player5]
        known_list = [player for player in player_list if player is not None]
        known_ids = [player.id for player in known_list]

        embed = discord.Embed(colour=Val.valorantRed)
        embed.title = f"Valorant Match of {len(known_list)} premades"
        embed.description = "\n".join([player.name for player in known_list])

        view = Val.Views.MatchView(ctx.author.id, known_ids, embed)
        await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Valorant(bot))
    print("Valorant Cog loaded")


async def teardown(bot):
    print("Valorant Cog unloaded")
    await bot.remove_cog(Valorant(bot))
