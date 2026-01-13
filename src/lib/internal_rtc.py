from lib.ulogging import uLogger
from lib.specific_time_source import SpecificTimeSource
from machine import RTC

class InternalRTC(SpecificTimeSource):
    def __init__(self) -> None:
        """
        InternalRTC abstracts management of the internal RTC of the microcontroller.
        """
        self.log = uLogger("InternalRTC")
        self.log.info("Initialising internal RTC")
        self.rtc = RTC()
        
    def get_time(self) -> tuple:
        """
        Get the current time from the internal RTC.
        Returns:
            A tuple with values: year, month, day, hours, minutes, seconds.
        """
        return self.rtc.datetime()[:6]
    
    def set_time(self, year: int, month: int, day: int, hours: int, minutes: int, seconds: int) -> None:
        """
        Set the current time on the internal RTC.
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            day: Day (1-31)
            hours: Hours (0-23)
            minutes: Minutes (0-59)
            seconds: Seconds (0-59)
        """
        self.rtc.datetime((year, month, day, 0, hours, minutes, seconds, 0))
