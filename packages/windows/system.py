"""Windows System Event Log generator."""

import datetime
import logging
import os
import random
from typing import List

from synth_logs.core.engine import LogGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.core.templates import TemplateManager

logger = logging.getLogger(__name__)


class SystemLogGenerator(LogGenerator):
    """Generator for Windows System Event Logs."""
    
    def __init__(self):
        """Initialize the generator."""
        super().__init__("windows_system")
        
        # Initialize template manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
        # Define the event types we can generate
        self.event_types = [
            {
                'template': 'windows/system/service_start.xml',
                'event_id': 7036,
                'description': 'Service started',
                'weight': 10,
                'time_patterns': ['business_hours']
            },
            {
                'template': 'windows/system/service_stop.xml',
                'event_id': 7036,
                'description': 'Service stopped',
                'weight': 5,
                'time_patterns': ['business_hours']
            },
            {
                'template': 'windows/system/time_change.xml',
                'event_id': 1,
                'description': 'System time changed',
                'weight': 1,
                'time_patterns': ['business_hours']
            }
        ]
        
        # Base frequency - how many events per second on average
        self.base_frequency = 0.2  # Events per second
        
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
            frequency *= 1.5
            
        # Reduce frequency during night hours (11pm - 6am)
        if hour >= 23 or hour < 6:
            frequency *= 0.2
            
        # Small random variation
        frequency *= random.uniform(0.8, 1.2)
        
        return frequency
        
    def generate(self, registry: EntityRegistry) -> str:
        """Generate a Windows System Event Log entry.
        
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
            
        # Get a random service from the registry, or create a generic one if none exist
        service = registry.get_random_service()
        if not service:
            service_name = f"Service{random.randint(1, 100)}"
            display_name = f"Generic Service {random.randint(1, 100)}"
        else:
            service_name = service.name.replace(' ', '')
            display_name = service.name
            
        # Prepare the context for the template
        context = {
            'event_id': event_type['event_id'],
            'description': event_type['description'],
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'hostname': hostname,
            'process_id': random.randint(1000, 10000),
            'thread_id': random.randint(1000, 10000),
            'service_name': service_name,
            'display_name': display_name,
            'status': 'running' if 'start' in event_type['description'].lower() else 'stopped'
        }
        
        # Ensure the template directory exists
        template_dir = os.path.join('templates', 'windows', 'system')
        os.makedirs(template_dir, exist_ok=True)
        
        # Create the template file if it doesn't exist
        template_path = os.path.join('windows', 'system', 'service_start.xml')
        template_file = os.path.join('templates', template_path)
        if not os.path.exists(template_file):
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            with open(template_file, 'w') as f:
                f.write("""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Service Control Manager" Guid="{555908d1-a6d7-4695-8e1e-26931d2012f4}" EventSourceName="Service Control Manager" />
    <EventID Qualifiers="16384">{{ event_id }}</EventID>
    <Version>0</Version>
    <Level>4</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8080000000000000</Keywords>
    <TimeCreated SystemTime="{{ timestamp }}" />
    <EventRecordID>{{ random_int(100000, 999999) }}</EventRecordID>
    <Correlation />
    <Execution ProcessID="{{ process_id }}" ThreadID="{{ thread_id }}" />
    <Channel>System</Channel>
    <Computer>{{ hostname }}</Computer>
    <Security />
  </System>
  <EventData>
    <Data Name="param1">{{ display_name }}</Data>
    <Data Name="param2">{{ status }}</Data>
  </EventData>
</Event>""")
            
        # Create other templates if they don't exist
        template_path = os.path.join('windows', 'system', 'service_stop.xml')
        template_file = os.path.join('templates', template_path)
        if not os.path.exists(template_file):
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            with open(template_file, 'w') as f:
                f.write("""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Service Control Manager" Guid="{555908d1-a6d7-4695-8e1e-26931d2012f4}" EventSourceName="Service Control Manager" />
    <EventID Qualifiers="16384">{{ event_id }}</EventID>
    <Version>0</Version>
    <Level>4</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8080000000000000</Keywords>
    <TimeCreated SystemTime="{{ timestamp }}" />
    <EventRecordID>{{ random_int(100000, 999999) }}</EventRecordID>
    <Correlation />
    <Execution ProcessID="{{ process_id }}" ThreadID="{{ thread_id }}" />
    <Channel>System</Channel>
    <Computer>{{ hostname }}</Computer>
    <Security />
  </System>
  <EventData>
    <Data Name="param1">{{ display_name }}</Data>
    <Data Name="param2">{{ status }}</Data>
  </EventData>
</Event>""")
        
        template_path = os.path.join('windows', 'system', 'time_change.xml')
        template_file = os.path.join('templates', template_path)
        if not os.path.exists(template_file):
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            with open(template_file, 'w') as f:
                f.write("""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Kernel-General" Guid="{A68CA8B7-004F-D7B6-A698-07E2DE0F1F5D}" />
    <EventID>{{ event_id }}</EventID>
    <Version>0</Version>
    <Level>4</Level>
    <Task>0</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8000000000000000</Keywords>
    <TimeCreated SystemTime="{{ timestamp }}" />
    <EventRecordID>{{ random_int(100000, 999999) }}</EventRecordID>
    <Correlation />
    <Execution ProcessID="{{ process_id }}" ThreadID="{{ thread_id }}" />
    <Channel>System</Channel>
    <Computer>{{ hostname }}</Computer>
    <Security UserID="S-1-5-19" />
  </System>
  <EventData>
    <Data Name="NewTime">{{ timestamp }}</Data>
    <Data Name="OldTime">{{ (datetime.datetime.now() - datetime.timedelta(minutes=random_int(1, 10))).strftime('%Y-%m-%dT%H:%M:%S.%fZ') }}</Data>
    <Data Name="Reason">System time synchronized with the hardware clock.</Data>
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
            logger.error(f"Error rendering template for Windows System Event: {e}")
            return f"ERROR: Failed to render Windows System Event: {e}"