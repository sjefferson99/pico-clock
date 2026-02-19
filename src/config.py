## Logging
# Level 0-4: 0 = Disabled, 1 = Critical, 2 = Error, 3 = Warning, 4 = Info
LOG_LEVEL = 2
# Handlers: Populate list with zero or more of the following log output handlers (case sensitive): "Console", "File"
LOG_HANDLERS = ["Console", "File"]
# Max log file size in bytes, there will be a maximum of 2 files at this size created
LOG_FILE_MAX_SIZE = 10240

## WIFI
WIFI_SSID = ""
WIFI_PASSWORD = ""
WIFI_COUNTRY = "GB"
WIFI_CONNECT_TIMEOUT_SECONDS = 10
WIFI_CONNECT_RETRIES = 1
WIFI_RETRY_BACKOFF_SECONDS = 5
# Leave as none for MAC based unique hostname or specify a custom hostname string
CUSTOM_HOSTNAME = "Pico-Clock"

## Timezone in IANA format
TIMEZONE = "Etc/UTC"

## NTP poll frequency - Minimum period is every 60 seconds to avoid NTP server blacklisting
NTP_SYNC_INTERVAL_SECONDS = 60

## I2C
SDA_PIN = 0
SCL_PIN = 1
I2C_ID = 0
I2C_FREQ = 400000

DISPLAY_ADDRESSES = {
    "hour_minute": 0x70,
    "status": 0x71,
    "seconds": 0x72,
    "day_month": 0x73,
    "year": 0x74
}

# Custom display brightness for HT16K33 displays: valid range 0 (dim) to 15 (maximum)
DISPLAY_BRIGHTNESS = 0
# GPIO for brightness toggle button - if not present, set to None and brightness will be set to DISPLAY_BRIGHTNESS
# If set to a valid GPIO pin number, the button will toggle between Full brightness (15), DISPLAY_BRIGHTNESS and off when pressed
BRIGHTNESS_BUTTON = 2

## Run RTC full test (clears current time and date settings, so only enable for testing)
RTC_FULL_TEST = False

## Overclocking - Pico1 default 133MHz, Pico2 default 150MHz
CLOCK_FREQUENCY = 133000000
