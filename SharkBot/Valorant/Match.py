from SharkBot import Valorant


class Match:
    def __init__(self, map: Valorant.Map, players: list[int]) -> None:
        self.map = map
        self.players = players
        self.calculate()

    def calculate(self):
        analysis = Valorant.Analysis.get()
        analysis = analysis.get_map_data(self.map)
