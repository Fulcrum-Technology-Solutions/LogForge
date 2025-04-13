"""Core engine for the synthetic log generator."""

import datetime
import importlib
import importlib.metadata
import logging
import os
import random
import threading
import time
from typing import Dict, List, Set, Type, Optional, Any, Tuple

from logforge.core.registry import EntityRegistry
from logforge.core.scheduler import Scheduler
from logforge.core.templates import TemplateManager
from logforge.outputs.base import OutputAdapter

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


class TemplateBasedGenerator(LogGenerator):
    """Generator that uses a template file directly."""
    
    def __init__(self, name: str, template_path: str, template_manager, metadata: Dict = None):
        """Initialize the generator.
        
        Args:
            name: Name of the generator
            template_path: Path to the template file
            template_manager: Template manager for rendering templates
            metadata: Optional metadata for the generator
        """
        super().__init__(name)
        self.template_path = template_path
        self.template_manager = template_manager
        self.metadata = metadata or {}
        
        # Default frequency if not specified in metadata
        self.base_frequency = self.metadata.get('base_frequency', 0.1)
        
        # Get patterns from metadata
        self.time_patterns = self.metadata.get('time_patterns', [])
        
    def get_frequency(self) -> float:
        """Get the current frequency of log generation.
        
        Returns:
            The frequency in entries per second
        """
        # Start with the base frequency
        frequency = self.base_frequency
        
        # Apply time-based patterns based on current time
        now = datetime.datetime.now()
        hour = now.hour
        
        # Increase frequency during business hours (9am - 5pm)
        if 9 <= hour < 17 and 'business_hours' in self.time_patterns:
            frequency *= self.metadata.get('business_hours_multiplier', 2.0)
            
        # Reduce frequency during night hours (11pm - 6am)
        if (hour >= 23 or hour < 6) and 'night_hours' in self.time_patterns:
            frequency *= self.metadata.get('night_hours_multiplier', 0.3)
            
        # Apply day of week patterns
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Weekend pattern
        if weekday >= 5 and 'weekend' in self.time_patterns:  # Saturday or Sunday
            frequency *= self.metadata.get('weekend_multiplier', 0.5)
            
        # Add some randomness
        frequency *= random.uniform(0.8, 1.2)
        
        return frequency
        
    def generate(self, registry: EntityRegistry) -> str:
        """Generate a log entry using the template.
        
        Args:
            registry: Entity registry to use
            
        Returns:
            The generated log entry
        """
        # Get random entities from registry
        user = registry.get_random_user()
        device = registry.get_random_device()
        service = registry.get_random_service()
        
        # Create context with common variables
        context = {
            # Standard context values
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'process_id': random.randint(1000, 10000),
            'thread_id': random.randint(1000, 10000),
            'hostname': device.hostname if device else f"host-{random.randint(1, 1000)}",
            'ip_address': device.ip_address if device else self.template_manager.random_private_ip(),
            'username': user.username if user else f"user{random.randint(1, 1000)}",
            'domain': "CONTOSO",
            'generator': self.name,
            
            # Add all metadata fields to context for use in templates
            **self.metadata.get('context', {})
        }
        
        # Log template context for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Rendering template for {self.name} with generator name: {context.get('generator', 'unknown')}")
        
        # Render the template
        try:
            rendered = self.template_manager.render_template(
                self.template_path,
                registry,
                context
            )
            
            # Return raw template output without any modifications
            # This ensures formats are preserved exactly as rendered
            return rendered
        except Exception as e:
            logger.error(f"Error rendering template for {self.name}: {e}")
            return f"ERROR: Failed to render template for {self.name}: {e}"


class Engine:
    """Core engine for the synthetic log generator."""
    
    def __init__(self, network_ranges: List[Tuple[str, str]] = None):
        """Initialize the engine.
        
        Args:
            network_ranges: Optional list of tuples with start and end IP addresses for internal networks
                           Each tuple can optionally include a name as a third element
                           Note: This parameter is kept for backward compatibility but is now ignored
                           as network ranges are loaded from the entity registry.
        """
        self.generators: Dict[str, LogGenerator] = {}
        self.outputs: List[OutputAdapter] = []
        self.registry = EntityRegistry()
        self.scheduler = Scheduler()
        self.running = False
        self.threads: List[threading.Thread] = []
        
        # Initialize template manager (network_ranges will be updated after registry is loaded)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
    def is_running(self) -> bool:
        """Check if the engine is running.
        
        Returns:
            True if the engine is running, False otherwise
        """
        return self.running
        
    def discover_packages(self):
        """Discover and load available packages."""
        logger.info("Discovering packages...")
        
        # First, discover packages (this is for backward compatibility)
        try:
            # Python 3.10+ way
            for entry_point in importlib.metadata.entry_points(group='logforge.packages'):
                logger.info(f"Loading package: {entry_point.name}")
                try:
                    register_func = entry_point.load()
                    register_func(self)
                except Exception as e:
                    logger.error(f"Failed to load package {entry_point.name}: {e}")
        except TypeError:
            # Python 3.9 and earlier way
            for entry_point in importlib.metadata.entry_points().get('logforge.packages', []):
                logger.info(f"Loading package: {entry_point.name}")
                try:
                    register_func = entry_point.load()
                    register_func(self)
                except Exception as e:
                    logger.error(f"Failed to load package {entry_point.name}: {e}")
        
        # Update the template manager with network ranges from the registry
        self.template_manager.set_network_ranges(self.registry.get_network_ranges())
        
        # Now directly discover and load all available generators
        self.discover_generators()
    
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
                    # Don't send error messages via HTTP, only log them
                    if log_entry.startswith("ERROR:"):
                        logger.error(log_entry)
                    else:
                        self._send_to_outputs(log_entry, generator)
                    
                # Sleep for the time calculated from the frequency
                sleep_time = 1.0 / frequency if frequency > 0 else 1.0
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in generator {generator.name}: {e}")
                time.sleep(1.0)  # Avoid tight loop in case of persistent errors
                
    def _send_to_outputs(self, log_entry: str, generator=None):
        """Send a log entry to all outputs.
        
        Args:
            log_entry: The log entry to send
            generator: The generator that produced this entry (for file extension info)
        """
        # Get the file extension from the generator's template path if available
        file_extension = None
        metadata = None
        
        if generator and hasattr(generator, 'template_path'):
            _, file_extension = os.path.splitext(generator.template_path)
            
            # Get metadata if available
            if hasattr(generator, 'metadata') and generator.metadata:
                metadata = dict(generator.metadata)  # Make a copy to avoid modifying original
            else:
                metadata = {}
                
            # Add generator name to metadata for file routing
            if hasattr(generator, 'name'):
                metadata['generator'] = generator.name
                
            # Add template path to metadata for folder-based routing
            metadata['template_path'] = generator.template_path
            
        for output in self.outputs:
            try:
                # Log which output we're sending to (debug level only)
                logger.debug(f"Sending log entry to output: {output.name} (type: {output.__class__.__name__})")
                
                # Determine proper file extension based on format in metadata 
                # This ensures file matches actual content format, not template extension
                output_extension = file_extension
                if metadata and 'format' in metadata:
                    format_value = metadata['format'].lower()
                    # Map format to appropriate extension
                    format_to_ext = {
                        'json': '.json',
                        'xml': '.xml',
                        'text': '.txt',
                        'csv': '.csv',
                        'cef': '.log',
                        'leef': '.log',
                        'kv': '.log',
                        'syslog': '.log'
                    }
                    if format_value in format_to_ext:
                        output_extension = format_to_ext[format_value]
                
                # Pass the file extension and metadata to the output if it supports it
                result = False
                if hasattr(output, 'send_with_extension'):
                    logger.debug(f"Output {output.name} supports send_with_extension method")
                    result = output.send_with_extension(log_entry, output_extension, metadata)
                else:
                    logger.debug(f"Output {output.name} using standard send method")
                    result = output.send(log_entry)
                    
                # Log the result (info level to avoid console during menu operation)
                if result:
                    logger.debug(f"Successfully sent log to output: {output.name}")
                else:
                    logger.info(f"Failed to send log to output: {output.name}")
            except Exception as e:
                logger.info(f"Error sending to output {output.name}: {e}")
                
    def discover_generators(self):
        """Discover and load all available generators via entry points."""
        logger.info("Discovering generators...")
        
        # First discover code-based generators from entry points
        try:
            # Python 3.10+ way
            for entry_point in importlib.metadata.entry_points(group='logforge.generators'):
                self._load_generator_from_entry_point(entry_point)
        except TypeError:
            # Python 3.9 and earlier way
            for entry_point in importlib.metadata.entry_points().get('logforge.generators', []):
                self._load_generator_from_entry_point(entry_point)
        
        # Then discover template-based generators
        self.discover_template_generators()
    
    def _load_generator_from_entry_point(self, entry_point):
        """Load a generator from an entry point.
        
        Args:
            entry_point: The entry point to load
        """
        logger.info(f"Loading generator: {entry_point.name}")
        try:
            generator_class = entry_point.load()
            generator = generator_class()
            self.register_generator(generator)
        except Exception as e:
            logger.error(f"Failed to load generator {entry_point.name}: {e}")
            
    def discover_template_generators(self):
        """Discover and create generators from templates in the template directory."""
        logger.info("Discovering template-based generators...")
        
        # Get all template paths
        template_paths = self.template_manager.get_all_template_paths()
        
        for template_path in template_paths:
            try:
                # Get metadata for this template
                metadata = self.template_manager.get_template_metadata(template_path)
                
                # Skip if this is not meant to be a generator
                if not metadata.get('is_generator', True):
                    continue
                
                # Create a generator name from the path
                # Format: vendor_product_datasource (from metadata if possible)
                vendor = metadata.get('vendor', '').lower() or os.path.dirname(template_path).split('/')[0]
                product = metadata.get('product', '').lower() or os.path.dirname(template_path).split('/')[1] if len(os.path.dirname(template_path).split('/')) > 1 else ''
                data_source = metadata.get('data_source', '').lower().replace(' ', '_') or os.path.splitext(os.path.basename(template_path))[0]
                
                # Construct generator name
                base_name = f"{vendor}_{product}"
                if data_source:
                    base_name = f"{base_name}_{data_source}"
                    
                # Clean up name (remove special chars)
                generator_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in base_name)
                
                # Don't create duplicate generators
                if generator_name in self.generators:
                    continue
                
                # Create and register the generator
                logger.info(f"Creating template-based generator: {generator_name} for {template_path}")
                generator = TemplateBasedGenerator(
                    name=generator_name,
                    template_path=template_path,
                    template_manager=self.template_manager,
                    metadata=metadata
                )
                self.register_generator(generator)
                
            except Exception as e:
                logger.error(f"Error creating generator for template {template_path}: {e}")