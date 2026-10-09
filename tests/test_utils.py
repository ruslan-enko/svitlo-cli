from core.utils import (
    button_id_from_group,
    format_time_duration,
    is_light_on,
    minutes_to_time_str,
    parse_group_from_button_id,
    parse_time_to_minutes,
    time_range_contains,
)


def test_format_time_duration():
    assert format_time_duration(0) == "0сек"
    assert format_time_duration(45) == "45сек"
    assert format_time_duration(90) == "1хв 30сек"
    assert format_time_duration(3665) == "1год 1хв 5сек"


def test_is_light_on():
    assert is_light_on("Світло є") is True
    assert is_light_on("Світла немає") is False
    assert is_light_on("Електроенергії немає з 14:00 до 16:00") is False
    assert is_light_on("") is False


def test_parse_time_to_minutes():
    assert parse_time_to_minutes("00:00") == 0
    assert parse_time_to_minutes("01:30") == 90
    assert parse_time_to_minutes("14:45") == 885
    assert parse_time_to_minutes("invalid") == 0


def test_minutes_to_time_str():
    assert minutes_to_time_str(0) == "00:00"
    assert minutes_to_time_str(90) == "01:30"
    assert minutes_to_time_str(885) == "14:45"


def test_time_range_contains():
    assert time_range_contains(600, 500, 700) is True
    assert time_range_contains(400, 500, 700) is False
    # Midnight wrap range (e.g. 23:00 to 02:00 -> 1380 to 120)
    assert time_range_contains(1400, 1380, 120) is True
    assert time_range_contains(60, 1380, 120) is True
    assert time_range_contains(500, 1380, 120) is False


def test_button_id_helpers():
    assert parse_group_from_button_id("btn-group-6_1") == "6.1"
    assert button_id_from_group("6.1") == "btn-group-6_1"
