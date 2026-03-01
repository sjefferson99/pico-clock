"""
Clock Core - Runs on Core 1 for precise, uninterrupted clock display updates.

This module handles the time-critical display update loop on the second core,
ensuring that clock displays are never disrupted by async networking operations
running on Core 0.
"""
import _thread
import time
from lib.ulogging import uLogger


class ClockCore:
    """
    Manages the clock display update loop running on Core 1.
    
    This class starts a dedicated thread on the Pico's second core that
    continuously reads time from the TimeSource abstraction and updates
    all clock displays with precise timing, independent of async operations
    on Core 0.
    """
    
    def __init__(self, time_source, displays: dict, i2c_lock = None) -> None:
        """
        Initialize the clock core with time source and displays.
        
        Args:
            time_source: TimeSource instance managing the best available time
            displays: Dictionary of Display objects keyed by name
            i2c_lock: Optional lock for thread-safe I2C operations
        """
        self.log = uLogger("ClockCore")
        self.time_source = time_source
        self.displays = displays
        self.running = False
        self.lock = _thread.allocate_lock()
        self.i2c_lock = i2c_lock if i2c_lock is not None else _thread.allocate_lock()
        self.last_time = None
        self.tests_running = []  # Internal list of running test names
        
    def start(self) -> None:
        """
        Start the clock update loop on Core 1.
        
        This spawns a new thread that will run continuously on the second
        core, dedicating it to clock display updates.
        """
        if self.running:
            self.log.warn("Clock core already running, ignoring start request")
            return
            
        self.log.info("Starting clock core on Core 1")
        self.running = True
        _thread.start_new_thread(self._clock_loop, ())
        
    def stop(self) -> None:
        """
        Signal the clock loop to stop.
        
        Note: The thread will complete its current iteration before stopping.
        """
        self.log.info("Stopping clock core")
        self.running = False
        
    def register_test(self, test_name: str) -> None:
        """
        Register a running test to pause the clock loop.
        
        Args:
            test_name: Unique identifier for the test
        """
        with self.lock:
            if test_name not in self.tests_running:
                self.tests_running.append(test_name)
                self.log.info(f"Test '{test_name}' registered, clock loop paused")
    
    def unregister_test(self, test_name: str) -> None:
        """
        Unregister a completed test to potentially resume the clock loop.
        
        Args:
            test_name: Unique identifier for the test
        """
        with self.lock:
            if test_name in self.tests_running:
                self.tests_running.remove(test_name)
                self.log.info(f"Test '{test_name}' unregistered")
                if not self.tests_running:
                    self.log.info("All tests complete, clock loop resuming")
    
    def _clock_loop_should_run(self) -> bool:
        """
        Determine if the clock loop should run.
        Thread-safe check of running tests.
        """
        with self.lock:
            return len(self.tests_running) == 0
    
    def _clock_loop(self) -> None:
        """
        Main clock loop running on Core 1.
        
        This is a tight blocking loop that:
        1. Reads time from TimeSource (which selects best available source)
        2. Updates displays when time changes
        3. Maintains precise timing independent of Core 0 async operations
        
        Runs continuously until stop() is called.
        """
        self.log.info("Clock core loop started on Core 1")
        self.last_time = None
        
        while self.running:
            try:
                # Check if we should pause for tests
                if not self._clock_loop_should_run():
                    time.sleep_ms(100)
                    continue
                
                # Get time from the best available source
                # Note: time_source.get_time() is thread-safe for reading
                now_time = self.time_source.get_time()
                
                # Only update displays when time actually changes
                if now_time != self.last_time:
                    self.log.info(f"Time change detected, updating displays. Time now: {now_time}")
                    self.last_time = now_time
                    
                    year, month, day, hour, minute, second = now_time[0:6]
                    
                    # Update all displays
                    self._update_displays(year, month, day, hour, minute, second)
                    
                    # Update status display every 5 seconds
                    if second % 5 == 0:
                        self._set_status_display()
                
                # Small sleep to prevent CPU hogging while maintaining responsiveness
                time.sleep_ms(50)
                
            except Exception as e:
                self.log.error(f"Error in clock core loop: {e}")
                time.sleep_ms(1000)  # Back off on error
        
        self.log.info("Clock core loop stopped")
    
    def _update_displays(self, year: int, month: int, day: int, 
                         hour: int, minute: int, second: int) -> None:
        """
        Update all clock displays with current time.
        Thread-safe with I2C lock to prevent bus contention.
        
        Args:
            year, month, day, hour, minute, second: Current time components
        """
        colon = self._should_render_seconds_colon(int(second))
        
        updates = [
            ("hour_minute", f"{hour:02d}{minute:02d}", {"colon": colon}),
            ("seconds", f"{second:02d}00", {"dots": 0b0100}),
            ("day_month", f"{day:02d}{month:02d}", {"dots": 0b0101}),
            ("year", f"{year:04d}", {}),
        ]
        
        # Use I2C lock to ensure thread-safe display updates
        with self.i2c_lock:
            for name, text, kwargs in updates:
                display = self.displays.get(name)
                if display:
                    try:
                        display.print_text(text, **kwargs)
                    except Exception as e:
                        self.log.error(f"Failed to update display '{name}': {e}")
    
    def _should_render_seconds_colon(self, seconds: int) -> bool:
        """
        Determine if seconds colon should display based on current second.
        Odds show, evens hide.
        
        Args:
            seconds: Current second value
            
        Returns:
            False to hide colon (odd seconds), True to show (even seconds)
        """
        seconds = seconds % 60
        return seconds % 2 == 0
    
    def _set_status_display(self) -> None:
        """
        Update the status display with the current time synchronization method.
        Thread-safe with I2C lock.
        """
        if self.displays.get("status") is None:
            return
        
        current_method = ""
        for method in self.time_source.get_time_sync_status():
            if method.get_status():
                current_method = method.get_name()
                break
        
        # Use I2C lock to ensure thread-safe display update
        with self.i2c_lock:
            if current_method:
                try:
                    self.displays["status"].print_text(current_method)
                except Exception as e:
                    self.log.error(f"Failed to update status display: {e}")
            else:
                try:
                    self.displays["status"].print_text("NONE")
                except Exception as e:
                    self.log.error(f"Failed to update status display: {e}")
