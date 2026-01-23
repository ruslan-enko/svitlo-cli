"""Update checker module for Svitlo CLI"""

import logging
import subprocess
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from packaging import version

from core.config import APP_VERSION, GITHUB_API_URL, UPDATE_CHECK_INTERVAL
from core.preferences import (
    save_last_update_check, get_last_update_check,
    save_latest_version, get_latest_version
)


class UpdateChecker:
    """Handles checking for and performing application updates"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_version = APP_VERSION
        self.latest_version = None
        self.is_update_available = False

    def is_update_check_needed(self) -> bool:
        """Check if enough time has passed since last update check"""
        last_check = get_last_update_check()
        if not last_check:
            return True
        
        last_check_time = datetime.fromisoformat(last_check)
        time_since_check = datetime.now() - last_check_time
        
        return time_since_check.total_seconds() >= UPDATE_CHECK_INTERVAL

    async def check_for_updates(self) -> Dict[str, Any]:
        """
        Check for updates from GitHub API
        
        Returns:
            Dict with keys:
                - 'success': bool
                - 'update_available': bool
                - 'current_version': str
                - 'latest_version': str (if update available)
                - 'download_url': str (if update available)
                - 'error': str (if failed)
        """
        if not self.is_update_check_needed():
            cached_version = get_latest_version()
            if cached_version and cached_version != self.current_version:
                try:
                    if self._compare_versions(self.current_version, cached_version):
                        return {
                            'success': True,
                            'update_available': True,
                            'current_version': self.current_version,
                            'latest_version': cached_version,
                            'download_url': f'https://github.com/ruslan-enko/svitlo-cli/releases/tag/{cached_version}'
                        }
                except Exception as e:
                    self.logger.debug(f"Version comparison failed: {e}")
            
            return {
                'success': True,
                'update_available': False,
                'current_version': self.current_version,
                'latest_version': self.current_version
            }

        try:
            response = requests.get(GITHUB_API_URL, timeout=5)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                return {
                    'success': False,
                    'update_available': False,
                    'error': 'Could not parse version from GitHub'
                }

            # Save the latest version for caching
            save_latest_version(latest_version)
            save_last_update_check(datetime.now().isoformat())
            
            # Compare versions
            update_available = self._compare_versions(self.current_version, latest_version)
            
            self.latest_version = latest_version
            self.is_update_available = update_available
            
            result = {
                'success': True,
                'update_available': update_available,
                'current_version': self.current_version,
                'latest_version': latest_version,
                'download_url': f'https://github.com/ruslan-enko/svitlo-cli/releases/tag/{latest_version}'
            }
            
            if update_available:
                self.logger.info(f"Update available: {self.current_version} -> {latest_version}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to check for updates: {e}")
            return {
                'success': False,
                'update_available': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during update check: {e}")
            return {
                'success': False,
                'update_available': False,
                'error': f'Unexpected error: {str(e)}'
            }

    def _compare_versions(self, current: str, latest: str) -> bool:
        """
        Compare two semantic versions
        
        Returns:
            True if latest is newer than current
        """
        try:
            current_ver = version.parse(current)
            latest_ver = version.parse(latest)
            return latest_ver > current_ver
        except Exception as e:
            self.logger.debug(f"Version comparison error: {e}")
            return False

    async def perform_update(self) -> Dict[str, Any]:
        """
        Perform the actual update by running pip install --upgrade
        
        Returns:
            Dict with keys:
                - 'success': bool
                - 'message': str
        """
        try:
            self.logger.info("Starting update process...")
            
            # Run pip install --upgrade svitlo-cli
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "svitlo-cli"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Update completed successfully")
                return {
                    'success': True,
                    'message': f'✓ Update to v{self.latest_version} completed successfully!\nPlease restart the application.'
                }
            else:
                error_msg = result.stderr or "Unknown error"
                self.logger.error(f"Update failed: {error_msg}")
                return {
                    'success': False,
                    'message': f'✗ Update failed: {error_msg}'
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error("Update timed out")
            return {
                'success': False,
                'message': '✗ Update timed out. Please try again later.'
            }
        except Exception as e:
            self.logger.error(f"Update error: {e}")
            return {
                'success': False,
                'message': f'✗ Update error: {str(e)}'
            }
