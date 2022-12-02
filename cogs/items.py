import discord
from discord.ext import commands

from SharkBot import Member, Errors, Item, Collection, Utils


class Items(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(aliases=["search"])
    async def item(self, ctx: commands.Context, *, search: str) -> None:
        member = Member.get(ctx.author.id)
        item = Item.search(search)
        if member.collection.contains(item):
            await ctx.reply(embed=item.embed, mention_author=False)
        else:
            fake_item = Item.FakeItem(item)
            await ctx.reply(embed=fake_item.embed, mention_author=False)

    @commands.hybrid_command(aliases=["i", "inv"])
    async def inventory(self, ctx: commands.Context) -> None:
        member = Member.get(ctx.author.id)
        member.inventory.sort()

        items = {}
        for item in member.inventory.items:
            if item.collection not in items:
                items[item.collection] = {}
            if item not in items[item.collection]:
                items[item.collection][item] = 0
            items[item.collection][item] += 1

        embed = discord.Embed()
        embed.title = f"{ctx.author.display_name}'s Inventory"
        embed.description = f"Balance: `${member.balance}`\nLevel: `{member.xp.level} | {member.xp.xp} xp`"
        embed.set_thumbnail(url=ctx.author.avatar.url)

        for collection, collection_items in items.items():
            embed.add_field(
                name=str(collection),
                value="\n".join([f"{qty}x {item.name} *({item.id})*" for item, qty in collection_items.items()]),
                inline=False
            )

        embeds = Utils.split_embeds(embed)
        for embed in embeds:
            await ctx.reply(embed=embed, mention_author=False)

        member.write_data()

    @commands.hybrid_command()
    async def sell(self, ctx: commands.Context, *, search: str) -> None:
        search = search.upper()

        member = Member.get(ctx.author.id)

        if search in ["ALL", "*"]:
            items = member.inventory.sellable_items
            if len(items) == 0:
                await ctx.reply("It looks like you don't have any items to sell!", mention_author=False)
                return
        elif search in ["DUPES", "D"]:
            items = [item for item in member.inventory.get_duplicates()]
            if len(items) == 0:
                await ctx.reply("It looks like you don't have any dupes! Nice!", mention_author=False)
                return
        else:
            item = Item.search(search)
            if not item.sellable:
                await ctx.reply(f"You can't sell **{item}**!", mention_author=False)
                return
            if not member.inventory.contains(item):
                await ctx.reply(f"It looks like you don't have **{item}** to sell!", mention_author=False)
                return
            else:
                items = [item]

        sold_value = 0
        for item in items:
            try:
                member.inventory.remove(item)
                sold_value += item.value
            except Errors.ItemNotInInventoryError:
                items.remove(item)

        member.balance += sold_value
        await ctx.reply(
            f"Sold `{len(items)} items` for **${sold_value}**. Your new balance is **${member.balance}**.",
            mention_author=False
        )

        member.write_data()

    @commands.command(aliases=["c", "col"])
    async def collection(self, ctx: commands.Context, *args: str) -> None:
        member = Member.get(ctx.author.id)

        if len(args) == 0:  # Collections Overview

            embed = discord.Embed()
            embed.title = f"{ctx.author.display_name}'s Collection"
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            total_items = 0

            for collection in Collection.collections:
                total_items += len(collection.items)
                collection_items_discovered = 0
                for item in collection.items:
                    if member.collection.contains(item):
                        collection_items_discovered += 1

                embed.add_field(name=f"{collection}",
                                value=f"{collection_items_discovered}/{len(collection)} items discovered",
                                inline=False)

            embed.description = f"{len(member.collection.items)}/{total_items} items discovered"

            await ctx.reply(embed=embed, mention_author=False)
            return

        elif args[0] in ["full", "*", "all"]:  # Full Collections Format

            embeds = [discord.Embed()]
            embeds[0].title = f"{ctx.author.display_name}'s Collection"
            embeds[0].description = f"{len(member.collection.items)} items discovered."
            embeds[0].set_thumbnail(url=ctx.author.display_avatar.url)

            length = 0

            for collection in Collection.collections:
                collection_items_discovered = 0
                items_text = ""
                for item in collection.items:
                    if member.collection.contains(item):
                        collection_items_discovered += 1
                        items_text += f"{item.name} *({item.id})*\n"
                    else:
                        items_text += f"??? *({item.id})*\n"

                icon = collection.icon

                length += len(items_text)
                if length > 5000:
                    length -= 5000
                    embeds.append(discord.Embed())
                    embeds[-1].title = f"{ctx.author.display_name}'s Collection"
                    embeds[-1].description = f"{len(member.collection.items)} items discovered."
                    embeds[-1].set_thumbnail(url=ctx.author.display_avatar.url)

                embeds[-1].add_field(
                    name=f"{icon}  {collection.name} ({collection_items_discovered}/{len(collection.collection)})",
                    value=items_text[:-1], inline=True)

            if len(embeds) > 1:
                for embed in embeds:
                    embed.title = f"{ctx.author.display_name}'s Collection ({embeds.index(embed) + 1}/{len(embeds)})"

            for embed in embeds:
                await ctx.reply(embed=embed, mention_author=False)

        else:  # Specific Collections Format

            collections_to_show = []
            for collectionName in args:
                for collection in Collection.collections:
                    if collectionName.lower() == collection.name.lower() or collectionName.upper() == collection.id:
                        collections_to_show.append(collection)
                        break

            if len(collections_to_show) != len(args):
                await ctx.reply("I don't recognise all of those collection names, please try again!",
                                mention_author=False)
                return

            collections_to_show = list(set(collections_to_show))

            embeds = [discord.Embed()]
            embeds[0].title = f"{ctx.author.display_name}'s Collection"
            embeds[0].description = f"{len(member.collection.items)} items discovered."
            embeds[0].set_thumbnail(url=ctx.author.display_avatar.url)

            length = 0

            for collection in collections_to_show:
                collection_items_discovered = 0
                items_text = ""
                for item in collection.items:
                    if member.collection.contains(item):
                        collection_items_discovered += 1
                        items_text += f"{item.name} *({item.id})*\n"
                    else:
                        items_text += f"??? *({item.id})*\n"

                icon = collection.icon

                length += len(items_text)
                if length > 5000:
                    length -= 5000
                    embeds.append(discord.Embed())
                    embeds[-1].title = f"{ctx.author.display_name}'s Collection"
                    embeds[-1].description = f"{len(member.collection.items)} items discovered."
                    embeds[-1].set_thumbnail(url=ctx.author.display_avatar.url)

                embeds[-1].add_field(
                    name=f"{icon}  {collection.name} ({collection_items_discovered}/{len(collection.items)})",
                    value=items_text[:-1], inline=True)

            if len(embeds) > 1:
                for embed in embeds:
                    embed.title = f"{ctx.author.display_name}'s Collection ({embeds.index(embed) + 1}/{len(embeds)})"

            for embed in embeds:
                await ctx.reply(embed=embed, mention_author=False)

    @commands.command(aliases=["gift"])
    async def give(self, ctx: commands.Context, target: discord.Member, *, search: str) -> None:
        member = Member.get(ctx.author.id)
        target_member = Member.get(target.id)
        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply("I'm afraid I couldn't find that item!", mention_author=False)
            return

        try:
            member.inventory.remove(item)
            target_member.inventory.add(item)
            await ctx.reply(f"You gave **{str(item)}** to *{target.display_name}*",
                            mention_author=False)
        except Errors.ItemNotInInventoryError:
            await ctx.reply(
                f"It looks like you don't have **{str(item)}** :pensive:",
                mention_author=False)
        member.write_data()

        target_member.write_data()


async def setup(bot):
    await bot.add_cog(Items(bot))
    print("Items Cog loaded")


async def teardown(bot):
    print("Items Cog unloaded")
    await bot.remove_cog(Items(bot))
