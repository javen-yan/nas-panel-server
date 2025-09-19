"""
Configuration manager for NAS panel server.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigManager:
    """Manages configuration for the NAS panel server."""
    
    DEFAULT_CONFIG = {
        'server': {
            'hostname': 'auto',  # Always use auto-detected hostname
            'ip': 'auto'
        },
        'mqtt': {
            'host': '0.0.0.0',
            'port': 1883,
            'topic': 'nas/panel/data',
            'qos': 1
        },
        'collection': {
            'interval': 5
        },
        'custom_collectors': []
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, will look for
                        config.yaml in current directory or use defaults.
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        config_file = None
        
        if self.config_path:
            # Use specified config file
            config_file = Path(self.config_path)
        else:
            # Look for config files in common locations
            possible_paths = [
                Path('config.yaml'),
                Path('config.yml'),
                Path('nas_panel_server.yaml'),
                Path('nas_panel_server.yml'),
                Path('/etc/nas-panel-server/config.yaml'),
                Path.home() / '.config' / 'nas-panel-server' / 'config.yaml'
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_file = path
                    break
        
        if config_file and config_file.exists():
            try:
                self.logger.info(f"Loading configuration from {config_file}")
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                
                if file_config:
                    # Merge with default config
                    self._deep_merge(self.config, file_config)
                    self.logger.info("Configuration loaded successfully")
                else:
                    self.logger.warning("Configuration file is empty, using defaults")
                    
            except Exception as e:
                self.logger.error(f"Error loading configuration: {e}")
                self.logger.info("Using default configuration")
        else:
            self.logger.info("No configuration file found, using defaults")
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'NAS_PANEL_HOSTNAME': ('server', 'hostname'),
            'NAS_PANEL_IP': ('server', 'ip'),
            'NAS_PANEL_MQTT_HOST': ('mqtt', 'host'),
            'NAS_PANEL_MQTT_PORT': ('mqtt', 'port'),
            'NAS_PANEL_MQTT_TOPIC': ('mqtt', 'topic'),
            'NAS_PANEL_MQTT_QOS': ('mqtt', 'qos'),
            'NAS_PANEL_INTERVAL': ('collection', 'interval'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert to appropriate type
                if key in ['port', 'qos', 'interval']:
                    try:
                        value = int(value)
                    except ValueError:
                        self.logger.warning(f"Invalid integer value for {env_var}: {value}")
                        continue
                
                # Set in config
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][key] = value
                self.logger.debug(f"Environment override: {env_var} = {value}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'mqtt.port')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'mqtt.port')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save_config(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            path: Path to save configuration. If None, uses original config path.
        """
        save_path = path or self.config_path or 'config.yaml'
        
        try:
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def validate_config(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate MQTT configuration
        mqtt_config = self.config.get('mqtt', {})
        
        port = mqtt_config.get('port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("MQTT port must be an integer between 1 and 65535")
        
        qos = mqtt_config.get('qos')
        if not isinstance(qos, int) or qos < 0 or qos > 2:
            errors.append("MQTT QoS must be 0, 1, or 2")
        
        # Validate collection configuration
        collection_config = self.config.get('collection', {})
        
        interval = collection_config.get('interval')
        if not isinstance(interval, (int, float)) or interval <= 0:
            errors.append("Collection interval must be a positive number")
        
        # Validate custom collectors
        custom_collectors = self.config.get('custom_collectors', [])
        if not isinstance(custom_collectors, list):
            errors.append("Custom collectors must be a list")
        else:
            for i, collector in enumerate(custom_collectors):
                if not isinstance(collector, dict):
                    errors.append(f"Custom collector {i} must be a dictionary")
                    continue
                
                name = collector.get('name')
                if not name or not isinstance(name, str):
                    errors.append(f"Custom collector {i} must have a valid name")
                
                collector_type = collector.get('type')
                if collector_type not in ['file', 'command', 'env']:
                    errors.append(f"Custom collector {i} has invalid type: {collector_type}")
        
        return errors
    
    def get_custom_collectors(self) -> List[Dict[str, Any]]:
        """Get list of custom collector configurations."""
        return self.config.get('custom_collectors', [])
    
    def add_custom_collector(self, collector_config: Dict[str, Any]) -> None:
        """
        Add a custom collector configuration.
        
        Args:
            collector_config: Dictionary containing collector configuration
        """
        if 'custom_collectors' not in self.config:
            self.config['custom_collectors'] = []
        
        self.config['custom_collectors'].append(collector_config)
    
    def remove_custom_collector(self, name: str) -> bool:
        """
        Remove a custom collector by name.
        
        Args:
            name: Name of the collector to remove
            
        Returns:
            True if collector was found and removed, False otherwise
        """
        custom_collectors = self.config.get('custom_collectors', [])
        
        for i, collector in enumerate(custom_collectors):
            if collector.get('name') == name:
                del custom_collectors[i]
                return True
        
        return False
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.config, indent=2)
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return self.to_json()