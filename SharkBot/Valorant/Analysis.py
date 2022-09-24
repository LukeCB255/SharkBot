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
        if map not in self.data.keys():
            raise Errors.MapNotFoundError(map.name)
        return self.data[map]


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
