"""
MQTT Protocol implementation for the built-in MQTT server.
"""

import struct
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


class MQTTMessageType(Enum):
    """MQTT message types."""
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14


class MQTTQoS(Enum):
    """MQTT Quality of Service levels."""
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


class MQTTConnectFlags:
    """MQTT CONNECT message flags."""
    def __init__(self, flags: int):
        self.username_flag = bool(flags & 0x80)
        self.password_flag = bool(flags & 0x40)
        self.will_retain = bool(flags & 0x20)
        self.will_qos = (flags & 0x18) >> 3
        self.will_flag = bool(flags & 0x04)
        self.clean_session = bool(flags & 0x02)
        self.reserved = bool(flags & 0x01)


class MQTTMessage:
    """Base MQTT message class."""
    
    def __init__(self, message_type: MQTTMessageType, flags: int = 0, payload: bytes = b''):
        self.message_type = message_type
        self.flags = flags
        self.payload = payload
        self.remaining_length = len(payload)
    
    def to_bytes(self) -> bytes:
        """Convert message to bytes."""
        # Fixed header
        fixed_header = (self.message_type.value << 4) | (self.flags & 0x0F)
        
        # Remaining length encoding
        remaining_length_bytes = self._encode_remaining_length(self.remaining_length)
        
        return bytes([fixed_header]) + remaining_length_bytes + self.payload
    
    @staticmethod
    def _encode_remaining_length(length: int) -> bytes:
        """Encode remaining length according to MQTT spec."""
        if length < 0:
            raise ValueError("Remaining length cannot be negative")
        elif length < 128:
            return bytes([length])
        elif length < 16384:
            return bytes([length % 128 | 0x80, length // 128])
        elif length < 2097152:
            return bytes([length % 128 | 0x80, (length // 128) % 128 | 0x80, length // 16384])
        else:
            return bytes([length % 128 | 0x80, (length // 128) % 128 | 0x80, 
                         (length // 16384) % 128 | 0x80, length // 2097152])
    
    @staticmethod
    def _decode_remaining_length(data: bytes, offset: int = 0) -> Tuple[int, int]:
        """Decode remaining length from bytes."""
        multiplier = 1
        value = 0
        pos = offset
        
        while pos < len(data):
            encoded_byte = data[pos]
            value += (encoded_byte & 127) * multiplier
            multiplier *= 128
            pos += 1
            
            if (encoded_byte & 128) == 0:
                break
        
        return value, pos - offset


class MQTTConnectMessage(MQTTMessage):
    """MQTT CONNECT message."""
    
    def __init__(self, client_id: str, clean_session: bool = True, 
                 username: Optional[str] = None, password: Optional[str] = None,
                 will_topic: Optional[str] = None, will_message: Optional[str] = None,
                 will_qos: int = 0, will_retain: bool = False, keep_alive: int = 60):
        self.client_id = client_id
        self.clean_session = clean_session
        self.username = username
        self.password = password
        self.will_topic = will_topic
        self.will_message = will_message
        self.will_qos = will_qos
        self.will_retain = will_retain
        self.keep_alive = keep_alive
        
        # Build payload
        payload = self._build_payload()
        super().__init__(MQTTMessageType.CONNECT, 0, payload)
    
    def _build_payload(self) -> bytes:
        """Build CONNECT message payload."""
        payload = b''
        
        # Protocol name
        protocol_name = b'MQTT'
        payload += struct.pack('!H', len(protocol_name)) + protocol_name
        
        # Protocol level
        payload += struct.pack('!B', 4)  # MQTT 3.1.1
        
        # Connect flags
        flags = 0
        if self.username:
            flags |= 0x80
        if self.password:
            flags |= 0x40
        if self.will_retain:
            flags |= 0x20
        flags |= (self.will_qos & 0x03) << 3
        if self.will_topic:
            flags |= 0x04
        if self.clean_session:
            flags |= 0x02
        
        payload += struct.pack('!B', flags)
        
        # Keep alive
        payload += struct.pack('!H', self.keep_alive)
        
        # Client ID
        client_id_bytes = self.client_id.encode('utf-8')
        payload += struct.pack('!H', len(client_id_bytes)) + client_id_bytes
        
        # Will topic and message
        if self.will_topic:
            will_topic_bytes = self.will_topic.encode('utf-8')
            payload += struct.pack('!H', len(will_topic_bytes)) + will_topic_bytes
            
            will_message_bytes = self.will_message.encode('utf-8') if self.will_message else b''
            payload += struct.pack('!H', len(will_message_bytes)) + will_message_bytes
        
        # Username and password
        if self.username:
            username_bytes = self.username.encode('utf-8')
            payload += struct.pack('!H', len(username_bytes)) + username_bytes
        
        if self.password:
            password_bytes = self.password.encode('utf-8')
            payload += struct.pack('!H', len(password_bytes)) + password_bytes
        
        return payload


class MQTTConnAckMessage(MQTTMessage):
    """MQTT CONNACK message."""
    
    def __init__(self, return_code: int = 0, session_present: bool = False):
        # CONNACK payload: session present (1 byte) + return code (1 byte)
        payload = struct.pack('!BB', 1 if session_present else 0, return_code)
        super().__init__(MQTTMessageType.CONNACK, 0, payload)


class MQTTPublishMessage(MQTTMessage):
    """MQTT PUBLISH message."""
    
    def __init__(self, topic: str, payload: bytes, qos: int = 0, 
                 retain: bool = False, packet_id: Optional[int] = None):
        self.topic = topic
        self.qos = qos
        self.retain = retain
        self.packet_id = packet_id
        
        # Build variable header and payload
        topic_bytes = topic.encode('utf-8')
        variable_header = struct.pack('!H', len(topic_bytes)) + topic_bytes
        
        if qos > 0 and packet_id is not None:
            variable_header += struct.pack('!H', packet_id)
        
        # Set flags
        flags = 0
        if retain:
            flags |= 0x01
        flags |= (qos & 0x03) << 1
        
        super().__init__(MQTTMessageType.PUBLISH, flags, variable_header + payload)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'MQTTPublishMessage':
        """Parse PUBLISH message from bytes."""
        if len(data) < 2:
            raise ValueError("Invalid PUBLISH message")
        
        # Parse topic length
        topic_length = struct.unpack('!H', data[:2])[0]
        if len(data) < 2 + topic_length:
            raise ValueError("Invalid PUBLISH message")
        
        # Parse topic
        topic = data[2:2+topic_length].decode('utf-8')
        
        # Parse packet ID if QoS > 0
        packet_id = None
        offset = 2 + topic_length
        if len(data) > offset:
            packet_id = struct.unpack('!H', data[offset:offset+2])[0]
            offset += 2
        
        # Payload is the rest
        payload = data[offset:] if offset < len(data) else b''
        
        return cls(topic, payload, packet_id=packet_id)


class MQTTSubscribeMessage(MQTTMessage):
    """MQTT SUBSCRIBE message."""
    
    def __init__(self, packet_id: int, subscriptions: List[Tuple[str, int]]):
        self.packet_id = packet_id
        self.subscriptions = subscriptions
        
        # Build payload
        payload = struct.pack('!H', packet_id)
        for topic, qos in subscriptions:
            topic_bytes = topic.encode('utf-8')
            payload += struct.pack('!H', len(topic_bytes)) + topic_bytes
            payload += struct.pack('!B', qos)
        
        super().__init__(MQTTMessageType.SUBSCRIBE, 2, payload)  # Flags = 2 for SUBSCRIBE


class MQTTSubAckMessage(MQTTMessage):
    """MQTT SUBACK message."""
    
    def __init__(self, packet_id: int, return_codes: List[int]):
        self.packet_id = packet_id
        self.return_codes = return_codes
        
        # Build payload
        payload = struct.pack('!H', packet_id)
        for return_code in return_codes:
            payload += struct.pack('!B', return_code)
        
        super().__init__(MQTTMessageType.SUBACK, 0, payload)


class MQTTPingReqMessage(MQTTMessage):
    """MQTT PINGREQ message."""
    
    def __init__(self):
        super().__init__(MQTTMessageType.PINGREQ, 0, b'')


class MQTTPingRespMessage(MQTTMessage):
    """MQTT PINGRESP message."""
    
    def __init__(self):
        super().__init__(MQTTMessageType.PINGRESP, 0, b'')


class MQTTDisconnectMessage(MQTTMessage):
    """MQTT DISCONNECT message."""
    
    def __init__(self):
        super().__init__(MQTTMessageType.DISCONNECT, 0, b'')


class MQTTParser:
    """MQTT message parser."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_message(self, data: bytes) -> Optional[MQTTMessage]:
        """Parse MQTT message from bytes."""
        if len(data) < 2:
            return None
        
        try:
            # Parse fixed header
            fixed_header = data[0]
            message_type = (fixed_header >> 4) & 0x0F
            flags = fixed_header & 0x0F
            
            # Parse remaining length
            remaining_length, length_bytes = MQTTMessage._decode_remaining_length(data, 1)
            
            # Check if we have complete message
            if len(data) < 1 + length_bytes + remaining_length:
                return None
            
            # Extract payload
            payload = data[1 + length_bytes:1 + length_bytes + remaining_length]
            
            # Create appropriate message object
            if message_type == MQTTMessageType.CONNECT.value:
                return self._parse_connect(payload)
            elif message_type == MQTTMessageType.PUBLISH.value:
                return self._parse_publish(payload, flags)
            elif message_type == MQTTMessageType.SUBSCRIBE.value:
                return self._parse_subscribe(payload)
            elif message_type == MQTTMessageType.PINGREQ.value:
                return MQTTPingReqMessage()
            elif message_type == MQTTMessageType.DISCONNECT.value:
                return MQTTDisconnectMessage()
            else:
                self.logger.warning(f"Unsupported message type: {message_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing MQTT message: {e}")
            return None
    
    def _parse_connect(self, payload: bytes) -> MQTTConnectMessage:
        """Parse CONNECT message."""
        if len(payload) < 10:
            raise ValueError("Invalid CONNECT message")
        
        offset = 0
        
        try:
            # Protocol name
            if offset + 2 > len(payload):
                raise ValueError("Incomplete protocol name length")
            protocol_length = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
            
            if offset + protocol_length > len(payload):
                raise ValueError("Incomplete protocol name")
            protocol_name = payload[offset:offset+protocol_length].decode('utf-8')
            offset += protocol_length
            
            if protocol_name != 'MQTT':
                raise ValueError(f"Unsupported protocol: {protocol_name}")
            
            # Protocol level
            if offset >= len(payload):
                raise ValueError("Incomplete protocol level")
            protocol_level = payload[offset]
            offset += 1
            
            if protocol_level != 4:
                raise ValueError(f"Unsupported protocol level: {protocol_level}")
            
            # Connect flags
            if offset >= len(payload):
                raise ValueError("Incomplete connect flags")
            connect_flags = MQTTConnectFlags(payload[offset])
            offset += 1
            
            # Keep alive
            if offset + 2 > len(payload):
                raise ValueError("Incomplete keep alive")
            keep_alive = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
            
            # Client ID
            if offset + 2 > len(payload):
                raise ValueError("Incomplete client ID length")
            client_id_length = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
            
            if offset + client_id_length > len(payload):
                raise ValueError("Incomplete client ID")
            
            if client_id_length == 0:
                # Empty client ID - generate one
                client_id = f"client_{int(time.time() * 1000)}"
            else:
                client_id = payload[offset:offset+client_id_length].decode('utf-8')
            offset += client_id_length
            
            # Will topic and message (if present)
            will_topic = None
            will_message = None
            if connect_flags.will_flag:
                if offset + 2 > len(payload):
                    raise ValueError("Incomplete will topic length")
                will_topic_length = struct.unpack('!H', payload[offset:offset+2])[0]
                offset += 2
                
                if offset + will_topic_length > len(payload):
                    raise ValueError("Incomplete will topic")
                will_topic = payload[offset:offset+will_topic_length].decode('utf-8')
                offset += will_topic_length
                
                if offset + 2 > len(payload):
                    raise ValueError("Incomplete will message length")
                will_message_length = struct.unpack('!H', payload[offset:offset+2])[0]
                offset += 2
                
                if offset + will_message_length > len(payload):
                    raise ValueError("Incomplete will message")
                will_message = payload[offset:offset+will_message_length].decode('utf-8')
                offset += will_message_length
            
            # Username and password (if present)
            username = None
            password = None
            if connect_flags.username_flag:
                if offset + 2 > len(payload):
                    raise ValueError("Incomplete username length")
                username_length = struct.unpack('!H', payload[offset:offset+2])[0]
                offset += 2
                
                if offset + username_length > len(payload):
                    raise ValueError("Incomplete username")
                username = payload[offset:offset+username_length].decode('utf-8')
                offset += username_length
            
            if connect_flags.password_flag:
                if offset + 2 > len(payload):
                    raise ValueError("Incomplete password length")
                password_length = struct.unpack('!H', payload[offset:offset+2])[0]
                offset += 2
                
                if offset + password_length > len(payload):
                    raise ValueError("Incomplete password")
                password = payload[offset:offset+password_length].decode('utf-8')
                offset += password_length
            
            return MQTTConnectMessage(
                client_id=client_id,
                clean_session=connect_flags.clean_session,
                username=username,
                password=password,
                will_topic=will_topic,
                will_message=will_message,
                will_qos=connect_flags.will_qos,
                will_retain=connect_flags.will_retain,
                keep_alive=keep_alive
            )
            
        except UnicodeDecodeError as e:
            raise ValueError(f"UTF-8 decode error: {e}")
        except struct.error as e:
            raise ValueError(f"Struct unpack error: {e}")
    
    def _parse_publish(self, payload: bytes, flags: int) -> MQTTPublishMessage:
        """Parse PUBLISH message."""
        if len(payload) < 2:
            raise ValueError("Invalid PUBLISH message")
        
        # Parse topic
        topic_length = struct.unpack('!H', payload[:2])[0]
        if len(payload) < 2 + topic_length:
            raise ValueError("Invalid PUBLISH message")
        
        topic = payload[2:2+topic_length].decode('utf-8')
        
        # Parse packet ID if QoS > 0
        packet_id = None
        offset = 2 + topic_length
        qos = (flags >> 1) & 0x03
        
        if qos > 0 and len(payload) > offset + 1:
            packet_id = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
        
        # Payload is the rest
        message_payload = payload[offset:] if offset < len(payload) else b''
        
        return MQTTPublishMessage(
            topic=topic,
            payload=message_payload,
            qos=qos,
            retain=bool(flags & 0x01),
            packet_id=packet_id
        )
    
    def _parse_subscribe(self, payload: bytes) -> MQTTSubscribeMessage:
        """Parse SUBSCRIBE message."""
        if len(payload) < 2:
            raise ValueError("Invalid SUBSCRIBE message")
        
        # Parse packet ID
        packet_id = struct.unpack('!H', payload[:2])[0]
        
        # Parse subscriptions
        subscriptions = []
        offset = 2
        
        while offset < len(payload):
            if offset + 2 > len(payload):
                break
            
            topic_length = struct.unpack('!H', payload[offset:offset+2])[0]
            offset += 2
            
            if offset + topic_length + 1 > len(payload):
                break
            
            topic = payload[offset:offset+topic_length].decode('utf-8')
            offset += topic_length
            
            qos = payload[offset]
            offset += 1
            
            subscriptions.append((topic, qos))
        
        return MQTTSubscribeMessage(packet_id, subscriptions)
