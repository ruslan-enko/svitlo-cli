import requests
from datetime import datetime
from typing import Dict, List, Optional
import re
import logging

try:
    from utils import handle_async_errors
except ImportError:
    def handle_async_errors(func):
        return func


class ScheduleFetcher:
    """Handles fetching power outage schedule data from the website"""
    BASE_URL = "https://poweron.loe.lviv.ua"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @handle_async_errors
    async def fetch_group_schedule(self, group: str) -> Dict:
        """Fetch power outage schedule for a specific group"""
        try:
            from bs4 import BeautifulSoup
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(self.BASE_URL, wait_until='networkidle', timeout=30000)
                html_content = await page.content()
                await browser.close()

            schedule_data = self._parse_main_page(html_content, group)
            self.logger.info(f"Successfully fetched schedule for group {group}")

            return {
                'success': True,
                'group': group,
                'data': schedule_data,
                'updated': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to fetch schedule for group {group}: {e}")
            mock_data = self._get_mock_schedule(group)
            mock_data['is_mock'] = True
            return {
                'success': False,
                'error': str(e),
                'group': group,
                'data': mock_data
            }

    def _parse_main_page(self, html: str, target_group: str) -> Dict:
        """Parse the main page HTML to extract schedule information"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        text_div = soup.select_one('.power-off__text')
        full_text = text_div.get_text() if text_div else soup.get_text()
        
        # Get full page text for next day parsing (second schedule is in different div)
        full_page_text = soup.get_text()

        schedule_date = self._extract_schedule_date(full_text)
        update_time = self._extract_update_time(full_text)
        
        pattern = rf'Група\s+{re.escape(target_group)}\.\s*Електроенергії\s*немає\s*з\s*([^\.]+)\.'
        match = re.search(pattern, full_text)

        if match:
            time_ranges = match.group(1).strip()
            off_ranges = self._parse_time_ranges(time_ranges)
            schedule = self._build_schedule_from_ranges(off_ranges)
            current_status = self._get_current_status(off_ranges)
            
            # Try to extract next day schedule using full page text
            next_day_data = self._extract_next_day_schedule(full_page_text, target_group)
            
            # Calculate next event time
            from datetime import datetime
            now = datetime.now()
            now_minutes = now.hour * 60 + now.minute
            
            next_event_text = 'Немає запланованих змін'
            for off_range in off_ranges:
                start_min = off_range['start'][0] * 60 + off_range['start'][1]
                end_min = off_range['end'][0] * 60 + off_range['end'][1]
                
                if start_min > now_minutes:
                    # Next outage will start
                    next_event_text = f"Наступне відключення о {off_range['start'][0]:02d}:{off_range['start'][1]:02d}"
                    break
                elif start_min <= now_minutes < end_min:
                    # Currently in outage, next event is when light comes back
                    next_event_text = f"Світло з'явиться о {off_range['end'][0]:02d}:{off_range['end'][1]:02d}"
                    break
            
            result = {
                'schedule': schedule,
                'current_status': current_status,
                'next_event': next_event_text,
                'is_mock': False,
                'schedule_date': schedule_date,
                'update_time': update_time
            }
            
            # Add next day schedule if available
            if next_day_data:
                result['next_day_schedule'] = next_day_data['schedule']
                result['next_day_date'] = next_day_data['schedule_date']
                result['next_day_event'] = next_day_data.get('next_event', '')
                result['has_next_day'] = True
            else:
                result['has_next_day'] = False

            return result

        mock_data = self._get_mock_schedule(target_group)
        mock_data['is_mock'] = True
        mock_data['schedule_date'] = schedule_date
        return mock_data

    def _extract_schedule_date(self, text: str) -> str:
        """Extract schedule date from text content"""
        match = re.search(r'Графік\s+погодинних\s+відключень\s+на\s+(\d{2}\.\d{2}\.\d{4})', text)
        if match:
            date_str = match.group(1)
            day, month, year = date_str.split('.')
            months_ua = [
                'січень', 'лютий', 'березень', 'квітень', 'травень', 'червень',
                'липень', 'серпень', 'вересень', 'жовтень', 'листопад', 'грудень'
            ]
            month_name = months_ua[int(month) - 1]
            return f"{day} {month_name} {year} року"
        return ""
    
    def _extract_next_day_date(self, text: str) -> str:
        """Extract next day schedule date from text content (if available)"""
        # Look for the second date pattern after the first schedule
        # Pattern: "Графік погодинних відключень на DD.MM.YYYY" appears again
        pattern = r'Графік\s+погодинних\s+відключень\s+на\s+(\d{2}\.\d{2}\.\d{4})'
        matches = re.findall(pattern, text)
        
        if len(matches) >= 2:
            # Second date is the next day schedule
            date_str = matches[1]
            day, month, year = date_str.split('.')
            months_ua = [
                'січень', 'лютий', 'березень', 'квітень', 'травень', 'червень',
                'липень', 'серпень', 'вересень', 'жовтень', 'листопад', 'грудень'
            ]
            month_name = months_ua[int(month) - 1]
            return f"{day} {month_name} {year} року"
        return ""
    
    def _extract_update_time(self, text: str) -> str:
        """Extract last update time from text content"""
        match = re.search(r'Інформація\s+станом\s+на\s+(\d{2}:\d{2}\s+\d{2}\.\d{2}\.\d{4})', text)
        if match:
            return match.group(1)
        return ""
    
    def _extract_next_day_schedule(self, text: str, target_group: str, current_off_ranges: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Extract next day schedule for target group if available"""
        # Find the position of the second date header (next day)
        # Looking for "Графік погодинних відключень на DD.MM.YYYY" where DD != first date
        import re
        
        # First, find all date headers with their positions
        date_pattern = r'Графік\s+погодинних\s+відключень\s+на\s+(\d{2}\.\d{2}\.\d{4})'
        matches = list(re.finditer(date_pattern, text))
        
        if len(matches) < 2:
            return None
        
        # Get the second date header position
        second_date_match = matches[1]
        next_day_date_str = second_date_match.group(1)
        
        # Convert to Ukrainian format
        day, month, year = next_day_date_str.split('.')
        months_ua = [
            'січень', 'лютий', 'березень', 'квітень', 'травень', 'червень',
            'липень', 'серпень', 'вересень', 'жовтень', 'листопад', 'грудень'
        ]
        month_name = months_ua[int(month) - 1]
        next_day_date = f"{day} {month_name} {year} року"
        
        # Get text from second date header onwards
        second_date_start = second_date_match.start()
        next_day_text = text[second_date_start:]
        
        # Find the target group in the next day text
        pattern = rf'Група\s+{re.escape(target_group)}\.\s*Електроенергії\s*немає\s*з\s*([^\.]+)\.'
        match = re.search(pattern, next_day_text)
        
        if match:
            time_ranges = match.group(1).strip()
            off_ranges = self._parse_time_ranges(time_ranges)
            schedule = self._build_schedule_from_ranges(off_ranges)
            
            # For next day, first event is always the first outage
            if off_ranges:
                first_out = off_ranges[0]
                next_event_text = f"Перше відключення о {first_out['start'][0]:02d}:{first_out['start'][1]:02d}"
            else:
                next_event_text = 'Немає запланованих змін'
            
            return {
                'schedule': schedule,
                'schedule_date': next_day_date,
                'has_next_day': True,
                'next_event': next_event_text
            }
        
        return None

    def _parse_time_ranges(self, text: str) -> List[Dict]:
        """Parse time ranges from text and return list of start/end times"""
        ranges = []
        for part in text.split(','):
            match = re.search(r'(?:з\s+)?(\d{1,2}):(\d{2})\s+до\s+(\d{1,2}):(\d{2})', part.strip())
            if match:
                ranges.append({
                    'start': (int(match.group(1)), int(match.group(2))),
                    'end': (int(match.group(3)), int(match.group(4)))
                })
        return ranges

    def _build_schedule_from_ranges(self, off_ranges: List[Dict]) -> List[Dict]:
        """Build complete schedule from outage time ranges"""
        schedule = []
        for i in range(48):
            hour = i // 2
            minute = 0 if i % 2 == 0 else 30
            time_point = (hour, minute)

            is_off = any(
                self._is_time_in_range(time_point, r['start'], r['end'])
                for r in off_ranges
            )

            schedule.append({
                'time_range': f"{hour:02d}:{minute:02d} - {hour:02d}:{minute:02d}",
                'status': 'off' if is_off else 'on'
            })
        return schedule

    def _is_time_in_range(self, time: tuple, start: tuple, end: tuple) -> bool:
        """Check if a specific time falls within a range"""
        time_min = time[0] * 60 + time[1]
        start_min = start[0] * 60 + start[1]
        end_min = end[0] * 60 + end[1]

        if start_min < end_min:
            return start_min <= time_min < end_min
        elif start_min > end_min:
            return time_min >= start_min or time_min < end_min
        return False

    def _get_current_status(self, off_ranges: List[Dict]) -> str:
        """Get current power status based on outage ranges"""
        now = datetime.now()
        current_time = (now.hour, now.minute)

        for off_range in off_ranges:
            if self._is_time_in_range(current_time, off_range['start'], off_range['end']):
                return 'Світла немає'
        return 'Світло є'

    def _get_mock_schedule(self, group: str) -> Dict:
        """Generate mock schedule data for testing/fallback purposes"""
        mock_data = {
            '1.1': '00:00 до 02:00, з 05:30 до 09:00, з 12:30 до 16:00, з 23:00 до 24:00',
            '1.2': '02:00 до 05:30, з 09:00 до 11:30, з 16:00 до 19:30',
            '2.1': '02:00 до 05:30, з 09:00 до 12:30, з 16:00 до 18:00',
            '2.2': '05:30 до 09:00, з 12:30 до 16:00, з 19:30 до 23:00',
            '3.1': '05:30 до 09:00, з 12:30 до 16:00, з 19:30 до 23:00',
            '3.2': '00:00 до 02:00, з 09:00 до 12:30, з 16:00 до 20:00',
            '4.1': '08:00 до 12:30, з 16:00 до 19:30, з 23:00 до 24:00',
            '4.2': '00:00 до 02:00, з 09:00 до 12:30, з 16:00 до 19:30, з 23:00 до 24:00',
            '5.1': '02:00 до 05:30, з 15:00 до 17:30, з 19:30 до 23:00',
            '5.2': '06:00 до 09:00, з 12:30 до 16:00, з 19:30 до 23:00',
            '6.1': '00:00 до 02:30, з 09:30 до 13:00, з 16:30 до 20:00',
            '6.2': '02:00 до 05:30, з 09:00 до 12:30, з 16:00 до 19:30',
        }

        time_ranges = mock_data.get(group, '')
        off_ranges = self._parse_time_ranges(time_ranges)
        schedule = self._build_schedule_from_ranges(off_ranges)
        current_status = self._get_current_status(off_ranges)

        return {
            'schedule': schedule,
            'current_status': current_status,
            'next_event': 'Немає запланованих змін'
        }