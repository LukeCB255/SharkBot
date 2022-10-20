from . import Errors
from .Agent import Agent
from .Map import Map
from .PlayerData import PlayerData
from .Match import Match
from . import Analysis
from . import Views

agents = Agent.agents
maps = Map.maps

defaultAgentValue = 1
maxAgentValue = 5
possible_agent_values = list(range(defaultAgentValue, maxAgentValue+1))

valorantRed = 0xfa4454
