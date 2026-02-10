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
        return self.rtc.datetime()[:3] + self.rtc.datetime()[4:7]
    
    def set_time(self, time_tuple: tuple) -> None:
        """
        Set the current time on the internal RTC.
        Args:
            time_tuple: A tuple with values: year, month, day, hours, minutes, seconds.
        """
        self.rtc.datetime((time_tuple[0], time_tuple[1], time_tuple[2], 0, time_tuple[3], time_tuple[4], time_tuple[5], 0))
