from lib.ulogging import uLogger
from lib.networking import WirelessNetwork
from machine import I2C
from lib.external_rtc import ExternalRTC
from lib.internal_rtc import InternalRTC
from asyncio import sleep_ms, create_task
from lib.specific_time_source import SpecificTimeSource

class TimeSyncStatus:
    def __init__(self, name: str, status: bool):
        self.name = name
        self.status = status
    
    def get_name(self) -> str:
        return self.name
    
    def get_status(self) -> bool:
        return self.status
    
    def set_status(self, status: bool) -> None:
        self.status = status

class TimeSource():
    """
    TimeSource returns time data from the best available time source based on sync status:
    GPS > NTP > External RTC (RTC) > Internal RTC (PRTC).
    """
    def __init__(self, wifi: WirelessNetwork, i2c: I2C) -> None:
        """
        Initialize TimeSource by initialising available time sources and
        setting the initial time source based on availability. TimeSource
        relies on the WirelessNetwork class to provide NTP sync status and to
        call the provided on_ntp_sync callback when an NTP sync occurs.
        TimeSource also manages the external RTC module if available, and will
        update it with the latest time when an NTP sync occurs.
        
        Args:
            wifi (WirelessNetwork): An instance of the WirelessNetwork class.
            i2c (I2C): An initialized I2C interface.
        """
        self.log = uLogger("TimeSource")
        self.log.info("Initialising TimeSource")
        self.wifi = wifi
        self.time_sync_status = [TimeSyncStatus("GPS", False), TimeSyncStatus("NTP", False), TimeSyncStatus("RTC", False), TimeSyncStatus("PRTC", False)]
        self.i2c = i2c
        self.rtc = InternalRTC()
        self.external_rtc = ExternalRTC(self.i2c)
        self.external_rtc_sync_status = False
        self.selected_time_source_name = None
        self.init_external_rtc()
        # At initialization all sync statuses are False because async_check_time_sync_status()
        # has not run yet. This initial update_time_source() intentionally relies on the
        # fallback logic (external/internal RTC) to choose a sane starting time source. Once
        # the async task starts updating time_sync_status, subsequent calls will promote NTP/PRTC.
        self.time_source: SpecificTimeSource = self.rtc
        self.update_time_source()

    def select_time_source(self, source_name: str, source: SpecificTimeSource, message: str = "") -> None:
        self.time_source = source
        if self.selected_time_source_name != source_name:
            if message:
                self.log.info(message)
            self.log.info(f"Selected time source: {source_name}")
            self.selected_time_source_name = source_name

    def init_external_rtc(self) -> None:
        """
        Initialize the external RTC module if available.
        """
        if self.external_rtc.init_DS3231():
            self.log.info("Using external DS3231 RTC module for timekeeping")
            self.wifi.set_ntp_sync_callback(self.on_ntp_sync)
        else:
            self.log.info("No external RTC module found, using internal RTC for timekeeping")
    
    def on_ntp_sync(self, timestamp: tuple) -> None:
        """
        Callback handler for when NTP synchronization succeeds.
        Updates the external RTC if available.
        
        Args:
            timestamp: A tuple with values (year, month, day, hour, minute, second, dayofweek, dayofyear)
        """
        try:
            if self.external_rtc.is_configured():
                self.external_rtc.set_time(timestamp[0:6])
                self.log.info("External RTC time updated from NTP")
                self.set_time_sync_status("RTC", True)
            return
        except Exception as e:
            self.log.error(f"Failed to update external RTC from NTP: {e}")
            self.set_time_sync_status("RTC", False)
            return
    
    def startup(self) -> None:
        """
        Start TimeSource asynchronous tasks.
        """
        self.log.info("Starting TimeSource")
        create_task(self.async_check_time_sync_status())

    async def async_check_time_sync_status(self) -> None:
        """
        Asynchronously loop to check the time synchronization status of network
        time sources and update the selected time source accordingly.
        """
        while True:
            ntp_status = self.wifi.get_ntp_sync_status()
            self.set_time_sync_status("NTP", ntp_status)
            prtc_status = self.wifi.get_prtc_sync_status()
            self.set_time_sync_status("PRTC", prtc_status)

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
        try:
            return self.time_source.get_time()
        except Exception as retry_error:
            self.log.error(f"Retrying to get time from updated source also failed: {retry_error}")
            raise

    def set_time(self, time_tuple: tuple) -> None:
        """
        Set the current time on the best available time source.
        Args:
            time_tuple: A tuple with values: year, month, day, hours, minutes, seconds.
        """
        try:
            self.time_source.set_time(time_tuple)
        except Exception as e:
            self.log.error(f"Error setting time on source: {e}. Updating available time sources to retry.")
            self.update_time_source()
            try:  
                self.time_source.set_time(*time_tuple)  
            except Exception as retry_error:  
                self.log.error(f"Retrying to set time on updated source also failed: {retry_error}")  
                raise  
    
    def update_time_source(self) -> None:
        """
        Select the best available time source object based on current sync statuses.
        Populates self.time_source with the actual time source object.
        """
        for status_entry in self.time_sync_status:
            source_name = status_entry.get_name()
            
            # Skip NTP as it's not a direct time source object
            if source_name == "NTP" or not status_entry.get_status():
                continue
            
            if source_name == "RTC":
                self.select_time_source("RTC", self.external_rtc)
                return
            elif source_name == "PRTC":
                self.select_time_source("PRTC", self.rtc)
                return
        
        # Default fallback to internal RTC
        if self.external_rtc.is_configured():
            self.select_time_source("RTC", self.external_rtc, "No confirmed sync source active, falling back to external RTC")
            return
        else:
            self.select_time_source("PRTC", self.rtc, "No confirmed sync source active and no external RTC, falling back to internal RTC")
            return

    def get_time_sync_status(self) -> list[TimeSyncStatus]:
        """
        Get the current time synchronization status for all time sources.
        Returns:
            A list of TimeSyncStatus objects with time source sync info.
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
            if method.get_name() == method_name:
                if method.get_status() != status:
                    method.set_status(status)
                    self.log.info(f"Time sync status updated: {method_name} set to {status}")
                return
        self.log.warn(f"Time sync method '{method_name}' not found in status list")
