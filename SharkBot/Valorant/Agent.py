import json
from typing import Union
from SharkBot import Valorant

dataFilepath = "data/static/valorant/agents.json"


class Agent:

    def __init__(self, data: dict[str, Union[str, list[str]]]) -> None:
        self.name: str = data["name"]
        self.aliases: list[str] = [self.name.lower()] + [name.lower() for name in data["aliases"]]


def get(search: str) -> Agent:
    search = search.lower()
    for agent in agents:
        if search in agent.aliases:
            return agent
    else:
        raise Valorant.Errors.AgentNotFoundError(search)


agents = []


def load_agents() -> None:
    global agents
    agents = []

    with open(dataFilepath, "r") as infile:
        data: list[dict[str, Union[str, list[str]]]] = json.load(infile)

    agents = [Agent(agentData) for agentData in data]


load_agents()
