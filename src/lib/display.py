from lib.ht16k33.ht16k33segment import HT16K33Segment
from lib.ulogging import uLogger
from asyncio import sleep_ms

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from machine import I2C

class Display(HT16K33Segment):

    def __init__(self, i2c: I2C, name: str, address: int, tests_running: list) -> None:
        """
        Display class extends HT16K33Segment to manage individual 7-segment
        displays, provides methods for initialization and running display tests.
        
        :param i2c: I2C bus object
        :type i2c: I2C
        :param name: Name of display
        :type name: str
        :param address: I2C address of the display
        :type address: int
        :param tests_running: Semaphore list to track running display tests
        :type tests_running: list
        """
        super().__init__(i2c, i2c_address=address)
        self.log = uLogger(f"Init display-0x{address:02X}: {name}")
        self.name = name
        self.set_brightness(15)
        self.set_blink_rate(0)
        self.set_colon(False)
        self.clear()
        self.draw()
        self.tests_running = tests_running

    async def async_display_test(self) -> None:
        """
        Run a display test on a given display.
        """
        try:
            self.log.info(f"Running display test on {self.name}")
            self.tests_running.append(self)
            colon_dot = False

            for output in '0123456789ABCDEF':
                for i in range(4):
                    self.set_character(output, i, colon_dot)
                    await sleep_ms(20)
                colon_dot = not colon_dot
                self.set_colon(colon_dot)
                self.draw()

        except Exception as e:
            self.log.error(f"Error during display test on {self.name}: {e}")

        finally:
            self.clear()
            self.draw()
            self.log.info(f"Display test completed on {self.name}")
            self.tests_running.remove(self)
    
    def get_name(self) -> str:
        """
        Get the name of the display.
        
        :return: Name of the display
        :rtype: str
        """
        return self.name
