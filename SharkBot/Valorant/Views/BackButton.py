import discord
from SharkBot import Valorant


class BackButton(discord.ui.Button):
    def __init__(self, state: str, label="Back"):
        super().__init__(label=label)
        self.state = state

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.go_back(interaction, self.state)
