"""
Main NAS Panel Server application.
"""

import sys
import signal
import logging
import argparse
from pathlib import Path
from typing import Optional

from .config_manager import ConfigManager
from .data_collector import DataCollector


class NASPanelServer:
    """Main NAS Panel Server application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the NAS Panel Server.
        
        Args:
            config_path: Path to configuration file
        """
        # Set up logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing NAS Panel Server")
        
        # Load configuration
        self.config_manager = ConfigManager(config_path)
        
        # Validate configuration
        errors = self.config_manager.validate_config()
        if errors:
            self.logger.error("Configuration validation failed:")
            for error in errors:
                self.logger.error(f"  - {error}")
            raise ValueError("Invalid configuration")
        
        # Initialize data collector
        self.data_collector = DataCollector(self.config_manager.get_config())
        
        # Signal handling
        self._setup_signal_handlers()
        
        self.logger.info("NAS Panel Server initialized successfully")
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('nas_panel_server.log', mode='a')
            ]
        )
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self) -> None:
        """Start the NAS Panel Server."""
        try:
            self.logger.info("Starting NAS Panel Server...")
            
            # Print configuration summary
            config = self.config_manager.get_config()
            self.logger.info(f"Server hostname: {config.get('server', {}).get('hostname', 'unknown')}")
            self.logger.info(f"MQTT broker: {config.get('mqtt', {}).get('host', 'unknown')}:{config.get('mqtt', {}).get('port', 'unknown')}")
            self.logger.info(f"MQTT topic: {config.get('mqtt', {}).get('topic', 'unknown')}")
            self.logger.info(f"Collection interval: {config.get('collection', {}).get('interval', 'unknown')}s")
            
            custom_collectors = config.get('custom_collectors', [])
            if custom_collectors:
                self.logger.info(f"Custom collectors: {len(custom_collectors)}")
                for collector in custom_collectors:
                    self.logger.info(f"  - {collector.get('name', 'unknown')} ({collector.get('type', 'unknown')})")
            
            # Start data collector
            self.data_collector.start()
            
            self.logger.info("NAS Panel Server started successfully")
            self.logger.info("Press Ctrl+C to stop the server")
            
            # Keep the main thread alive
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the NAS Panel Server."""
        self.logger.info("Stopping NAS Panel Server...")
        
        try:
            # Stop data collector
            self.data_collector.stop()
            
            self.logger.info("NAS Panel Server stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
    
    def test_collection(self) -> None:
        """Test data collection once and print results."""
        self.logger.info("Testing data collection...")
        
        try:
            data = self.data_collector.collect_once()
            
            if data:
                import json
                print("\nCollected data:")
                print(json.dumps(data, indent=2))
                self.logger.info("Data collection test successful")
            else:
                self.logger.warning("No data collected")
                
        except Exception as e:
            self.logger.error(f"Error during collection test: {e}")
            raise


def main():
    """Main entry point for the NAS Panel Server."""
    parser = argparse.ArgumentParser(
        description="NAS Panel Server - System monitoring with MQTT publishing"
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '-t', '--test',
        action='store_true',
        help='Test data collection once and exit'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--generate-config',
        type=str,
        help='Generate a sample configuration file at the specified path'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Generate config if requested
    if args.generate_config:
        try:
            config_manager = ConfigManager()
            config_manager.save_config(args.generate_config)
            print(f"Sample configuration saved to {args.generate_config}")
            return
        except Exception as e:
            print(f"Error generating configuration: {e}")
            sys.exit(1)
    
    # Initialize server
    try:
        server = NASPanelServer(args.config)
        
        if args.test:
            # Test mode
            server.test_collection()
        else:
            # Normal operation
            server.start()
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()