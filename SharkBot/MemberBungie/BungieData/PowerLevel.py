import discord

from .BungieData import BungieData
import SharkBot

class HashTranslations:
    STAT_HASHES = {
        3897883278: "Armour",
        1480404414: "Weapons",
        3289069874: "Power Bonus"
    }
    WEAPON_TYPES = {
        2: "Kinetic",
        3: "Energy",
        4: "Power"
    }
    ARMOUR_CLASSES = {
        21: "Warlock",
        22: "Titan",
        23: "Hunter"
    }
    ARMOUR_SLOTS = {
        45: "Head",
        46: "Arms",
        47: "Chest",
        48: "Legs",
        49: "Class"
    }

def _create_blank_dataset():
    return {
        "Weapons": {
            "Kinetic": 0,
            "Energy": 0,
            "Power": 0
        },
        "Armor": {
            "Titan": {
                "Head": 0,
                "Arms": 0,
                "Chest": 0,
                "Legs": 0,
                "Class": 0
            },
            "Warlock": {
                "Head": 0,
                "Arms": 0,
                "Chest": 0,
                "Legs": 0,
                "Class": 0
            },
            "Hunter": {
                "Head": 0,
                "Arms": 0,
                "Chest": 0,
                "Legs": 0,
                "Class": 0
            }
        },
        "Power Bonus": 0
    }

class PowerLevel(BungieData):
    _COMPONENTS = [102,201,205,300]
    _THUMBNAIL_URL = None

    @staticmethod
    def _process_data(data):
        # Get All Item Buckets
        item_buckets: list[list[dict]] = [data["profileInventory"]["data"]["items"]]
        for bucket_location in ["characterInventories", "characterEquipment"]:
            for data in data[bucket_location]["data"].values():
                item_buckets.append(data["items"])

        raw_data = _create_blank_dataset()
        item_instances: dict[str, dict] = data["itemComponents"]["instances"]["data"]
        for bucket in item_buckets:
            for item in bucket:
                if (item_instance_id:=item.get("itemInstanceId")) is None:
                    continue
                item_instance = item_instances[str(item_instance_id)]
                if (primary_stat:=item_instance.get("primaryStat")) is None:
                    continue
                if (item_type:=HashTranslations.STAT_HASHES.get(primary_stat["statHash"])) is None:
                    continue
                stat_value: int = primary_stat["value"]
                if item_type == "Power Bonus":
                    raw_data["Power Bonus"] = max(stat_value, raw_data["Power Bonus"])
                    continue
                item_category_hashes: list[str] = SharkBot.Destiny.Definitions.DestinyInventoryItemDefinition.get(item["itemHash"])["itemCategoryHashes"]
                if item_type == "Weapons":
                    weapon_type = None
                    for category_hash, category_name in HashTranslations.WEAPON_TYPES.items():
                        if category_hash in item_category_hashes:
                            weapon_type = category_name
                            break
                    if stat_value > raw_data["Weapons"][weapon_type]:
                        raw_data["Weapons"][weapon_type] = stat_value
                else: # Armour
                    armor_class, armor_slot = None, None
                    for category_hash, category_name in HashTranslations.ARMOUR_SLOTS.items():
                        if category_hash in item_category_hashes:
                            armor_slot = category_name
                            break
                    for category_hash, category_name in HashTranslations.ARMOUR_CLASSES.items():
                        if category_hash in item_category_hashes:
                            armor_class = category_name
                            break
                    if stat_value > raw_data["Armour"][armor_class][armor_slot]:
                        raw_data["Armour"][armor_class][armor_slot] = stat_value
        return raw_data

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
