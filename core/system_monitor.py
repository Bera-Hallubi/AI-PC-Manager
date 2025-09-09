"""
System Monitor for AI PC Manager
Provides real-time system monitoring and performance metrics
"""

import os
import time
import psutil
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json
from pathlib import Path

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SystemMonitor:
    """Real-time system monitoring and performance tracking"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        self.metrics_history = []
        self.max_history = 1000  # Keep last 1000 data points
        
        # Monitoring intervals (optimized for UI performance)
        self.cpu_interval = 5.0  # seconds (increased for better performance)
        self.memory_interval = 5.0
        self.disk_interval = 20.0  # Much less frequent disk checks
        self.network_interval = 10.0
        self.process_interval = 30.0  # Much less frequent process checks
        
        # Performance thresholds (adjusted to reduce false alerts)
        self.cpu_threshold = 85.0  # %
        self.memory_threshold = 90.0  # %
        self.disk_threshold = 95.0  # % (increased from 90% to reduce alerts)
        self.temperature_threshold = 80.0  # °C
        
        # Data storage
        self.data_path = os.path.join(settings.get('data.base_path', './data'), 'monitoring')
        os.makedirs(self.data_path, exist_ok=True)
        
        # Performance optimization: caching
        self._cached_metrics = None
        self._cache_time = 0
        self._cache_duration = 2.0  # Cache for 2 seconds
    
    def start_monitoring(self, callback: Callable[[Dict[str, Any]], None] = None):
        """
        Start system monitoring
        
        Args:
            callback: Function to call with monitoring data
        """
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        if callback:
            self.callbacks.append(callback)
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_cpu_check = 0
        last_memory_check = 0
        last_disk_check = 0
        last_network_check = 0
        last_process_check = 0
        
        while self.monitoring:
            try:
                current_time = time.time()
                metrics = {}
                
                # CPU monitoring
                if current_time - last_cpu_check >= self.cpu_interval:
                    metrics.update(self._get_cpu_metrics())
                    last_cpu_check = current_time
                
                # Memory monitoring
                if current_time - last_memory_check >= self.memory_interval:
                    metrics.update(self._get_memory_metrics())
                    last_memory_check = current_time
                
                # Disk monitoring
                if current_time - last_disk_check >= self.disk_interval:
                    metrics.update(self._get_disk_metrics())
                    last_disk_check = current_time
                
                # Network monitoring
                if current_time - last_network_check >= self.network_interval:
                    metrics.update(self._get_network_metrics())
                    last_network_check = current_time
                
                # Process monitoring
                if current_time - last_process_check >= self.process_interval:
                    metrics.update(self._get_process_metrics())
                    last_process_check = current_time
                
                # Add timestamp
                metrics['timestamp'] = current_time
                metrics['datetime'] = datetime.now().isoformat()
                
                # Store metrics
                self._store_metrics(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logger.error(f"Error in monitoring callback: {e}")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = cpu_freq.current if cpu_freq else None
            cpu_freq_max = cpu_freq.max if cpu_freq else None
            
            # CPU count
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = None
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'usage_per_core': cpu_per_core,
                    'frequency_mhz': cpu_freq_current,
                    'frequency_max_mhz': cpu_freq_max,
                    'count_physical': cpu_count,
                    'count_logical': cpu_count_logical,
                    'load_average': load_avg
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return {}
    
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory performance metrics"""
        try:
            # Virtual memory
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024**3)  # GB
            memory_available = memory.available / (1024**3)  # GB
            memory_used = memory.used / (1024**3)  # GB
            memory_percent = memory.percent
            
            # Swap memory
            swap = psutil.swap_memory()
            swap_total = swap.total / (1024**3)  # GB
            swap_used = swap.used / (1024**3)  # GB
            swap_percent = swap.percent
            
            return {
                'memory': {
                    'total_gb': round(memory_total, 2),
                    'available_gb': round(memory_available, 2),
                    'used_gb': round(memory_used, 2),
                    'usage_percent': memory_percent,
                    'swap_total_gb': round(swap_total, 2),
                    'swap_used_gb': round(swap_used, 2),
                    'swap_percent': swap_percent
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return {}
    
    def _get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk performance metrics"""
        try:
            disk_metrics = {}
            
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # Skip network drives and special filesystems
                    if 'cdrom' in partition.opts or partition.fstype == '':
                        continue
                    
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_metrics[partition.device] = {
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'usage_percent': round((usage.used / usage.total) * 100, 2)
                    }
                    
                except PermissionError:
                    # Skip partitions we can't access
                    continue
            
            # Get disk I/O statistics
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    disk_metrics['io'] = {
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count,
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_time_ms': disk_io.read_time,
                        'write_time_ms': disk_io.write_time
                    }
            except Exception as e:
                logger.debug(f"Could not get disk I/O stats: {e}")
            
            return {'disk': disk_metrics}
            
        except Exception as e:
            logger.error(f"Error getting disk metrics: {e}")
            return {}
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network performance metrics"""
        try:
            network_metrics = {}
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            if net_io:
                network_metrics['total'] = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errin': net_io.errin,
                    'errout': net_io.errout,
                    'dropin': net_io.dropin,
                    'dropout': net_io.dropout
                }
            
            # Get per-interface statistics
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io_per_nic.items():
                network_metrics[interface] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errin': stats.errin,
                    'errout': stats.errout,
                    'dropin': stats.dropin,
                    'dropout': stats.dropout
                }
            
            # Get network connections
            try:
                connections = psutil.net_connections()
                network_metrics['connections'] = {
                    'total': len(connections),
                    'established': len([c for c in connections if c.status == 'ESTABLISHED']),
                    'listening': len([c for c in connections if c.status == 'LISTEN'])
                }
            except Exception as e:
                logger.debug(f"Could not get network connections: {e}")
            
            return {'network': network_metrics}
            
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {}
    
    def _get_process_metrics(self) -> Dict[str, Any]:
        """Get process performance metrics with Windows permission handling"""
        try:
            # Get all processes with error handling for Windows permissions
            processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                    try:
                        proc_info = proc.info
                        # Only include processes we can access
                        if proc_info.get('name') and proc_info.get('pid'):
                            processes.append(proc_info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                        # Skip processes we can't access
                        continue
                    except Exception:
                        # Skip any other errors
                        continue
            except Exception as e:
                logger.warning(f"Process monitoring limited due to permissions: {e}")
                return {
                    'top_cpu_processes': [],
                    'top_memory_processes': [],
                    'total_processes': 0
                }
            
            # Sort by CPU usage
            processes_by_cpu = sorted(processes, key=lambda p: p.get('cpu_percent', 0) or 0, reverse=True)
            top_cpu_processes = [
                {
                    'pid': p.get('pid', 0),
                    'name': p.get('name', 'unknown'),
                    'cpu_percent': p.get('cpu_percent', 0) or 0,
                    'memory_percent': p.get('memory_percent', 0) or 0,
                    'status': p.get('status', 'unknown')
                }
                for p in processes_by_cpu[:10]
            ]
            
            # Sort by memory usage
            processes_by_memory = sorted(processes, key=lambda p: p.get('memory_percent', 0) or 0, reverse=True)
            top_memory_processes = [
                {
                    'pid': p.get('pid', 0),
                    'name': p.get('name', 'unknown'),
                    'cpu_percent': p.get('cpu_percent', 0) or 0,
                    'memory_percent': p.get('memory_percent', 0) or 0,
                    'status': p.get('status', 'unknown')
                }
                for p in processes_by_memory[:10]
            ]
            
            # Process counts by status
            status_counts = {}
            for process in processes:
                status = process.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'processes': {
                    'total_count': len(processes),
                    'top_cpu': top_cpu_processes,
                    'top_memory': top_memory_processes,
                    'status_counts': status_counts
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting process metrics: {e}")
            return {}
    
    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in history"""
        self.metrics_history.append(metrics)
        
        # Keep only recent history
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts"""
        try:
            alerts = []
            
            # CPU alert
            if 'cpu' in metrics and 'usage_percent' in metrics['cpu']:
                cpu_usage = metrics['cpu']['usage_percent']
                if cpu_usage > self.cpu_threshold:
                    alerts.append({
                        'type': 'cpu_high',
                        'message': f"High CPU usage: {cpu_usage:.1f}%",
                        'value': cpu_usage,
                        'threshold': self.cpu_threshold
                    })
            
            # Memory alert
            if 'memory' in metrics and 'usage_percent' in metrics['memory']:
                memory_usage = metrics['memory']['usage_percent']
                if memory_usage > self.memory_threshold:
                    alerts.append({
                        'type': 'memory_high',
                        'message': f"High memory usage: {memory_usage:.1f}%",
                        'value': memory_usage,
                        'threshold': self.memory_threshold
                    })
            
            # Disk alert
            if 'disk' in metrics:
                for device, disk_info in metrics['disk'].items():
                    if isinstance(disk_info, dict) and 'usage_percent' in disk_info:
                        disk_usage = disk_info['usage_percent']
                        if disk_usage > self.disk_threshold:
                            alerts.append({
                                'type': 'disk_high',
                                'message': f"High disk usage on {device}: {disk_usage:.1f}%",
                                'value': disk_usage,
                                'threshold': self.disk_threshold,
                                'device': device
                            })
            
            # Log alerts
            for alert in alerts:
                logger.warning(f"Performance Alert: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics with caching"""
        try:
            import time
            current_time = time.time()
            
            # Return cached metrics if still valid
            if (self._cached_metrics is not None and 
                current_time - self._cache_time < self._cache_duration):
                return self._cached_metrics
            
            # Get fresh metrics
            metrics = {}
            metrics.update(self._get_cpu_metrics())
            metrics.update(self._get_memory_metrics())
            metrics.update(self._get_disk_metrics())
            metrics.update(self._get_network_metrics())
            metrics.update(self._get_process_metrics())
            
            metrics['timestamp'] = current_time
            metrics['datetime'] = datetime.now().isoformat()
            
            # Cache the results
            self._cached_metrics = metrics
            self._cache_time = current_time
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return {}
    
    def get_metrics_history(self, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics history for specified duration"""
        try:
            cutoff_time = time.time() - (duration_minutes * 60)
            return [m for m in self.metrics_history if m.get('timestamp', 0) > cutoff_time]
            
        except Exception as e:
            logger.error(f"Error getting metrics history: {e}")
            return []
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of current system status"""
        try:
            metrics = self.get_current_metrics()
            
            # Calculate overall health score
            health_score = 100
            
            if 'cpu' in metrics and 'usage_percent' in metrics['cpu']:
                cpu_usage = metrics['cpu']['usage_percent']
                health_score -= min(cpu_usage * 0.3, 30)  # Max 30 points deduction
            
            if 'memory' in metrics and 'usage_percent' in metrics['memory']:
                memory_usage = metrics['memory']['usage_percent']
                health_score -= min(memory_usage * 0.2, 20)  # Max 20 points deduction
            
            if 'disk' in metrics:
                max_disk_usage = 0
                for device, disk_info in metrics['disk'].items():
                    if isinstance(disk_info, dict) and 'usage_percent' in disk_info:
                        max_disk_usage = max(max_disk_usage, disk_info['usage_percent'])
                health_score -= min(max_disk_usage * 0.1, 10)  # Max 10 points deduction
            
            health_score = max(0, health_score)
            
            # Determine status
            if health_score >= 80:
                status = "Excellent"
            elif health_score >= 60:
                status = "Good"
            elif health_score >= 40:
                status = "Fair"
            else:
                status = "Poor"
            
            return {
                'health_score': round(health_score, 1),
                'status': status,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting system summary: {e}")
            return {
                'health_score': 0,
                'status': 'Unknown',
                'error': str(e)
            }
    
    def save_metrics_to_file(self, filename: str = None) -> bool:
        """Save current metrics to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"metrics_{timestamp}.json"
            
            filepath = os.path.join(self.data_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.metrics_history, f, indent=2, default=str)
            
            logger.info(f"Metrics saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_monitoring()
            logger.info("System monitor cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global system monitor instance
system_monitor = SystemMonitor()
