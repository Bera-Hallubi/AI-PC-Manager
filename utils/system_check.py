"""
System Requirements Checker for AI PC Manager
Validates system requirements and dependencies
"""

import os
import sys
import platform
import subprocess
import importlib
from typing import Dict, List, Tuple, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class SystemChecker:
    """System requirements and dependency checker"""
    
    def __init__(self):
        self.requirements = {
            'python': {
                'min_version': (3, 8),
                'current_version': sys.version_info[:2],
                'required': True
            },
            'ram': {
                'min_gb': 8,
                'recommended_gb': 16,
                'required': True
            },
            'storage': {
                'min_gb': 2,
                'recommended_gb': 5,
                'required': True
            }
        }
        
        self.python_packages = [
            'PyQt6',
            'psutil',
            'pyyaml',
            'loguru',
            'torch',
            'transformers',
            'faster-whisper',
            'speechrecognition',
            'pyaudio',
            'sounddevice',
            'pyttsx3',
            'pyautogui',
            'keyboard',
            'mouse',
            'chromadb',
            'sentence-transformers'
        ]
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """Check all system requirements"""
        results = {
            'overall_status': 'pass',
            'python': self._check_python_version(),
            'ram': self._check_ram(),
            'storage': self._check_storage(),
            'packages': self._check_python_packages(),
            'audio': self._check_audio_system(),
            'gpu': self._check_gpu(),
            'recommendations': []
        }
        
        # Determine overall status
        critical_failures = []
        if not results['python']['status']:
            critical_failures.append('Python version')
        if not results['ram']['status']:
            critical_failures.append('RAM')
        if not results['storage']['status']:
            critical_failures.append('Storage')
        
        if critical_failures:
            results['overall_status'] = 'fail'
            results['critical_failures'] = critical_failures
        elif not results['packages']['all_installed']:
            results['overall_status'] = 'warning'
        
        return results
    
    def _check_python_version(self) -> Dict[str, Any]:
        """Check Python version"""
        current = sys.version_info[:2]
        required = self.requirements['python']['min_version']
        
        status = current >= required
        message = f"Python {current[0]}.{current[1]}"
        
        if status:
            message += " ✅"
        else:
            message += f" ❌ (Requires {required[0]}.{required[1]}+)"
        
        return {
            'status': status,
            'current': current,
            'required': required,
            'message': message
        }
    
    def _check_ram(self) -> Dict[str, Any]:
        """Check available RAM"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            
            min_required = self.requirements['ram']['min_gb']
            recommended = self.requirements['ram']['recommended_gb']
            
            status = total_gb >= min_required
            message = f"{total_gb:.1f}GB RAM"
            
            if total_gb >= recommended:
                message += " ✅ (Recommended)"
            elif status:
                message += " ⚠️ (Minimum)"
            else:
                message += f" ❌ (Requires {min_required}GB+)"
            
            return {
                'status': status,
                'total_gb': total_gb,
                'min_required': min_required,
                'recommended': recommended,
                'message': message
            }
            
        except ImportError:
            return {
                'status': False,
                'message': "Cannot check RAM (psutil not installed)",
                'error': 'psutil_missing'
            }
    
    def _check_storage(self) -> Dict[str, Any]:
        """Check available storage"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            
            min_required = self.requirements['storage']['min_gb']
            recommended = self.requirements['storage']['recommended_gb']
            
            status = free_gb >= min_required
            message = f"{free_gb:.1f}GB free storage"
            
            if free_gb >= recommended:
                message += " ✅ (Recommended)"
            elif status:
                message += " ⚠️ (Minimum)"
            else:
                message += f" ❌ (Requires {min_required}GB+)"
            
            return {
                'status': status,
                'free_gb': free_gb,
                'min_required': min_required,
                'recommended': recommended,
                'message': message
            }
            
        except ImportError:
            return {
                'status': False,
                'message': "Cannot check storage (psutil not installed)",
                'error': 'psutil_missing'
            }
    
    def _check_python_packages(self) -> Dict[str, Any]:
        """Check Python package dependencies"""
        installed_packages = []
        missing_packages = []
        
        for package in self.python_packages:
            try:
                # Handle packages with different import names
                import_name = self._get_import_name(package)
                importlib.import_module(import_name)
                installed_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        all_installed = len(missing_packages) == 0
        message = f"{len(installed_packages)}/{len(self.python_packages)} packages installed"
        
        if all_installed:
            message += " ✅"
        else:
            message += f" ❌ (Missing: {', '.join(missing_packages)})"
        
        return {
            'all_installed': all_installed,
            'installed': installed_packages,
            'missing': missing_packages,
            'total': len(self.python_packages),
            'message': message
        }
    
    def _get_import_name(self, package_name: str) -> str:
        """Get the correct import name for a package"""
        import_mapping = {
            'PyQt6': 'PyQt6',
            'psutil': 'psutil',
            'pyyaml': 'yaml',
            'loguru': 'loguru',
            'torch': 'torch',
            'transformers': 'transformers',
            'faster-whisper': 'faster_whisper',
            'speechrecognition': 'speech_recognition',
            'pyaudio': 'pyaudio',
            'sounddevice': 'sounddevice',
            'pyttsx3': 'pyttsx3',
            'pyautogui': 'pyautogui',
            'keyboard': 'keyboard',
            'mouse': 'mouse',
            'chromadb': 'chromadb',
            'sentence-transformers': 'sentence_transformers'
        }
        return import_mapping.get(package_name, package_name)
    
    def _check_audio_system(self) -> Dict[str, Any]:
        """Check audio system availability"""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            p.terminate()
            
            if device_count > 0:
                return {
                    'status': True,
                    'device_count': device_count,
                    'message': f"Audio system available ({device_count} devices) ✅"
                }
            else:
                return {
                    'status': False,
                    'device_count': 0,
                    'message': "No audio devices found ❌"
                }
                
        except ImportError:
            return {
                'status': False,
                'message': "Cannot check audio (pyaudio not installed)",
                'error': 'pyaudio_missing'
            }
        except Exception as e:
            return {
                'status': False,
                'message': f"Audio system error: {str(e)}",
                'error': str(e)
            }
    
    def _check_gpu(self) -> Dict[str, Any]:
        """Check GPU availability"""
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            
            if cuda_available:
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
                message = f"GPU available: {gpu_name} ({gpu_count} device(s)) ✅"
            else:
                message = "No GPU available (CPU only) ⚠️"
            
            return {
                'status': cuda_available,
                'available': cuda_available,
                'device_count': torch.cuda.device_count() if cuda_available else 0,
                'device_name': torch.cuda.get_device_name(0) if cuda_available else None,
                'message': message
            }
            
        except ImportError:
            return {
                'status': False,
                'message': "Cannot check GPU (torch not installed)",
                'error': 'torch_missing'
            }
        except Exception as e:
            return {
                'status': False,
                'message': f"GPU check error: {str(e)}",
                'error': str(e)
            }
    
    def get_installation_commands(self) -> List[str]:
        """Get commands to install missing packages"""
        results = self.check_system_requirements()
        missing_packages = results['packages']['missing']
        
        if not missing_packages:
            return ["All packages are already installed!"]
        
        commands = []
        
        # Basic pip install
        commands.append(f"pip install {' '.join(missing_packages)}")
        
        # Alternative installation methods for problematic packages
        if 'pyaudio' in missing_packages:
            if platform.system() == "Windows":
                commands.append("# For Windows, you might need:")
                commands.append("pip install pipwin")
                commands.append("pipwin install pyaudio")
            else:
                commands.append("# For Linux/Mac, you might need:")
                commands.append("sudo apt-get install portaudio19-dev python3-pyaudio  # Ubuntu/Debian")
                commands.append("brew install portaudio  # macOS")
                commands.append("pip install pyaudio")
        
        if 'PyQt6' in missing_packages:
            commands.append("# Alternative PyQt6 installation:")
            commands.append("pip install PyQt6")
        
        return commands
    
    def print_system_report(self):
        """Print a detailed system report"""
        results = self.check_system_requirements()
        
        print("🔍 AI PC Manager - System Requirements Check")
        print("=" * 50)
        
        # Overall status
        status_icon = "✅" if results['overall_status'] == 'pass' else "❌" if results['overall_status'] == 'fail' else "⚠️"
        print(f"\nOverall Status: {status_icon} {results['overall_status'].upper()}")
        
        # Python version
        print(f"\n🐍 Python: {results['python']['message']}")
        
        # RAM
        print(f"\n🧠 RAM: {results['ram']['message']}")
        
        # Storage
        print(f"\n💾 Storage: {results['storage']['message']}")
        
        # Packages
        print(f"\n📦 Packages: {results['packages']['message']}")
        
        # Audio
        print(f"\n🎤 Audio: {results['audio']['message']}")
        
        # GPU
        print(f"\n🎮 GPU: {results['gpu']['message']}")
        
        # Installation commands if needed
        if not results['packages']['all_installed']:
            print(f"\n🔧 Installation Commands:")
            commands = self.get_installation_commands()
            for cmd in commands:
                print(f"  {cmd}")
        
        # Recommendations
        if results['overall_status'] != 'pass':
            print(f"\n💡 Recommendations:")
            if results['overall_status'] == 'fail':
                print("  - Fix critical failures before running the application")
            if not results['packages']['all_installed']:
                print("  - Install missing packages using the commands above")
            if not results['gpu']['status']:
                print("  - Consider using a GPU for better AI performance")
            if results['ram']['total_gb'] < 16:
                print("  - Consider upgrading RAM for better performance")


def check_requirements():
    """Quick requirements check function"""
    checker = SystemChecker()
    checker.print_system_report()
    return checker.check_system_requirements()


if __name__ == "__main__":
    check_requirements()
