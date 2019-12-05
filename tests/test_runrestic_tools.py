import time

import pytest

from runrestic.runrestic.tools import (
    deep_update,
    make_size,
    parse_size,
    parse_time,
    timethis,
)


def test_make_size():
    assert make_size(100) == "100 B"
    assert make_size(1000000) == "976.56 KiB"
    assert make_size(1000000000) == "953.67 MiB"
    assert make_size(1000000000000) == "931.32 GiB"
    assert make_size(1000000000000000) == "909.49 TiB"
    with pytest.raises(TypeError):
        make_size("string")


def test_parse_size():
    assert parse_size("910 TiB") == 1024 * 1024 * 1024 * 1024 * 910
    assert parse_size("910 GiB") == 1024 * 1024 * 1024 * 910
    assert parse_size("910 MiB") == 1024 * 1024 * 910
    assert parse_size("910 KiB") == 1024 * 910
    assert parse_size("910 B") == 910
    with pytest.raises(TypeError):
        parse_size(123)


def test_parse_time():
    assert parse_time("0:50") == 50
    assert parse_time("2:20") == 2 * 60 + 20
    assert parse_time("2:00:00") == 2 * 60 * 60
    assert parse_time("23:59:59") == 24 * 60 * 60 - 1


# def test_timethis():
#     times = {}
#
#     @timethis(times)
#     def testrun():
#         time.sleep(0.2)
#
#     testrun()
#     assert {k: round(v, 2) for k, v in times.items()} == {"testrun": 0.20}


def test_deep_update():
    new = deep_update({"x": {"y": "z"}, "foo": "bar"}, {"x": {"z": "y"}, "foo": "baz"})
    assert new == {"x": {"y": "z", "z": "y"}, "foo": "baz"}
