from lib.ulogging import uLogger
from lib.networking import WirelessNetwork
from lib.ht16k33.ht16k33segment import HT16K33Segment
from config import DISPLAY_ADDREESSES, CLOCK_FREQUENCY, SDA_PIN, SCL_PIN, I2C_ID, I2C_FREQ
from machine import freq, I2C, RTC
from asyncio import sleep_ms, create_task, get_event_loop
from time import sleep

class Clock:
    
    def __init__(self) -> None:
        """
        Clock device for displaying time and date on HT16K33 7-segment displays.
        """
        self.log = uLogger("Clock")
        self.log.warn("Pico-Clock has been restarted")
        self.version = "0.0.1"
        self.log.info("Setting CPU frequency to: " + str(CLOCK_FREQUENCY / 1000000) + "MHz")
        freq(CLOCK_FREQUENCY)
        self.i2c = I2C(I2C_ID, sda = SDA_PIN, scl = SCL_PIN, freq = I2C_FREQ)
        self.wifi = WirelessNetwork()
        self.rtc = RTC()

    def startup(self) -> None:
        self.log.info("Starting Clock")

        self.wifi.startup()

        self.displays = {}
        for name, address in DISPLAY_ADDREESSES.items():
            self.displays[name] = HT16K33Segment(self.i2c, i2c_address=address)
            self.displays[name].set_brightness(15)
            self.displays[name].set_blink_rate(0)
            self.displays[name].set_colon(False)
            self.displays[name].clear()
            self.displays[name].draw()
            self.log.info(f"Initialized display '{name}' at address 0x{address:02X}")
            self.display_test(name)
        
        self.log.info("Clock started with displays: " + ", ".join(self.displays.keys()))

        self.log.info("Starting clock loop")
        create_task(self.async_clock_loop())

        loop = get_event_loop()
        loop.run_forever()

    def display_test(self, display: str) -> None:
        """
        Run a display test on a given display.
        """
        try:
            if display in self.displays:
                self.log.info(f"Running display test on {display}")

                colon_dot = False

                for output in '0123456789ABCDEF':
                    for i in range(4):
                        self.displays[display].set_character(output, i, colon_dot)
                        sleep(0.02)
                    colon_dot = not colon_dot
                    self.displays[display].set_colon(colon_dot)
                    self.displays[display].draw()
            else:
                self.log.error(f"Display {display} not found for test")
        
        except Exception as e:
            self.log.error(f"Error during display test on {display}: {e}")

    
    async def async_clock_loop(self) -> None:
        """
        Main clock loop to update time and date displays.
        """
        self.log.info("Entering clock loop")
        self.last_time = self.rtc.datetime()
        while True:
            
            if self.rtc.datetime() != self.last_time:
                self.log.info(f"Time now is {self.rtc.datetime()}")
                hour, minute, second = self.rtc.datetime()[4:7]
                time_string = f"{hour:02d}{minute:02d}{second:02d}"
                self.log.info(f"Updating display to: {time_string}")
                for i in range(4):
                    self.displays["hour_minute"].set_character(time_string[i], i)
                self.render_seconds_colon(int(second))
                self.displays["hour_minute"].draw()
                self.last_time = self.rtc.datetime()

            await sleep_ms(1)
    
    def render_seconds_colon(self, seconds: int) -> None:
        """
        Display seconds colon based on current second passed - odds show, evens hide.
        """
        seconds = seconds % 60

        if seconds % 2 == 1:
            self.log.info("Hiding seconds colon")
            self.displays["hour_minute"].set_colon(False)
        else:
            self.log.info("Showing seconds colon")
            self.displays["hour_minute"].set_colon(True)
