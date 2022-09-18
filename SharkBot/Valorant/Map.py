import json
from SharkBot import Valorant

dataFilepath = "data/static/valorant/maps.json"


class Map:
    maps = []

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def get(cls, search: str):
        search = search.capitalize()
        for map in cls.maps:
            if map.name == search:
                return map
        else:
            raise Valorant.Errors.MapNotFoundError(search)


def load_maps() -> None:
    Map.maps.clear()

    with open(dataFilepath, "r") as infile:
        data: list[str] = json.load(infile)

    Map.maps = [Map(mapName) for mapName in data]


load_maps()
