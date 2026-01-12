class DS3231:
    I2C_ADDRESS = 0x68

    REGISTERS = {
        "seconds": 0x00,
        "minutes": 0x01,
        "hours": 0x02,
        "day": 0x03,
        "date": 0x04,
        "month": 0x05,
        "year": 0x06,
        "control": 0x0E,
        "status": 0x0F,
        "aging_offset": 0x10,
        "temp_msb": 0x11,
        "temp_lsb": 0x12,
    }

    def __init__(self, i2c):
        """
        Initialize DS3231 with given I2C interface.
        Args:
            i2c: An initialized I2C interface.
        """
        self.i2c = i2c
        self.address = DS3231.I2C_ADDRESS

    def bcd_to_decimal(self, bcd):
        """Convert BCD to decimal."""
        return (bcd >> 4) * 10 + (bcd & 0x0F)
    
    def decimal_to_bcd(self, decimal):
        """Convert decimal to BCD."""
        return ((decimal // 10) << 4) | (decimal % 10)
    
    def read_time(self) -> tuple:
        """
        Read current time from DS3231.
        Returns:
            A tuple with values: year, month, day, hours, minutes, seconds.
        """
        data = self.i2c.readfrom_mem(self.address, DS3231.REGISTERS["seconds"], 7)
        seconds = self.bcd_to_decimal(data[0] & 0x7F)
        minutes = self.bcd_to_decimal(data[1] & 0x7F)
        hours = self.bcd_to_decimal(data[2] & 0x3F)  # 24-hour format
        day = self.bcd_to_decimal(data[4] & 0x3F)
        month = self.bcd_to_decimal(data[5] & 0x1F)
        year = self.bcd_to_decimal(data[6]) + 2000
        return (
            year,
            month,
            day,
            hours,
            minutes,
            seconds
        )
    
    def set_time(self, year, month, day, hours, minutes, seconds):
        """
        Set current time on DS3231.
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            day: Day (1-31)
            hours: Hours (0-23)
            minutes: Minutes (0-59)
            seconds: Seconds (0-59)
        """
        data = bytearray(7)
        data[0] = self.decimal_to_bcd(seconds)
        data[1] = self.decimal_to_bcd(minutes)
        data[2] = self.decimal_to_bcd(hours)  # 24-hour format
        data[3] = self.decimal_to_bcd(0)  # Day of week not used
        data[4] = self.decimal_to_bcd(day)
        data[5] = self.decimal_to_bcd(month)
        data[6] = self.decimal_to_bcd(year - 2000)
        self.i2c.writeto_mem(self.address, DS3231.REGISTERS["seconds"], data)
