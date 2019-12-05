import re
from typing import Any, Dict


def make_size(size: int) -> str:
    if size > 1 << 40:
        return f"{size / (1 << 40):.2f} TiB"
    if size > 1 << 30:
        return f"{size / (1 << 30):.2f} GiB"
    if size > 1 << 20:
        return f"{size / (1 << 20):.2f} MiB"
    if size > 1 << 10:
        return f"{size / (1 << 10):.2f} KiB"
    return f"{size:.0f} B"


def parse_size(size: str) -> float:
    re_bytes = re.compile(r"([0-9.]+) ?([a-zA-Z]*B)")
    number, unit = re_bytes.findall(size)[0]
    units = {
        "B": 1,
        "kB": 10 ** 3,
        "MB": 10 ** 6,
        "GB": 10 ** 9,
        "TB": 10 ** 12,
        "KiB": 1024,
        "MiB": 2 ** 20,
        "GiB": 2 ** 30,
        "TiB": 2 ** 40,
    }
    return float(number) * units[unit]


def parse_time(time_str: str) -> int:
    re_time = re.compile(r"(?:([0-9]+):)?([0-9]+):([0-9]+)")
    hours, minutes, seconds = (int(x) if x else 0 for x in re_time.findall(time_str)[0])
    if minutes:
        seconds += minutes * 60
    if hours:
        seconds += hours * 3600
    return seconds


def deep_update(base: Dict[Any, Any], update: Dict[Any, Any]) -> Dict[Any, Any]:
    new = base.copy()
    for key, value in update.items():
        base_value = new.get(key, {})
        if not isinstance(base_value, dict):
            new[key] = value
        elif isinstance(value, dict):
            new[key] = deep_update(base_value, value)
        else:
            new[key] = value
    return new
