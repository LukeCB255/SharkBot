from SharkBot.Errors import SharkError


class ChampionNotFoundError(SharkError):
    pass


class ShieldNotFoundError(SharkError):
    pass


class LostSectorNotFoundError(SharkError):
    pass


class LostSectorRewardNotFoundError(SharkError):
    pass
