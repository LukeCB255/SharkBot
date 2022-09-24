from SharkBot.Valorant import Errors, Map, Agent


class Analysis:

    def __init__(self, data: dict[str, dict[str, list[int]]]):
        self.data = {
            Map.get(mapName): {
                Agent.get(agentName): agentData for agentName, agentData in mapData.items()
            } for mapName, mapData in data.items()
        }

