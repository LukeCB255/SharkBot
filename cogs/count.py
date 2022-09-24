import random
from datetime import datetime, timedelta
from typing import Union

import discord
from discord.ext import commands

from SharkBot import Member, Item, IDs


def convert_to_num(message):
    result = ""

    for char in message.content:
        if char.isdigit():
            result = result + char

    if result == "":
        return None
    else:
        return int(result)


async def get_last_count(message) -> Union[discord.Message, None]:
    found = False
    async for pastMessage in message.channel.history(limit=None):
        if not found:
            found = pastMessage.id == message.id
        else:
            if pastMessage.author.id in IDs.blacklist or convert_to_num(pastMessage) is None:
                continue
            return pastMessage
    return None


async def get_last_member_count(message) -> Union[discord.Message, None]:
    found = False
    async for pastMessage in message.channel.history(limit=None):
        if not found:
            found = pastMessage.id == message.id
        else:
            if pastMessage.author.id is not message.author.id:
                continue
            return pastMessage
    return None


class Count(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def updatetally(self, ctx: commands.Context) -> None:
        channel = await self.bot.fetch_channel(IDs.channels["Count"])

        outputText = "Working on it!"
        message = await ctx.send(f"```{outputText}```")
        outputText += "\n"

        for member in Member.members.values():
            member.counts = 0

        progress = 0
        async for pastMessage in channel.history(limit=None):
            progress += 1
            if progress % 200 == 0:
                outputText += f"\n{progress} messages processed..."
                await message.edit(content=f"```{outputText}```")

            if pastMessage.author.id in IDs.blacklist:
                continue
            if convert_to_num(pastMessage) is None:
                continue

            member = Member.get(pastMessage.author.id)
            member.counts += 1

        for member in Member.members.values():
            member.write_data()

        outputText += "\n\nDone!"
        await message.edit(content=f"```{outputText}```")

        await self.tally(ctx)

    @commands.hybrid_command()
    async def tally(self, ctx: commands.Context) -> None:
        server = await self.bot.fetch_guild(IDs.servers["Shark Exorcist"])
        memberNames = {member.id: member.display_name async for member in server.fetch_members()}

        members = [member for member in Member.members.values() if member.counts > 0]
        members.sort(key=lambda m: m.counts, reverse=True)

        table = []
        lastCounts = 10000
        rank = 0
        trueRank = 0
        for member in members:
            trueRank += 1
            if member.counts < lastCounts:
                lastCounts = member.counts
                rank = trueRank

            memberName = memberNames[member.id] if member.id in memberNames else "*Exorcised Shark*"

            table.append({
                "name": memberName,
                "rank": rank,
                "counts": member.counts
            })

        outputText = "\n".join([f"{row['rank']}. {row['name']} - {row['counts']}" for row in table])

        embed = discord.Embed()
        embed.title = "Count to 10,000"
        embed.description = outputText

        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def timeline(self, ctx: commands.Context) -> None:
        channel = await self.bot.fetch_channel(IDs.channels["Count"])

        outputText = "Working on it!"
        message = await ctx.send(f"```{outputText}```")
        outputText += "\n"

        table = {}
        progress = 0
        async for pastMessage in channel.history(limit=None, oldest_first=True):
            progress += 1
            if progress % 200 == 0:
                outputText += f"\n{progress} messages processed..."
                await message.edit(content=f"```{outputText}```")

            date = datetime.strftime(pastMessage.created_at, "%d/%m/%Y")
            table[date] = table.get(date, 0) + 1

        resultText = "\n".join([f"{date} - {counts}" for date, counts in table.items()])

        embed = discord.Embed()
        embed.title = "Timeline"
        embed.description = resultText

        await message.edit(content=None, embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id != IDs.channels["Count"]:
            return
        if message.author.id in IDs.blacklist:
            return
        if convert_to_num(message) is None:
            return
        member = Member.get(message.author.id)

        countCorrect = True
        lastCount = await get_last_count(message)
        lastMemberCount = await get_last_member_count(message)
        if lastCount is not None:
            countValue = convert_to_num(message)
            lastCountValue = convert_to_num(lastCount)

            if message.author == lastCount.author:
                countCorrect = False
                await message.add_reaction("❗")

            if message.created_at - lastMemberCount.created_at < timedelta(minutes=10):
                countCorrect = False
                await message.add_reaction("🕒")

            if countValue != lastCountValue + 1:
                countCorrect = False
                await message.add_reaction("👀")

        if countCorrect:

            member.counts += 1
            member.balance += 1

            box = None

            if Item.currentEventBox is not None and not member.collection.contains(Item.currentEventBox):
                box = Item.currentEventBox

            if box is None and member.counts == 0:
                roll = random.randint(1, 25)
                if roll < 3:
                    box = Item.get("LOOTE")
                elif roll < 10:
                    box = Item.get("LOOTL")
                else:
                    box = Item.get("LOOTR")

            if box is None:
                if random.randint(1, 8) == 8:
                    roll = random.randint(1, 100)
                    if roll < 3:
                        box = Item.get("LOOTE")
                    elif roll < 10:
                        box = Item.get("LOOTL")
                    elif roll < 25:
                        box = Item.get("LOOTR")
                    elif roll < 50:
                        box = Item.get("LOOTU")
                    else:
                        box = Item.get("LOOTC")

            if box is not None:
                member.inventory.add(box)
                member.stats.countingBoxes += 1
                await message.reply(
                    f"Hey, would you look at that! You found a {box.rarity.icon} **{box.name}**!",
                    mention_author=False
                )

            await member.missions.log_action("count", message.author)
        else:
            member.stats.incorrectCounts += 1

        member.write_data()

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.channel.id != IDs.channels["Count"]:
            return

        member = Member.get(before.author.id)

        reactionsList = [reaction.emoji for reaction in before.reactions]

        if "👀" in reactionsList and "🤩" not in reactionsList:
            lastCount = await get_last_count(after)
            if convert_to_num(after) == convert_to_num(lastCount) + 1:
                await after.add_reaction("🤩")

                member.write_data()


async def setup(bot):
    await bot.add_cog(Count(bot))
    print("Count Cog loaded")


async def teardown(bot):
    print("Count Cog unloaded")
    await bot.remove_cog(Count(bot))
