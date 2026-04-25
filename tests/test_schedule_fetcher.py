from core.schedule_fetcher import ScheduleFetcher


def test_parse_time_ranges_handles_multiple_ranges() -> None:
    fetcher = ScheduleFetcher()
    ranges = fetcher._parse_time_ranges("з 00:00 до 02:30, з 14:00 до 16:00")
    assert ranges == [
        {"start": (0, 0), "end": (2, 30)},
        {"start": (14, 0), "end": (16, 0)},
    ]


def test_build_schedule_marks_off_slots() -> None:
    fetcher = ScheduleFetcher()
    off_ranges = [{"start": (1, 0), "end": (2, 0)}]

    schedule = fetcher._build_schedule_from_ranges(off_ranges)

    assert len(schedule) == 48
    assert schedule[2]["time_range"] == "01:00 - 01:30"
    assert schedule[2]["status"] == "off"
    assert schedule[3]["time_range"] == "01:30 - 02:00"
    assert schedule[3]["status"] == "off"
    assert schedule[4]["status"] == "on"


def test_extract_update_time_when_present() -> None:
    fetcher = ScheduleFetcher()
    text = "Інформація станом на 08:30 25.04.2026"
    assert fetcher._extract_update_time(text) == "08:30 25.04.2026"
