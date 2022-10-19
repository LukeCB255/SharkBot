import discord
from SharkBot import Valorant

options = [discord.SelectOption(label=agent.name) for agent in Valorant.agents]


class AgentsSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.agent_selected(interaction, self.values[0])
