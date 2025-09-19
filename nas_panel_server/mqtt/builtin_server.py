"""
Built-in MQTT server for NAS panel server.
"""

import socket
import threading
import time
import json
import logging
from typing import Dict, Any, Optional
from .protocol import MQTTParser, MQTTMessage, MQTTConnectMessage, MQTTPublishMessage, MQTTPingReqMessage, MQTTDisconnectMessage
from .client_manager import MQTTClientManager, MQTTClient


class BuiltinMQTTServer:
    """Built-in MQTT server implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MQTT server with configuration."""
        self.config = config
        self.mqtt_config = config.get('mqtt', {})
        
        self.host = self.mqtt_config.get('host', '0.0.0.0')
        self.port = self.mqtt_config.get('port', 1883)
        self.topic = self.mqtt_config.get('topic', 'nas/panel/data')
        self.qos = self.mqtt_config.get('qos', 1)
        
        self.server_socket = None
        self.is_running = False
        self.server_thread = None
        self.client_threads = []
        
        # Initialize components
        self.parser = MQTTParser()
        self.client_manager = MQTTClientManager()
        
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """Start the MQTT server."""
        if self.is_running:
            self.logger.warning("MQTT server is already running")
            return
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            
            self.logger.info(f"Starting MQTT server on {self.host}:{self.port}")
            
            # Start server thread
            self.is_running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            cleanup_thread.start()
            
            self.logger.debug("MQTT server started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start MQTT server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the MQTT server."""
        if not self.is_running:
            return
        
        self.logger.debug("Stopping MQTT server...")
        self.is_running = False
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Disconnect all clients
        for client_id in list(self.client_manager.clients.keys()):
            self.client_manager.remove_client(client_id)
        
        # Wait for server thread
        if self.server_thread:
            self.server_thread.join(timeout=5)
        
        self.logger.debug("MQTT server stopped")
    
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
            
            # Create PUBLISH message
            packet_id = None
            if self.qos > 0:
                # Generate packet ID for QoS > 0
                packet_id = int(time.time() * 1000) % 65536
            
            publish_message = MQTTPublishMessage(
                topic=self.topic,
                payload=json_data.encode('utf-8'),
                qos=self.qos,
                retain=True,  # Retain the latest data
                packet_id=packet_id
            )
            
            # Route message to subscribers
            self.client_manager._route_message(publish_message)
            
            self.logger.debug(f"Published data to topic {self.topic}")
            return True
                
        except Exception as e:
            self.logger.error(f"Error publishing data: {e}")
            return False
    
    def _server_loop(self) -> None:
        """Main server loop that accepts client connections."""
        while self.is_running:
            try:
                # Accept client connection
                client_socket, address = self.server_socket.accept()
                
                # Create client object
                client = MQTTClient(
                    client_id="",  # Will be set after CONNECT
                    socket=client_socket,
                    address=address,
                    connected_at=time.time(),
                    last_ping=time.time(),
                    keep_alive=60,
                    clean_session=True,
                    subscriptions=set()
                )
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client,),
                    daemon=True
                )
                client_thread.start()
                self.client_threads.append(client_thread)
                
            except socket.error as e:
                if self.is_running:
                    self.logger.error(f"Error accepting client connection: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error in server loop: {e}")
    
    def _handle_client(self, client: MQTTClient) -> None:
        """Handle individual client connection."""
        buffer = b''
        
        try:
            while self.is_running:
                # Receive data
                data = client.socket.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while buffer:
                    try:
                        # Check if we have at least the fixed header
                        if len(buffer) < 2:
                            break
                        
                        # Parse fixed header
                        fixed_header = buffer[0]
                        message_type = (fixed_header >> 4) & 0x0F
                        flags = fixed_header & 0x0F
                        
                        # Parse remaining length
                        remaining_length, length_bytes = MQTTMessage._decode_remaining_length(buffer, 1)
                        fixed_header_length = 1 + length_bytes
                        total_length = fixed_header_length + remaining_length
                        
                        # Check if we have complete message
                        if len(buffer) < total_length:
                            break
                        
                        # Extract message payload
                        message_payload = buffer[fixed_header_length:total_length]
                        
                        # Create message object based on type
                        if message_type == 1:  # CONNECT
                            message = self.parser._parse_connect(message_payload)
                        elif message_type == 3:  # PUBLISH
                            message = self.parser._parse_publish(message_payload, flags)
                        elif message_type == 4:  # PUBACK
                            # PUBACK message - just acknowledge, no response needed
                            buffer = buffer[total_length:]
                            continue
                        elif message_type == 8:  # SUBSCRIBE
                            message = self.parser._parse_subscribe(message_payload)
                        elif message_type == 12:  # PINGREQ
                            message = MQTTPingReqMessage()
                        elif message_type == 14:  # DISCONNECT
                            message = MQTTDisconnectMessage()
                        else:
                            self.logger.warning(f"Unsupported message type: {message_type}")
                            buffer = buffer[total_length:]
                            continue
                        
                        # Remove processed data from buffer
                        buffer = buffer[total_length:]
                        
                        # Handle the message
                        self._process_message(client, message)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing message from client {client.address}: {e}")
                        # Skip this message and continue
                        if len(buffer) >= 2:
                            # Try to find next message boundary
                            try:
                                _, length_bytes = MQTTMessage._decode_remaining_length(buffer, 1)
                                skip_length = 1 + length_bytes
                                if len(buffer) > skip_length:
                                    buffer = buffer[skip_length:]
                                else:
                                    break
                            except:
                                buffer = buffer[1:]  # Skip one byte and try again
                        else:
                            break
                
        except Exception as e:
            self.logger.error(f"Error handling client {client.address}: {e}")
        finally:
            # Clean up client
            if client.client_id:
                self.client_manager.remove_client(client.client_id)
            else:
                try:
                    client.socket.close()
                except:
                    pass
    
    def _process_message(self, client: MQTTClient, message: MQTTMessage) -> None:
        """Process incoming message from client."""
        try:
            # Handle CONNECT message specially
            if isinstance(message, MQTTConnectMessage):
                # Create a temporary client with the client ID
                temp_client = MQTTClient(
                    client_id=message.client_id,
                    socket=client.socket,
                    address=client.address,
                    connected_at=client.connected_at,
                    last_ping=time.time(),
                    keep_alive=message.keep_alive,
                    clean_session=message.clean_session,
                    subscriptions=set(),
                    username=message.username,
                    password=message.password,
                    will_topic=message.will_topic,
                    will_message=message.will_message,
                    will_qos=message.will_qos,
                    will_retain=message.will_retain
                )
                
                # Add client to manager
                self.client_manager.add_client(temp_client)
                
                # Update the original client object with the new client ID
                client.client_id = temp_client.client_id
                
                # Send CONNACK
                connack = self.client_manager._handle_connect(temp_client, message)
                client.socket.send(connack.to_bytes())
                
                # Send retained messages for subscribed topics
                for topic in temp_client.subscriptions:
                    self.client_manager.send_retained_messages(temp_client, topic)
                
                return
            
            # Handle other messages - get the actual client from manager
            actual_client = self.client_manager.get_client_by_socket(client.socket)
            if actual_client:
                response = self.client_manager.handle_message(actual_client, message)
                if response:
                    client.socket.send(response.to_bytes())
            else:
                self.logger.warning(f"No client found for socket {client.socket}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _cleanup_loop(self) -> None:
        """Cleanup loop for inactive clients."""
        while self.is_running:
            try:
                time.sleep(60)  # Check every minute
                self.client_manager.cleanup_inactive_clients(timeout=300)  # 5 minute timeout
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        stats = self.client_manager.get_stats()
        stats.update({
            'server_running': self.is_running,
            'host': self.host,
            'port': self.port,
            'topic': self.topic,
            'qos': self.qos
        })
        return stats


class SimpleMQTTBroker:
    """
    Legacy class for backward compatibility.
    Use MQTTServer instead.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 1883):
        self.host = host
        self.port = port
        self.is_running = False
        self.logger = logging.getLogger(f"{__name__}.SimpleMQTTBroker")
    
    def start(self) -> None:
        """Start the simple MQTT broker."""
        self.logger.info(f"Simple MQTT broker would start on {self.host}:{self.port}")
        self.logger.info("Note: Use MQTTServer for full functionality")
        self.is_running = True
    
    def stop(self) -> None:
        """Stop the simple MQTT broker."""
        self.is_running = False
        self.logger.info("Simple MQTT broker stopped")