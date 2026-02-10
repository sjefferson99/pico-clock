from config import RTC_FULL_TEST
from lib.specific_time_source import SpecificTimeSource
from lib.ulogging import uLogger
from lib.ds3231.ds3231 import DS3231

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from machine import I2C

class ExternalRTC(SpecificTimeSource):
    """
    ExternalRTC manages external RTC modules connected via I2C.
    Calls to the specific installed RTC module methods are abstracted
    through this class.
    Ensure new modules are added to supported_modules and
    initialisation methods are created (e.g., init_DS3231()).
    Module methods must extend SpecificTimeSource.
    """

    def __init__(self, i2c: I2C) -> None:
        """
        ExternalRTC manages external RTC modules connected via I2C.
        Calls to the specific installed RTC module methods are abstracted
        through this class.

        Call get_supported_modules() to see supported RTC types.
        Call init_{modulename}() to attempt initialisation.
        
        Args:
            i2c: An initialised I2C interface.
        """
        super().__init__()
        self.log = uLogger("ExternalRTC")
        self.log.info("initialising external RTC module")
        self.i2c = i2c
        self.RTC: SpecificTimeSource | None= None
        self.supported_modules = ["DS3231"]
        self.RTC_configured = False

    def init_DS3231(self) -> bool:
        """
        Attempt to initialise the DS3231 RTC module if an I2C bus scan returns
        a device at the expected address (0x68).
        Returns:
            True if DS3231 initialised successfully, False otherwise.
        """
        try:
            i2c_devices = self.i2c.scan()
            if DS3231.I2C_ADDRESS not in i2c_devices:
                self.log.warn("DS3231 RTC module not found on I2C bus")
                self.RTC = None
                return False
            
            self.RTC = DS3231(self.i2c)
            self.RTC_configured = True

            if RTC_FULL_TEST:
                self.log.info("Running DS3231 RTC module read/write test")
                test_date = (2024, 1, 12, 21, 22, 23)
                self.RTC.set_time(*test_date)
                
                year, month, day, hours, minutes, seconds = self.RTC.get_time()
                if (year, month, day, hours, minutes, seconds) != test_date:
                    raise Exception("DS3231 RTC module read/write test failed")
                else:                
                    self.log.info(f"DS3231 time read as {year}-{month:02d}-{day:02d} {hours:02d}:{minutes:02d}:{seconds:02d}")
                    self.log.info("DS3231 RTC module read/write test passed")
            
            else:
                timetuple = self.RTC.get_time()
                self.log.info("Full external RTC test skipped (RTC_FULL_TEST is False)")
                self.log.info(f"DS3231 time read as {timetuple}")
                
            
        except Exception as e:
            self.log.error(f"Failed to initialise DS3231 RTC module: {e}")
            self.RTC = SpecificTimeSource()
            return False
        
        return True
    
    def get_time(self) -> tuple:
        """
        Read current time from the RTC module.
        Returns:
            A tuple with values: year, month, day, hours, minutes, seconds.
        """
        if self.RTC is None:
            raise Exception("RTC module not initialised")
        return self.RTC.get_time()
    
    def set_time(self, time_tuple: tuple) -> None:
        """
        Set current time on the RTC module.
        Args:
            time_tuple: A tuple with values: year, month, day, hours, minutes, seconds.
        """
        if self.RTC is None:
            raise Exception("RTC module not initialised")
        self.RTC.set_time(*time_tuple)
    
    def get_supported_modules(self) -> list:
        """
        Get a list of supported RTC module types.
        Returns:
            A list of supported RTC module type names.
        """
        return self.supported_modules
    
    def is_configured(self) -> bool:
        """
        Check if an RTC module has been successfully initialised.
        Returns:
            True if an RTC module is configured, False otherwise.
        """
        return self.RTC_configured
