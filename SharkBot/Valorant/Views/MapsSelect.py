import discord
from SharkBot import Valorant

options = []
for map in Valorant.maps:
    option = discord.SelectOption(label=map.name)
    options.append(option)


class MapsSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.mapSelected(interaction, self.values[0])
