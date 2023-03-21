import discord

from .BungieData import BungieData
import SharkBot

STATS_DICT = {
    stat.name.title(): str(stat.value) for stat in SharkBot.Destiny.Enums.GuardianStats
}

class Stats(BungieData):
    _COMPONENTS = [200]
    _THUMBNAIL_URL = None

    @staticmethod
    def _process_data(data):
        results: dict[str, dict[str, int]] = {}
        for guardian_data in data["characters"]["data"].values():
            guardian = SharkBot.Destiny.Guardian(guardian_data)
            guardian_light = guardian_data["light"]
            guardian_stats = {
                stat_name: guardian_data["stats"][stat_hash] for stat_name, stat_hash in STATS_DICT.items()
            }
            results[f"{guardian} `{guardian_light}`"] = guardian_stats
        return results

    # @staticmethod
    # def _process_cache_write(data):
    #     return data

    # @staticmethod
    # def _process_cache_load(data):
    #     return data

    # @classmethod
    # def _format_cache_embed_data(cls, embed: discord.Embed, data, **kwargs):
    #     cls._format_embed_data(embed, data)

    # @staticmethod
    # def _format_embed_data(embed: discord.Embed, data, **kwargs):
    #     embed.description = f"\n```{SharkBot.Utils.JSON.dumps(data)}```"
