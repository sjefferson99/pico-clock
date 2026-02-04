from lib.ulogging import uLogger
from config import TIME_SIGNAL_PIN
from machine import Pin
from asyncio import create_task, sleep_ms
from time import ticks_ms


class TimeSignal:
    """Class to handle time signal input from a GPIO pin."""

    def __init__(self):
        self.log = uLogger("TimeSignal")
        self.log.info("Initializing TimeSignal")
        self.pin = Pin(TIME_SIGNAL_PIN, Pin.IN, Pin.PULL_DOWN)
        
    def startup(self):
        """Start monitoring the time signal."""
        self.log.info("Starting time signal monitoring")
        create_task(self.async_monitor_signal())

    async def async_monitor_signal(self):
        """Asynchronously monitor the time signal pin for changes."""
        self.log.info(f"Monitoring time signal on pin {TIME_SIGNAL_PIN}")
        previous_state = self.pin.value()
        previous_time = ticks_ms()
        while True:
            current_state = self.pin.value()
            if current_state != previous_state:
                self.log.info(f"Time signal changed to {current_state}")
                previous_state = current_state
                now = ticks_ms()
                self.log.info(f"Time signal change detected at {now} ms (delta {now - previous_time} ms)")
                previous_time = now
            await sleep_ms(1)  