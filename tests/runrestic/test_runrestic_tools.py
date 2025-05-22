import pytest

from runrestic.runrestic.tools import (
    deep_update,
    make_size,
    parse_line,
    parse_size,
    parse_time,
)

OUTPUT = """Start of the output
Dummy counter: 123 something
Two counters: value 1: 456, value 2: 7.89
Three counters: value 1: 1.1, value 2: 22, value 3: 33.3 kB
End of output
"""

OUTPUT_2 = """Start of the output
Two counters: value 1: 456, value 2: 7.89
Three counters: in next line
Three counters: value 1: 1.1, value 2: 22, value 3: 33.3 kB
MORE DATA
Dummy counter: 123 something
End of output
"""


def test_make_size():
    assert make_size(100) == "100 B"
    assert make_size(1000000) == "976.56 KiB"
    assert make_size(1000000000) == "953.67 MiB"
    assert make_size(1000000000000) == "931.32 GiB"
    assert make_size(1000000000000000) == "909.49 TiB"
    with pytest.raises(TypeError):
        make_size("string")  # type: ignore[arg-type]


def test_parse_size():
    assert parse_size("910 TiB") == 1024 * 1024 * 1024 * 1024 * 910
    assert parse_size("910 GiB") == 1024 * 1024 * 1024 * 910
    assert parse_size("910 MiB") == 1024 * 1024 * 910
    assert parse_size("910 KiB") == 1024 * 910
    assert parse_size("910 B") == 910
    with pytest.raises(TypeError):
        parse_size(123)  # type: ignore[arg-type]
    # Test missing units
    assert parse_size("910") == 0.0


def test_parse_time():
    assert parse_time("0:50") == 50
    assert parse_time("2:20") == 2 * 60 + 20
    assert parse_time("2:00:00") == 2 * 60 * 60
    assert parse_time("23:59:59") == 24 * 60 * 60 - 1
    # Test wrong time format
    assert parse_time("42") == 0


def test_deep_update():
    new = deep_update({"x": {"y": "z"}, "foo": "bar"}, {"x": {"z": "y"}, "foo": "baz"})
    assert new == {"x": {"y": "z", "z": "y"}, "foo": "baz"}


def test_parse_line_match_one():
    assert parse_line(r"Dummy counter: (\d+) something", OUTPUT, "-1") == "123"
    assert parse_line(r"Dummy counter: (\d+) something", OUTPUT_2, "-1") == "123"


def test_parse_line_no_match_one():
    default = "-1"
    assert (
        parse_line(r"Dummy counter NONE: (\d+) something", OUTPUT, default) == default
    )


def test_parse_line_match_two():
    assert parse_line(
        r"Two counters: value 1: (\d+), value 2: ([\d\.]+)", OUTPUT, ("-1", "-1")
    ) == ("456", "7.89")


def test_parse_line_no_match_two():
    default = ("0", "0.0")
    assert (
        parse_line(
            r"Two counters: value 1: (\d+) NO, value 2: ([\d\.]+)", OUTPUT, default
        )
        == default
    )
    assert (
        parse_line(
            r"Two counters: value 1: (\d+) NO, value 2: ([\d\.]+)", OUTPUT_2, default
        )
        == default
    )


def test_parse_line_match_three():
    assert parse_line(
        r"Three counters: value 1: ([\d\.]+), value 2: (\d+), value 3: ([\d\.]+ [kMG]?B)",
        OUTPUT,
        ("-1", "-1", "-1"),
    ) == ("1.1", "22", "33.3 kB")
    assert parse_line(
        r"Three counters: value 1: ([\d\.]+), value 2: (\d+), value 3: ([\d\.]+ [kMG]?B)",
        OUTPUT_2,
        ("-1", "-1", "-1"),
    ) == ("1.1", "22", "33.3 kB")


def test_parse_line_no_match_three():
    assert parse_line(
        r"Three counters: value missing: ([\d\.]+), value 2: (\d+), value 3: ([\d\.]+ [kMG]?B)",
        OUTPUT,
        ("-1", "-1", "-1"),
    ) == ("-1", "-1", "-1")
