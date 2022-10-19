import discord
from SharkBot import Member, Valorant
from .MapsSelect import MapsSelect
from .AgentsSelect import AgentsSelect
from .ValueSelect import ValueSelect

length = 29


class AgentsView(discord.ui.View):
    def __init__(self, member_id: int, target_id: int, embed: discord.Embed, timeout=120):
        super().__init__(timeout=timeout)
        self.member = Member.get(member_id)
        self.target = Member.get(target_id)
        self.embed = embed
        self.map = None
        self.agent = None
        self.add_item(MapsSelect())

    async def map_selected(self, interaction: discord.Interaction, map_name: str) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return

        self.clear_items()

        self.map = Valorant.Map.get(map_name)
        agents = [[agent.name, self.target.valorant.get_agent_value(agent, self.map)] for agent in Valorant.agents]
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

        self.clear_items()

        self.agent = Valorant.Agent.get(agent)
        value = self.target.valorant.get_agent_value(self.agent, self.map)
        self.embed.title = f"{agent} preference for {self.map.name}"
        self.embed.description = f"Select a value to modify your preference.\n```{agent}: {value}```"

        self.add_item(ValueSelect())

        await interaction.response.edit_message(embed=self.embed, view=self)

    async def value_selected(self, interaction, value: int):
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return

        self.clear_items()

        self.target.valorant.set_agent_value(self.agent, self.map, value)
        self.embed.description = f"Value set.\n```{self.agent.name}: {value}```"

        await interaction.response.edit_message(embed=self.embed, view=None)

        self.target.write_data()
