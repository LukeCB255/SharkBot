import discord
from SharkBot import Member, Valorant, Utils
from .MapsSelect import MapsSelect


class AgentsView(discord.ui.View):
    def __init__(self, memberid: int, embed: discord.Embed, timeout=120):
        super().__init__(timeout=timeout)
        self.member = Member.get(memberid)
        self.embed = embed
        self.add_item(MapsSelect())

    async def map_selected(self, interaction: discord.Interaction, mapName: str) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return
        selectedMap = Valorant.Map.get(mapName)
        self.embed.title = f"Agent preferences for {mapName}"
        agents = []
        agentStr = "```"
        length = 17 + len(mapName)
        for agent in Valorant.agents:
            agents.append([agent.name, self.member.valorant.get_agent_value(agent, selectedMap)])
        agents.sort(key=lambda x: x[1], reverse=True)
        for i in agents:
            name = f"{i[0]}:"
            agentStr += f"{name.ljust(length)}{i[1]}\n"
        agentStr += "```"
        self.embed.description = agentStr
        await interaction.response.edit_message(embed=self.embed, view=None)
