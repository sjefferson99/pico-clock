from lib.ulogging import uLogger
from lib.networking import WirelessNetwork
from machine import freq, I2C
from config import DISPLAY_ADDRESSES, CLOCK_FREQUENCY, I2C_ID, SDA_PIN, SCL_PIN, I2C_FREQ
from asyncio import sleep_ms, create_task, get_event_loop
from lib.display import Display
from lib.time_source import TimeSource

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
        self.displays = {}
        self.tests_running = []        
        self.wifi = WirelessNetwork()
        self.time_source = TimeSource(self.wifi, self.i2c)

    def startup(self) -> None:
        self.log.info("Starting Pico Clock")
        self.wifi.startup()
        self.time_source.startup()
        self.init_displays()
        self.test_all_displays()

        self.log.info("Starting clock loop")
        create_task(self.async_clock_loop())
        self.log.info("Clock started with displays: " + ", ".join(self.displays.keys()))

        loop = get_event_loop()
        loop.run_forever()

    def init_displays(self) -> None:
        """
        Initialize all connected displays into a list of available displays.
        """
        for name, address in DISPLAY_ADDRESSES.items():
            self.log.info(f"Initializing display '{name}' at address 0x{address:02X}")
            try:
                self.displays[name] = Display(self.i2c, name, address, self.tests_running)
            
            except Exception as e:
                self.log.error(f"Failed to initialize display '{name}' at address 0x{address:02X}: {e}")

        self.log.info(f"Initialized {len(self.displays)} displays: " + ", ".join(self.displays.keys()))
    
    def test_all_displays(self) -> None:
        """
        Run display tests on all initialized displays.
        """
        self.log.info("Starting display tests for all displays")
        for name, display in self.displays.items():
            self.log.info(f"Testing display '{name}'")
            create_task(display.async_display_test())

    def clock_loop_should_run(self) -> bool:
        """
        Determine if the clock loop should run.
        """
        result = True

        if len(self.tests_running) > 0:
            result = False
        
        return result
    
    async def async_clock_loop(self) -> None:
        """
        Main clock loop to update time and date displays.
        """
        self.log.info("Entering clock loop")
        self.last_time = self.time_source.get_time()

        while True:
            
            if not self.clock_loop_should_run():
                await sleep_ms(100)
                continue
            
            now_time = self.time_source.get_time()
            if now_time != self.last_time:
                self.log.info(f"Time now is {now_time}")
                hour, minute, second = now_time[3:6]
                time_string = f"{hour:02d}{minute:02d}{second:02d}"
                self.log.info(f"Updating display to: {time_string}")
                for i in range(4):
                    self.displays["hour_minute"].set_character(time_string[i], i)
                self.render_seconds_colon(int(second))
                self.displays["hour_minute"].draw()
                self.last_time = now_time
                
                if second % 5 == 0:
                    self.set_status_display()

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
    
    def set_status_display(self) -> None:
        """
        Update the status display with the current time synchronization method.
        """
        if self.displays.get("status") is None:
            return
        
        current_method = ""
        for method in self.time_source.get_time_sync_status():
            
            if method.get_status():
                current_method = method.get_name()
                break

        if current_method:
            self.log.info(f"Time synchronised via {current_method}, updating status display")
            self.displays["status"].print_text(current_method)
        else:
            self.log.info("No time synchronisation method active, updating status display to NONE")
            self.displays["status"].print_text("NONE")
