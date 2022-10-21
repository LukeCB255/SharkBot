import os
import json

from SharkBot.Valorant import Errors, Map, Agent

analysisPath = "data/live/valorant/analysis.json"


class Analysis:

    def __init__(self, data: dict[str, dict[str, list[int]]]):
        self.data: dict[Map, dict[Agent, list[int]]] = {
            Map.get(mapName): {
                Agent.get(agentName): agentData for agentName, agentData in mapData.items()
            } for mapName, mapData in data.items()
        }

    def get_map_data(self, map: Map) -> dict[Agent, list[int]]:
        """
        Fetches the values of every agent for a given map

        :param map: The map to return the data for
        :return: Returns a dictionary of Agent objects and their corresponding values for the given map
        """
        if map not in self.data.keys():
            raise Errors.MapNotFoundError(map.name)
        return self.data[map]

    def get_agent_data(self, agent: Agent) -> dict[Map, list[int]]:
        data = {}
        for map, mapData in self.data.items():
            if agent in mapData.keys():
                data[map] = mapData[agent]
        return data


_analysis = None


def get() -> Analysis:
    global _analysis
    if _analysis is not None:
        return _analysis
    if not os.path.exists(analysisPath):
        raise Errors.NoAnalysisFileError()
    with open(analysisPath, "r") as infile:
        analysisData: dict[str, dict[str, list[int]]] = json.load(infile)
    _analysis = Analysis(analysisData)
    return _analysis


if not os.path.exists("/".join(analysisPath.split("/")[:-1])):
    os.makedirs("/".join(analysisPath.split("/")[:-1]))
