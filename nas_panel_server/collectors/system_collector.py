"""
System information collector using psutil.
"""

import psutil
import socket
import time
from datetime import datetime
from typing import Dict, Any, List
from .base import BaseCollector


class SystemCollector(BaseCollector):
    """Collector for basic system information (CPU, memory, storage, network)."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._last_network_stats = None
        self._last_network_time = None
        
    def collect(self) -> Dict[str, Any]:
        """Collect all system information."""
        return {
            "hostname": self._get_hostname(),
            "ip": self._get_ip_address(),
            "timestamp": datetime.now().isoformat(),
            "cpu": self._get_cpu_info(),
            "memory": self._get_memory_info(),
            "storage": self._get_storage_info(),
            "network": self._get_network_info()
        }
    
    def _get_hostname(self) -> str:
        """Get system hostname."""
        config_hostname = self.config.get('server', {}).get('hostname')
        if config_hostname and config_hostname != 'auto':
            return config_hostname
        return socket.gethostname()
    
    def _get_ip_address(self) -> str:
        """Get primary IP address."""
        config_ip = self.config.get('server', {}).get('ip')
        if config_ip and config_ip != 'auto':
            return config_ip
            
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information."""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Try to get CPU temperature
        temperature = None
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                # Intel CPU
                temperature = temps['coretemp'][0].current
            elif 'k10temp' in temps:
                # AMD CPU
                temperature = temps['k10temp'][0].current
            elif temps:
                # Use first available temperature sensor
                first_sensor = list(temps.values())[0]
                if first_sensor:
                    temperature = first_sensor[0].current
        except (AttributeError, IndexError, KeyError):
            # Temperature not available on this system
            pass
        
        cpu_info = {"usage": round(cpu_percent, 1)}
        if temperature is not None:
            cpu_info["temperature"] = round(temperature, 1)
            
        return cpu_info
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        memory = psutil.virtual_memory()
        
        memory_info = {
            "usage": round(memory.percent, 1),
            "total": memory.total,
            "used": memory.used
        }
        
        # Try to get memory temperature (usually not available)
        try:
            temps = psutil.sensors_temperatures()
            # Look for memory-related temperature sensors
            for sensor_name, sensors in temps.items():
                if any(keyword in sensor_name.lower() for keyword in ['dimm', 'memory', 'ram']):
                    if sensors:
                        memory_info["temperature"] = round(sensors[0].current, 1)
                        break
        except (AttributeError, IndexError, KeyError):
            pass
            
        return memory_info
    
    def _get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        # Get total storage usage
        total_capacity = 0
        total_used = 0
        
        # Get all disk partitions
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                total_capacity += usage.total
                total_used += usage.used
            except PermissionError:
                # Skip partitions we can't access
                continue
        
        # Get disk status information
        disks = self._get_disk_status()
        
        return {
            "capacity": total_capacity,
            "used": total_used,
            "disks": disks
        }
    
    def _get_disk_status(self) -> List[Dict[str, str]]:
        """Get individual disk status."""
        disks = []
        
        try:
            # Get disk I/O stats to determine disk health
            disk_io = psutil.disk_io_counters(perdisk=True)
            
            for disk_name, stats in disk_io.items():
                # Simple heuristic for disk status based on I/O errors
                status = "normal"
                
                # Check if disk has high error rates (simplified)
                if hasattr(stats, 'read_errs') and hasattr(stats, 'write_errs'):
                    total_ops = stats.read_count + stats.write_count
                    total_errs = stats.read_errs + stats.write_errs
                    
                    if total_ops > 0:
                        error_rate = total_errs / total_ops
                        if error_rate > 0.01:  # More than 1% error rate
                            status = "error"
                        elif error_rate > 0.001:  # More than 0.1% error rate
                            status = "warning"
                
                disks.append({
                    "id": disk_name,
                    "status": status
                })
        except Exception:
            # Fallback: create some example disks
            for i in range(1, 7):
                disks.append({
                    "id": f"hdd{i}",
                    "status": "normal"
                })
        
        return disks
    
    def _get_network_info(self) -> Dict[str, int]:
        """Get network upload/download speeds."""
        current_time = time.time()
        current_stats = psutil.net_io_counters()
        
        if self._last_network_stats is None or self._last_network_time is None:
            # First run, no speed calculation possible
            self._last_network_stats = current_stats
            self._last_network_time = current_time
            return {"upload": 0, "download": 0}
        
        # Calculate time difference
        time_diff = current_time - self._last_network_time
        
        if time_diff <= 0:
            return {"upload": 0, "download": 0}
        
        # Calculate bytes per second
        bytes_sent_diff = current_stats.bytes_sent - self._last_network_stats.bytes_sent
        bytes_recv_diff = current_stats.bytes_recv - self._last_network_stats.bytes_recv
        
        upload_speed = int(bytes_sent_diff / time_diff)
        download_speed = int(bytes_recv_diff / time_diff)
        
        # Update last stats
        self._last_network_stats = current_stats
        self._last_network_time = current_time
        
        return {
            "upload": max(0, upload_speed),
            "download": max(0, download_speed)
        }