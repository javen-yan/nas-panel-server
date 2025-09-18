"""
Main data collector that coordinates all collectors and handles scheduling.
"""

import time
import threading
import logging
from typing import Dict, Any, List
from .collectors import SystemCollector, CustomCollector
from .mqtt_server import MQTTServer


class DataCollector:
    """Main data collector that coordinates system and custom collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the data collector."""
        self.config = config
        self.collection_config = config.get('collection', {})
        
        self.interval = self.collection_config.get('interval', 5)  # seconds
        
        # Initialize collectors
        self.system_collector = SystemCollector(config)
        self.custom_collector = CustomCollector(config)
        
        # Initialize MQTT server
        self.mqtt_server = MQTTServer(config)
        
        # Control variables
        self.is_running = False
        self.collection_thread = None
        
        self.logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """Start the data collection service."""
        if self.is_running:
            self.logger.warning("Data collector is already running")
            return
        
        try:
            # Start MQTT server first
            self.mqtt_server.start()
            
            # Start collection thread
            self.is_running = True
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            
            self.logger.info(f"Data collector started with {self.interval}s interval")
            
        except Exception as e:
            self.logger.error(f"Failed to start data collector: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop the data collection service."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping data collector...")
        self.is_running = False
        
        # Stop MQTT server
        self.mqtt_server.stop()
        
        # Wait for collection thread to finish
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        
        self.logger.info("Data collector stopped")
    
    def collect_once(self) -> Dict[str, Any]:
        """
        Collect data once from all collectors.
        
        Returns:
            Combined data from all collectors
        """
        try:
            # Collect system data
            system_data = self.system_collector.collect()
            
            # Collect custom data
            custom_data = self.custom_collector.collect()
            
            # Merge data
            if custom_data:
                system_data['custom'] = custom_data
            
            return system_data
            
        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            return {}
    
    def _collection_loop(self) -> None:
        """Main collection loop that runs in a separate thread."""
        self.logger.info("Starting data collection loop")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Collect data
                data = self.collect_once()
                
                if data:
                    # Publish to MQTT
                    success = self.mqtt_server.publish_data(data)
                    if success:
                        self.logger.debug("Data published successfully")
                    else:
                        self.logger.warning("Failed to publish data")
                else:
                    self.logger.warning("No data collected")
                
                # Calculate sleep time to maintain interval
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Collection took {elapsed_time:.2f}s, longer than interval {self.interval}s")
                    
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                time.sleep(1)  # Brief pause before retrying
        
        self.logger.info("Data collection loop stopped")


class ScheduledCollector:
    """Alternative collector using schedule library for more complex scheduling."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the scheduled collector."""
        self.config = config
        self.data_collector = DataCollector(config)
        
        self.logger = logging.getLogger(f"{__name__}.ScheduledCollector")
    
    def start(self) -> None:
        """Start the scheduled collector."""
        try:
            import schedule
            
            interval = self.config.get('collection', {}).get('interval', 5)
            
            # Schedule the collection job
            schedule.every(interval).seconds.do(self._collect_and_publish)
            
            # Start MQTT server
            self.data_collector.mqtt_server.start()
            
            self.logger.info(f"Scheduled collector started with {interval}s interval")
            
            # Run scheduler
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except ImportError:
            self.logger.error("Schedule library not available, falling back to simple collector")
            self.data_collector.start()
        except KeyboardInterrupt:
            self.logger.info("Scheduled collector interrupted")
        except Exception as e:
            self.logger.error(f"Error in scheduled collector: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the scheduled collector."""
        self.data_collector.stop()
    
    def _collect_and_publish(self) -> None:
        """Collect data and publish to MQTT."""
        try:
            data = self.data_collector.collect_once()
            if data:
                self.data_collector.mqtt_server.publish_data(data)
        except Exception as e:
            self.logger.error(f"Error in scheduled collection: {e}")