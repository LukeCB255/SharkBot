import discord
from SharkBot import Valorant

options_with_all = [discord.SelectOption(label=map.name) for map in Valorant.Map.maps]
options_without_all = options_with_all[1:]


class MapsSelect(discord.ui.Select):
    def __init__(self, remove_all: bool = False):
        if remove_all:
            options = options_without_all
        else:
            options = options_with_all
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.map_selected(interaction, self.values[0])
