"""Output adapter for sending logs to stdout."""

import logging
import sys
from typing import TextIO

from logforge.outputs.base import OutputAdapter

logger = logging.getLogger(__name__)


class StdoutAdapter(OutputAdapter):
    """Output adapter for sending logs to stdout."""
    
    def __init__(self, name: str = "stdout", output_stream: TextIO = None):
        """Initialize the stdout adapter.
        
        Args:
            name: The name of the adapter
            output_stream: The output stream to use (defaults to sys.stdout)
        """
        super().__init__(name)
        self.output_stream = output_stream or sys.stdout
        
    def send(self, log_entry: str) -> bool:
        """Send a log entry to stdout.
        
        Args:
            log_entry: The log entry to send
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        try:
            print(log_entry, file=self.output_stream, flush=True)
            return True
        except Exception as e:
            logger.error(f"Error sending log to stdout: {e}")
            return False
            
    def close(self):
        """Close the output adapter.
        
        For stdout, this is a no-op as we don't want to close stdout.
        """
        # No need to close stdout
        pass