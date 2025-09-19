"""
MQTT Client Manager for handling client connections and sessions.
"""

import socket
import threading
import time
import logging
from typing import Dict, Set, Optional, List, Callable, Any
from dataclasses import dataclass
from .protocol import MQTTMessage, MQTTConnectMessage, MQTTConnAckMessage, MQTTPublishMessage, MQTTSubscribeMessage, MQTTSubAckMessage, MQTTPingReqMessage, MQTTPingRespMessage, MQTTDisconnectMessage


@dataclass
class MQTTClient:
    """Represents a connected MQTT client."""
    client_id: str
    socket: socket.socket
    address: tuple
    connected_at: float
    last_ping: float
    keep_alive: int
    clean_session: bool
    subscriptions: Set[str]
    will_topic: Optional[str] = None
    will_message: Optional[str] = None
    will_qos: int = 0
    will_retain: bool = False
    username: Optional[str] = None
    password: Optional[str] = None


class MQTTClientManager:
    """Manages MQTT client connections and sessions."""
    
    def __init__(self):
        self.clients: Dict[str, MQTTClient] = {}
        self.client_sockets: Dict[socket.socket, str] = {}  # socket -> client_id
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of client_ids
        self.retained_messages: Dict[str, MQTTPublishMessage] = {}
        
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {
            'connect': self._handle_connect,
            'publish': self._handle_publish,
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe,
            'pingreq': self._handle_pingreq,
            'disconnect': self._handle_disconnect,
        }
    
    def add_client(self, client: MQTTClient) -> None:
        """Add a new client to the manager."""
        with self._lock:
            self.clients[client.client_id] = client
            self.client_sockets[client.socket] = client.client_id
            self.logger.debug(f"Client {client.client_id} connected from {client.address}")
    
    def remove_client(self, client_id: str) -> None:
        """Remove a client from the manager."""
        with self._lock:
            if client_id in self.clients:
                client = self.clients[client_id]
                
                # Remove from subscriptions
                for topic in list(client.subscriptions):
                    self._unsubscribe_from_topic(client_id, topic)
                
                # Remove from socket mapping
                if client.socket in self.client_sockets:
                    del self.client_sockets[client.socket]
                
                # Close socket
                try:
                    client.socket.close()
                except:
                    pass
                
                del self.clients[client_id]
                self.logger.debug(f"Client {client_id} disconnected")
    
    def get_client_by_socket(self, socket: socket.socket) -> Optional[MQTTClient]:
        """Get client by socket."""
        with self._lock:
            client_id = self.client_sockets.get(socket)
            return self.clients.get(client_id) if client_id else None
    
    def get_client_by_id(self, client_id: str) -> Optional[MQTTClient]:
        """Get client by ID."""
        with self._lock:
            return self.clients.get(client_id)
    
    def handle_message(self, client: MQTTClient, message: MQTTMessage) -> Optional[MQTTMessage]:
        """Handle incoming message from client."""
        message_type = message.message_type.name.lower()
        
        if message_type in self.message_handlers:
            return self.message_handlers[message_type](client, message)
        else:
            self.logger.warning(f"Unhandled message type: {message_type}")
            return None
    
    def _handle_connect(self, client: MQTTClient, message: MQTTConnectMessage) -> MQTTConnAckMessage:
        """Handle CONNECT message."""
        # Validate client ID
        if not message.client_id or len(message.client_id) == 0:
            return MQTTConnAckMessage(return_code=2)  # Identifier rejected
        
        # Check for duplicate client ID
        if message.client_id in self.clients and not message.clean_session:
            return MQTTConnAckMessage(return_code=2)  # Identifier rejected
        
        # Update client information
        client.client_id = message.client_id
        client.keep_alive = message.keep_alive
        client.clean_session = message.clean_session
        client.username = message.username
        client.password = message.password
        client.will_topic = message.will_topic
        client.will_message = message.will_message
        client.will_qos = message.will_qos
        client.will_retain = message.will_retain
        
        # If clean session, clear existing subscriptions
        if message.clean_session:
            client.subscriptions.clear()
        
        # Accept connection
        return MQTTConnAckMessage(return_code=0, session_present=False)
    
    def _handle_publish(self, client: MQTTClient, message: MQTTPublishMessage) -> None:
        """Handle PUBLISH message."""
        # Store retained message if retain flag is set
        if message.retain:
            if len(message.payload) == 0:
                # Empty payload means delete retained message
                self.retained_messages.pop(message.topic, None)
            else:
                self.retained_messages[message.topic] = message
        
        # Route message to subscribers
        self._route_message(message)
    
    def _handle_subscribe(self, client: MQTTClient, message: MQTTSubscribeMessage) -> MQTTSubAckMessage:
        """Handle SUBSCRIBE message."""
        return_codes = []
        
        for topic, qos in message.subscriptions:
            # Add subscription
            self._subscribe_to_topic(client.client_id, topic)
            client.subscriptions.add(topic)
            self.logger.debug(f"Client {client.client_id} subscribed to topic {topic} with QoS {qos}")
            
            # Return code (0-2 for success, 0x80 for failure)
            return_codes.append(min(qos, 2))
        
        return MQTTSubAckMessage(message.packet_id, return_codes)
    
    def _handle_unsubscribe(self, client: MQTTClient, message: MQTTMessage) -> MQTTMessage:
        """Handle UNSUBSCRIBE message."""
        # TODO: Implement unsubscribe parsing and handling
        pass
    
    def _handle_pingreq(self, client: MQTTClient, message: MQTTMessage) -> MQTTPingRespMessage:
        """Handle PINGREQ message."""
        client.last_ping = time.time()
        return MQTTPingRespMessage()
    
    def _handle_disconnect(self, client: MQTTClient, message: MQTTMessage) -> None:
        """Handle DISCONNECT message."""
        # Send will message if configured
        if client.will_topic and client.will_message:
            will_message = MQTTPublishMessage(
                topic=client.will_topic,
                payload=client.will_message.encode('utf-8'),
                qos=client.will_qos,
                retain=client.will_retain
            )
            self._route_message(will_message)
        
        # Remove client
        self.remove_client(client.client_id)
    
    def _subscribe_to_topic(self, client_id: str, topic: str) -> None:
        """Subscribe client to topic."""
        with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(client_id)
    
    def _unsubscribe_from_topic(self, client_id: str, topic: str) -> None:
        """Unsubscribe client from topic."""
        with self._lock:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(client_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
    
    def _route_message(self, message: MQTTPublishMessage) -> None:
        """Route message to all subscribers of the topic."""
        with self._lock:
            # Find all clients subscribed to this topic
            subscribers = set()
            
            # Exact topic match
            if message.topic in self.subscriptions:
                subscribers.update(self.subscriptions[message.topic])
                self.logger.debug(f"Found {len(self.subscriptions[message.topic])} subscribers for exact topic {message.topic}")
            
            # Wildcard topic matches
            for topic_pattern, client_ids in self.subscriptions.items():
                if self._topic_matches(message.topic, topic_pattern):
                    subscribers.update(client_ids)
                    self.logger.debug(f"Found {len(client_ids)} subscribers for pattern {topic_pattern}")
            
            self.logger.debug(f"Total subscribers for topic {message.topic}: {len(subscribers)}")
            
            # Send message to all subscribers
            for client_id in subscribers:
                client = self.clients.get(client_id)
                if client:
                    try:
                        self.logger.debug(f"Sending message to client {client_id}")
                        self._send_message_to_client(client, message)
                    except Exception as e:
                        self.logger.error(f"Error sending message to client {client_id}: {e}")
                        # Remove problematic client
                        self.remove_client(client_id)
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches subscription pattern."""
        # Simple wildcard matching for + and #
        if '+' in pattern or '#' in pattern:
            # Convert pattern to regex
            import re
            regex_pattern = pattern.replace('+', '[^/]+').replace('#', '.*')
            return bool(re.match(f'^{regex_pattern}$', topic))
        else:
            return topic == pattern
    
    def _send_message_to_client(self, client: MQTTClient, message: MQTTMessage) -> None:
        """Send message to specific client."""
        try:
            data = message.to_bytes()
            client.socket.send(data)
        except Exception as e:
            self.logger.error(f"Error sending message to client {client.client_id}: {e}")
            raise
    
    def send_retained_messages(self, client: MQTTClient, topic: str) -> None:
        """Send retained messages for a topic to a client."""
        with self._lock:
            # Send exact topic match
            if topic in self.retained_messages:
                self._send_message_to_client(client, self.retained_messages[topic])
            
            # Send wildcard matches
            for retained_topic, message in self.retained_messages.items():
                if self._topic_matches(retained_topic, topic):
                    self._send_message_to_client(client, message)
    
    def cleanup_inactive_clients(self, timeout: int = 300) -> None:
        """Remove clients that haven't pinged within timeout."""
        current_time = time.time()
        inactive_clients = []
        
        with self._lock:
            for client_id, client in self.clients.items():
                if current_time - client.last_ping > timeout:
                    inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            self.logger.debug(f"Removing inactive client: {client_id}")
            self.remove_client(client_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        with self._lock:
            return {
                'connected_clients': len(self.clients),
                'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
                'retained_messages': len(self.retained_messages),
                'topics': list(self.subscriptions.keys())
            }
