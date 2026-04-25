from core.utils import (
    button_id_from_group,
    format_time_duration,
    parse_group_from_button_id,
    time_range_contains,
)


def test_format_time_duration_zero_seconds() -> None:
    assert format_time_duration(0) == "0сек"


def test_format_time_duration_full_value() -> None:
    assert format_time_duration(3661) == "1год 1хв 1сек"


def test_parse_group_from_button_id_valid() -> None:
    assert parse_group_from_button_id("btn-group-6_1") == "6.1"


def test_button_id_from_group_valid() -> None:
    assert button_id_from_group("5.2") == "btn-group-5_2"


def test_time_range_contains_regular_window() -> None:
    assert time_range_contains(9 * 60 + 30, 9 * 60, 10 * 60)
    assert not time_range_contains(10 * 60, 9 * 60, 10 * 60)


def test_time_range_contains_midnight_crossing() -> None:
    start = 23 * 60
    end = 2 * 60
    assert time_range_contains(23 * 60 + 30, start, end)
    assert time_range_contains(60, start, end)
    assert not time_range_contains(12 * 60, start, end)
