from lib.ulogging import uLogger
from lib.networking import WirelessNetwork
from machine import I2C
from config import I2C_ID, SDA_PIN, SCL_PIN, I2C_FREQ
from lib.external_rtc import ExternalRTC
from lib.internal_rtc import InternalRTC
from asyncio import sleep_ms, create_task
from lib.specific_time_source import SpecificTimeSource

class TimeSource():
    """
    Timesource returns time data from the best available time source based on sync status:
    GPS > NTP > PRTC > Internal RTC.
    """
    def __init__(self, wifi: WirelessNetwork) -> None:
        """
        Initialize TimeSource by initialising available time sources and
        returning data from the best available source.
        Requires the WirelessNetwork instance to perform NTP and RTC operations

        Args:
            wifi (WirelessNetwork): An instance of the WirelessNetwork class.
        """
        super().__init__()
        self.log = uLogger("TimeSource")
        self.log.info("Initialising TimeSource")
        self.wifi = wifi
        self.time_sync_status = [{"name": "GPS", "status": False}, {"name": "RTC", "status": False}, {"name": "NTP", "status": False}, {"name": "PRTC", "status": False}]
        self.i2c = I2C(I2C_ID, sda = SDA_PIN, scl = SCL_PIN, freq = I2C_FREQ)
        self.rtc = InternalRTC()
        self.external_rtc = ExternalRTC(self.i2c)
        self.init_external_rtc()
        self.time_source: SpecificTimeSource = self.rtc
        self.update_time_source()

    def init_external_rtc(self) -> None:
        """
        Initialize the external RTC module if available.
        """
        if self.external_rtc.init_DS3231():
            self.log.info("Using external DS3231 RTC module for timekeeping")
            self.wifi.enable_external_rtc(self.external_rtc)
        else:
            self.log.info("No external RTC module found, using internal RTC for timekeeping")
    
    def startup(self) -> None:
        """
        Start TimeSource asynchronous tasks.
        """
        self.log.info("Starting TimeSource")
        create_task(self.async_check_time_sync_status())

    async def async_check_time_sync_status(self) -> None:
        """
        Asynchronously loop to check the time synchronization status of all
        time sources and update the selected time source accordingly.
        """
        while True:
            ntp_status = self.wifi.get_ntp_sync_status()
            self.set_time_sync_status("NTP", ntp_status)
            prtc_status = self.wifi.get_prtc_sync_status()
            self.set_time_sync_status("PRTC", prtc_status)
            external_rtc_status = self.wifi.get_external_rtc_status()
            self.set_time_sync_status("RTC", external_rtc_status)

            self.update_time_source()

            await sleep_ms(1000)

    def get_time(self) -> tuple:
        """
        Get the current time from the best available time source.
        Returns:
            A tuple with values: year, month, day, hours, minutes, seconds.
        """
        try:
            return self.time_source.get_time()
        except Exception as e:
            self.log.error(f"Error getting time from source: {e}. Updating available time sources to retry.")
            self.update_time_source()
            return self.time_source.get_time()
    
    def set_time(self, year: int, month: int, day: int, hours: int, minutes: int, seconds: int) -> None:
        """
        Set the current time on the best available time source.
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            day: Day (1-31)
            hours: Hours (0-23)
            minutes: Minutes (0-59)
            seconds: Seconds (0-59)
        """
        try:
            self.time_source.set_time(year, month, day, hours, minutes, seconds)
        except Exception as e:
            self.log.error(f"Error setting time on source: {e}. Updating available time sources to retry.")
            self.update_time_source()
            self.time_source.set_time(year, month, day, hours, minutes, seconds)
    
    def update_time_source(self) -> None:
        """
        Select the best available time source object based on current sync statuses.
        Populates self.time_source with the actual time source object.
        """
        for status_entry in self.time_sync_status:
            source_name = status_entry["name"]
            
            # Skip NTP as it's not a direct time source object
            if source_name == "NTP" or not status_entry["status"]:
                continue
            
            if source_name == "RTC":
                self.log.info(f"Selected time source: {source_name}")
                self.time_source = self.external_rtc
                return
            elif source_name == "PRTC":
                self.log.info(f"Selected time source: {source_name}")
                self.time_source = self.rtc
                return
        
        # Default fallback to internal RTC
        self.log.error("No time source available, using potentially incorrect internal RTC value")
        self.time_source = self.rtc

    def get_time_sync_status(self) -> list:
        """
        Get the current time synchronization status for all time sources.
        Returns:
            A list of dictionaries with time source names and their sync statuses.
        """
        return self.time_sync_status
    
    def set_time_sync_status(self, method_name: str, status: bool) -> None:
        """
        Update the status of a time synchronization method.

        This method updates the `status` field of the entry in `self.time_sync_status`
        whose `name` matches the given `method_name`. It is used to record whether a
        specific time sync mechanism (for example, "NTP" or "PRTC") is currently
        considered active or has successfully synchronized the system time.

        :param method_name: Name of the time sync method to update (must match an
                            existing entry in `self.time_sync_status`).
        :param status: Boolean flag indicating the new status for the method (True if
                       the method is available/has succeeded, False otherwise).
        """
        for method in self.get_time_sync_status():
            if method["name"] == method_name:
                method["status"] = status
                self.log.info(f"Time sync status updated: {method_name} set to {status}")
                return
        self.log.warn(f"Time sync method '{method_name}' not found in status list")
