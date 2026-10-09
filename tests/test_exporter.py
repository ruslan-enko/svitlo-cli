
from core.exporter import _parse_date_string, generate_ics_content


def test_parse_date_string():
    dt = _parse_date_string("05.08.2026")
    assert dt.day == 5
    assert dt.month == 8
    assert dt.year == 2026

    dt2 = _parse_date_string("12 Лютого 2026")
    assert dt2.day == 12
    assert dt2.month == 2
    assert dt2.year == 2026


def test_generate_ics_content():
    schedule_data = {
        'schedule_date': '05.08.2026',
        'off_ranges': [
            {'start': (14, 0), 'end': (16, 30)}
        ],
        'has_next_day': False
    }

    content = generate_ics_content("6.1", schedule_data)
    assert "BEGIN:VCALENDAR" in content
    assert "END:VCALENDAR" in content
    assert "SUMMARY:Відключення світла (Група 6.1)" in content
    assert "20260805T140000" in content
    assert "20260805T163000" in content
