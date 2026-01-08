# Pico Clock
A 7 segment display based clock powered by the RPI pico. Modular in terms of what data is on display based on displays connected. Also variety of precision time sources to ensure the time displayed is accurate and future plans to create a portable NTP server with high accuracy and precision.

## Development
A pico w or pico 2 w baord should be compatible and sufficient. Ensure it is on recent firmware as it relised on asyncio. Development is on: [v1.27.0](https://micropython.org/resources/firmware/RPI_PICO_W-20251209-v1.27.0.uf2)

## Hardware
- [Pico W or Pico 2 W](https://shop.pimoroni.com/products/raspberry-pi-pico-2-w?variant=54852253024635)
- [I2C driven 7 segment displays](https://www.amazon.co.uk/dp/B0DGPWXBSV)
- [I2C RTC](https://shop.pimoroni.com/products/adafruit-ds3231-precision-rtc-breakout?variant=16610898055)
- [GPS with PPS output](https://shop.pimoroni.com/products/adafruit-ultimate-gps-breakout?variant=288854706)

## Build
Connect the pico 3v3 out and ground to display's power and I2C output to display's I2C input. Default is GPIO 0 and 1, but is configurable in config.py
Each display has a separate function denoted by it's I2C address. The address is configured by connecting solder pads: [Datasheet](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-7-segment-led-featherwings.pdf)
To save you frustrating googling for specific pinout from he datasheet vagueness, the pinout looking down on the display from above - left to right is: +3.3v, Gnd, Clock, Data. You can reverse polarity safely to just guess, ask me how I know...

"hour_min": 0x70
"status": 0x71
"seconds": 0x72
"day_month": 0x73
"year": 0x74

## Code
Copy src folder to pico, review config file and then restart to execute main.py.