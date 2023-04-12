from typing import Iterator


class ProfileResponseData:

    def __init__(self, data: dict):
        self.data = data

    def __getattr__(self, item):
        return self.data[item]

    @property
    def items(self) -> Iterator[dict]:
        for item_data in self.data["profileInventory"]["data"]["items"]:
            yield item_data
        for bucket in ["characterInventories", "characterEquipment"]:
            for character in self.data[bucket]["data"].values():
                for item_data in character["items"]:
                    yield item_data
