from core.schedule_fetcher import ScheduleFetcher


def test_time_ranges_parser():
    fetcher = ScheduleFetcher()
    ranges = fetcher._parse_time_ranges("з 14:00 до 16:30, з 20:00 до 22:00")
    assert len(ranges) == 2
    assert ranges[0] == {'start': (14, 0), 'end': (16, 30)}
    assert ranges[1] == {'start': (20, 0), 'end': (22, 0)}


def test_build_schedule_from_ranges():
    fetcher = ScheduleFetcher()
    off_ranges = [{'start': (1, 0), 'end': (2, 0)}]
    schedule = fetcher._build_schedule_from_ranges(off_ranges)
    assert len(schedule) == 48

    # 01:00 - 01:30 and 01:30 - 02:00 should be 'off'
    off_items = [item for item in schedule if item['status'] == 'off']
    assert len(off_items) == 2
    assert off_items[0]['time_range'] == "01:00 - 01:30"
    assert off_items[1]['time_range'] == "01:30 - 02:00"
