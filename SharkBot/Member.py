import json
import os
from datetime import datetime, timedelta
from typing import Union, Optional
import discord
from discord.ext import commands

from SharkBot import Cooldown, MemberInventory, MemberCollection, MemberVault, Mission, MemberStats, Utils, XP, Errors, IDs, Handlers, MemberDataConverter, Valorant
from SharkBot.Handlers import firestoreHandler

BIRTHDAY_FORMAT = "%d/%m/%Y"
_MEMBERS_DIRECTORY = "data/live/members"
_SNAPSHOTS_DIRECTORY = "data/live/snapshots/members"
REQUIRED_PATHS = [
    _MEMBERS_DIRECTORY, _SNAPSHOTS_DIRECTORY
]


class Member:

    def __init__(self, member_data: dict) -> None:

        member_data = MemberDataConverter.convert(member_data)

        self.id: int = member_data["id"]
        self.balance: int = member_data["balance"]
        self._bank_balance: int = member_data["bank_balance"]
        self.inventory = MemberInventory(self, member_data["inventory"])
        self.collection = MemberCollection(self, member_data["collection"])
        self.vault = MemberVault(**member_data["vault"])
        self.counts: int = member_data["counts"]
        self.cooldowns = {
            "hourly": Cooldown.Cooldown("hourly", member_data["cooldowns"]["hourly"], timedelta(hours=1)),
            "daily": Cooldown.Cooldown("daily", member_data["cooldowns"]["daily"], timedelta(days=1)),
            "weekly": Cooldown.Cooldown("weekly", member_data["cooldowns"]["weekly"], timedelta(weeks=1))
        }
        self.missions = Mission.MemberMissions(self, member_data["missions"])
        if member_data["birthday"] is None:
            self.birthday = None
        else:
            self.birthday = datetime.strptime(member_data["birthday"], BIRTHDAY_FORMAT)
        self.lastClaimedBirthday: int = member_data["lastClaimedBirthday"]
        self.stats = MemberStats(member_data["stats"])
        self.valorant = Valorant.PlayerData(member_data["valorant"])
        self.last_claimed_advent: int = member_data["last_claimed_advent"]
        self.xp = XP(member_data["xp"], self)
        self.legacy: dict = member_data["legacy"]
        self.used_codes: list[str] = member_data["used_codes"]
        self._discord_user: Optional[discord.User] = None
        self._data_version: int = member_data["data_version"]

    async def fetch_discord_user(self, bot: commands.Bot):
        if self._discord_user is None:
            self._discord_user = bot.get_user(self.id)
            if self._discord_user is None:
                self._discord_user = await bot.fetch_user(self.id)

    @property
    def snapshot_data(self) -> Optional[dict[str, Union[str, int]]]:
        if self._discord_user is None:
            return None
        return {
            "id": str(self.id),
            "display_name": self._discord_user.display_name,
            "avatar_url": self._discord_user.display_avatar.replace(size=256).url,
            "balance": self.balance,
            "bank_balance": self._bank_balance,
            "counts": self.counts,
            "xp": self.xp.xp,
            "level": self.xp.level
        }

    @property
    def wiki_profile_url(self) -> str:
        return f"https://sharkbot.online/profile/{self.id}"

    def write_data(self) -> None:
        """
        Saves the Member data to the .json
        """

        member_data = {
            "id": self.id,
            "data_version": self._data_version,
            "balance": self.balance,
            "bank_balance": self._bank_balance,
            "inventory": self.inventory.item_ids,
            "collection": self.collection.item_ids,
            "vault": self.vault.data,
            "counts": self.counts,
            "cooldowns": {
                "hourly": self.cooldowns["hourly"].timestring,
                "daily": self.cooldowns["daily"].timestring,
                "weekly": self.cooldowns["weekly"].timestring
            },
            "missions": self.missions.data,
            "birthday": None if self.birthday is None else datetime.strftime(self.birthday, BIRTHDAY_FORMAT),
            "lastClaimedBirthday": self.lastClaimedBirthday,
            "stats": self.stats.data,
            "valorant": self.valorant.raw_data,
            "last_claimed_advent": self.last_claimed_advent,
            "xp": self.xp.xp,
            "legacy": self.legacy,
            "used_codes": self.used_codes
        }

        with open(f"{_MEMBERS_DIRECTORY}/{self.id}.json", "w") as outfile:
            json.dump(member_data, outfile, indent=4)


    @property
    def snapshot_has_changed(self) -> bool:
        if not os.path.exists(f"{_SNAPSHOTS_DIRECTORY}/{self.id}.json"):
            return True
        with open(f"{_SNAPSHOTS_DIRECTORY}/{self.id}.json", "r") as infile:
            old_snapshot = json.load(infile)

        return old_snapshot != self.snapshot_data

    def write_snapshot(self, snapshot: Optional[dict]):
        if snapshot is None:
            snapshot = self.snapshot_data
        with open(f"{_SNAPSHOTS_DIRECTORY}/{self.id}.json", "w+") as outfile:
            json.dump(snapshot, outfile, indent=2)

    def upload_data(self, force_upload: bool = False, snapshot: Optional[dict] = None, write: bool = True) -> str:
        if force_upload or self.snapshot_has_changed:
            if snapshot is None:
                snapshot = self.snapshot_data
            if snapshot is None:
                return "Snapshot is None"
            Handlers.firestoreHandler.upload_data(snapshot)
            if write:
                self.write_snapshot(snapshot)
            return f"Success - {self._discord_user.display_name}#{self._discord_user.discriminator}"

    # Banking

    @property
    def bank_balance(self) -> int:
        return self._bank_balance

    @bank_balance.setter
    def bank_balance(self, value: int):
        if value < 0:
            raise Errors.BankBalanceBelowZeroError(self.id, value)
        else:
            self._bank_balance = value

    # Cleanup

    def delete_file(self) -> None:
        """
        Deletes the Member's .json data file
        """

        os.remove(f"{_MEMBERS_DIRECTORY}/{self.id}.json")
        global members
        del members[self.id]


def get(member_id: int) -> Member:
    member = members.get(member_id)
    if member is None:
        member = Member(get_default_values())
        member.id = member_id
        member.write_data()
        members[member_id] = member

    return member


def get_default_values() -> dict:
    with open (f"data/static/members/default_values.json", "r") as infile:
        return json.load(infile)


def load_member_files() -> None:
    global members
    members = {}
    for filename in Utils.get_dir_filepaths(_MEMBERS_DIRECTORY, ".json"):
        with open(filename, "r") as infile:
            data = json.load(infile)
            member = Member(data)
            members[int(data["id"])] = member


for path in REQUIRED_PATHS:
    Utils.FileChecker.directory(path)

members: dict[int, Member] = {}
load_member_files()
