import discord
from SharkBot import Valorant


class BackButton(discord.ui.Button):
    def __init__(self, state: str, label="Go Back"):
        super().__init__(label=label, emoji="⬅")
        self.state = state

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.go_back(interaction, self.state)
