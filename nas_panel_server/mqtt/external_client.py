"""
External MQTT Client for connecting to external MQTT brokers.
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False
    mqtt = None


class ExternalMQTTClient:
    """External MQTT client for connecting to external MQTT brokers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize external MQTT client with configuration."""
        if not PAHO_AVAILABLE:
            raise ImportError("paho-mqtt is required for external MQTT support. Install with: pip install paho-mqtt")
        
        self.config = config
        self.mqtt_config = config.get('mqtt', {})
        
        self.host = self.mqtt_config.get('host', 'localhost')
        self.port = self.mqtt_config.get('port', 1883)
        self.topic = self.mqtt_config.get('topic', 'nas/panel/data')
        self.qos = self.mqtt_config.get('qos', 1)
        self.username = self.mqtt_config.get('username')
        self.password = self.mqtt_config.get('password')
        self.client_id = self.mqtt_config.get('client_id', 'nas_panel_server')
        self.keep_alive = self.mqtt_config.get('keep_alive', 60)
        
        self.client = None
        self.is_connected = False
        self.is_running = False
        self.connection_thread = None
        
        # Callbacks
        self.on_connect_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None
        self.on_message_callback: Optional[Callable] = None
        
        self.logger = logging.getLogger(__name__)
    
    def set_callbacks(self, on_connect: Optional[Callable] = None, 
                     on_disconnect: Optional[Callable] = None,
                     on_message: Optional[Callable] = None) -> None:
        """Set callback functions."""
        self.on_connect_callback = on_connect
        self.on_disconnect_callback = on_disconnect
        self.on_message_callback = on_message
    
    def start(self) -> None:
        """Start the external MQTT client."""
        if self.is_running:
            self.logger.warning("External MQTT client is already running")
            return
        
        try:
            # Create MQTT client
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
                client_id=self.client_id,
                clean_session=True
            )
            
            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            self.client.on_unsubscribe = self._on_unsubscribe
            
            # Set username and password if provided
            if self.username:
                self.client.username_pw_set(self.username, self.password)
            
            self.logger.info(f"Starting external MQTT client connecting to {self.host}:{self.port}")
            
            # Start connection in a separate thread
            self.is_running = True
            self.connection_thread = threading.Thread(target=self._connection_loop, daemon=True)
            self.connection_thread.start()
            
            self.logger.debug("External MQTT client started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start external MQTT client: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the external MQTT client."""
        if not self.is_running:
            return
        
        self.logger.debug("Stopping external MQTT client...")
        self.is_running = False
        
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass
        
        # Wait for connection thread
        if self.connection_thread:
            self.connection_thread.join(timeout=5)
        
        self.is_connected = False
        self.logger.debug("External MQTT client stopped")
    
    def publish_data(self, data: Dict[str, Any]) -> bool:
        """
        Publish data to the MQTT topic.
        
        Args:
            data: The data to publish
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            self.logger.error("External MQTT client is not connected")
            return False
        
        try:
            # Convert data to JSON
            json_data = json.dumps(data, indent=None, separators=(',', ':'))
            
            # Publish message
            result = self.client.publish(
                topic=self.topic,
                payload=json_data,
                qos=self.qos,
                retain=True
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published data to topic {self.topic}")
                return True
            else:
                self.logger.error(f"Failed to publish data: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing data: {e}")
            return False
    
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            qos: Quality of Service level
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            self.logger.error("External MQTT client is not connected")
            return False
        
        try:
            result = self.client.subscribe(topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Subscribed to topic {topic}")
                return True
            else:
                self.logger.error(f"Failed to subscribe to topic {topic}: {result[0]}")
                return False
        except Exception as e:
            self.logger.error(f"Error subscribing to topic {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            self.logger.error("External MQTT client is not connected")
            return False
        
        try:
            result = self.client.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Unsubscribed from topic {topic}")
                return True
            else:
                self.logger.error(f"Failed to unsubscribe from topic {topic}: {result[0]}")
                return False
        except Exception as e:
            self.logger.error(f"Error unsubscribing from topic {topic}: {e}")
            return False
    
    def _connection_loop(self) -> None:
        """Main connection loop."""
        while self.is_running:
            try:
                if not self.is_connected:
                    # Connect to broker
                    self.client.connect(self.host, self.port, self.keep_alive)
                    self.client.loop_start()
                    
                    # Wait for connection
                    timeout = 10
                    start_time = time.time()
                    while not self.is_connected and (time.time() - start_time) < timeout and self.is_running:
                        time.sleep(0.1)
                    
                    if not self.is_connected:
                        self.logger.error("Connection timeout")
                        time.sleep(5)  # Wait before retry
                        continue
                
                # Keep connection alive
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in connection loop: {e}")
                self.is_connected = False
                time.sleep(5)  # Wait before retry
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects."""
        if rc == 0:
            self.is_connected = True
            self.logger.debug(f"Connected to MQTT broker at {self.host}:{self.port}")
            
            # Subscribe to the configured topic
            self.subscribe(self.topic, self.qos)
            
            if self.on_connect_callback:
                self.on_connect_callback(client, userdata, flags, rc)
        else:
            self.is_connected = False
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects."""
        self.is_connected = False
        if rc == 0:
            self.logger.debug("Disconnected from MQTT broker")
        else:
            self.logger.warning(f"Unexpected disconnection from MQTT broker, return code {rc}")
        
        if self.on_disconnect_callback:
            self.on_disconnect_callback(client, userdata, rc)
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            # Try to parse JSON data
            try:
                data = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                data = msg.payload.decode()
            
            self.logger.debug(f"Received message on topic {msg.topic}: {data}")
            
            if self.on_message_callback:
                self.on_message_callback(client, userdata, msg)
                
        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published."""
        self.logger.debug(f"Message published with mid {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is acknowledged."""
        self.logger.debug(f"Subscription acknowledged with QoS {granted_qos}")
    
    def _on_unsubscribe(self, client, userdata, mid):
        """Callback for when unsubscription is acknowledged."""
        self.logger.debug("Unsubscription acknowledged")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            'connected': self.is_connected,
            'host': self.host,
            'port': self.port,
            'topic': self.topic,
            'qos': self.qos,
            'client_id': self.client_id,
            'running': self.is_running
        }
