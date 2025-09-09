"""
System Controller for AI PC Manager
Handles application management, file operations, and system control
"""

import os
import sys
import json
import subprocess
import psutil
import pyautogui
import keyboard
import mouse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import time
import shutil
import winreg
import platform
import re

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SystemController:
    """Handles system operations and application management"""
    
    def __init__(self):
        self.config = settings.get_system_config()
        self.app_database_path = self.config.get('app_database_path', './data/discovered_apps.json')
        self.search_depth = self.config.get('search_depth', 10)
        self.search_timeout = self.config.get('search_timeout', 30)
        
        # Initialize PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = self.config.get('automation_delay', 0.1)
        
        # Load application database
        self.app_database = self._load_app_database()
        
        # Common application names and their executable names
        self.common_apps = {
            'chrome': ['chrome.exe', 'google chrome'],
            'firefox': ['firefox.exe', 'mozilla firefox'],
            'edge': ['msedge.exe', 'microsoft edge'],
            'notepad': ['notepad.exe'],
            'calculator': ['calc.exe', 'calculator'],
            'explorer': ['explorer.exe', 'file explorer'],
            'task manager': ['taskmgr.exe'],
            'control panel': ['control.exe'],
            'settings': ['ms-settings:'],
            'cmd': ['cmd.exe', 'command prompt'],
            'powershell': ['powershell.exe'],
            'visual studio code': ['code.exe'],
            'visual studio': ['devenv.exe'],
            'word': ['winword.exe', 'microsoft word'],
            'excel': ['excel.exe', 'microsoft excel'],
            'powerpoint': ['powerpnt.exe', 'microsoft powerpoint'],
            'outlook': ['outlook.exe', 'microsoft outlook'],
            'teams': ['teams.exe', 'microsoft teams'],
            'discord': ['discord.exe'],
            'spotify': ['spotify.exe'],
            'steam': ['steam.exe'],
            'vlc': ['vlc.exe'],
            'photoshop': ['photoshop.exe', 'adobe photoshop'],
            'illustrator': ['illustrator.exe', 'adobe illustrator'],
            'premiere': ['premiere pro.exe', 'adobe premiere pro']
        }
    
    def _load_app_database(self) -> Dict[str, Any]:
        """Load discovered applications database"""
        try:
            if os.path.exists(self.app_database_path):
                with open(self.app_database_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading app database: {e}")
            return {}
    
    def _save_app_database(self):
        """Save discovered applications database"""
        try:
            os.makedirs(os.path.dirname(self.app_database_path), exist_ok=True)
            with open(self.app_database_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_database, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving app database: {e}")
    
    def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application by name
        
        Args:
            app_name: Name of the application to open
            
        Returns:
            Dictionary with success status and details
        """
        try:
            app_name_lower = app_name.lower().strip()
            normalized = self._normalize_app_name(app_name_lower)
            # Common friendly aliases
            alias_map = {
                'calculator': 'calc',
                'calc': 'calc',
                'cmd': 'cmd',
                'commandprompt': 'cmd',
                'fileexplorer': 'explorer',
                'explorer': 'explorer',
            }
            alias = alias_map.get(normalized)
            key_for_common = alias if alias else normalized
            
            # First, try to find in common apps
            if key_for_common in self.common_apps:
                return self._launch_common_app(key_for_common)
            # Fuzzy match common apps by containment
            for common_key in self.common_apps.keys():
                if common_key in normalized or normalized in common_key:
                    return self._launch_common_app(common_key)
            
            # Check if we have it in our database
            if normalized in self.app_database:
                return self._launch_from_database(normalized)
            
            # Search for the application
            search_result = self.search_application(normalized)
            if search_result:
                return self._launch_found_app(search_result)
            
            # Try to launch as a command
            return self._launch_as_command(normalized)
            
        except Exception as e:
            logger.error(f"Error opening application {app_name}: {e}")
            return {
                'success': False,
                'message': f"Failed to open {app_name}: {str(e)}",
                'error': str(e)
            }
    
    def _launch_common_app(self, app_name: str) -> Dict[str, Any]:
        """Launch a common application"""
        try:
            app_info = self.common_apps[app_name]
            # Try each candidate executable/name until one works
            candidates: List[str] = app_info if isinstance(app_info, list) else [app_info]
            
            last_error = None
            for executable in candidates:
                try:
                    if executable.endswith('.exe'):
                        subprocess.Popen([executable], shell=True)
                        launched = True
                    elif executable.startswith('ms-') or ':' in executable:
                        os.system(f'start {executable}')
                        launched = True
                    else:
                        # Try via PATH
                        subprocess.Popen([executable], shell=True)
                        launched = True
                    if launched:
                        logger.info(f"Launched common app: {app_name} via {executable}")
                        return {
                            'success': True,
                            'message': f"Opened {app_name}",
                            'app_name': app_name,
                            'method': 'common_app'
                        }
                except Exception as e:
                    last_error = str(e)
                    continue
            
            raise RuntimeError(last_error or "Failed to launch any candidate")
            
        except Exception as e:
            logger.error(f"Error launching common app {app_name}: {e}")
            return {
                'success': False,
                'message': f"Failed to open {app_name}",
                'error': str(e)
            }
    
    def _launch_from_database(self, app_name: str) -> Dict[str, Any]:
        """Launch application from database"""
        try:
            app_info = self.app_database[app_name]
            executable_path = app_info.get('path')
            
            if executable_path and os.path.exists(executable_path):
                subprocess.Popen([executable_path], shell=True)
                logger.info(f"Launched app from database: {app_name}")
                return {
                    'success': True,
                    'message': f"Opened {app_name}",
                    'app_name': app_name,
                    'path': executable_path,
                    'method': 'database'
                }
            else:
                # Path no longer exists, remove from database
                del self.app_database[app_name]
                self._save_app_database()
                return self.search_application(app_name)
                
        except Exception as e:
            logger.error(f"Error launching from database {app_name}: {e}")
            return {
                'success': False,
                'message': f"Failed to open {app_name}",
                'error': str(e)
            }
    
    def _launch_found_app(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """Launch application found through search"""
        try:
            app_path = search_result['path']
            app_name = search_result['name']
            
            # Add to database for future use
            self.app_database[app_name.lower()] = {
                'path': app_path,
                'name': app_name,
                'discovered_at': time.time()
            }
            self._save_app_database()
            
            # Launch the application
            subprocess.Popen([app_path], shell=True)
            
            logger.info(f"Launched found app: {app_name}")
            return {
                'success': True,
                'message': f"Opened {app_name}",
                'app_name': app_name,
                'path': app_path,
                'method': 'search'
            }
            
        except Exception as e:
            logger.error(f"Error launching found app: {e}")
            return {
                'success': False,
                'message': f"Failed to open found application",
                'error': str(e)
            }
    
    def _launch_as_command(self, command: str) -> Dict[str, Any]:
        """Try to launch as a system command"""
        try:
            # Try different ways to execute the command
            result = subprocess.run([command], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Launched as command: {command}")
                return {
                    'success': True,
                    'message': f"Executed command: {command}",
                    'command': command,
                    'method': 'command'
                }
            else:
                return {
                    'success': False,
                    'message': f"Command failed: {command}",
                    'error': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            return {
                'success': False,
                'message': f"Failed to execute command: {command}",
                'error': str(e)
            }
    
    def search_application(self, search_term: str) -> Optional[Dict[str, Any]]:
        """
        Search for applications on the system
        
        Args:
            search_term: Term to search for
            
        Returns:
            Dictionary with app information if found, None otherwise
        """
        try:
            search_term_lower = self._normalize_app_name(search_term)
            
            # Search in common apps first
            for app_name, executables in self.common_apps.items():
                if search_term_lower in app_name or any(search_term_lower in exe.lower() for exe in executables):
                    return {
                        'name': app_name,
                        'path': executables[0],
                        'type': 'common_app'
                    }
            
            # Search in system PATH
            path_result = self._search_in_path(search_term)
            if path_result:
                return path_result
            
            # Search in common installation directories
            install_dirs = [
                r"C:\Program Files",
                r"C:\Program Files (x86)",
                r"C:\Users\{}\AppData\Local\Programs".format(os.getenv('USERNAME', '')),
                r"C:\Users\{}\AppData\Roaming".format(os.getenv('USERNAME', ''))
            ]
            
            for install_dir in install_dirs:
                if os.path.exists(install_dir):
                    result = self._search_in_directory(install_dir, search_term)
                    if result:
                        return result
            
            # Search in Start Menu
            start_menu_result = self._search_start_menu(search_term)
            if start_menu_result:
                return start_menu_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for application {search_term}: {e}")
            return None

    def _normalize_app_name(self, name: str) -> str:
        """Normalize app name by removing punctuation and spaces."""
        cleaned = re.sub(r"[^a-z0-9]+", "", name.lower())
        return cleaned
    
    def _search_in_path(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Search for executable in system PATH"""
        try:
            path_dirs = os.environ.get('PATH', '').split(os.pathsep)
            
            for path_dir in path_dirs:
                if os.path.exists(path_dir):
                    for file in os.listdir(path_dir):
                        if search_term.lower() in file.lower() and file.endswith('.exe'):
                            return {
                                'name': file,
                                'path': os.path.join(path_dir, file),
                                'type': 'path_executable'
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching in PATH: {e}")
            return None
    
    def _search_in_directory(self, directory: str, search_term: str, depth: int = 0) -> Optional[Dict[str, Any]]:
        """Recursively search for executable in directory"""
        try:
            if depth > self.search_depth:
                return None
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if (search_term.lower() in file.lower() and 
                        file.endswith('.exe') and 
                        not file.startswith('.')):
                        
                        full_path = os.path.join(root, file)
                        return {
                            'name': file,
                            'path': full_path,
                            'type': 'directory_search'
                        }
                
                # Limit depth to avoid long searches
                if depth >= self.search_depth:
                    break
                depth += 1
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching in directory {directory}: {e}")
            return None
    
    def _search_start_menu(self, search_term: str) -> Optional[Dict[str, Any]]:
        """Search in Windows Start Menu"""
        try:
            if platform.system() != 'Windows':
                return None
            
            start_menu_paths = [
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
                r"C:\Users\{}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs".format(os.getenv('USERNAME', ''))
            ]
            
            for start_menu_path in start_menu_paths:
                if os.path.exists(start_menu_path):
                    result = self._search_shortcuts(start_menu_path, search_term)
                    if result:
                        return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching Start Menu: {e}")
            return None
    
    def _search_shortcuts(self, directory: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Search for .lnk shortcuts"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if (search_term.lower() in file.lower() and 
                        file.endswith('.lnk')):
                        
                        # Try to resolve the shortcut
                        shortcut_path = os.path.join(root, file)
                        target_path = self._resolve_shortcut(shortcut_path)
                        
                        if target_path and os.path.exists(target_path):
                            return {
                                'name': file.replace('.lnk', ''),
                                'path': target_path,
                                'type': 'shortcut'
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching shortcuts: {e}")
            return None
    
    def _resolve_shortcut(self, shortcut_path: str) -> Optional[str]:
        """Resolve Windows shortcut to target path"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            return shortcut.Targetpath
        except Exception as e:
            logger.error(f"Error resolving shortcut {shortcut_path}: {e}")
            return None
    
    def close_application(self, app_name: str) -> Dict[str, Any]:
        """
        Close an application by name
        
        Args:
            app_name: Name of the application to close
            
        Returns:
            Dictionary with success status and details
        """
        try:
            app_name_lower = app_name.lower().strip()
            closed_processes = []
            
            # Find processes matching the app name
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    proc_exe = proc.info['exe']
                    
                    # Check if process name matches
                    if (app_name_lower in proc_name or 
                        (proc_exe and app_name_lower in os.path.basename(proc_exe).lower())):
                        
                        proc.terminate()
                        closed_processes.append(proc.info['name'])
                        logger.info(f"Closed process: {proc.info['name']}")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if closed_processes:
                return {
                    'success': True,
                    'message': f"Closed {len(closed_processes)} process(es): {', '.join(closed_processes)}",
                    'closed_processes': closed_processes
                }
            else:
                return {
                    'success': False,
                    'message': f"No running processes found for {app_name}",
                    'closed_processes': []
                }
                
        except Exception as e:
            logger.error(f"Error closing application {app_name}: {e}")
            return {
                'success': False,
                'message': f"Failed to close {app_name}: {str(e)}",
                'error': str(e)
            }
    
    def take_screenshot(self, filename: str = None) -> Dict[str, Any]:
        """
        Take a screenshot of the current screen
        
        Args:
            filename: Optional filename for the screenshot
            
        Returns:
            Dictionary with success status and file path
        """
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # Ensure screenshots directory exists
            screenshots_dir = os.path.join(settings.get('data.base_path', './data'), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            
            filepath = os.path.join(screenshots_dir, filename)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            return {
                'success': True,
                'message': f"Screenshot saved as {filename}",
                'filepath': filepath,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {
                'success': False,
                'message': f"Failed to take screenshot: {str(e)}",
                'error': str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        
        Returns:
            Dictionary with system information
        """
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024**3)  # GB
            memory_used = memory.used / (1024**3)    # GB
            memory_percent = memory.percent
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024**3)      # GB
            disk_used = disk.used / (1024**3)        # GB
            disk_percent = (disk.used / disk.total) * 100
            
            # System information
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Running processes
            process_count = len(psutil.pids())
            
            return {
                'success': True,
                'system_info': {
                    'platform': platform.platform(),
                    'processor': platform.processor(),
                    'architecture': platform.architecture()[0],
                    'hostname': platform.node(),
                    'cpu': {
                        'count': cpu_count,
                        'usage_percent': cpu_percent,
                        'frequency_mhz': cpu_freq.current if cpu_freq else 'N/A'
                    },
                    'memory': {
                        'total_gb': round(memory_total, 2),
                        'used_gb': round(memory_used, 2),
                        'usage_percent': memory_percent
                    },
                    'disk': {
                        'total_gb': round(disk_total, 2),
                        'used_gb': round(disk_used, 2),
                        'usage_percent': round(disk_percent, 2)
                    },
                    'uptime_seconds': int(uptime),
                    'uptime_hours': round(uptime / 3600, 2),
                    'process_count': process_count,
                    'boot_time': time.ctime(boot_time)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'success': False,
                'message': f"Failed to get system information: {str(e)}",
                'error': str(e)
            }
    
    def search_files(self, search_term: str, search_path: str = None) -> Dict[str, Any]:
        """
        Search for files on the system
        
        Args:
            search_term: Term to search for
            search_path: Optional specific path to search in
            
        Returns:
            Dictionary with search results
        """
        try:
            if not search_path:
                # Search in common directories
                search_paths = [
                    os.path.expanduser("~"),
                    "C:\\",
                    "D:\\" if os.path.exists("D:\\") else None
                ]
                search_paths = [p for p in search_paths if p and os.path.exists(p)]
            else:
                search_paths = [search_path]
            
            results = []
            search_term_lower = search_term.lower()
            
            for search_path in search_paths:
                if os.path.exists(search_path):
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            if search_term_lower in file.lower():
                                file_path = os.path.join(root, file)
                                try:
                                    file_size = os.path.getsize(file_path)
                                    results.append({
                                        'name': file,
                                        'path': file_path,
                                        'size_bytes': file_size,
                                        'size_mb': round(file_size / (1024**2), 2),
                                        'directory': root
                                    })
                                except OSError:
                                    continue
                        
                        # Limit search depth
                        if len(root.split(os.sep)) - len(search_path.split(os.sep)) > self.search_depth:
                            dirs.clear()
            
            # Sort by relevance (exact matches first, then by name similarity)
            results.sort(key=lambda x: (
                search_term_lower not in x['name'].lower(),
                x['name'].lower()
            ))
            
            return {
                'success': True,
                'message': f"Found {len(results)} files matching '{search_term}'",
                'results': results[:50],  # Limit to 50 results
                'total_found': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {
                'success': False,
                'message': f"Failed to search files: {str(e)}",
                'error': str(e)
            }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Save app database
            self._save_app_database()
            logger.info("System Controller cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global system controller instance
system_controller = SystemController()
