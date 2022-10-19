import discord
from SharkBot import Valorant

options = [discord.SelectOption(label=map.name) for map in Valorant.maps]


class MapsSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.map_selected(interaction, self.values[0])
