from . import Errors

from .Agent import Agent
from .Map import Map
agents = Agent.agents
maps = Map.maps

from .PlayerData import PlayerData
from . import Analysis

defaultAgentValue = 1
maxAgentValue = 5
possible_agent_values = list(range(defaultAgentValue, maxAgentValue+1))


valorantRed = 0xfa4454

from . import Views
