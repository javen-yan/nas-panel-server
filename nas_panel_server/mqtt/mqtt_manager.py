"""
Unified MQTT Manager for NAS Panel Server.

This module provides a unified interface for both built-in and external MQTT implementations.
"""

import logging
from typing import Dict, Any, Optional, Union
from .builtin_server import BuiltinMQTTServer
from .external_client import ExternalMQTTClient


class MQTTManager:
    """Unified MQTT manager that supports both built-in and external MQTT."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MQTT manager with configuration."""
        self.config = config
        self.mqtt_config = config.get('mqtt', {})
        
        # Determine MQTT type
        self.mqtt_type = self.mqtt_config.get('type', 'builtin')  # 'builtin' or 'external'
        self.host = self.mqtt_config.get('host', 'localhost')
        self.port = self.mqtt_config.get('port', 1883)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize the appropriate MQTT implementation
        self._mqtt_impl: Optional[Union[BuiltinMQTTServer, ExternalMQTTClient]] = None
        self._initialize_mqtt()
    
    def _initialize_mqtt(self) -> None:
        """Initialize the appropriate MQTT implementation."""
        try:
            if self.mqtt_type == 'builtin':
                self.logger.debug("Initializing built-in MQTT server")
                self._mqtt_impl = BuiltinMQTTServer(self.config)
            elif self.mqtt_type == 'external':
                self.logger.debug("Initializing external MQTT client")
                self._mqtt_impl = ExternalMQTTClient(self.config)
            else:
                raise ValueError(f"Unsupported MQTT type: {self.mqtt_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize MQTT {self.mqtt_type}: {e}")
            raise
    
    def start(self) -> None:
        """Start the MQTT service."""
        if self._mqtt_impl is None:
            raise RuntimeError("MQTT implementation not initialized")
        
        self.logger.debug(f"Starting MQTT {self.mqtt_type} service")
        self._mqtt_impl.start()
    
    def stop(self) -> None:
        """Stop the MQTT service."""
        if self._mqtt_impl is None:
            return
        
        self.logger.debug(f"Stopping MQTT {self.mqtt_type} service")
        self._mqtt_impl.stop()
    
    def publish_data(self, data: Dict[str, Any]) -> bool:
        """
        Publish data to the MQTT topic.
        
        Args:
            data: The data to publish
            
        Returns:
            True if successful, False otherwise
        """
        if self._mqtt_impl is None:
            self.logger.error("MQTT implementation not initialized")
            return False
        
        return self._mqtt_impl.publish_data(data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get MQTT service statistics."""
        if self._mqtt_impl is None:
            return {'error': 'MQTT implementation not initialized'}
        
        stats = self._mqtt_impl.get_stats()
        stats['mqtt_type'] = self.mqtt_type
        return stats
    
    def is_running(self) -> bool:
        """Check if MQTT service is running."""
        if self._mqtt_impl is None:
            return False
        
        if hasattr(self._mqtt_impl, 'is_running'):
            return self._mqtt_impl.is_running
        elif hasattr(self._mqtt_impl, 'is_connected'):
            return self._mqtt_impl.is_connected
        else:
            return False
    
    def set_callbacks(self, on_connect=None, on_disconnect=None, on_message=None) -> None:
        """Set callback functions (only for external MQTT)."""
        if self.mqtt_type == 'external' and hasattr(self._mqtt_impl, 'set_callbacks'):
            self._mqtt_impl.set_callbacks(on_connect, on_disconnect, on_message)
        else:
            self.logger.warning("Callbacks are only supported for external MQTT")
    
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """Subscribe to a topic (only for external MQTT)."""
        if self.mqtt_type == 'external' and hasattr(self._mqtt_impl, 'subscribe'):
            return self._mqtt_impl.subscribe(topic, qos)
        else:
            self.logger.warning("Subscribe is only supported for external MQTT")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from a topic (only for external MQTT)."""
        if self.mqtt_type == 'external' and hasattr(self._mqtt_impl, 'unsubscribe'):
            return self._mqtt_impl.unsubscribe(topic)
        else:
            self.logger.warning("Unsubscribe is only supported for external MQTT")
            return False


def create_mqtt_manager(config: Dict[str, Any]) -> MQTTManager:
    """
    Factory function to create an MQTT manager.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        MQTTManager instance
    """
    return MQTTManager(config)
