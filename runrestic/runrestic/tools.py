"""
This module provides utility functions for parsing and manipulating data related to Restic operations.

It includes functions to parse sizes, times, and lines of text using regular expressions, as well as
a utility to deeply update nested dictionaries. These functions are used throughout the application
to process and format data.
"""

import logging
import re
from typing import Any, TypeVar

logger = logging.getLogger(__name__)


def make_size(size: int) -> str:
    """
    Convert a size in bytes to a human-readable string with appropriate units.

    Args:
        size (int): The size in bytes.

    Returns:
        str: The size formatted as a human-readable string (e.g., "1.23 GiB").
    """
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
    """
    Parse a human-readable size string into a size in bytes.

    Args:
        size (str): The size string (e.g., "1.23 GiB").

    Returns:
        float: The size in bytes. Returns 0.0 if parsing fails.
    """
    re_bytes = re.compile(r"([0-9.]+) ?([a-zA-Z]*B)")
    try:
        number, unit = re_bytes.findall(size)[0]
    except IndexError:
        logger.error("Failed to parse size of '%s'", size)
        return 0.0
    units = {
        "B": 1,
        "kB": 10**3,
        "MB": 10**6,
        "GB": 10**9,
        "TB": 10**12,
        "KiB": 1024,
        "MiB": 2**20,
        "GiB": 2**30,
        "TiB": 2**40,
    }
    return float(number) * units.get(unit, 1)


def parse_time(time_str: str) -> int:
    """
    Parse a time string in the format "HH:MM:SS" or "MM:SS" into seconds.

    Args:
        time_str (str): The time string to parse.

    Returns:
        int: The total time in seconds. Returns 0 if parsing fails.
    """
    re_time = re.compile(r"(?:([0-9]+):)?([0-9]+):([0-9]+)")
    try:
        hours, minutes, seconds = (int(x) if x else 0 for x in re_time.findall(time_str)[0])
    except IndexError:
        logger.error("Failed to parse time of '%s'", time_str)
        return 0
    if minutes:
        seconds += minutes * 60
    if hours:
        seconds += hours * 3600
    return seconds


def deep_update(base: dict[Any, Any], update: dict[Any, Any]) -> dict[Any, Any]:
    """
    Recursively update a nested dictionary with values from another dictionary.

    Args:
        base (dict[Any, Any]): The base dictionary to update.
        update (dict[Any, Any]): The dictionary with updates.

    Returns:
        dict[Any, Any]: A new dictionary with the updates applied.
    """
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


ParsedType = TypeVar("ParsedType", str, tuple[str, ...])


def parse_line(
    regex: str,
    output: str,
    default: ParsedType,
) -> ParsedType:
    r"""
    Parse a line of text using a regular expression and return matched variables.

    If there is no match in the output, the variables will be returned with their default values.

    Args:
        regex (str): The regular expression to match the requested variables.
        output (str): The text output to be parsed.
        default (T): Default values to return if parsing fails.

    Returns:
        ParsedType: The parsed result or the default values.

    Examples:
        >>> parse_line(
        ...     regex=r"Files:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified",
        ...     output="Files: 10 new, 5 changed, 20 unmodified",
        ...     default=("0", "0", "0")
        ... )
        ('10', '5', '20')
    """
    try:
        parsed = re.findall(regex, output)[0]
    except IndexError:
        logger.error("No match in output for regex '%s'", regex)
        return default
    if isinstance(parsed, type(default)):
        return parsed
    else:
        logger.error(
            f"The format of the parsed output '{parsed}' does not match the expected format as per default '{default}'.",
        )
    return default
