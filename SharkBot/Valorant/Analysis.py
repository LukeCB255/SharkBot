import os

from SharkBot.Valorant import Errors, Map, Agent

analysisPath = "data/live/valorant/analysis.json"


class Analysis:

    def __init__(self, data: dict[str, dict[str, list[int]]]):
        self.data = {
            Map.get(mapName): {
                Agent.get(agentName): agentData for agentName, agentData in mapData.items()
            } for mapName, mapData in data.items()
        }


if not os.path.exists("/".join(analysisPath.split("/")[:-1])):
    os.makedirs("/".join(analysisPath.split("/")[:-1]))
