import discord

options = [discord.SelectOption(label=a) for a in range(1, 6)]


class ValueSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.value_selected(interaction, int(self.values[0]))
