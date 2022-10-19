import discord
from SharkBot import Member, Valorant, Utils
from .MapsSelect import MapsSelect
from .AgentsSelect import AgentsSelect


class AgentsView(discord.ui.View):
    def __init__(self, member_id: int, embed: discord.Embed, timeout=120):
        super().__init__(timeout=timeout)
        self.member = Member.get(member_id)
        self.embed = embed
        self.add_item(MapsSelect())

    async def map_selected(self, interaction: discord.Interaction, map_name: str) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return

        self.clear_items()
        selected_map = Valorant.Map.get(map_name)
        length = 17 + len(map_name)
        agents = [[agent.name, self.member.valorant.get_agent_value(agent, selected_map)] for agent in Valorant.agents]
        agents.sort(key=lambda x: x[1], reverse=True)

        agent_str = "\n".join([f"{f'{a[0]}:'.ljust(length)}{a[1]}" for a in agents])
        agent_str = f"```{agent_str}```"

        self.embed.title = f"Agent preferences for {map_name}"
        self.embed.description = f"Select an agent to modify that preference.\n{agent_str}"

        self.add_item(AgentsSelect())

        await interaction.response.edit_message(embed=self.embed, view=self)

    async def agent_selected(self, interaction: discord.Interaction, agent: str) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return
        await interaction.response.defer()
