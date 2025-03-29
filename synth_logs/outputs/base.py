"""Base output adapter interface."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class OutputAdapter(ABC):
    """Base class for output adapters."""
    
    def __init__(self, name: str):
        """Initialize the output adapter.
        
        Args:
            name: The name of the output adapter
        """
        self.name = name
        
    @abstractmethod
    def send(self, log_entry: str) -> bool:
        """Send a log entry to the output.
        
        Args:
            log_entry: The log entry to send
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        pass
        
    @abstractmethod
    def close(self):
        """Close the output adapter."""
        pass