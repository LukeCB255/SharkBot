import random

import discord
from discord.ext import commands

from SharkBot import Member, Errors, Item, Collection, Views, IDs


class Collectibles(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(aliases=["search"])
    async def item(self, ctx: commands.Context, *, search: str) -> None:
        member = Member.get(ctx.author.id)
        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply(f"Sorry, I couldn't find *{search}*!", mention_author=False)
            return
        if member.collection.contains(item):
            await ctx.reply(embed=item.embed, mention_author=False)
        else:
            fakeItem = Item.FakeItem(item)
            await ctx.reply(embed=fakeItem.embed, mention_author=False)

    @commands.hybrid_command(aliases=["i", "inv"])
    async def inventory(self, ctx: commands.Context) -> None:
        member = Member.get(ctx.author.id)
        member.inventory.sort()

        items = {}

        for collection in Collection.collections:
            items[collection] = {}
            for item in collection.items:
                if member.inventory.items.count(item) > 0:
                    items[collection][item] = member.inventory.items.count(item)

        collectionsToRemove = []
        for collection in items:
            if len(items[collection]) == 0:
                collectionsToRemove.append(collection)

        for collection in collectionsToRemove:
            items.pop(collection)

        rawEmbedData = []

        for collection in items:
            collectionData = ""
            for item in items[collection]:
                collectionData += f"{items[collection][item]}x {item.name} *({item.id})*\n"
                if len(collectionData) > 1000:
                    rawEmbedData.append([collection, collectionData[:-1]])
                    collectionData = ""

            if collectionData != "":
                rawEmbedData.append([collection, collectionData[:-1]])

        embedData = [[]]

        embedLength = 0
        for data in rawEmbedData:
            if embedLength + len(data[1]) > 5000:
                embedData.append([])
                embedLength = 0
            embedData[-1].append(data)
            embedLength += len(data[1])

        embeds = []

        for data in embedData:
            embed = discord.Embed()
            embed.description = f"Balance: ${member.balance}"
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            for collectionData in data:
                collection = collectionData[0]
                collectionItems = collectionData[1]

                embed.add_field(name=f"{collection.icon}  {collection.name}", value=collectionItems,
                                inline=True)

            embeds.append(embed)

        for embed in embeds:
            if len(embeds) > 1:
                embed.title = f"{ctx.author.display_name}'s Inventory (Page {embeds.index(embed) + 1}/{len(embeds)})"
            else:
                embed.title = f"{ctx.author.display_name}'s Inventory"
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def additem(self, ctx: commands.Context, target: discord.Member, *, search: str) -> None:
        targetMember = Member.get(target.id)
        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply("Sorry, I couldn't find that item!", mention_author=False)
            return
        targetMember.inventory.add(item)
        await ctx.reply(f"Added **{item.name}** to *{target.display_name}*'s inventory.", mention_author=False)
        targetMember.write_data()

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def removeitem(self, ctx: commands.Context, target: discord.Member, *, search: str) -> None:
        targetMember = Member.get(target.id)
        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply("Sorry, I couldn't find that item!", mention_author=False)
            return
        try:
            targetMember.inventory.remove(item)
        except Errors.ItemNotInInventoryError:
            await ctx.reply(f"Couldn't find item in *{target.display_name}*'s inventory", mention_author=False)
            return
        await ctx.reply(f"Removed **{item.name}** from *{target.display_name}*'s inventory.", mention_author=False)
        targetMember.write_data()

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def grantall(self, ctx: commands.Context, *itemids: str) -> None:
        items = [Item.get(itemid) for itemid in itemids]

        members = Member.members.values()
        for member in members:
            for item in items:
                member.inventory.add(item)
        await ctx.send(f"Granted {[item.name for item in items]} each to {len(members)} members.")

        for member in members:
            member.write_data()

    @commands.command()
    async def open(self, ctx: commands.Context, boxType: str = "all") -> None:
        member = Member.get(ctx.author.id)

        if boxType.lower() in ["all", "*"]:  # $open all
            boxes = member.inventory.lootboxes
            if len(boxes) == 0:
                await ctx.reply("It doesn't look like you have any lootboxes!", mention_author=False)
                return
        else:  # $open specific lootbox
            try:
                box = Item.search(boxType)
            except Errors.ItemNotFoundError:
                await ctx.send("I couldn't find that lootbox!", mention_author=False)
                return
            if type(box) != Item.Lootbox:
                await ctx.send("That item isn't a lootbox!", mention_author=False)
                return
            if not member.inventory.contains(box):
                await ctx.send(f"I'm afraid you don't have a {box.text}", mention_author=False)
                return
            boxes = [box]

        openedData: list[list[Item.Item, Item.Lootbox, bool]] = []

        for box in boxes:
            item = box.roll()

            if box.id == "LOOTM":  # Force Mythic Lootbox to guarantee new item
                if member.collection.contains(item):
                    possibleItems = [item for item in Collection.mythic.items if not member.collection.contains(item)]
                    if len(possibleItems) > 0:
                        item = random.choice(possibleItems)

            openedData.append([box, item, not member.collection.contains(item)])

            member.inventory.remove(box)
            member.inventory.add(item)
            member.stats.openedBoxes += 1

        member.write_data()

        for box, item, newItem in openedData:
            embed = discord.Embed()
            embed.title = f"{box.name} opened!"
            if newItem:
                embed.description = f"You got :sparkles: *{item.text}* :sparkles:!"
            else:
                embed.description = f"You got *{item.text}*!"
            embed.colour = item.collection.colour
            embed.set_footer(text=item.description)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

            await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(
        description="Claim Hourly, Daily and Weekly rewards."
    )
    async def claim(self, ctx: commands.Context) -> None:
        member = Member.get(ctx.author.id)

        embed = discord.Embed()
        embed.title = "Claim All"
        embed.colour = discord.Colour.blurple()
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embedText = "Free shit!"

        claimedBoxes = []

        if member.cooldowns["hourly"].expired:  # Hourly Claim
            member.cooldowns["hourly"].reset()
            roll = random.randint(1, 10000)
            if roll < 6500:
                lootbox = Item.get("LOOTC")
            elif roll < (6500 + 3000):
                lootbox = Item.get("LOOTU")
            elif roll < (6500 + 3000 + 400):
                lootbox = Item.get("LOOTR")
            elif roll < (6500 + 3000 + 400 + 80):
                lootbox = Item.get("LOOTL")
            elif roll < (6500 + 3000 + 400 + 80 + 15):
                lootbox = Item.get("LOOTE")
            else:
                lootbox = Item.get("LOOTM")
            if Item.currentEventBox is not None:
                roll = random.randint(1, 3)
                if roll != 3:
                    lootbox = Item.currentEventBox
            claimedBoxes.append(lootbox)
            member.inventory.add(lootbox)
            embed.add_field(name="Hourly",
                            value=f"Success! You claimed a {lootbox.rarity.icon} **{lootbox.name}**!",
                            inline=False)
        else:
            embed.add_field(name="Hourly",
                            value=f"You still have {member.cooldowns['hourly'].time_remaining_string} left!",
                            inline=False)

        if member.cooldowns["daily"].expired:  # Daily Claim
            member.cooldowns["daily"].reset()
            roll = random.randint(1, 10000)
            if roll < 2000:
                lootbox = Item.get("LOOTU")
            elif roll < (2000 + 6500):
                lootbox = Item.get("LOOTR")
            elif roll < (2000 + 6500 + 1200):
                lootbox = Item.get("LOOTL")
            elif roll < (2000 + 6500 + 1200 + 250):
                lootbox = Item.get("LOOTE")
            else:
                lootbox = Item.get("LOOTM")
            claimedBoxes.append(lootbox)
            member.inventory.add(lootbox)
            embed.add_field(name="Daily",
                            value=f"Success! You claimed a {lootbox.rarity.icon} **{lootbox.name}**!",
                            inline=False)
        else:
            embed.add_field(name="Daily",
                            value=f"You still have {member.cooldowns['daily'].time_remaining_string} left!",
                            inline=False)

        if member.cooldowns["weekly"].expired:  # Weekly Claim
            member.cooldowns["weekly"].reset()
            roll = random.randint(1, 10000)
            if roll < 2000:
                lootbox = Item.get("LOOTR")
            elif roll < (2000 + 6500):
                lootbox = Item.get("LOOTL")
            elif roll < (2000 + 6500 + 1000):
                lootbox = Item.get("LOOTE")
            else:
                lootbox = Item.get("LOOTM")
            claimedBoxes.append(lootbox)
            member.inventory.add(lootbox)
            embed.add_field(name="Weekly",
                            value=f"Success! You claimed a {lootbox.rarity.icon} **{lootbox.name}**!",
                            inline=False)
        else:
            embed.add_field(name="Weekly",
                            value=f"You still have {member.cooldowns['weekly'].time_remaining_string} left!",
                            inline=False)

        embed.description = embedText

        view = Views.ClaimView(claimedBoxes, ctx.author.id, embed) if claimedBoxes else None

        await ctx.reply(embed=embed, view=view, mention_author=False)

        if claimedBoxes:
            await member.missions.log_action("claim", ctx)
            member.stats.claims += 1
            member.stats.claimedBoxes += len(claimedBoxes)

        member.write_data()

    @commands.hybrid_command()
    async def sell(self, ctx: commands.Context, *, search: str) -> None:
        member = Member.get(ctx.author.id)
        if search.lower() in ["dupes", "duplicates"]:
            dupes_found = 0
            sold_value = 0
            for item in member.inventory.items:
                if type(item) is Item.Lootbox:
                    continue
                if member.inventory.items.count(item) > 1:
                    for i in range(1, member.inventory.items.count(item)):
                        member.inventory.remove(item)
                        member.balance += item.value
                        sold_value += item.value
                        dupes_found += 1

            if dupes_found > 0:
                await ctx.reply(
                    f"You sold **{dupes_found} item(s)** for $*{sold_value}*. Your new balance is $*{member.balance}*.",
                    mention_author=False)
                member.write_data()
            else:
                await ctx.reply(f"You don't have any duplicates! Nice!", mention_author=False)
            return

        if search.lower() in ["all", "*"]:
            items = 0
            amount = 0
            itemList = []
            for item in member.inventory.items:
                if type(item) is Item.Lootbox:
                    continue
                itemList.append(item)
            for item in itemList:
                items += 1
                amount += item.value
                member.inventory.remove(item)
                member.balance += item.value
            member.stats.soldItems += items
            await ctx.reply(
                f"You sold **{items} item(s)** for $*{amount}*. Your new balance is $*{member.balance}*.",
                mention_author=False)
            member.write_data()

            return

        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply("Sorry, I couldn't find that item!", mention_author=False)
            return

        if type(item) == Item.Lootbox:
            await ctx.reply("You can't sell lootboxes!", mention_author=False)
            return

        try:
            member.inventory.remove(item)
            member.balance += item.value
            await ctx.reply(
                f"You sold **{item.name}** for *${item.value}*. Your new balance is $*{member.balance}*.",
                mention_author=False)
            member.write_data()

        except Errors.ItemNotInInventoryError:
            await ctx.reply(f"It looks like you don't have an **{item.name}** :pensive:", mention_author=False)

    @commands.command(aliases=["c", "col"])
    async def collection(self, ctx: commands.Context, *args: str) -> None:
        member = Member.get(ctx.author.id)

        if len(args) == 0:  # Collections Overview

            embed = discord.Embed()
            embed.title = f"{ctx.author.display_name}'s Collection"
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            totalItems = 0

            for collection in Collection.collections:
                totalItems += len(collection.items)
                collectionItemsDiscovered = 0
                for item in collection.items:
                    if member.collection.contains(item):
                        collectionItemsDiscovered += 1

                icon = collection.icon

                embed.add_field(name=f"{icon}  {collection.name}",
                                value=f"{collectionItemsDiscovered}/{len(collection.items)} items discovered",
                                inline=False)

            embed.description = f"{len(member.collection.items)}/{totalItems} items discovered"

            await ctx.reply(embed=embed, mention_author=False)
            return

        elif args[0] in ["full", "*", "all"]:  # Full Collections Format

            embeds = [discord.Embed()]
            embeds[0].title = f"{ctx.author.display_name}'s Collection"
            embeds[0].description = f"{len(member.collection.items)} items discovered."
            embeds[0].set_thumbnail(url=ctx.author.display_avatar.url)

            length = 0

            for collection in Collection.collections:
                collectionItemsDiscovered = 0
                itemsList = ""
                for item in collection.items:
                    if member.collection.contains(item):
                        collectionItemsDiscovered += 1
                        itemsList += f"{item.name} *({item.id})*\n"
                    else:
                        itemsList += f"??? *({item.id})*\n"

                icon = collection.icon

                length += len(itemsList)
                if length > 5000:
                    length -= 5000
                    embeds.append(discord.Embed())
                    embeds[-1].title = f"{ctx.author.display_name}'s Collection"
                    embeds[-1].description = f"{len(member.collection.items)} items discovered."
                    embeds[-1].set_thumbnail(url=ctx.author.display_avatar.url)

                embeds[-1].add_field(
                    name=f"{icon}  {collection.name} ({collectionItemsDiscovered}/{len(collection.collection)})",
                    value=itemsList[:-1], inline=True)

            if len(embeds) > 1:
                for embed in embeds:
                    embed.title = f"{ctx.author.display_name}'s Collection ({embeds.index(embed) + 1}/{len(embeds)})"

            for embed in embeds:
                await ctx.reply(embed=embed, mention_author=False)

        else:  # Specific Collections Format

            collectionsToShow = []
            for collectionName in args:
                for collection in Collection.collections:
                    if collectionName.lower() == collection.name.lower() or collectionName.upper() == collection.id:
                        collectionsToShow.append(collection)
                        break

            if len(collectionsToShow) != len(args):
                await ctx.reply("I don't recognise all of those collection names, please try again!",
                                mention_author=False)
                return

            collectionsToShow = list(set(collectionsToShow))

            embeds = [discord.Embed()]
            embeds[0].title = f"{ctx.author.display_name}'s Collection"
            embeds[0].description = f"{len(member.collection.items)} items discovered."
            embeds[0].set_thumbnail(url=ctx.author.display_avatar.url)

            length = 0

            for collection in collectionsToShow:
                collectionItemsDiscovered = 0
                itemsList = ""
                for item in collection.items:
                    if member.collection.contains(item):
                        collectionItemsDiscovered += 1
                        itemsList += f"{item.name} *({item.id})*\n"
                    else:
                        itemsList += f"??? *({item.id})*\n"

                icon = collection.icon

                length += len(itemsList)
                if length > 5000:
                    length -= 5000
                    embeds.append(discord.Embed())
                    embeds[-1].title = f"{ctx.author.display_name}'s Collection"
                    embeds[-1].description = f"{len(member.collection.items)} items discovered."
                    embeds[-1].set_thumbnail(url=ctx.author.display_avatar.url)

                embeds[-1].add_field(
                    name=f"{icon}  {collection.name} ({collectionItemsDiscovered}/{len(collection.items)})",
                    value=itemsList[:-1], inline=True)

            if len(embeds) > 1:
                for embed in embeds:
                    embed.title = f"{ctx.author.display_name}'s Collection ({embeds.index(embed) + 1}/{len(embeds)})"

            for embed in embeds:
                await ctx.reply(embed=embed, mention_author=False)

    @commands.command(aliases=["gift"])
    async def give(self, ctx: commands.Context, target: discord.Member, *, search: str) -> None:
        member = Member.get(ctx.author.id)
        targetMember = Member.get(target.id)
        try:
            item = Item.search(search)
        except Errors.ItemNotFoundError:
            await ctx.reply("I'm afraid I couldn't find that item!", mention_author=False)
            return

        try:
            member.inventory.remove(item)
            targetMember.inventory.add(item)
            await ctx.reply(f"You gave {item.rarity.icon} **{item.name}** to *{target.display_name}*",
                            mention_author=False)
        except Errors.ItemNotInInventoryError:
            await ctx.reply(
                f"It looks like you don't have {item.rarity.icon} **{item.name}** :pensive:",
                mention_author=False)
        member.write_data()

        targetMember.write_data()


async def setup(bot):
    await bot.add_cog(Collectibles(bot))
    print("Collectibles Cog loaded")


async def teardown(bot):
    print("Collectibles Cog unloaded")
    await bot.remove_cog(Collectibles(bot))
