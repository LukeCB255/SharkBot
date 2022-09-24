from SharkBot import Valorant, Errors


class PlayerData:

    def __init__(self, data: dict[str, dict[str, int]]):
        self.data: dict[Valorant.Map, dict[Valorant.Agent, int]] = {
            Valorant.Map.get(mapName): {
                Valorant.Agent.get(agentName): value for agentName, value in mapData.items()
            } for mapName, mapData in data.items()
        }

    @property
    def raw_data(self) -> dict[str, dict[str, int]]:
        return {
            map.name: {
                agent.name: value for agent, value in mapData.items()
            } for map, mapData in self.data.items()
        }

    def get_agent_value(self, agent: Valorant.Agent, map: Valorant.Map) -> int:
        if map not in self.data.keys():
            map = Valorant.maps[0]
            if map not in self.data.keys():
                return Valorant.defaultAgentValue

        if agent in self.data[map].keys():
            return self.data[map][agent]
        else:
            return Valorant.defaultAgentValue

    def set_agent_value(self, agent: Valorant.Agent, map: Valorant.Map, value: int):
        if value < Valorant.defaultAgentValue or value > Valorant.maxAgentValue:
            raise Valorant.Errors.InvalidAgentValueError(value)

        if map not in self.data.keys():
            self.data[map] = {}

        self.data[map][agent] = value
