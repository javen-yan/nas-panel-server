"""
Base collector class for system information collection.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseCollector(ABC):
    """Base class for all system information collectors."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the collector with configuration."""
        self.config = config or {}
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect system information.
        
        Returns:
            Dict containing the collected information.
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if the collector can run on this system.
        
        Returns:
            True if the collector can run, False otherwise.
        """
        return True