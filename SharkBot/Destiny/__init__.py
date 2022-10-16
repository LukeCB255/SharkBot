from datetime import timedelta, time, datetime, date

from . import Errors
from . import Champion
from . import Shield
from . import LostSectorReward
from . import LostSector
from . import Season
from . import Raid
from . import Dungeon
from . import Nightfall

from SharkBot.Cooldown import Cooldown as _Cooldown

lightfallCountdown = _Cooldown(
    name="Lightfall Cooldown",
    expiry="28/02/2023-18:00:00",
    duration=timedelta(days=356)
)

resetTime = time(hour=17)  # UTC time


def get_current_day() -> date:
    dtnow = datetime.utcnow()
    if dtnow.time() < resetTime:
        dtnow -= timedelta(days=1)
    return dtnow.date()
