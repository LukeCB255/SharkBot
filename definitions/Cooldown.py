from datetime import datetime, timedelta

timeFormat = "%S:%M:%H/%d:%m:%Y"


class Cooldown:

    def __init__(self, name: str, expiry: str, duration: timedelta):
        self.name = name
        self.expiry = datetime.strptime(expiry, timeFormat)
        self.duration = timedelta

    @property
    def expired(self):
        return datetime.now() > self.expiry

    def extend(self):
        self.expiry += self.duration
