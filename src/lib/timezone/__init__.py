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

    def time_tuple_to_local_time(self, time_tuple: tuple) -> tuple:
        """
        Convert time tuple to local time tuple
        """

        # Pad time_tuple with 0s up to 8 elements
        padded_time_tuple = time_tuple + (0,) * (8 - len(time_tuple))

        epoch = time.mktime(padded_time_tuple)
        local_time = localPZtime.tztime(epoch, self.posix_str)
        return local_time[:6]

    def epoch_to_local_time_iso8601(self, time_tuple: tuple) -> str:
        """
        Convert time tuple to ISO8601 formatted local time string
        """
        # Pad time_tuple with 0s up to 8 elements
        padded_time_tuple = time_tuple + (0,) * (8 - len(time_tuple))

        epoch = time.mktime(padded_time_tuple)
        local_time = localPZtime.tziso(epoch, self.posix_str)
        return local_time






