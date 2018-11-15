import re

re_bytes = re.compile('([0-9.]+) ?([a-zA-Z]*B)')
re_time = re.compile('(?:([0-9]+):)?([0-9]+):([0-9]+)')


def make_size(size: int):
    size = float(size)
    if size > 1 << 40:
        return "{:.2f} TiB".format(size / (1 << 40))
    if size > 1 << 30:
        return "{:.2f} GiB".format(size / (1 << 30))
    if size > 1 << 20:
        return "{:.2f} MiB".format(size / (1 << 20))
    if size > 1 << 10:
        return "{:.2f} KiB".format(size / (1 << 10))
    return "{:.0f} B".format(size)


def parse_size(size: str):
    number, unit = re_bytes.findall(size)[0]
    units = {
        "B": 1, "kB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12,
        "KiB": 1024, "MiB": 2 ** 20, "GiB": 2 ** 30, "TiB": 2 ** 40,
    }
    return float(number) * units[unit]


def parse_time(time: str):
    hours, minutes, seconds = (int(x) if x else 0 for x in re_time.findall(time)[0])
    if minutes:
        seconds += minutes * 60
    if hours:
        seconds += hours * 3600
    return seconds
