import io
import json
from typing import Optional, Literal, Callable
import logging
from datetime import datetime, time, timedelta

import discord
from discord.ext import commands, tasks

last_notif: Optional[datetime] = None

task_logger = logging.getLogger("task")

import SharkBot

disabled = SharkBot.Checks.disabled("Due to an issue with the latest version of `next.js`, this command has temporarily been disabled.\nJames is working on a fix for this issue, we hope it will be resolved soon.")

_MANIFEST_INTERVAL_FILE = "data/live/bot/manifest_interval.txt"
SharkBot.Utils.FileChecker.file(_MANIFEST_INTERVAL_FILE, str(60*60*2))
with open(_MANIFEST_INTERVAL_FILE, "r") as _infile:
    _manifest_interval = int(_infile.read())

_LOADING_ICON_URL = "https://cdn.dribbble.com/users/2081/screenshots/4645074/loading.gif"

SEAL_HASHES: dict[str, str] = {}
root_seal_node = SharkBot.Destiny.Definitions.DestinyPresentationNodeDefinition.get(616318467)
for child_node in root_seal_node["children"]["presentationNodes"]:
    child_node_hash = str(child_node["presentationNodeHash"])
    child_node_definition = SharkBot.Destiny.Definitions.DestinyPresentationNodeDefinition.get(child_node_hash)
    child_seal_name = child_node_definition["displayProperties"]["name"].lower()
    if child_seal_name == "classified":
        continue
    SEAL_HASHES[child_seal_name] = str(child_node_hash)
    child_completion_record = SharkBot.Destiny.Definitions.DestinyRecordDefinition.get(child_node_definition["completionRecordHash"])
    if child_completion_record["titleInfo"]["hasTitle"]:
        SEAL_HASHES[child_completion_record["titleInfo"]["titlesByGender"]["Male"].lower()] = str(child_node_hash)


with open("data/static/bungie/definitions/PatternSources.json", "r") as f:
    _pattern_sources = {
        weapon_name: [weapon_source.lower() for weapon_source in sources] for weapon_name, sources in json.load(f).items()
    }

for _sources in _pattern_sources.values():
    _sources.append(None)

_PATTERN_SOURCES = []
for _sources in _pattern_sources.values():
    _PATTERN_SOURCES.extend(_sources)
_PATTERN_SOURCES = list(set(_PATTERN_SOURCES))

import logging

cog_logger = logging.getLogger("cog")


class Destiny(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_tokens.start()
        self.reset.start()
        self.check_manifest_loop.start()
        self.check_blog_posts.start()

    def cog_unload(self) -> None:
        self.reset.cancel()
        self.check_tokens.cancel()
        self.check_manifest_loop.cancel()
        self.check_blog_posts.cancel()

    @tasks.loop(minutes=5)
    async def check_blog_posts(self):
        try:
            blog_posts = await SharkBot.Destiny.BlogPost.fetch_new_posts()
            if blog_posts:
                channel = await self.bot.fetch_channel(SharkBot.IDs.channels["Destiny Blog"])
                for post in blog_posts:
                    await channel.send(embed=post.to_embed())
                SharkBot.Destiny.BlogPost.update_last_publish_date(blog_posts[-1].publish_date)
        except Exception as error:
            await SharkBot.Utils.task_loop_handler(self.bot, error)

    @check_blog_posts.before_loop
    async def before_check_blog_posts(self):
        await self.bot.wait_until_ready()

    @tasks.loop(time=time(hour=13))
    async def check_tokens(self):
        try:
            for member in SharkBot.Member.members:
                if member.bungie.refresh_token_expiring:
                    await member.bungie.soft_refresh()
                    dev = self.bot.get_user(SharkBot.IDs.dev)
                    if dev is None:
                        dev = await self.bot.fetch_user(SharkBot.IDs.dev)
                    await dev.send(f"Performed auto-token refresh for {member.id}")
        except Exception as error:
            await SharkBot.Utils.task_loop_handler(self.bot, error)

    @tasks.loop(time=SharkBot.Destiny.reset_time)
    async def reset(self) -> None:
        try:
            channel = await self.bot.fetch_channel(SharkBot.IDs.channels["Destiny Reset"])
            embeds = SharkBot.Destiny.Reset.get_embeds()
            for embed in embeds:
                task_logger.info(f"Sent '{embed.title}' Embed")
                await channel.send(embed=embed)
        except Exception as error:
            await SharkBot.Utils.task_loop_handler(self.bot, error)

    @commands.hybrid_group()
    async def destiny(self, ctx: commands.Context) -> None:
        await ctx.send_help(self.destiny)

    @destiny.command()
    async def component_types(self, ctx: commands.Context, long_format: bool = False):
        embed = discord.Embed()
        embed.title = "ComponentTypeEnum"
        embed.description = "This is a list of ComponentTypeEnum within the Bungie API. If you don't know what that is, then it's not that important, just ignore it."
        if long_format:
            for component_type in SharkBot.Destiny.ComponentTypeEnum.enum_list:
                embed.add_field(
                    name=f"{component_type.name} - {component_type.enum}",
                    value=component_type.description,
                    inline=False
                )
        else:
            embed.description += "\n\n" + "\n".join(f"`{component_type.enum}` {component_type.name}" for component_type in SharkBot.Destiny.ComponentTypeEnum.enum_list)

        for e in SharkBot.Utils.split_embeds(embed):
            await ctx.reply(embed=e, mention_author=False)


    @destiny.command()
    @SharkBot.Checks.is_mod()
    async def send_embeds(self, ctx: commands.Context, channel: discord.TextChannel, include_weekly: bool = False):
        await ctx.send("Sending Destiny Reset Embeds")
        if channel.id == SharkBot.IDs.channels["Destiny Reset"]:
            await ctx.send("Deleting old embeds")
            async for message in channel.history(limit=10, after=(datetime.today() - timedelta(days=1))):
                if message.author.id != SharkBot.IDs.users["SharkBot"]:
                    continue
                await message.delete()
        embeds = SharkBot.Destiny.Reset.get_embeds(include_weekly)
        for embed in embeds:
            await channel.send(embed=embed)

    @destiny.command(
        description="Shows info about today's active Lost Sector"
    )
    async def sector(self, ctx: commands.Context) -> None:
        current_sector = SharkBot.Destiny.LostSector.get_current()
        reward = SharkBot.Destiny.LostSectorReward.get_current()

        if current_sector is None:
            embed = discord.Embed()
            embed.title = "Today's Lost Sector"
            embed.description = "Lost Sector Unknown (Season just started)"
            embed.set_thumbnail(
                url="https://www.bungie.net/common/destiny2_content/icons/6a2761d2475623125d896d1a424a91f9.png"
            )
            await ctx.reply(embed=embed)
            return

        embed = discord.Embed()
        embed.title = f"{current_sector.name}\n{current_sector.destination}"
        embed.description = f"{current_sector.burn} Burn {reward}"
        embed.set_thumbnail(
            url="https://www.bungie.net/common/destiny2_content/icons/6a2761d2475623125d896d1a424a91f9.png"
        )
        embed.add_field(
            name=f"Legend {SharkBot.Icon.get('light_icon')} {SharkBot.Destiny.PowerCap.Activity.LEGEND}",
            value=f"{current_sector.legend.details}"
        )
        embed.add_field(
            name=f"Master {SharkBot.Icon.get('light_icon')} {SharkBot.Destiny.PowerCap.Activity.MASTER}",
            value=f"{current_sector.master.details}"
        )

        await ctx.send(embed=embed)

    @destiny.command(
        description="Shows info about today's Nightfall"
    )
    @discord.app_commands.choices(
        nightfall=[
            discord.app_commands.Choice(name=nf.name, value=nf.name) for nf in SharkBot.Destiny.Nightfall.current_rotation
        ]
    )
    async def nightfall(self, ctx: commands.Context, nightfall: str = SharkBot.Destiny.Nightfall.get_current().name):
        current_nightfall = SharkBot.Destiny.Nightfall.get(nightfall)

        if current_nightfall is None:
            embed = discord.Embed()
            embed.title = "This Week's Nightfall"
            embed.description = "Nightfall Rotation Unknown (Season just started)"
            embed.set_thumbnail(
                url="https://www.bungie.net/common/destiny2_content/icons/a72e5ce5c66e21f34a420271a30d7ec3.png"
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed()
        embed.title = f"{current_nightfall.name}\n{current_nightfall.destination}"
        embed.set_thumbnail(
            url="https://www.bungie.net/common/destiny2_content/icons/a72e5ce5c66e21f34a420271a30d7ec3.png"
        )
        embed.add_field(
            name=f"Legend {SharkBot.Icon.get('light_icon')} {SharkBot.Destiny.PowerCap.Activity.LEGEND}",
            value=" ".join(current_nightfall.legend.icons),
            inline=False
        )
        embed.add_field(
            name=f"Master {SharkBot.Icon.get('light_icon')} {SharkBot.Destiny.PowerCap.Activity.MASTER}",
            value=" ".join(current_nightfall.master.icons),
            inline=False
        )
        embed.add_field(
            name=f"Grandmaster {SharkBot.Icon.get('light_icon')} {SharkBot.Destiny.PowerCap.Activity.GRANDMASTER}",
            value=" ".join(current_nightfall.grandmaster.icons),
            inline=False
        )

        await ctx.send(embed=embed)

    @destiny.command(
        description="Shows info about this season's GMs"
    )
    async def grandmaster(self, ctx: commands.Context) -> None:
        current = SharkBot.Destiny.Nightfall.get_current()

        if datetime.utcnow() < datetime(2023, 1, 17):
            embed = discord.Embed()
            embed.title = "Grandmaster Nightfalls"
            embed.description = "Grandmaster Nightfalls release on January 17th, 2023"
            await ctx.reply(embed=embed, mention_author=False)
            return

        embed = discord.Embed()
        embed.title = "Grandmaster Nightfalls"
        embed.description = f"{SharkBot.Icon.get('light_icon')} {SharkBot.Destiny.PowerCap.Activity.GRANDMASTER}"
        embed.colour = discord.Colour.dark_red()

        embed.add_field(
            name=f"{current.name} - {current.destination} (This Week)",
            value=current.grandmaster.icons_str,
            inline=False
        )

        for nightfall in SharkBot.Destiny.Nightfall.rotation_from(current)[1:]:
            embed.add_field(
                name=f"{nightfall.name} - {nightfall.destination}",
                value=nightfall.grandmaster.icons_str,
                inline=False
            )

        await ctx.reply(embed=embed, mention_author=False)

    @destiny.command(
        hidden=True
    )
    async def sector_list(self, ctx: commands.Context) -> None:
        embed = discord.Embed()
        embed.title = "Lost Sectors"
        embed.set_thumbnail(
            url="https://www.bungie.net/common/destiny2_content/icons/6a2761d2475623125d896d1a424a91f9.png"
        )
        for lostSector in SharkBot.Destiny.LostSector.lost_sectors:
            embed.add_field(
                name=f"{lostSector.name} - {lostSector.destination}",
                value=f"Champions: *{lostSector.champion_list}*\nShields: *{lostSector.shield_list}*",
                inline=False
            )

        await ctx.send(embed=embed)

    @destiny.command(
        description="Gives details about the current Season"
    )
    async def season(self, ctx: commands.Context) -> None:
        season = SharkBot.Destiny.Season.current
        embed = discord.Embed()
        embed.title = f"Season {season.number} - {season.name}"
        embed.description = f"**{season.calendar_string}**\n{season.time_remaining_string} left in the Season"
        embed.set_thumbnail(
            url=season.icon_url
        )

        await ctx.reply(embed=embed, mention_author=False)

    @destiny.command(
        description=f"Shows the Power Caps for {SharkBot.Destiny.Season.current.name}."
    )
    async def power_cap(self, ctx: commands.Context):
        icon = SharkBot.Icon.get("light_icon")
        embed = discord.Embed(
            title=f"{SharkBot.Destiny.Season.current.name} Power Caps",
            colour=discord.Colour.greyple()
        )
        embed.set_author(
            name=ctx.author.name,
            icon_url=ctx.author.display_avatar.url
        )
        embed.set_thumbnail(
            url=SharkBot.Destiny.Season.current.icon_url
        )
        embed.add_field(
            name="__Gear Caps__",
            value="\n".join(f"**{name}** {icon} {value}" for name, value in SharkBot.Destiny.PowerCap.Gear.items()),
            inline=False
        )
        embed.add_field(
            name="__Max Effective Power__",
            value="\n".join(f"**{name}** {icon} {value}" for name, value in SharkBot.Destiny.PowerCap.MaxEffectivePower.items()),
            inline=False
        )
        embed.add_field(
            name="__Activity Power__",
            value="\n".join(f"**{name}** {icon} {value}" for name, value in SharkBot.Destiny.PowerCap.Activity.items()),
            inline=False
        )
        await ctx.reply(embed=embed, mention_author=False)


    @destiny.command(
        description="Gives information about this week's raids."
    )
    async def raid(self, ctx: commands.Context) -> None:
        seasonal = SharkBot.Destiny.Raid.seasonal
        featured = SharkBot.Destiny.Raid.get_current()

        embed = discord.Embed()
        embed.title = "Raids"
        embed.set_thumbnail(
            url="https://www.bungie.net/common/destiny2_content/icons/9230cd18bcb0dd87d47a554afb5edea8.png"
        )
        embed.add_field(
            name="Seasonal",
            value=seasonal.name,
            inline=False
        )
        embed.add_field(
            name="Featured",
            value=featured.name,
            inline=False
        )

        await ctx.reply(embed=embed, mention_author=False)

    @destiny.command(
        description="Gives information about this week's dungeons."
    )
    async def dungeon(self, ctx: commands.Context) -> None:
        seasonal = SharkBot.Destiny.Dungeon.seasonal
        featured = SharkBot.Destiny.Dungeon.get_current()

        embed = discord.Embed()
        embed.title = "Dungeons"
        embed.set_thumbnail(
            url="https://www.bungie.net/common/destiny2_content/icons/082c3d5e7a44343114b5d056c3006e4b.png"
        )
        embed.add_field(
            name="Seasonal",
            value=seasonal.name,
            inline=False
        )
        embed.add_field(
            name="Featured",
            value=featured.name,
            inline=False
        )

        await ctx.reply(embed=embed, mention_author=False)

    @destiny.command(
        description="Gives the XP requirements for the given artifact power bonus."
    )
    async def bonus(self, ctx: commands.Context, level: int):
        embed = discord.Embed()
        embed.title = "Artifact Power Bonus"
        embed.colour = discord.Colour.teal()
        embed.set_thumbnail(
            url="https://www.bungie.net/common/destiny2_content/icons/7b513c9215111507dbf31e3806cc1fcf.jpg"
        )

        def calc_xp(targetlevel: int) -> int:
            return ((targetlevel-2) * 110000) + 55000

        if level < 1:
            embed.description = "Power Bonus must be greater than zero, dangus"
        else:
            if level == 1:
                embed.description = "+1 given by default"
                bonus_range = list(range(2, 6))
            else:
                bonus_range = list(range(level, level+5))

            for lvl in bonus_range:
                xp = calc_xp(lvl)
                total_xp = sum([calc_xp(x) for x in range(2, lvl+1)])
                embed.add_field(
                    name=f"`+{'{:,}'.format(lvl)}` Bonus",
                    value=f"`{'{:,}'.format(xp)}` xp\n`{'{:,}'.format(total_xp)}` xp total",
                    inline=False
                )

        await ctx.send(embed=embed)

    @discord.app_commands.command(
        description="Authorizes SharkBot to get your Destiny 2 data from Bungie"
    )
    async def bungie_auth(self, interaction: discord.Interaction):
        embed = discord.Embed()
        embed.title = "Bungie Auth"
        embed.description = "In order to fetch your Destiny 2 Profile, you need to authorize SharkBot with Bungie\n"
        embed.description += "The link below will take you to the SharkBot OAuth2 portal, where you can sign in with your Bungie Account"
        embed.add_field(
            name="Bungie Auth Link",
            value=f"https://sharkbot.online/bungie_auth/discord/{interaction.user.id}"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @destiny.command(
        description="De-Authorizes SharkBot from your Bungie Account"
    )
    async def deauth(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        embed = discord.Embed()
        embed.title = "Bungie Deauthentication"
        embed.description = "Removing credentials from SharkBot..."
        embed.colour = discord.Colour.blurple()

        reply_message = await ctx.reply(embed=embed, mention_author=False)

        exists = member.bungie.delete_credentials()
        if exists:
            embed.description = "Removed Bungie Authentication."
            embed.colour = discord.Colour.green()
        else:
            embed.description = "Your Bungie Account is already not authorised with SharkBot"
            embed.colour = discord.Colour.red()

        await reply_message.edit(embed=embed)


    @destiny.command(
        description="Shows your Progress with your craftable weapons"
    )
    async def patterns(self, ctx: commands.Context, source: Optional[str] = None):
        if source is not None and source.lower() not in _PATTERN_SOURCES:
            return await ctx.send(f"Invalid source: {source}")
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.craftables.send_embeds(ctx, source=source)

    @patterns.autocomplete("source")
    async def patterns_source_autocomplete(self, interaction: discord.Interaction, current: str):
        return await SharkBot.Autocomplete.pattern_source(interaction, current)

    @destiny.command(
        description="Shows your progress on the Conqueror Seal this season"
    )
    async def conqueror(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.conqueror.send_embeds(ctx)


    @destiny.command(
        description="Shows the weapons you are yet to acquire from the Monument to Lost Light"
    )
    async def monument(self, ctx: commands.Context, *, year: str = "*"):
        year = year.lower()
        if year == "*":
            years = ["1", "2", "3", "4", "5"]
        elif year in ["1", "one", "rw", "red war"]:
            years = ["1"]
        elif year in ["2", "two", "forsaken"]:
            years = ["2"]
        elif year in ["3", "three", "shadowkeep"]:
            years = ["3"]
        elif year in ["4", "four", "beyond", "beyond light"]:
            years = ["4"]
        elif year in ["5", "five", "wq", "witch queen"]:
            years = ["5"]
        else:
            await ctx.reply(f"`{year}` is not a valid Year for me to look for!")
            return

        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.monument.send_embeds(ctx, years=years)

    @destiny.command(
        description="Shows the levels of the weapons you have crafted"
    )
    async def levels(self, ctx: commands.Context, filter_by: Optional[Literal["<", "<=", "==", ">=", ">"]] = None, level: Optional[int] = None):

        f: Optional[Callable[[list[str, int, str]], bool]] = None
        if filter_by is not None:
            if level is None:
                embed = discord.Embed()
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
                embed.colour = discord.Colour.red()
                embed.title = "Something went wrong!"
                embed.description = "You can't specify a filter and then no value to filter off of!"
                await ctx.reply(embed=embed)
                return
            else:
                if filter_by == "<":
                    f = lambda d: d.level < level
                elif filter_by == "<=":
                    f = lambda d: d.level <= level
                elif filter_by == "==":
                    f = lambda d: d.level == level
                elif filter_by == ">=":
                    f = lambda d: d.level >= level
                elif filter_by == ">":
                    f = lambda d: d.level > level
                else:
                    embed = discord.Embed()
                    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
                    embed.colour = discord.Colour.red()
                    embed.title = "Something went wrong!"
                    embed.description = f"I don't recognise `{filter_by}` as a filter condition. Please use `<`, `<=`, `=`, `>=` or `>`"
                    await ctx.reply(embed=embed)
                    return

        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.weapon_levels.send_embeds(ctx, f=f)

    # @destiny.command(
    #     description="Shows the various currencies on your characters."
    # )
    # async def currencies(self, ctx: commands.Context):
    #     member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
    #     await member.bungie.currencies.send_embeds(ctx)

    @destiny.command(
        description="Shows your progress of storing bounties against a checklist."
    )
    async def prep(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.bounty_prep.send_embeds(ctx)

    # @destiny.command(
    #     description="Shows your progress for the Seal requested"
    # )
    # async def seal(self, ctx: commands.Context, *, seal: str):
    #     if seal not in SEAL_HASHES.values():
    #         if seal.lower() in SEAL_HASHES:
    #             seal = SEAL_HASHES[seal.lower()]
    #         else:
    #             raise SharkBot.Destiny.Errors.SealNotFoundError(seal)
    #     member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
    #     await member.bungie.seals.send_embeds(ctx, seal_hash=seal)

    # @seal.autocomplete("seal")
    # async def seal_seal_autocomplete(self, interaction: discord.Interaction, current: str):
    #     return await SharkBot.Autocomplete.seal(interaction, current)

    # @destiny.command(
    #     description="Shows the current Phase and Reward for the Wellspring"
    # )
    # async def wellspring(self, ctx: commands.Context):
    #     current_wellspring = SharkBot.Destiny.Wellspring.get_current()
    #     embed = discord.Embed(
    #         title=f"Wellspring: __{current_wellspring.mode}__"
    #     )
    #     embed.add_field(
    #         name="Weapon",
    #         value=f"{current_wellspring.weapon.icons} **{current_wellspring.weapon.name}**\n*{current_wellspring.weapon.type}*",
    #         inline=False
    #     )
    #     embed.add_field(
    #         name="Boss",
    #         value=f"*{current_wellspring.boss}*",
    #         inline=False
    #     )
    #     embed.set_thumbnail(url="https://www.light.gg/Content/Images/wellspring-icon.png")
    #     embed.colour = discord.Colour.dark_green()
    #     await ctx.reply(embed=embed, mention_author=False)

    @destiny.command(
        description="Shows the Season Pass level you've reached in each Season"
    )
    async def season_levels(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.season_levels.send_embeds(ctx)

    @tasks.loop(seconds=_manifest_interval)
    async def check_manifest_loop(self):
        task_logger.info("Checking Destiny Manifest Version")
        if await SharkBot.Destiny.Manifest.is_outdated():
            task_logger.warning("Manifest Outdated, Updating...")
            dev = await self.bot.fetch_user(SharkBot.IDs.dev)
            current_version = SharkBot.Destiny.Manifest.get_current_manifest()["Response"]["version"]
            embed=discord.Embed(
                title="Manifest Update"
            )
            embed.add_field(
                name="Current Version",
                value=f"`{current_version}`",
                inline=False
            )
            embed.add_field(
                name="Updating Manifest...",
                value="`Working on it...`",
                inline=False
            )
            message = await dev.send(embed=embed)
            await SharkBot.Destiny.Manifest.update_manifest_async()
            new_version = SharkBot.Destiny.Manifest.get_current_manifest()["Response"]["version"]
            embed.set_field_at(
                index=-1,
                name="Updated Manifest",
                value=f"`{new_version}`",
                inline=False
            )
            await message.edit(embed=embed)
        else:
            task_logger.info("Manifest Up to Date")

    @check_manifest_loop.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @check_manifest_loop.error
    async def check_manifest_loop_error(self, error: Exception):
        if isinstance(error, SharkBot.Errors.Manifest.FetchFailedError):
            if error.status_code == 503:
                if last_notif is None or (datetime.utcnow() - last_notif) < timedelta(hours=2):
                    dev = await self.bot.fetch_user(SharkBot.IDs.dev)
                    await dev.send("`Destiny API still offline.`")
                return
        await SharkBot.Utils.task_loop_handler(self.bot, error)

    @commands.command()
    @commands.is_owner()
    async def change_manifest_interval(self, ctx: commands.Context, seconds: int):
        self.check_manifest_loop.change_interval(seconds=seconds)
        global _manifest_interval
        _manifest_interval = seconds
        with open(_MANIFEST_INTERVAL_FILE, "w+") as _outfile:
            _outfile.write(str(seconds))
        await ctx.reply(f"Changed interval to `{seconds}s`")

    @commands.command()
    @SharkBot.Checks.is_mod()
    async def get_new_hashes(self, ctx: commands.Context):
        message = await ctx.reply("Working on it...")
        result = SharkBot.Destiny.Manifest.get_all_new_hashes()
        with io.BytesIO(json.dumps(result, indent=2).encode("utf-8")) as file_io:
            file = discord.File(filename="new_hashes.json", fp=file_io)
        await message.edit(attachments=[file])
        SharkBot.Destiny.Manifest.update_seen_hashes()

    @commands.command()
    @SharkBot.Checks.is_mod()
    async def get_new_definitions(self, ctx: commands.Context):
        message = await ctx.reply("Working on it...")
        hash_result = SharkBot.Destiny.Manifest.get_all_new_hashes()
        result = {}
        for definition_type, hashes in hash_result.items():
            result[definition_type] = SharkBot.Destiny.Manifest.get_definitions(definition_type, hashes)
        with io.BytesIO(json.dumps(result, indent=2).encode("utf-8")) as file_io:
            file = discord.File(filename="new_hashes.json", fp=file_io)
        await message.edit(attachments=[file])
        SharkBot.Destiny.Manifest.update_seen_hashes()

    @commands.command()
    @SharkBot.Checks.is_mod()
    async def lookup_via_file(self, ctx: commands.Context):
        if len(ctx.message.attachments) == 0:
            await ctx.reply("Where file?")
            return
        to_find: dict[str, list[int]] = json.loads(await ctx.message.attachments[0].read())
        message = await ctx.reply("Working on it...")
        result = {}
        for definition_type, hashes in to_find.items():
            result[definition_type] = SharkBot.Destiny.Manifest.get_definitions(definition_type, hashes)
        with io.BytesIO(json.dumps(result, indent=2).encode("utf-8")) as file_io:
            file = discord.File(filename="definitions.json", fp=file_io)
        await message.edit(attachments=[file])
        SharkBot.Destiny.Manifest.update_seen_hashes()

    @destiny.command(
        aliases=["engrams"],
        description="Shows how many Engrams you have at each vendor."
    )
    async def engram_tracker(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.engram_tracker.send_embeds(ctx)

    @destiny.command(
        description="Shows the Power Level offset of your gear."
    )
    async def power_level(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.power_level.send_embeds(ctx)

    # @destiny.command(
    #     description="Shows your progress with each of your incomplete Exotic Catalysts."
    # )
    # async def catalysts(self, ctx: commands.Context, show_missing: bool = False):
    #     member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
    #     await member.bungie.catalysts.send_embeds(ctx, show_missing=show_missing)

    @destiny.command(
        aliases=["pinnacle"],
        description="Shows the sources of Pinnacle and Powerful gear currently available for each of your characters."
    )
    async def pinnacles(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.pinnacles.send_embeds(ctx)

    @destiny.command(
        aliases=["gg"],
        description="Shows your Guardian Games Rank and Medals."
    )
    async def games(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.guardian_games.send_embeds(ctx)

    # @destiny.command(
    #     aliases=["intrinsic"],
    #     description="Shows Intrinsic Exotic Weapons and their breaker types"
    # )
    # async def intrinsics(self, ctx: commands.Context):
    #     embed = discord.Embed(
    #         title="Intrinsic Weapons",
    #         description=f"There are {sum(len(l) for l in SharkBot.Destiny.Intrinsics.values())} intrinsic weapons in Destiny 2"
    #     )
    #     for breaker_type, weapon_list in SharkBot.Destiny.Intrinsics.items():
    #         embed.add_field(
    #             name=str(SharkBot.Destiny.Champion.get(breaker_type)),
    #             value="\n".join(f"- {weapon}" for weapon in weapon_list),
    #             inline=False
    #         )
    #     await ctx.reply(embed=embed)

    @destiny.command(
        description="Shows the Stats of your Characters"
    )
    async def stats(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.stats.send_embeds(ctx)


    @destiny.command(
        description="Shows the objectives for your current Guardian Rank"
    )
    async def guardian_rank(self, ctx: commands.Context):
        member = SharkBot.Member.get(ctx.author.id, discord_user=ctx.author)
        await member.bungie.guardian_ranks.send_embeds(ctx)


async def setup(bot):
    await bot.add_cog(Destiny(bot))
    print("Destiny Cog Loaded")
    cog_logger.info("Destiny Cog Loaded")


async def teardown(bot):
    await bot.remove_cog(Destiny(bot))
    print("Destiny Cog Unloaded")
    cog_logger.info("Destiny Cog Unloaded")