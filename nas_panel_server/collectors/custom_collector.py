"""
Custom collector for user-defined system information.
"""

import os
import subprocess
from typing import Dict, Any, List
from .base import BaseCollector


class CustomCollector(BaseCollector):
    """Collector for custom user-defined system information."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.custom_collectors = self.config.get('custom_collectors', [])
    
    def collect(self) -> Dict[str, Any]:
        """Collect custom information based on configuration."""
        custom_data = {}
        
        for collector_config in self.custom_collectors:
            try:
                name = collector_config.get('name')
                if not name:
                    continue
                
                value = self._collect_single(collector_config)
                if value is not None:
                    custom_data[name] = {
                        'value': value,
                        'unit': collector_config.get('unit', ''),
                        'type': collector_config.get('type', 'unknown')
                    }
            except Exception as e:
                # Log error but continue with other collectors
                custom_data[collector_config.get('name', 'unknown')] = {
                    'error': str(e),
                    'type': collector_config.get('type', 'unknown')
                }
        
        return custom_data
    
    def _collect_single(self, config: Dict[str, Any]) -> Any:
        """Collect data from a single custom collector configuration."""
        collector_type = config.get('type', '').lower()
        
        if collector_type == 'file':
            return self._collect_from_file(config)
        elif collector_type == 'command':
            return self._collect_from_command(config)
        elif collector_type == 'env':
            return self._collect_from_env(config)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")
    
    def _collect_from_file(self, config: Dict[str, Any]) -> Any:
        """Collect data from a file."""
        file_path = config.get('path')
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r') as f:
            content = f.read().strip()
        
        # Apply transformation if specified
        transform = config.get('transform')
        if transform:
            # Simple eval-based transformation (be careful with security)
            try:
                # Create a safe namespace for eval
                namespace = {
                    'float': float,
                    'int': int,
                    'str': str,
                    'len': len,
                    'abs': abs,
                    'round': round,
                    'min': min,
                    'max': max
                }
                # Replace 'x' with the actual content
                transform_code = transform.replace('lambda x:', '').strip()
                result = eval(transform_code, namespace, {'x': content})
                return result
            except Exception as e:
                raise ValueError(f"Transform failed: {e}")
        
        # Try to convert to number if possible
        try:
            if '.' in content:
                return float(content)
            else:
                return int(content)
        except ValueError:
            return content
    
    def _collect_from_command(self, config: Dict[str, Any]) -> Any:
        """Collect data from a shell command."""
        command = config.get('command')
        if not command:
            raise ValueError("No command specified")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10  # 10 second timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Command failed with code {result.returncode}: {result.stderr}")
            
            output = result.stdout.strip()
            
            # Apply transformation if specified
            transform = config.get('transform')
            if transform:
                try:
                    namespace = {
                        'float': float,
                        'int': int,
                        'str': str,
                        'len': len,
                        'abs': abs,
                        'round': round,
                        'min': min,
                        'max': max
                    }
                    transform_code = transform.replace('lambda x:', '').strip()
                    result = eval(transform_code, namespace, {'x': output})
                    return result
                except Exception as e:
                    raise ValueError(f"Transform failed: {e}")
            
            # Try to convert to number if possible
            try:
                if '.' in output:
                    return float(output)
                else:
                    return int(output)
            except ValueError:
                return output
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Command timed out")
    
    def _collect_from_env(self, config: Dict[str, Any]) -> Any:
        """Collect data from environment variables."""
        env_var = config.get('variable')
        if not env_var:
            raise ValueError("No environment variable specified")
        
        value = os.environ.get(env_var)
        if value is None:
            default = config.get('default')
            if default is not None:
                value = default
            else:
                raise ValueError(f"Environment variable {env_var} not found")
        
        # Apply transformation if specified
        transform = config.get('transform')
        if transform:
            try:
                namespace = {
                    'float': float,
                    'int': int,
                    'str': str,
                    'len': len,
                    'abs': abs,
                    'round': round,
                    'min': min,
                    'max': max
                }
                transform_code = transform.replace('lambda x:', '').strip()
                result = eval(transform_code, namespace, {'x': value})
                return result
            except Exception as e:
                raise ValueError(f"Transform failed: {e}")
        
        return value