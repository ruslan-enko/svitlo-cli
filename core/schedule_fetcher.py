from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
import logging

try:
    from core.utils import handle_async_errors
except ImportError:
    def handle_async_errors(func):
        return func


from core.config import AVAILABLE_GROUPS, MONTHS_UA
from core.utils import time_range_contains
from core.data_manager import save_last_data, load_last_data

class ScheduleFetcher:
    """Handles fetching power outage schedule data from the website"""
    BASE_URL = "https://poweron.loe.lviv.ua"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @handle_async_errors
    async def fetch_schedules(self) -> Dict:
        """Fetch power outage schedules for all groups"""
        html_content = ""
        
        try:
            from bs4 import BeautifulSoup
            from playwright.async_api import async_playwright

            browser = None
            page = None
            
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    try:
                        await page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=30000)
                        # Wait a bit for JavaScript to execute
                        await page.wait_for_timeout(2000)
                        html_content = await page.content()
                    except Exception as e:
                        self.logger.error(f"Page load error: {e}")
                        raise
                    finally:
                        if page:
                            await page.close()
                        if browser:
                            await browser.close()
                
                schedules = {}
                for group in AVAILABLE_GROUPS:
                    schedules[group] = self._parse_main_page(html_content, group)
                
                self.logger.info("Successfully fetched schedules for all groups")

                result = {
                    'success': True,
                    'data': schedules,
                    'updated': datetime.now().isoformat()
                }
                
                # Save to persistent storage
                save_last_data(result)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Playwright error: {e}")
                raise
                
        except Exception as e:
            self.logger.error(f"Failed to fetch schedules: {e}")
            
            # Try to load last saved data
            last_data = load_last_data()
            if last_data:
                self.logger.info("Loaded last saved data from storage")
                return {
                    'success': False,
                    'is_stale': True,
                    'data': last_data.get('data', {}),
                    'updated': last_data.get('updated', ''),
                    'error': f"Помилка завантаження. Використовуємо збережені дані: {str(e)}"
                }
                
            return {
                'success': False,
                'error': f"Помилка завантаження і немає збережених даних: {str(e)}",
                'data': {}
            }

    def _parse_main_page(self, html: str, target_group: str) -> Dict:
        """Parse the main page HTML to extract schedule information"""
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
        
        from core.config import MONTHS_UA
        today_formatted = f"{now.day} {MONTHS_UA[now.month - 1]} {now.year}"
        
        # Default initialization for today (no outages)
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

    def _extract_schedule_date(self, text: str) -> str:
        """Extract schedule date from text content"""
        match = re.search(r'Графік\s+погодинних\s+відключень\s+на\s+(\d{2}\.\d{2}\.\d{4})', text)
        if match:
            date_str = match.group(1)
            day, month, year = date_str.split('.')
            month_name = MONTHS_UA[int(month) - 1]
            return f"{day} {month_name} {year}"
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
        month_name = MONTHS_UA[int(month) - 1]
        next_day_date = f"{day} {month_name} {year}"
        
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
                'next_event': next_event_text,
                'off_ranges': off_ranges
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
                end_hour = 24  # Keep as 24:00 for midnight end

            schedule.append({
                'time_range': f"{hour:02d}:{minute:02d} - {end_hour:02d}:{end_minute:02d}",
                'status': 'off' if is_off else 'on'
            })
        return schedule

    def _get_current_status(self, off_ranges: List[Dict]) -> str:
        """Get current power status based on outage ranges"""
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

        return None