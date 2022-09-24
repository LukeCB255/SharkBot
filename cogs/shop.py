import discord
from discord.ext import commands

from SharkBot import Listing, Member, Errors, Item, Views


class Shop(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def shop(self, ctx: commands.Context) -> None:
        embed = discord.Embed()
        embed.title = "Shop"
        embed.description = "Fucking Capitalists"
        for listing in Listing.listings:
            embed.add_field(
                name=f"{listing.item.text} - ${listing.price}",
                value=f"*{listing.item.description}*",
                inline=False
            )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command()
    async def buy(self, ctx: commands.Context, quantity: int, *, search: str) -> None:
        member = Member.get(ctx.author.id)
        search = search.lower()
        num = quantity
        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply("I'm afraid I couldn't find that item!", mention_author=False)
            return
        if item not in Listing.availableItems:
            await ctx.reply("I'm afraid you can't buy that!", mention_author=False)
            return
        listing = discord.utils.get(Listing.listings, item=item)
        if num == "max":
            num = member.balance // listing.price
        if member.balance < num * listing.price or num == 0:
            await ctx.reply(
                f"I'm afraid you don't have enough to buy {item.rarity.icon} **{item.name}**",
                mention_author=False)
            return
        for i in range(num):
            member.balance -= listing.price
            member.inventory.add(item)
            member.stats.boughtBoxes += 1

        embed = discord.Embed()
        embed.title = f"Bought {num}x {item.rarity.icon} {item.name}"
        embed.description = f"You bought {num}x {item.rarity.icon} {item.name} for *${listing.price * num}*"
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)

        view = Views.BuyView([item] * num, ctx.author.id, embed)

        await ctx.reply(embed=embed, view=view)
        member.write_data()


async def setup(bot):
    await bot.add_cog(Shop(bot))
    print("Shop Cog loaded")


async def teardown(bot):
    print("Shop Cog unloaded")
    await bot.remove_cog(Shop(bot))
