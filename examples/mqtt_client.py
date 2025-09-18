#!/usr/bin/env python3
"""
Example MQTT client for NAS Panel Server.
"""

import json
import time
import argparse
import paho.mqtt.client as mqtt


class NASPanelClient:
    """Example MQTT client for receiving NAS panel data."""
    
    def __init__(self, host="localhost", port=1883, topic="nas/panel/data"):
        self.host = host
        self.port = port
        self.topic = topic
        
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.last_data = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response."""
        if rc == 0:
            print(f"Connected to MQTT broker at {self.host}:{self.port}")
            client.subscribe(self.topic)
            print(f"Subscribed to topic: {self.topic}")
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received."""
        try:
            # Parse JSON data
            data = json.loads(msg.payload.decode())
            self.last_data = data
            
            # Print formatted data
            self._print_data(data)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects."""
        if rc != 0:
            print("Unexpected disconnection from MQTT broker")
        else:
            print("Disconnected from MQTT broker")
    
    def _print_data(self, data):
        """Print formatted system data."""
        print("\n" + "="*60)
        print(f"📊 NAS Panel Data - {data.get('timestamp', 'Unknown time')}")
        print("="*60)
        
        # Basic info
        print(f"🖥️  Hostname: {data.get('hostname', 'Unknown')}")
        print(f"🌐 IP Address: {data.get('ip', 'Unknown')}")
        
        # CPU info
        cpu = data.get('cpu', {})
        cpu_usage = cpu.get('usage', 0)
        cpu_temp = cpu.get('temperature')
        
        print(f"🔥 CPU Usage: {cpu_usage:.1f}%", end="")
        if cpu_temp is not None:
            print(f" (Temp: {cpu_temp:.1f}°C)")
        else:
            print()
        
        # Memory info
        memory = data.get('memory', {})
        mem_usage = memory.get('usage', 0)
        mem_total = memory.get('total', 0)
        mem_used = memory.get('used', 0)
        mem_temp = memory.get('temperature')
        
        print(f"💾 Memory: {mem_usage:.1f}% ", end="")
        if mem_total > 0:
            print(f"({self._format_bytes(mem_used)}/{self._format_bytes(mem_total)})", end="")
        if mem_temp is not None:
            print(f" (Temp: {mem_temp:.1f}°C)")
        else:
            print()
        
        # Storage info
        storage = data.get('storage', {})
        storage_capacity = storage.get('capacity', 0)
        storage_used = storage.get('used', 0)
        disks = storage.get('disks', [])
        
        if storage_capacity > 0:
            storage_usage = (storage_used / storage_capacity) * 100
            print(f"💿 Storage: {storage_usage:.1f}% ({self._format_bytes(storage_used)}/{self._format_bytes(storage_capacity)})")
        
        if disks:
            disk_status = {}
            for disk in disks:
                status = disk.get('status', 'unknown')
                disk_status[status] = disk_status.get(status, 0) + 1
            
            status_str = []
            for status, count in disk_status.items():
                emoji = {"normal": "✅", "warning": "⚠️", "error": "❌"}.get(status, "❓")
                status_str.append(f"{emoji} {count} {status}")
            
            print(f"🗂️  Disks: {' | '.join(status_str)}")
        
        # Network info
        network = data.get('network', {})
        upload = network.get('upload', 0)
        download = network.get('download', 0)
        
        print(f"🌐 Network: ⬆️ {self._format_bytes(upload)}/s | ⬇️ {self._format_bytes(download)}/s")
        
        # Custom data
        custom = data.get('custom', {})
        if custom:
            print("🔧 Custom Data:")
            for name, info in custom.items():
                if isinstance(info, dict):
                    value = info.get('value', 'N/A')
                    unit = info.get('unit', '')
                    print(f"   - {name}: {value} {unit}")
                else:
                    print(f"   - {name}: {info}")
    
    def _format_bytes(self, bytes_value):
        """Format bytes into human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def start(self):
        """Start the MQTT client."""
        try:
            print(f"Connecting to MQTT broker at {self.host}:{self.port}...")
            self.client.connect(self.host, self.port, 60)
            
            print("Starting MQTT client loop...")
            print("Press Ctrl+C to stop")
            
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client.disconnect()
    
    def get_last_data(self):
        """Get the last received data."""
        return self.last_data


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="NAS Panel MQTT Client")
    
    parser.add_argument(
        '-H', '--host',
        type=str,
        default='localhost',
        help='MQTT broker host (default: localhost)'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=1883,
        help='MQTT broker port (default: 1883)'
    )
    
    parser.add_argument(
        '-t', '--topic',
        type=str,
        default='nas/panel/data',
        help='MQTT topic to subscribe to (default: nas/panel/data)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Receive one message and exit'
    )
    
    args = parser.parse_args()
    
    client = NASPanelClient(args.host, args.port, args.topic)
    
    if args.once:
        # Connect and wait for one message
        print(f"Connecting to {args.host}:{args.port} and waiting for one message...")
        
        received = False
        
        def on_message_once(client, userdata, msg):
            nonlocal received
            try:
                data = json.loads(msg.payload.decode())
                print(json.dumps(data, indent=2))
                received = True
                client.disconnect()
            except Exception as e:
                print(f"Error: {e}")
                received = True
                client.disconnect()
        
        client.client.on_message = on_message_once
        client.client.connect(args.host, args.port, 60)
        client.client.subscribe(args.topic)
        
        # Wait for message or timeout
        timeout = 30
        start_time = time.time()
        
        while not received and (time.time() - start_time) < timeout:
            client.client.loop(timeout=1)
        
        if not received:
            print(f"No message received within {timeout} seconds")
    else:
        # Normal operation
        client.start()


if __name__ == '__main__':
    main()