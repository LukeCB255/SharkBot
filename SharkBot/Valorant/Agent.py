import json
from typing import Union
from SharkBot import Valorant

dataFilepath = "data/static/valorant/agents.json"


class Agent:
    agents = []

    def __init__(self, data: dict[str, Union[str, list[str]]]) -> None:
        self.name: str = data["name"]
        self.aliases: list[str] = [self.name.lower()] + [name.lower() for name in data["aliases"]]

    @classmethod
    def get(cls, search: str):
        search = search.lower()
        for agent in cls.agents:
            if search in agent.aliases:
                return agent
        else:
            raise Valorant.Errors.AgentNotFoundError(search)

    def __str__(self) -> str:
        return self.name


def load_agents() -> None:
    Agent.agents.clear()

    with open(dataFilepath, "r") as infile:
        data: list[dict[str, Union[str, list[str]]]] = json.load(infile)

    Agent.agents = [Agent(agentData) for agentData in data]


load_agents()
