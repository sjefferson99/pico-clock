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
CUSTOM_HOSTNAME = None

NTP_SYNC_INTERVAL_SECONDS = 86400

## I2C
SDA_PIN = 0
SCL_PIN = 1
I2C_ID = 0
I2C_FREQ = 400000

# DISPLAY_ADDREESSES = {
#     "hour_min": 0x70,
#     "seconds": 0x71,
#     "day_month": 0x72,
#     "year": 0x73,
#     "unused": 0x74
# }

DISPLAY_ADDREESSES = {
    "hour_min": 0x70
}

## Overclocking - Pico1 default 133MHz, Pico2 default 150MHz
CLOCK_FREQUENCY = 133000000
