import re

from lib.timezone.db import timezone_to_posix

def time_tuple_to_local_time(time_tuple: tuple, timezone: str) -> tuple:
    posix_str = timezone_to_posix(timezone)
    if posix_str is None:
        return time_tuple

    normalised = _normalise(posix_str)
    base, *rules = _split_posix(normalised)
    std, offset, dst, dst_offset = _parse_base(base)

    print(std, offset, dst, dst_offset)
    print(normalised, base, rules)

    for rule in rules:
        month, week, day, hour = _parse_rule(rule)
        print(month, week, day, hour)

    return time_tuple

def _split_posix(posix_str: str) -> tuple:
    return tuple(posix_str.split(','))

def _normalise(posix_str: str) -> str:
    normalised = posix_str.upper()
    return normalised

BASE_RE = re.compile(r"([A-Za-z]+)([-+]?\d+)([A-Za-z]+)?([-+]?\d+)?")
def _parse_base(base: str) -> tuple:
    m = BASE_RE.match(base)
    if not m:
        raise ValueError(f"Invalid base: {base}")

    std, offset, dst, dst_offset = m.groups()
    offset = int(offset)
    dst_offset = int(dst_offset) if dst_offset else None

    return std, offset, dst, dst_offset

RULE_RE = re.compile(r"M(\d+)\.(\d+)\.(\d+)(/(\d+))?")

def _parse_rule(rule: str) -> tuple:
    m = RULE_RE.match(rule)
    if not m:
        raise ValueError(f"Invalid rule: {rule}")

    month = int(m.group(1))
    week  = int(m.group(2))
    day   = int(m.group(3))
    hour  = int(m.group(5)) if m.group(5) else 2  # default 02:00

    return month, week, day, hour

time_tuple_to_local_time((2026, 2, 18, 21, 10, 43), 'Europe/London')