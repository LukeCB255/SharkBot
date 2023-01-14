from datetime import datetime
from typing import TypedDict, Optional


_EXPIRY_FORMAT = "%d/%m/%Y-%H:%M:%S"


class _MemberEffectData(TypedDict):
    id: str
    expiry: Optional[str]
    charges: Optional[int]


class _MemberEffect:

    def __init__(self, effect_id: str, expiry: Optional[str] = None, charges: Optional[int] = None):
        if expiry is not None:
            expiry = datetime.strptime(expiry, _EXPIRY_FORMAT)
        self.id = effect_id
        self.expiry = expiry
        self.charges = charges

    @property
    def _expiry_data(self) -> Optional[str]:
        if self.expiry is None:
            return None
        else:
            return datetime.strftime(self.expiry, _EXPIRY_FORMAT)


class MemberEffects:
    pass
