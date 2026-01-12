from lib.ulogging import uLogger
from lib.ds3231.ds3231 import DS3231

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from machine import I2C

class ExternalRTC:
    
    MODULE_OPERATIONS = {
        "DS3231": {
            "read_time": "read_time",
            "set_time": "set_time",
        }
    }

    def __init__(self, i2c: I2C) -> None:
        """
        ExternalRTC manages external RTC modules connected via I2C.
        Calls to the specific installed RTC module methods are abstracted
        through this class.

        Call get_supported_modules() to see supported RTC types.
        Call get_supported_operations() to see supported operations.
        Call init_{modulename}() to attempt initialisation.
        
        Args:
            i2c: An initialised I2C interface.
        """
        self.log = uLogger("ExternalRTC")
        self.log.info("Initializing external RTC module")
        self.i2c = i2c
        self.RTC = None
        self.rtc_type = None
        

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
            self.rtc_type = "DS3231"

            self.log.info("Running DS3231 RTC module read/write test")
            test_date = (2024, 1, 12, 21, 22, 23)
            self.RTC.set_time(*test_date)
            
            year, month, day, hours, minutes, seconds = self.RTC.read_time()
            if (year, month, day, hours, minutes, seconds) != test_date:
                raise Exception("DS3231 RTC module read/write test failed")
            else:                
                self.log.info(f"DS3231 time read as {year}-{month:02d}-{day:02d} {hours:02d}:{minutes:02d}:{seconds:02d}")
                self.log.info("DS3231 RTC module read/write test passed")
            
        except Exception as e:
            self.log.error(f"Failed to initialize DS3231 RTC module: {e}")
            self.RTC = None
            self.rtc_type = None
        
        return True if self.RTC else False
    
    def _call_rtc_method(self, operation: str, *args, **kwargs):
        """
        Call a method on the underlying RTC module using the abstraction mapping.
        
        Args:
            operation: The operation name (e.g., "read_time", "set_time")
            *args: Positional arguments to pass to the RTC method
            **kwargs: Keyword arguments to pass to the RTC method
            
        Returns:
            The return value from the RTC module method
            
        Raises:
            Exception if RTC not initialised or operation not supported
        """
        if not self.RTC:
            raise Exception(f"{self.rtc_type or 'RTC'} module not initialised")
        
        # Check if operation is supported by any module
        supported_ops = set()
        for module_ops in self.MODULE_OPERATIONS.values():
            supported_ops.update(module_ops.keys())
        
        if operation not in supported_ops:
            raise Exception(f"Operation '{operation}' not supported")
        
        # Get the actual method name for this RTC module type
        if self.rtc_type in self.MODULE_OPERATIONS:
            rtc_method_name = self.MODULE_OPERATIONS[self.rtc_type].get(operation, operation)
        else:
            rtc_method_name = operation
        
        if not hasattr(self.RTC, rtc_method_name):
            raise Exception(f"RTC module {self.rtc_type} does not support '{operation}'")
        
        method = getattr(self.RTC, rtc_method_name)
        return method(*args, **kwargs)
    
    def read_time(self) -> tuple:
        """
        Read current time from the RTC module.
        Returns:
            A tuple with values: year, month, day, hours, minutes, seconds.
        """
        return self._call_rtc_method("read_time")
    
    def set_time(self, year: int, month: int, day: int, hours: int, minutes: int, seconds: int) -> None:
        """
        Set current time on the RTC module.
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            day: Day (1-31)
            hours: Hours (0-23)
            minutes: Minutes (0-59)
            seconds: Seconds (0-59)
        """
        return self._call_rtc_method("set_time", year, month, day, hours, minutes, seconds)
    
    def get_supported_modules(self) -> list:
        """
        Get a list of supported RTC module types.
        Returns:
            A list of supported RTC module type names.
        """
        return list(self.MODULE_OPERATIONS.keys())
    
    def get_supported_operations(self, module_type: str = "") -> list:
        """
        Get a list of supported operations across all RTC modules.
        Or get operations for a specific module type if provided.
        Args:
            module_type[str]: Optional RTC module type name.
        Returns:
            A list of supported operation names.
        """
        if module_type:
            if module_type in self.MODULE_OPERATIONS:
                return list(self.MODULE_OPERATIONS[module_type].keys())
            else:
                return []
        else:
            supported_ops = set()
            for module_ops in self.MODULE_OPERATIONS.values():
                supported_ops.update(module_ops.keys())
            return list(supported_ops)
