class SharkError(Exception):
    pass


class MemberFileNotFoundError(SharkError):
    pass


class AccountAlreadyLinkedError(SharkError):
    pass


class AccountNotLinkedError(SharkError):
    pass


class AccountAlreadyInUseError(SharkError):
    pass


class ItemNotInInventoryError(SharkError):
    pass


class ItemNotInCollectionError(SharkError):
    pass


class CollectionNotFoundError(SharkError):
    pass


class RarityNotFoundError(SharkError):
    pass


class ItemNotFoundError(SharkError):
    pass


class TestError(SharkError):
    pass


class MissionNotFoundError(SharkError):
    pass


class MissionTypeNotFoundError(SharkError):
    pass
