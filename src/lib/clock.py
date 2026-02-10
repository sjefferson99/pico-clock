from lib.ulogging import uLogger
from lib.networking import WirelessNetwork
from machine import freq, I2C
from config import DISPLAY_ADDRESSES, CLOCK_FREQUENCY, I2C_ID, SDA_PIN, SCL_PIN, I2C_FREQ, BRIGHTNESS_BUTTON
from asyncio import sleep_ms, create_task, get_event_loop, Event
from lib.display import Display
from lib.time_source import TimeSource
from lib.button import Button

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
        self.brightness_button_event = Event()
        if BRIGHTNESS_BUTTON is not None:
            self.brightness_button = Button(BRIGHTNESS_BUTTON, "Brightness", self.brightness_button_event)
        else:
            self.brightness_button = None
    
    def startup(self) -> None:
        self.log.info("Starting Pico Clock")
        self.wifi.startup()
        self.time_source.startup()
        self.init_displays()
        self.test_all_displays()

        self.log.info("Starting clock loop")
        create_task(self.async_clock_loop())
        self.log.info("Clock started with displays: " + ", ".join(self.displays.keys()))
        
        if self.brightness_button:
            self.log.info("Starting brightness button watcher")
            create_task(self.brightness_button.wait_for_press())
            create_task(self.brightness_button_watcher())
                
        self.log.info("Pico Clock startup complete, entering main loop")

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
    
    async def brightness_button_watcher(self) -> None:
        """
        Watcher for brightness button presses, which will toggle display
        brightness on press.
        """
        if self.brightness_button is None:
            self.log.error("Brightness button watcher started but no brightness button configured, exiting watcher")
            return
        
        self.log.info("Entering brightness button watcher loop")
        
        while True:
            await self.brightness_button_event.wait()
            self.brightness_button_event.clear()

            for display in self.displays.values():
                display.toggle_brightness()
            
            await sleep_ms(20)
    
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
                self.log.info(f"Time change detected, updating displays. Time now: {now_time}")
                self.last_time = now_time
                
                year, month, day, hour, minute, second = now_time[0:6]
                
                colon = self.should_render_seconds_colon(int(second))
                updates = [
                    ("hour_minute", f"{hour:02d}{minute:02d}", {"colon": colon}),
                    ("seconds", f"{second:02d}" + "00", {"dots": 0b0100}),
                    ("day_month", f"{day:02d}{month:02d}", {"dots": 0b0101}),
                    ("year", f"{year:04d}", {}),
                ]

                for name, text, kwargs in updates:
                    display = self.displays.get(name)
                    if display:
                        display.print_text(text, **kwargs)

                if second % 5 == 0:
                    self.set_status_display()

            await sleep_ms(1)
    
    def should_render_seconds_colon(self, seconds: int) -> bool:
        """
        Determine if seconds colon should display based on current second
        passed - odds show, evens hide.
        """
        seconds = seconds % 60

        if seconds % 2 == 1:
            self.log.info("Should hide seconds colon")
            return False
        else:
            self.log.info("Should show seconds colon")
            return True
    
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
