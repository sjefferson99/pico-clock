from lib.ulogging import uLogger
from lib.networking import WirelessNetwork
from machine import freq, I2C
from config import DISPLAY_ADDRESSES, CLOCK_FREQUENCY, I2C_ID, SDA_PIN, SCL_PIN, I2C_FREQ, BRIGHTNESS_BUTTON
from asyncio import sleep_ms, create_task, get_event_loop, Event
from lib.display import Display
from lib.time_source import TimeSource
from lib.button import Button
from lib.clock_core import ClockCore
import _thread

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
        self.i2c_lock = _thread.allocate_lock()  # Lock for thread-safe I2C access
        self.displays = {}        
        self.wifi = WirelessNetwork()
        self.time_source = TimeSource(self.wifi, self.i2c)
        self.clock_core = None  # Will be initialized after displays are set up
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

        # Initialize and start ClockCore on Core 1 after displays are ready
        self.log.info("Initializing clock core for Core 1")
        self.clock_core = ClockCore(self.time_source, self.displays, self.i2c_lock)
        
        # Connect displays to clock core for test registration
        for display in self.displays.values():
            display.set_clock_core(self.clock_core)
        
        self.log.info("Starting clock core on Core 1")
        self.clock_core.start()
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
                self.displays[name] = Display(self.i2c, name, address)
            
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

            # Use I2C lock to prevent conflicts with Core 1 display updates
            with self.i2c_lock:
                for display in self.displays.values():
                    try:
                        display.toggle_brightness()
                    except Exception as e:
                        self.log.error(f"Failed to toggle brightness for display '{display.get_name()}': {e}")
            
            await sleep_ms(20)
