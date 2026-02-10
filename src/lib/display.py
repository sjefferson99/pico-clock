from lib.ht16k33.ht16k33segment import HT16K33Segment
from lib.ulogging import uLogger
from asyncio import sleep_ms
from config import DISPLAY_BRIGHTNESS

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
        self.brightness_state = 1
        self.power_on()
        self.set_brightness(DISPLAY_BRIGHTNESS)
        self.set_blink_rate(0)
        self.set_colon(False)
        self.clear()
        self.draw()
        self.tests_running = tests_running
        self.load_glyphs()

    def load_glyphs(self) -> None:
        """
        Load custom glyphs for the display.
                0
                _
            5 |   | 1
              |   |
                - <----- 6
            4 |   | 2
              | _ |
                3
        """
        self.glyphs = {
            'G': 0b00111101,
            'N': 0b00110111,
            'O': 0b00111111,
            'P': 0b01110011,
            'R': 0b00110001,
            'S': 0b01101101,
            'T': 0b01111000            
        }
    
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

    def print_text(self, text: str, colon: bool = False, dots: int = 0) -> None:
        """
        Print text to the display.
        The display can show up to 4 characters; excess characters are ignored.
        
        :param text: Text to display
        :type text: str
        :param colon: Whether to display the colon
        :type colon: bool
        :param dots: 4-bit binary number (0b0000-0b1111) defining dot states
                 Bit order is left-to-right: bit 3 -> position 0, bit 0 -> position 3
        :type dots: int
        """
        text = str(text)
        dot_mask = dots & 0x0F
        self.clear()
        for i in range(min(4, len(text))):
            has_dot = ((dot_mask >> (3 - i)) & 0x01) == 1
            self.print_character(text[i], i, has_dot=has_dot)
        self.set_colon(colon)
        self.draw()

    def print_character(self, char: str, position: int, has_dot: bool=False) -> None:
        """
        Print a single character at a specified position on the display.
        Current supported characters are 0-9, A-F and custom glyphs G, N, O, P, R, S, T.
        Unsupported characters are rendered as blank.
        
        :param char: Character to display
        :type char: str
        :param position: Position on the display (0-3)
        :type position: int
        :param has_dot: Whether the character has a dot
        :type has_dot: bool
        """
        char = char.upper()
        if char in '0123456789ABCDEF':
            self.set_character(char, position, has_dot)
        else:
            if char in self.glyphs:
                self.set_glyph(self.glyphs[char], position, has_dot)
            else:
                if hasattr(self, "log") and self.log is not None:
                    self.log.warn(f"Unsupported character {char} at position {position}; displaying blank.")
                self.set_glyph(0x00, position, has_dot)

    def toggle_brightness(self) -> None:
        """
        Toggle brightness between 3 levels: Full (15), Configured (DISPLAY_BRIGHTNESS) and Off (0).
        """
        if self.brightness_state == 2:
            self.brightness_state = 0
            self.power_off()
            self.log.info(f"Toggling brightness for display '{self.name}' to 0 (off)")
            return
        
        elif self.brightness_state == 0:
            self.brightness_state = 1
            self.power_on()
            brightness = DISPLAY_BRIGHTNESS
            
        else:
            self.brightness_state = 2
            self.power_on()
            brightness = 15
            
        
        self.log.info(f"Toggling brightness for display '{self.name}' to {brightness} (state {self.brightness_state})")
        self.set_brightness(brightness)
