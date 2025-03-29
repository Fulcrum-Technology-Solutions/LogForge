"""Core engine for the synthetic log generator."""

import importlib
import importlib.metadata
import logging
import threading
import time
from typing import Dict, List, Set, Type, Optional

from synth_logs.core.registry import EntityRegistry
from synth_logs.core.scheduler import Scheduler
from synth_logs.outputs.base import OutputAdapter

logger = logging.getLogger(__name__)


class LogGenerator:
    """Base class for log generators."""
    
    def __init__(self, name: str):
        """Initialize the log generator.
        
        Args:
            name: The name of the log generator
        """
        self.name = name
        self.active = False
        
    def generate(self, registry: EntityRegistry) -> str:
        """Generate a log entry.
        
        Args:
            registry: The entity registry to use for generating logs
            
        Returns:
            The generated log entry
        """
        raise NotImplementedError("Log generators must implement the generate method")
    
    def get_frequency(self) -> float:
        """Get the current frequency of log generation in entries per second.
        
        Returns:
            The frequency in entries per second
        """
        raise NotImplementedError("Log generators must implement the get_frequency method")


class Engine:
    """Core engine for the synthetic log generator."""
    
    def __init__(self):
        """Initialize the engine."""
        self.generators: Dict[str, LogGenerator] = {}
        self.outputs: List[OutputAdapter] = []
        self.registry = EntityRegistry()
        self.scheduler = Scheduler()
        self.running = False
        self.threads: List[threading.Thread] = []
        
    def discover_packages(self):
        """Discover and load available packages."""
        logger.info("Discovering packages...")
        
        try:
            # Python 3.10+ way
            for entry_point in importlib.metadata.entry_points(group='synth_logs.packages'):
                logger.info(f"Loading package: {entry_point.name}")
                try:
                    register_func = entry_point.load()
                    register_func(self)
                except Exception as e:
                    logger.error(f"Failed to load package {entry_point.name}: {e}")
        except TypeError:
            # Python 3.9 and earlier way
            for entry_point in importlib.metadata.entry_points().get('synth_logs.packages', []):
                logger.info(f"Loading package: {entry_point.name}")
                try:
                    register_func = entry_point.load()
                    register_func(self)
                except Exception as e:
                    logger.error(f"Failed to load package {entry_point.name}: {e}")
    
    def register_generator(self, generator: LogGenerator):
        """Register a log generator.
        
        Args:
            generator: The log generator to register
        """
        logger.info(f"Registering generator: {generator.name}")
        self.generators[generator.name] = generator
        
    def add_output(self, output: OutputAdapter):
        """Add an output adapter.
        
        Args:
            output: The output adapter to add
        """
        logger.info(f"Adding output: {output.name}")
        self.outputs.append(output)
        
    def start_generator(self, name: str):
        """Start a specific log generator.
        
        Args:
            name: The name of the generator to start
        """
        if name in self.generators:
            logger.info(f"Starting generator: {name}")
            generator = self.generators[name]
            generator.active = True
            thread = threading.Thread(
                target=self._generator_loop,
                args=(generator,),
                daemon=True,
                name=f"generator-{name}"
            )
            thread.start()
            self.threads.append(thread)
        else:
            logger.warning(f"Generator not found: {name}")
            
    def stop_generator(self, name: str):
        """Stop a specific log generator.
        
        Args:
            name: The name of the generator to stop
        """
        if name in self.generators:
            logger.info(f"Stopping generator: {name}")
            self.generators[name].active = False
        else:
            logger.warning(f"Generator not found: {name}")
            
    def start(self):
        """Start the engine."""
        logger.info("Starting engine...")
        if not self.outputs:
            logger.warning("No outputs configured, logs will not be sent anywhere")
        
        self.running = True
        for name, generator in self.generators.items():
            if generator.active:
                self.start_generator(name)
                
    def stop(self):
        """Stop the engine."""
        logger.info("Stopping engine...")
        self.running = False
        
        for generator in self.generators.values():
            generator.active = False
            
        for thread in self.threads:
            thread.join(timeout=2.0)
            
        self.threads = []
        
    def _generator_loop(self, generator: LogGenerator):
        """Run the generator loop.
        
        Args:
            generator: The generator to run
        """
        while self.running and generator.active:
            try:
                frequency = generator.get_frequency()
                if frequency > 0:
                    log_entry = generator.generate(self.registry)
                    self._send_to_outputs(log_entry)
                    
                # Sleep for the time calculated from the frequency
                sleep_time = 1.0 / frequency if frequency > 0 else 1.0
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in generator {generator.name}: {e}")
                time.sleep(1.0)  # Avoid tight loop in case of persistent errors
                
    def _send_to_outputs(self, log_entry: str):
        """Send a log entry to all outputs.
        
        Args:
            log_entry: The log entry to send
        """
        for output in self.outputs:
            try:
                output.send(log_entry)
            except Exception as e:
                logger.error(f"Error sending to output {output.name}: {e}")