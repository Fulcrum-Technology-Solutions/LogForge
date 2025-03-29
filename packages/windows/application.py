"""Windows Application Event Log generator."""

import datetime
import logging
import os
import random
from typing import List

from synth_logs.core.engine import LogGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.core.templates import TemplateManager

logger = logging.getLogger(__name__)


class ApplicationLogGenerator(LogGenerator):
    """Generator for Windows Application Event Logs."""
    
    def __init__(self):
        """Initialize the generator."""
        super().__init__("windows_application")
        
        # Initialize template manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
        # Define the event types we can generate
        self.event_types = [
            {
                'template': 'windows/application/info.xml',
                'event_id': 1000,
                'level': 'Information',
                'description': 'Application information',
                'weight': 20,
                'time_patterns': ['business_hours']
            },
            {
                'template': 'windows/application/warning.xml',
                'event_id': 1001,
                'level': 'Warning',
                'description': 'Application warning',
                'weight': 5,
                'time_patterns': ['business_hours']
            },
            {
                'template': 'windows/application/error.xml',
                'event_id': 1002,
                'level': 'Error',
                'description': 'Application error',
                'weight': 2,
                'time_patterns': ['business_hours']
            },
            {
                'template': 'windows/application/crash.xml',
                'event_id': 1000,
                'level': 'Error',
                'description': 'Application crash',
                'weight': 1,
                'time_patterns': ['business_hours']
            }
        ]
        
        # Application names
        self.applications = [
            "Microsoft.Office.Outlook",
            "Microsoft.Office.Word",
            "Microsoft.Office.Excel",
            "Microsoft.Office.PowerPoint",
            "MicrosoftEdge",
            "Chrome",
            "Firefox",
            "Teams",
            "Skype",
            "Notepad",
            "Calculator",
            "Explorer"
        ]
        
        # Base frequency - how many events per second on average
        self.base_frequency = 0.1  # Events per second
        
    def get_frequency(self) -> float:
        """Get the current frequency of log generation.
        
        Returns:
            The frequency in entries per second
        """
        # Get the current time
        now = datetime.datetime.now()
        
        # Start with the base frequency
        frequency = self.base_frequency
        
        # Apply time-based patterns
        hour = now.hour
        
        # Increase frequency during business hours (9am - 5pm)
        if 9 <= hour < 17:
            frequency *= 2.0
            
        # Reduce frequency during night hours (11pm - 6am)
        if hour >= 23 or hour < 6:
            frequency *= 0.1
            
        # Small random variation
        frequency *= random.uniform(0.8, 1.2)
        
        return frequency
        
    def generate(self, registry: EntityRegistry) -> str:
        """Generate a Windows Application Event Log entry.
        
        Args:
            registry: The entity registry to use for generating logs
            
        Returns:
            The generated log entry as an XML string
        """
        # Select an event type based on weights
        weights = [event['weight'] for event in self.event_types]
        event_type = random.choices(self.event_types, weights=weights, k=1)[0]
        
        # Get a random device from the registry, or create a generic one if none exist
        device = registry.get_random_device()
        if not device:
            hostname = f"WIN-{random.randint(10000, 99999)}"
        else:
            hostname = device.hostname
            
        # Get a random application
        application = random.choice(self.applications)
        
        # Error messages for different levels
        info_messages = [
            "Application started successfully",
            "Configuration loaded",
            "Feature enabled",
            "Auto-save completed",
            "Update check completed, no updates available"
        ]
        
        warning_messages = [
            "Configuration file is outdated",
            "Feature is deprecated",
            "Performance is degraded",
            "Connection attempt timed out, retrying",
            "Device is running low on memory"
        ]
        
        error_messages = [
            "Failed to connect to server",
            "Configuration file is corrupt",
            "Required file not found",
            "Access denied to resource",
            "Database connection failed"
        ]
        
        crash_messages = [
            "Application has stopped working",
            "Fatal error occurred",
            "Unhandled exception",
            "Memory access violation",
            "Stack overflow detected"
        ]
        
        # Select a message based on the level
        if event_type['level'] == 'Information':
            message = random.choice(info_messages)
        elif event_type['level'] == 'Warning':
            message = random.choice(warning_messages)
        elif event_type['level'] == 'Error' and 'crash' in event_type['description'].lower():
            message = random.choice(crash_messages)
        else:
            message = random.choice(error_messages)
            
        # Prepare the context for the template
        context = {
            'event_id': event_type['event_id'],
            'level': event_type['level'],
            'description': event_type['description'],
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'hostname': hostname,
            'process_id': random.randint(1000, 10000),
            'thread_id': random.randint(1000, 10000),
            'application': application,
            'message': message
        }
        
        # Ensure the template directory exists
        template_dir = os.path.join('templates', 'windows', 'application')
        os.makedirs(template_dir, exist_ok=True)
        
        # Create the template files if they don't exist
        for template_name in ['info.xml', 'warning.xml', 'error.xml', 'crash.xml']:
            template_path = os.path.join('windows', 'application', template_name)
            template_file = os.path.join('templates', template_path)
            if not os.path.exists(template_file):
                os.makedirs(os.path.dirname(template_file), exist_ok=True)
                with open(template_file, 'w') as f:
                    f.write("""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="{{ application }}" Guid="{D16D0BBE-7129-472A-B1E9-8E0AD5D8F3B4}" />
    <EventID Qualifiers="0">{{ event_id }}</EventID>
    <Version>0</Version>
    <Level>{{ 2 if level == 'Error' else (3 if level == 'Warning' else 4) }}</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x80000000000000</Keywords>
    <TimeCreated SystemTime="{{ timestamp }}" />
    <EventRecordID>{{ random_int(100000, 999999) }}</EventRecordID>
    <Correlation />
    <Execution ProcessID="{{ process_id }}" ThreadID="{{ thread_id }}" />
    <Channel>Application</Channel>
    <Computer>{{ hostname }}</Computer>
    <Security />
  </System>
  <EventData>
    <Data>{{ message }}</Data>
    <Data>{{ application }}</Data>
    <Data>{{ random_int(10000, 99999) }}</Data>
  </EventData>
</Event>""")
        
        # Render the template
        try:
            return self.template_manager.render_template(
                event_type['template'],
                registry,
                context
            )
        except Exception as e:
            logger.error(f"Error rendering template for Windows Application Event: {e}")
            return f"ERROR: Failed to render Windows Application Event: {e}"