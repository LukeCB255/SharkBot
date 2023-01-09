from typing import Optional

from SharkBot import Errors, Icon


class Rarity:

    def __init__(self, name: str, value: int, icon_name: str) -> None:
        self.name = name
        self.value = value
        self._icon_name: str = icon_name

    @property
    def icon(self) -> str:
        return Icon.get(self._icon_name)


common = Rarity("Common", 5, "common_item")
uncommon = Rarity("Uncommon", 10, "uncommon_item")
rare = Rarity("Rare", 20, "rare_item")
legendary = Rarity("Legendary", 50, "legendary_item")
exotic = Rarity("Exotic", 150, "exotic_item")
mythic = Rarity("Mythic", 500, "mythic_item")

lootboxes = Rarity("Lootboxes", 100, "lootboxes_item")

valentines = Rarity("Valentines", 10, "valentines_item")
witch_queen = Rarity("Witch Queen", 10, "witch_queen_item")
easter = Rarity("Easter", 10, "easter_item")
summer = Rarity("Summer", 10, "summer_item")
slime_rancher = Rarity("Slime Rancher", 10, "slime_rancher_item")
halloween = Rarity("Halloween", 10, "halloween_item")
christmas = Rarity("Christmas", 10, "christmas_item")
new_year = Rarity("New Year", 10, "new_year_item")
fragment = Rarity("Fragment", 500, "fragment_item")

rarities = [
    common,
    uncommon,
    rare,
    legendary,
    exotic,
    lootboxes,
    mythic,
    valentines,
    witch_queen,
    easter,
    summer,
    slime_rancher,
    halloween,
    christmas,
    new_year,
    fragment
]


def get(search: str) -> Rarity:
    search = search.upper()
    for rarity in rarities:
        if search == rarity.name.upper():
            return rarity
    raise Errors.RarityNotFoundError(search)
