"""Windows Security Event Log generator."""

import datetime
import logging
import os
import random
from typing import List

from synth_logs.core.engine import LogGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.core.templates import TemplateManager

logger = logging.getLogger(__name__)


class SecurityLogGenerator(LogGenerator):
    """Generator for Windows Security Event Logs."""
    
    def __init__(self):
        """Initialize the generator."""
        super().__init__("windows_security")
        
        # Initialize template manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
        # Define the event types we can generate
        self.event_types = [
            {
                'template': 'windows/security/login_success.xml',
                'event_id': 4624,
                'description': 'Successful logon',
                'weight': 10,
                'time_patterns': ['business_hours', 'after_hours']
            },
            {
                'template': 'windows/security/login_failure.xml',
                'event_id': 4625,
                'description': 'Failed logon',
                'weight': 3,
                'time_patterns': ['business_hours', 'after_hours']
            },
            {
                'template': 'windows/security/account_locked.xml',
                'event_id': 4740,
                'description': 'Account locked out',
                'weight': 1,
                'time_patterns': ['business_hours', 'after_hours']
            },
            {
                'template': 'windows/security/privilege_use.xml',
                'event_id': 4672,
                'description': 'Special privileges assigned to new logon',
                'weight': 5,
                'time_patterns': ['business_hours']
            },
            {
                'template': 'windows/security/process_creation.xml',
                'event_id': 4688,
                'description': 'A new process has been created',
                'weight': 15,
                'time_patterns': ['business_hours']
            }
        ]
        
        # Base frequency - how many events per second on average
        self.base_frequency = 0.5  # Events per second
        
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
            frequency *= 0.3
            
        # Small random variation
        frequency *= random.uniform(0.8, 1.2)
        
        return frequency
        
    def generate(self, registry: EntityRegistry) -> str:
        """Generate a Windows Security Event Log entry.
        
        Args:
            registry: The entity registry to use for generating logs
            
        Returns:
            The generated log entry as an XML string
        """
        # Select an event type based on weights
        weights = [event['weight'] for event in self.event_types]
        event_type = random.choices(self.event_types, weights=weights, k=1)[0]
        
        # Get a random user from the registry, or create a generic one if none exist
        user = registry.get_random_user()
        if not user:
            username = f"user{random.randint(1, 1000)}"
            domain = "CONTOSO"
        else:
            username = user.username
            domain = "CONTOSO"  # Could be derived from user properties if available
            
        # Get a random device from the registry, or create a generic one if none exist
        device = registry.get_random_device()
        if not device:
            hostname = f"WIN-{random.randint(10000, 99999)}"
            ip_address = self.template_manager.random_private_ip()
        else:
            hostname = device.hostname
            ip_address = device.ip_address
            
        # Prepare the context for the template
        context = {
            'event_id': event_type['event_id'],
            'description': event_type['description'],
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'username': username,
            'domain': domain,
            'hostname': hostname,
            'ip_address': ip_address,
            'process_id': random.randint(1000, 10000),
            'thread_id': random.randint(1000, 10000),
            'session_id': random.randint(1, 100),
            'logon_type': random.choice([2, 3, 5, 7, 8, 10]),
            'status_code': '0x0' if 'success' in event_type['description'].lower() else f'0x{random.randint(1, 0xFFFFF):x}',
            'sub_status_code': '0x0' if 'success' in event_type['description'].lower() else f'0x{random.randint(1, 0xFFFF):x}'
        }
        
        # Ensure the template directory exists
        template_dir = os.path.join('templates', 'windows', 'security')
        os.makedirs(template_dir, exist_ok=True)
        
        # Create the template file if it doesn't exist
        template_path = os.path.join('windows', 'security', 'login_success.xml')
        template_file = os.path.join('templates', template_path)
        if not os.path.exists(template_file):
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            with open(template_file, 'w') as f:
                f.write("""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-A5BA-3E3B0328C30D}" />
    <EventID>{{ event_id }}</EventID>
    <Version>0</Version>
    <Level>0</Level>
    <Task>12544</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8020000000000000</Keywords>
    <TimeCreated SystemTime="{{ timestamp }}" />
    <EventRecordID>{{ random_int(100000, 999999) }}</EventRecordID>
    <Correlation />
    <Execution ProcessID="{{ process_id }}" ThreadID="{{ thread_id }}" />
    <Channel>Security</Channel>
    <Computer>{{ hostname }}</Computer>
    <Security />
  </System>
  <EventData>
    <Data Name="SubjectUserSid">S-1-5-18</Data>
    <Data Name="SubjectUserName">{{ username }}</Data>
    <Data Name="SubjectDomainName">{{ domain }}</Data>
    <Data Name="SubjectLogonId">0x{{ random_int(100000, 999999) | format('x') }}</Data>
    <Data Name="TargetUserSid">S-1-5-21-{{ random_int(1000000000, 9999999999) }}-{{ random_int(1000000000, 9999999999) }}-{{ random_int(1000000000, 9999999999) }}-{{ random_int(1000, 9999) }}</Data>
    <Data Name="TargetUserName">{{ username }}</Data>
    <Data Name="TargetDomainName">{{ domain }}</Data>
    <Data Name="TargetLogonId">0x{{ random_int(100000, 999999) | format('x') }}</Data>
    <Data Name="LogonType">{{ logon_type }}</Data>
    <Data Name="LogonProcessName">Advapi</Data>
    <Data Name="AuthenticationPackageName">Negotiate</Data>
    <Data Name="WorkstationName">{{ hostname }}</Data>
    <Data Name="LogonGuid">{00000000-0000-0000-0000-000000000000}</Data>
    <Data Name="TransmittedServices">-</Data>
    <Data Name="LmPackageName">-</Data>
    <Data Name="KeyLength">0</Data>
    <Data Name="ProcessId">0x{{ process_id | format('x') }}</Data>
    <Data Name="ProcessName">C:\\Windows\\System32\\svchost.exe</Data>
    <Data Name="IpAddress">{{ ip_address }}</Data>
    <Data Name="IpPort">{{ random_port() }}</Data>
    <Data Name="ImpersonationLevel">%%1833</Data>
    <Data Name="RestrictedAdminMode">-</Data>
    <Data Name="TargetOutboundUserName">-</Data>
    <Data Name="TargetOutboundDomainName">-</Data>
    <Data Name="VirtualAccount">%%1843</Data>
    <Data Name="TargetLinkedLogonId">0x0</Data>
    <Data Name="ElevatedToken">%%1842</Data>
  </EventData>
</Event>""")
            
        # Create other templates if they don't exist
        template_path = os.path.join('windows', 'security', 'login_failure.xml')
        template_file = os.path.join('templates', template_path)
        if not os.path.exists(template_file):
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            with open(template_file, 'w') as f:
                f.write("""<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-A5BA-3E3B0328C30D}" />
    <EventID>{{ event_id }}</EventID>
    <Version>0</Version>
    <Level>0</Level>
    <Task>12544</Task>
    <Opcode>0</Opcode>
    <Keywords>0x8010000000000000</Keywords>
    <TimeCreated SystemTime="{{ timestamp }}" />
    <EventRecordID>{{ random_int(100000, 999999) }}</EventRecordID>
    <Correlation />
    <Execution ProcessID="{{ process_id }}" ThreadID="{{ thread_id }}" />
    <Channel>Security</Channel>
    <Computer>{{ hostname }}</Computer>
    <Security />
  </System>
  <EventData>
    <Data Name="SubjectUserSid">S-1-5-18</Data>
    <Data Name="SubjectUserName">-</Data>
    <Data Name="SubjectDomainName">-</Data>
    <Data Name="SubjectLogonId">0x0</Data>
    <Data Name="TargetUserSid">S-1-0-0</Data>
    <Data Name="TargetUserName">{{ username }}</Data>
    <Data Name="TargetDomainName">{{ domain }}</Data>
    <Data Name="Status">{{ status_code }}</Data>
    <Data Name="FailureReason">%%2313</Data>
    <Data Name="SubStatus">{{ sub_status_code }}</Data>
    <Data Name="LogonType">{{ logon_type }}</Data>
    <Data Name="LogonProcessName">NtLmSsp</Data>
    <Data Name="AuthenticationPackageName">NTLM</Data>
    <Data Name="WorkstationName">{{ hostname }}</Data>
    <Data Name="TransmittedServices">-</Data>
    <Data Name="LmPackageName">-</Data>
    <Data Name="KeyLength">0</Data>
    <Data Name="ProcessId">0x{{ process_id | format('x') }}</Data>
    <Data Name="ProcessName">C:\\Windows\\System32\\svchost.exe</Data>
    <Data Name="IpAddress">{{ ip_address }}</Data>
    <Data Name="IpPort">{{ random_port() }}</Data>
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
            logger.error(f"Error rendering template for Windows Security Event: {e}")
            return f"ERROR: Failed to render Windows Security Event: {e}"