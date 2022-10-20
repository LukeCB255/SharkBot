import discord
from SharkBot import Member, Valorant
from .MapsSelect import MapsSelect


class MatchView(discord.ui.View):
    def __init__(self, member_id: int, embed: discord.Embed, timeout=120):
        super().__init__(timeout=timeout)
        self.member = Member.get(member_id)
        self.embed = embed
        self.map = None
        self.add_item(MapsSelect(True))

    async def map_selected(self, interaction: discord.Interaction, map_name: str) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return
        await interaction.response.defer()
