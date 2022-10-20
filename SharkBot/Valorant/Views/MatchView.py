import discord
from SharkBot import Member, Valorant
from .MapsSelect import MapsSelect


class MatchView(discord.ui.View):
    def __init__(self, member_id: int, players: list[int], embed: discord.Embed, timeout=120):
        super().__init__(timeout=timeout)
        self.member = Member.get(member_id)
        self.players = [Member.get(player_id) for player_id in players]
        self.embed = embed
        self.map = None
        self.add_item(MapsSelect(False))

    async def map_selected(self, interaction: discord.Interaction, map_name: str) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.defer()
            return

        self.clear_items()

        self.embed.title = f"{self.embed.title} on {map_name}"
        self.map = Valorant.Map.get(map_name)

        await interaction.response.edit_message(embed=self.embed, view=self)
