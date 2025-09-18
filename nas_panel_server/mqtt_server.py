"""
Built-in MQTT server for NAS panel server.
"""

import threading
import time
import json
import logging
from typing import Dict, Any, Callable, Optional
import paho.mqtt.client as mqtt_client


class MQTTServer:
    """Simple MQTT server implementation using paho-mqtt."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MQTT server with configuration."""
        self.config = config
        self.mqtt_config = config.get('mqtt', {})
        
        self.host = self.mqtt_config.get('host', '0.0.0.0')
        self.port = self.mqtt_config.get('port', 1883)
        self.topic = self.mqtt_config.get('topic', 'nas/panel/data')
        self.qos = self.mqtt_config.get('qos', 1)
        
        self.client = None
        self.is_running = False
        self.server_thread = None
        
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """Start the MQTT server."""
        if self.is_running:
            self.logger.warning("MQTT server is already running")
            return
        
        try:
            # Create MQTT client
            self.client = mqtt_client.Client(
                callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1,
                client_id="nas_panel_server",
                protocol=mqtt_client.MQTTv311,
                clean_session=True
            )
            
            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_unsubscribe = self._on_unsubscribe
            
            # Start the client loop in a separate thread
            self.client.loop_start()
            
            # For simplicity, we'll act as a standalone MQTT publisher
            # In a real implementation, you would connect to a proper MQTT broker
            self.logger.info(f"Starting MQTT server on {self.host}:{self.port}")
            self.logger.info("Note: This is a simplified MQTT implementation for demonstration")
            
            # Start server thread
            self.is_running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            self.logger.info("MQTT server started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start MQTT server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the MQTT server."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping MQTT server...")
        self.is_running = False
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
        
        self.logger.info("MQTT server stopped")
    
    def publish_data(self, data: Dict[str, Any]) -> bool:
        """
        Publish data to the MQTT topic.
        
        Args:
            data: The data to publish
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_running:
            self.logger.error("MQTT server is not running")
            return False
        
        try:
            # Convert data to JSON
            json_data = json.dumps(data, indent=None, separators=(',', ':'))
            
            # For demonstration purposes, we'll just log the data
            # In a real implementation, this would publish to a proper MQTT broker
            self.logger.debug(f"Publishing data to topic {self.topic}")
            self.logger.debug(f"Data: {json_data}")
            
            # Store the last published data for potential subscribers
            if not hasattr(self, '_last_data'):
                self._last_data = {}
            self._last_data[self.topic] = json_data
            
            return True
                
        except Exception as e:
            self.logger.error(f"Error publishing data: {e}")
            return False
    
    def _server_loop(self) -> None:
        """Main server loop."""
        # This is a simplified implementation
        # In a real MQTT broker, this would handle client connections,
        # subscriptions, message routing, etc.
        
        while self.is_running:
            try:
                # Keep the server alive
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in server loop: {e}")
                break
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects."""
        if rc == 0:
            self.logger.info("MQTT client connected successfully")
        else:
            self.logger.error(f"MQTT client connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects."""
        if rc == 0:
            self.logger.info("MQTT client disconnected successfully")
        else:
            self.logger.warning(f"MQTT client disconnected unexpectedly with code {rc}")
    
    def _on_message(self, client, userdata, message):
        """Callback for when a message is received."""
        self.logger.debug(f"Received message on topic {message.topic}: {message.payload.decode()}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is acknowledged."""
        self.logger.debug(f"Subscription acknowledged with QoS {granted_qos}")
    
    def _on_unsubscribe(self, client, userdata, mid):
        """Callback for when unsubscription is acknowledged."""
        self.logger.debug("Unsubscription acknowledged")


class SimpleMQTTBroker:
    """
    A very simple MQTT broker implementation for demonstration.
    In production, you should use a proper MQTT broker like Mosquitto.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 1883):
        self.host = host
        self.port = port
        self.is_running = False
        self.clients = {}
        self.subscriptions = {}
        self.retained_messages = {}
        
        self.logger = logging.getLogger(f"{__name__}.SimpleMQTTBroker")
    
    def start(self) -> None:
        """Start the simple MQTT broker."""
        # Note: This is a very basic implementation
        # For production use, consider using an embedded broker
        # or running a separate MQTT broker process
        
        self.logger.info(f"Simple MQTT broker would start on {self.host}:{self.port}")
        self.logger.info("Note: Using paho-mqtt client as broker substitute")
        self.is_running = True
    
    def stop(self) -> None:
        """Stop the simple MQTT broker."""
        self.is_running = False
        self.logger.info("Simple MQTT broker stopped")