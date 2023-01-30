import os
from datetime import datetime
import psutil

import discord
from discord.ext import tasks, commands

from SharkBot import Errors, Member, IDs, Code

_ani_codes = {
    "SharkBot1stAnniv": {
        "items": {
            "LOOTAP": 1,
            "LOOTSHARK": 11,
            "LOOTPAST": 11,
            "LOOTTL": 11,
            "LOOTA": 11,
            "LOOTAG": 11,
            "LOOTC": 1,
            "LOOTU": 1,
            "LOOTR": 1,
            "LOOTL": 1,
            "LOOTE": 1,
            "LOOTM": 1,
            "LOOTCON": 1,
            "LOOTCONADV": 1,
            "C111": 1,
            "U111": 1,
            "R111": 1,
            "L111": 1
        },
        "xp": 111,
        "balance": 1111
    },
    "Thankyou2023": {
        "items": {
            "LOOTLOVE": 1,
            "LOOTWQ": 1,
            "LOOTEA": 1,
            "LOOTS": 1,
            "LOOTSR": 1,
            "LOOTH": 1,
            "LOOTCH": 1,
            "LOOTNY": 1,
            "LOOTRED": 1,
            "LOOTLNY": 1,
            "LOOTZ": 1,
            "LOOTA": 1,
            "LOOTTL": 1,
        },
        "balance": 20,
        "xp": 23
    },
    "HiddenInSight": {
        "items": {
            "LOOTAG": 1,
            "LOOTA": 3,
            "LOOTPAST": 3,
            "LOOTTL": 3
        }
    },
    "SharkBotCommon110": {
        "items": {
            "LOOTC": 1
        },
        "xp": 1
    },
    "SharkBotUncommon110": {
        "items": {
            "LOOTU": 1
        },
        "xp": 2
    },
    "SharkBotRare110": {
        "items": {
            "LOOTR": 1
        },
        "xp": 3
    },
    "SharkBotLegendary110": {
        "items": {
            "LOOTL": 1
        },
        "xp": 4
    },
    "8376r483hnj": {
        "items": {
            "LOOTSHARK": 1
        },
        "xp": 1,
        "balance": 11
    },
    "iehfdeud763hgwej": {
        "items": {
            "LOOTSHARK": 1
        },
        "xp": 1,
        "balance": 11
    }
}


class Admin(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def test_error(self, ctx: commands.Context) -> None:
        raise Errors.TestError()

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def add_ani_codes(self, ctx: commands.Context):
        message = await ctx.reply("Adding Anniversary Codes")
        for code, code_data in _ani_codes.items():
            code = code.upper()
            Code.add_code(code)
            code = Code.get(code)
            item_rewards = code_data.get("items")
            xp_rewards = code_data.get("xp")
            balance_rewards = code_data.get("balance")
            if item_rewards is not None:
                for item_id, num in item_rewards.items():
                    for i in range(num):
                        code.add_reward("item", item_id)
            if xp_rewards is not None:
                code.add_reward("xp", xp_rewards)
            if balance_rewards is not None:
                code.add_reward("money", balance_rewards)
        await message.edit(content="Done!")

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def clean_members(self, ctx: commands.Context) -> None:
        user_ids = [user.id for user in self.bot.users]
        message_output = "Cleaning members...\n"
        message = await ctx.send(f"```{message_output}```")
        kept = 0
        removed = 0
        for member in list(Member.members):
            if member.id not in user_ids:
                message_output += f"\nRemoved {member.id}."
                await message.edit(content=f"```{message_output}```")
                member.delete_file()
                removed += 1
            else:
                kept += 1
        message_output += f"\n\nRemoved {removed} members, kept {kept}."
        await message.edit(content=f"```{message_output}```")
        Member.load_member_files()
        
    @commands.command()
    @commands.is_owner()
    async def get_emojis(self, ctx: commands.Context) -> None:
        output_text = "```Python\nicons = {"
        for emoji in ctx.guild.emojis:
            output_text += f'\n\t"{emoji.name}": "<:{emoji.name}:{emoji.id}>",'
        output_text = output_text[:-1] + "\n}\n```"
        await ctx.reply(output_text, mention_author=False)

    @commands.command()
    @commands.has_role(IDs.roles["Mod"])
    async def system_status(self, ctx: commands.Context) -> None:
        vm = psutil.virtual_memory()

        total_mb = "{:,.2f} MB".format(vm.total/(1024*1024))
        total_gb = "{:,.2f} GB".format(vm.total/(1024*1024*1024))
        used_mb = "{:,.2f} MB".format(vm.used/(1024*1024))
        used_gb = "{:,.2f} GB".format(vm.used/(1024*1024*1024))
        free_mb = "{:,.2f} MB".format(vm.free/(1024*1024))
        free_gb = "{:,.2f} GB".format(vm.free/(1024*1024*1024))
        percent = f"{100-vm.percent}%"

        process = psutil.Process(os.getpid()).memory_info()
        process_mb = "{:,.2f} MB".format(process.rss / 1024 ** 2)
        process_gb = "{:,.2f} GB".format(process.rss / 1024 ** 3)
        process_percent_used = "{:,.2f}% Used".format((process.rss / vm.used) * 100)
        process_percent_total = "{:,.2f}% Total".format((process.rss / vm.total) * 100)

        embed = discord.Embed()
        embed.colour = discord.Color.greyple()
        embed.title = "System Status"
        embed.add_field(
            name="Total RAM",
            value=f"{total_mb}\n{total_gb}"
        )
        embed.add_field(
            name="Used RAM",
            value=f"{used_mb}\n{used_gb}"
        )
        embed.add_field(
            name="Free RAM",
            value=f"{free_mb}\n{free_gb}"
        )
        embed.add_field(
            name="Percentage Free RAM",
            value=f"{percent}"
        )
        embed.add_field(
            name="Used by Python",
            value=f"{process_mb}\n{process_gb}\n{process_percent_used}\n{process_percent_total}"
        )

        await ctx.send(embed=embed)

    @commands.hybrid_group()
    @commands.has_role(IDs.roles["Mod"])
    async def purge(self, ctx: commands.Context) -> None:
        await ctx.send("Purge Command")

    @purge.command()
    @commands.has_role(IDs.roles["Mod"])
    async def last(self, ctx: commands.Context, number: int) -> None:
        message = await ctx.reply(f"```Deleting last {number} messages.```")
        deleted = await ctx.channel.purge(limit=number, before=discord.Object(ctx.message.id))
        await message.edit(content=f"```Deleted last {len(deleted)} messages.```")

    @purge.command()
    @commands.has_role(IDs.roles["Mod"])
    async def to(self, ctx: commands.Context, target: discord.Message) -> None:
        message = await ctx.reply(f"```Deleting up to {target.id}.```")
        deleted = await ctx.channel.purge(before=discord.Object(ctx.message.id), after=discord.Object(target.id))
        await message.edit(content=f"```Deleted {len(deleted)} messages.")

    @purge.command()
    @commands.has_role(IDs.roles["Mod"])
    async def member(self, ctx: commands.Context, target: discord.Member, limit: int = 100) -> None:
        message = await ctx.reply(f"```Deleting messages from {target.display_name} in last {limit} messages.```")
        deleted = await ctx.channel.purge(
            limit=limit,
            check=lambda m: m.author.id == target.id,
            before=discord.Object(ctx.message.id)
        )
        await message.edit(content=f"```Deleted {len(deleted)} messages from {target.display_name}.```")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        with open("data/live/bot/lastmessage.txt", "w+") as outfile:
            outfile.write(datetime.strftime(datetime.now(), "%d/%m/%Y-%H:%M:%S:%f"))

    @commands.command()
    @commands.is_owner()
    async def write_members(self, ctx: commands.Context, upload: bool = False):
        for member in Member.members:
            member.write_data(upload=upload)
        await ctx.reply(f"Saved data for {len(Member.members)} Members.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Admin(bot))
    print("Admin Cog loaded")


async def teardown(bot):
    print("Admin Cog unloaded")
    await bot.remove_cog(Admin(bot))
