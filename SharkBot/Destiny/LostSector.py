import json
import datetime
from typing import Union, TypedDict
from SharkBot.Destiny import Champion, Shield, Errors as DestinyErrors


class _DifficultyData(TypedDict):
    champions: dict[str, int]
    shields: dict[str, int]


class _LostSectorData(TypedDict):
    name: str
    destination: str
    burn: str
    embed_url: str
    legend: _DifficultyData
    master: _DifficultyData


class LostSector:

    def __init__(self, name: str, destination: str, burn: str, embed_url: str,
                 legend: _DifficultyData, master: _DifficultyData) -> None:
        self.name = name
        self.destination = destination
        self.burn = Shield.get(burn)
        self.embed_url = embed_url
        self.champions: list[Champion.Champion] = [Champion.get(champion) for champion in legend["champions"]]
        self.shields: list[Shield.Shield] = [Shield.get(shield) for shield in legend["shields"]]

    @property
    def champion_list(self) -> str:
        return ", ".join(champion.text for champion in self.champions)

    @property
    def shield_list(self) -> str:
        return ", ".join(shield.text for shield in self.shields)


class Difficulty:

    def __init__(self, champions: dict[str, int], shields: dict[str, int]) -> None:
        self.champions = {Champion.get(champion): number for champion, number in champions.items()}
        self.shields = {Shield.get(shield): number for shield, number in shields.items()}

    @property
    def champion_types(self) -> list[Champion.Champion]:
        return list(self.champions.keys())

    @property
    def shield_types(self) -> list[Shield.Shield]:
        return list(self.shields.keys())


with open("data/static/destiny/lost_sectors/lost_sectors.json", "r") as infile:
    lostSectorData: list[_LostSectorData] = json.load(infile)

lostSectors = [LostSector(**data) for data in lostSectorData]
rotationStart = datetime.datetime(2022, 9, 13)
resetTime = datetime.time(18)


def get(search: str) -> LostSector:
    for lostSector in lostSectors:
        if lostSector.name == search:
            return lostSector
    else:
        raise DestinyErrors.LostSectorNotFoundError(search)


with open("data/static/destiny/lost_sectors/rotation.json") as infile:
    rotationData = json.load(infile)

rotation = [get(sectorName) for sectorName in rotationData]


def get_current() -> LostSector:
    dtnow = datetime.datetime.now()
    if dtnow.time() < resetTime:
        dtnow = dtnow - datetime.timedelta(days=1)
    days = (dtnow - rotationStart).days
    position = days % len(rotation)
    return rotation[position]
