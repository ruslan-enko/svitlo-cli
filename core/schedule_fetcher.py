import logging
import re
from datetime import datetime, timedelta

import httpx

from core.config import AVAILABLE_GROUPS, MONTHS_UA
from core.data_manager import load_last_data, save_last_data
from core.utils import time_range_contains


class ScheduleFetcher:
    """Handles fetching power outage schedule data from Lvivoblenergo website."""
    BASE_URL = "https://poweron.loe.lviv.ua"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "uk,en-US;q=0.9,en;q=0.8",
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def fetch_schedules(self) -> dict:
        """Fetch power outage schedules for all groups using httpx first, then Playwright fallback."""
        html_content = ""

        # Try fast HTTP GET via httpx
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=self.HEADERS) as client:
                response = await client.get(self.BASE_URL)
                if response.status_code == 200 and len(response.text) > 500:
                    html_content = response.text
                    self.logger.info("Successfully fetched main page via httpx")
        except Exception as e:
            self.logger.warning(f"httpx fetch failed: {e}. Trying Playwright fallback...")

        # If httpx failed, attempt Playwright as fallback
        if not html_content:
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(user_agent=self.HEADERS["User-Agent"])
                    page = await context.new_page()
                    try:
                        await page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=30000)
                        await page.wait_for_timeout(1500)
                        html_content = await page.content()
                    finally:
                        await page.close()
                        await browser.close()
            except Exception as e:
                self.logger.error(f"Playwright fallback also failed: {e}")

        # If we successfully obtained HTML content
        if html_content:
            try:
                schedules = {}
                for group in AVAILABLE_GROUPS:
                    schedules[group] = self._parse_main_page(html_content, group)

                result = {
                    'success': True,
                    'data': schedules,
                    'updated': datetime.now().isoformat()
                }
                save_last_data(result)
                return result
            except Exception as e:
                self.logger.error(f"Error parsing schedule HTML: {e}")

        # Fallback to cached data if network or parsing failed
        last_data = load_last_data()
        if last_data:
            self.logger.info("Loaded last saved data from cache")
            return {
                'success': False,
                'is_stale': True,
                'data': last_data.get('data', {}),
                'updated': last_data.get('updated', ''),
                'error': "Не вдалося оновити дані. Використовуємо кешований розклад."
            }

        return {
            'success': False,
            'is_stale': False,
            'error': "Не вдалося завантажити дані і немає збереженого кешу.",
            'data': {}
        }

    def _parse_main_page(self, html: str, target_group: str) -> dict:
        """Parse the main page HTML to extract schedule information for a given group."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        text_div = soup.select_one('.power-off__text')
        full_text = text_div.get_text() if text_div else soup.get_text()
        full_page_text = soup.get_text()

        update_time = self._extract_update_time(full_text)

        now = datetime.now()
        today_date = now.strftime('%d.%m.%Y')
        tomorrow = now + timedelta(days=1)
        tomorrow_date = tomorrow.strftime('%d.%m.%Y')

        today_formatted = f"{now.day} {MONTHS_UA[now.month - 1]} {now.year}"

        result = {
            'schedule': self._build_schedule_from_ranges([]),
            'current_status': 'Світло є',
            'next_event': 'Немає запланованих змін',
            'schedule_date': today_formatted,
            'update_time': update_time,
            'off_ranges': [],
            'has_next_day': False
        }

        date_pattern = r'Графік\s+погодинних\s+відключень\s+на\s+(\d{2}\.\d{2}\.\d{4})'
        matches = list(re.finditer(date_pattern, full_page_text))

        # Fallback date pattern if phrasing is slightly different
        if not matches:
            date_pattern_fallback = r'відключен[ья].*?(\d{2}\.\d{2}\.\d{4})'
            matches = list(re.finditer(date_pattern_fallback, full_page_text, re.IGNORECASE))

        for i, match in enumerate(matches):
            date_str = match.group(1)

            start_idx = match.end()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(full_page_text)
            section_text = full_page_text[start_idx:end_idx]

            group_pattern = rf'Група\s+{re.escape(target_group)}\.\s*Електроенергії\s*немає\s*з\s*([^\.]+)\.'
            group_match = re.search(group_pattern, section_text)

            off_ranges = []
            if group_match:
                time_ranges = group_match.group(1).strip()
                off_ranges = self._parse_time_ranges(time_ranges)
            else:
                # Try secondary parsing style (e.g. table cells or fallback text)
                off_ranges = self._parse_secondary_group_ranges(section_text, target_group)

            schedule = self._build_schedule_from_ranges(off_ranges)

            try:
                day, month, year = date_str.split('.')
                formatted_date = f"{int(day)} {MONTHS_UA[int(month) - 1]} {year}"
            except ValueError:
                formatted_date = date_str

            if date_str == today_date:
                result['schedule'] = schedule
                result['schedule_date'] = formatted_date
                result['off_ranges'] = off_ranges
                result['current_status'] = self._get_current_status(off_ranges)

                now_minutes = now.hour * 60 + now.minute
                next_event_text = 'Немає запланованих змін'
                for off_range in off_ranges:
                    start_min = off_range['start'][0] * 60 + off_range['start'][1]
                    end_min = off_range['end'][0] * 60 + off_range['end'][1]

                    if start_min > now_minutes:
                        next_event_text = f"Наступне відключення о {off_range['start'][0]:02d}:{off_range['start'][1]:02d}"
                        break
                    elif start_min <= now_minutes < end_min:
                        next_event_text = f"Світло з'явиться о {off_range['end'][0]:02d}:{off_range['end'][1]:02d}"
                        break
                result['next_event'] = next_event_text

            elif date_str == tomorrow_date:
                result['has_next_day'] = True
                result['next_day_schedule'] = schedule
                result['next_day_date'] = formatted_date
                result['next_day_off_ranges'] = off_ranges

                if off_ranges:
                    first_out = off_ranges[0]
                    result['next_day_event'] = f"Перше відключення о {first_out['start'][0]:02d}:{first_out['start'][1]:02d}"
                else:
                    result['next_day_event'] = 'Немає запланованих змін'

        return result

    def _parse_secondary_group_ranges(self, text: str, target_group: str) -> list[dict]:
        """Secondary fallback parser for group time ranges."""
        ranges = []
        pattern = rf'{re.escape(target_group)}[:\s]+((?:з\s+)?\d{{1,2}}:\d{{2}}\s+до\s+\d{{1,2}}:\d{{2}}.*)'
        match = re.search(pattern, text)
        if match:
            ranges = self._parse_time_ranges(match.group(1))
        return ranges

    def _extract_update_time(self, text: str) -> str:
        """Extract last update time from text content."""
        match = re.search(r'Інформація\s+станом\s+на\s+(\d{2}:\d{2}\s+\d{2}\.\d{2}\.\d{4})', text)
        if match:
            return match.group(1)
        return ""

    def _parse_time_ranges(self, text: str) -> list[dict]:
        """Parse time ranges from text and return list of start/end times."""
        ranges = []
        for part in text.split(','):
            match = re.search(r'(?:з\s+)?(\d{1,2}):(\d{2})\s+до\s+(\d{1,2}):(\d{2})', part.strip())
            if match:
                ranges.append({
                    'start': (int(match.group(1)), int(match.group(2))),
                    'end': (int(match.group(3)), int(match.group(4)))
                })
        return ranges

    def _build_schedule_from_ranges(self, off_ranges: list[dict]) -> list[dict]:
        """Build complete 48-half-hour schedule from outage time ranges."""
        schedule = []
        for i in range(48):
            hour = i // 2
            minute = 0 if i % 2 == 0 else 30
            time_point = (hour, minute)

            is_off = any(
                time_range_contains(
                    time_point[0] * 60 + time_point[1],
                    r['start'][0] * 60 + r['start'][1],
                    r['end'][0] * 60 + r['end'][1]
                )
                for r in off_ranges
            )

            end_hour = hour if minute == 0 else hour + 1
            end_minute = 30 if minute == 0 else 0
            if end_hour == 24:
                end_hour = 24

            schedule.append({
                'time_range': f"{hour:02d}:{minute:02d} - {end_hour:02d}:{end_minute:02d}",
                'status': 'off' if is_off else 'on'
            })
        return schedule

    def _get_current_status(self, off_ranges: list[dict]) -> str:
        """Get current power status based on outage ranges."""
        now = datetime.now()
        current_time = (now.hour, now.minute)

        for off_range in off_ranges:
            if time_range_contains(
                current_time[0] * 60 + current_time[1],
                off_range['start'][0] * 60 + off_range['start'][1],
                off_range['end'][0] * 60 + off_range['end'][1]
            ):
                return 'Світла немає'
        return 'Світло є'