import time

from lib.timezone import localPZtime
from lib.timezone.db import TIMEZONE_TO_POSIX, timezone_to_posix
from lib.ulogging import uLogger

DEFAULT_TIMEZONE = "Etc/UTC"

class Timezone:
    def __init__(self, timezone: str | None = None) -> None:
        self.timezone = timezone
        self.posix_str = None

        self.log = uLogger("Timezone")

        self._setup()

    def _setup(self):
        if self.timezone is None:
            self.log.warn("No timezone specified, using default")
            self.timezone = DEFAULT_TIMEZONE

        self.log.info(f"Configuring timezone to {self.timezone}")
        self.posix_str = timezone_to_posix(self.timezone)

        if self.posix_str is None:
            self.log.warn(f"Timezone {self.timezone} not found in database, using default {DEFAULT_TIMEZONE}")
            self.timezone = DEFAULT_TIMEZONE
            self.posix_str = timezone_to_posix(DEFAULT_TIMEZONE)

        self.log.info(f"Timezone set to {self.timezone}")
        self.log.info(f"POSIX timezone string: {self.posix_str}")

    def utc_time_tuple_to_local_time(self, utc_time_tuple: tuple) -> tuple:
        """
        Convert a UTC time tuple to a local time tuple based on the configured timezone.
        utc_time_tuple: A tuple with values: year, month, day, hours, minutes, seconds.
        """
        mktime_tuple = utc_time_tuple + (0, 0)
        epoch_time = int(time.mktime(mktime_tuple))
        local_time = localPZtime.tztime(epoch_time, self.posix_str)
        return local_time[:6]






