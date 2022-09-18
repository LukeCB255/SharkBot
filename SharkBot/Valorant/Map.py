import json
from SharkBot import Valorant

dataFilepath = "data/static/valorant/maps.json"


class Map:

    def __init__(self, name: str) -> None:
        self.name = name


def get(search: str) -> Map:
    search = search.capitalize()
    for map in maps:
        if map.name == search:
            return map
    else:
        raise Valorant.Errors.MapNotFoundError(search)


maps = []


def load_maps() -> None:
    global maps
    maps = []

    with open(dataFilepath, "r") as infile:
        data: list[str] = json.load(infile)

    maps = [Map(mapName) for mapName in data]


load_maps()
