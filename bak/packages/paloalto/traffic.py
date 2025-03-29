"""PaloAlto Traffic Log generator."""

import datetime
import json
import logging
import os
import random
import ipaddress
from typing import List, Dict, Any

from synth_logs.core.engine import LogGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.core.templates import TemplateManager

logger = logging.getLogger(__name__)


class TrafficLogGenerator(LogGenerator):
    """Generator for PaloAlto Traffic Logs."""
    
    def __init__(self):
        """Initialize the generator."""
        super().__init__("paloalto_traffic")
        
        # Initialize template manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
        # Define the traffic event types
        self.event_types = [
            {
                'template': 'paloalto/traffic/allowed.json',
                'description': 'Allowed traffic',
                'weight': 15,
                'time_patterns': ['business_hours', 'after_hours'],
                'context': {
                    'action': 'allow',
                    'threat_content_type': 'none',
                    'flags': '0x400000',
                    'session_end_reason': 'aged-out'
                }
            },
            {
                'template': 'paloalto/traffic/denied.json',
                'description': 'Denied traffic',
                'weight': 5,
                'time_patterns': ['business_hours', 'after_hours'],
                'context': {
                    'action': 'deny',
                    'threat_content_type': 'none',
                    'flags': '0x400000',
                    'session_end_reason': 'policy-deny'
                }
            },
            {
                'template': 'paloalto/traffic/dropped.json',
                'description': 'Dropped traffic',
                'weight': 3,
                'time_patterns': ['business_hours', 'after_hours'],
                'context': {
                    'action': 'drop',
                    'threat_content_type': 'none',
                    'flags': '0x400000',
                    'session_end_reason': 'policy-drop'
                }
            },
            {
                'template': 'paloalto/traffic/nat.json',
                'description': 'NAT traffic',
                'weight': 8,
                'time_patterns': ['business_hours'],
                'context': {
                    'action': 'allow',
                    'threat_content_type': 'none',
                    'flags': '0x401000',
                    'session_end_reason': 'aged-out'
                }
            }
        ]
        
        # Define common applications with weights
        self.applications = [
            {'name': 'web-browsing', 'weight': 15},
            {'name': 'ssl', 'weight': 12},
            {'name': 'dns', 'weight': 10},
            {'name': 'smtp', 'weight': 5},
            {'name': 'ms-rdp', 'weight': 3},
            {'name': 'ssh', 'weight': 4},
            {'name': 'ldap', 'weight': 2},
            {'name': 'ms-ds-smb', 'weight': 3},
            {'name': 'ntp', 'weight': 1},
            {'name': 'snmp', 'weight': 1}
        ]
        
        # Define protocol numbers
        self.protocols = {
            'tcp': 6,
            'udp': 17,
            'icmp': 1
        }
        
        # Internal zones and security policies
        self.zones = {
            'internal': ['Trust', 'LAN', 'DMZ', 'Server'],
            'external': ['Untrust', 'WAN', 'Internet']
        }
        
        self.security_policies = [
            'Allow_Outbound', 'Allow_Inbound', 'Deny_Blocked', 'Allow_Internal',
            'DMZ_Services', 'Guest_Access', 'Inter_VLAN', 'Baseline_Security'
        ]
        
        # Base frequency
        self.base_frequency = 2.0  # Events per second
    
    def get_random_application(self) -> str:
        """Get a random application based on weights.
        
        Returns:
            A random application name
        """
        weights = [app['weight'] for app in self.applications]
        app = random.choices(self.applications, weights=weights, k=1)[0]
        return app['name']
    
    def get_random_protocol(self) -> Dict[str, Any]:
        """Get a random protocol.
        
        Returns:
            Dictionary with protocol info
        """
        proto_name = random.choice(list(self.protocols.keys()))
        return {
            'name': proto_name,
            'number': self.protocols[proto_name]
        }
    
    def get_zone_pair(self) -> Dict[str, str]:
        """Get a source/destination zone pair.
        
        Returns:
            Dictionary with source and destination zones
        """
        if random.random() < 0.7:  # 70% of traffic is outbound
            src_zone = random.choice(self.zones['internal'])
            dst_zone = random.choice(self.zones['external'])
        elif random.random() < 0.7:  # 70% of remaining is internal
            src_zone = random.choice(self.zones['internal'])
            dst_zone = random.choice(self.zones['internal'])
        else:  # inbound traffic
            src_zone = random.choice(self.zones['external'])
            dst_zone = random.choice(self.zones['internal'])
        
        return {'src_zone': src_zone, 'dst_zone': dst_zone}
    
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
        """Generate a PaloAlto Traffic Log entry.
        
        Args:
            registry: The entity registry to use for generating logs
            
        Returns:
            The generated log entry as a JSON string
        """
        # Select an event type based on weights
        weights = [event['weight'] for event in self.event_types]
        event_type = random.choices(self.event_types, weights=weights, k=1)[0]
        
        # Get device information
        device = registry.get_random_device()
        if not device:
            src_hostname = f"host-{random.randint(1, 1000)}"
            src_ip = self.template_manager.random_private_ip()
            dst_hostname = f"srv-{random.randint(1, 1000)}"
            dst_ip = self.template_manager.random_ip()  # Public IP for destination
        else:
            src_hostname = device.hostname
            src_ip = device.ip_address
            if random.random() < 0.3:  # 30% chance of internal destination
                dst_device = registry.get_random_device()
                if dst_device and dst_device != device:
                    dst_hostname = dst_device.hostname
                    dst_ip = dst_device.ip_address
                else:
                    dst_hostname = f"srv-{random.randint(1, 1000)}"
                    dst_ip = self.template_manager.random_private_ip()
            else:
                service = registry.get_random_service()
                if service:
                    dst_hostname = service.name
                    dst_ip = service.ip_address or self.template_manager.random_ip()
                else:
                    dst_hostname = f"srv-{random.randint(1, 1000)}"
                    dst_ip = self.template_manager.random_ip()
        
        # Get protocol details
        protocol = self.get_random_protocol()
        
        # Get ports
        if protocol['name'] == 'tcp' or protocol['name'] == 'udp':
            if protocol['name'] == 'tcp':
                common_ports = [80, 443, 22, 3389, 8080, 8443]
            else:  # UDP
                common_ports = [53, 123, 161, 500, 514, 1194]
                
            if random.random() < 0.7:  # 70% chance of using common ports
                dst_port = random.choice(common_ports)
            else:
                dst_port = random.randint(1024, 65535)
                
            src_port = random.randint(10000, 65535)
        else:
            src_port = 0
            dst_port = 0
        
        # Get zone and policy information
        zones = self.get_zone_pair()
        security_rule = random.choice(self.security_policies)
        
        # Calculate traffic details
        bytes_sent = random.randint(100, 10000000)
        bytes_received = random.randint(100, 10000000)
        packets_sent = int(bytes_sent / random.randint(40, 1500))
        packets_received = int(bytes_received / random.randint(40, 1500))
        
        # Calculate session duration
        session_start = datetime.datetime.now() - datetime.timedelta(seconds=random.randint(1, 3600))
        session_duration = random.randint(1, 3600)
        
        # Format timestamps
        receive_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        start_time = session_start.strftime('%Y/%m/%d %H:%M:%S')
        
        # Get application
        application = self.get_random_application()
        
        # Create the log context
        context = {
            # Add event type context
            **event_type.get('context', {}),
            
            # Add standard fields
            'receive_time': receive_time,
            'serial': f"012{random.randint(10000000, 99999999)}",
            'type': 'TRAFFIC',
            'subtype': 'end',
            'time_generated': receive_time,
            
            # Firewall details
            'firewall_hostname': f"PA-{random.randint(1000, 9999)}",
            'virtual_system': 'vsys1',
            
            # Source/Destination info
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'src_hostname': src_hostname,
            'dst_hostname': dst_hostname,
            'src_zone': zones['src_zone'],
            'dst_zone': zones['dst_zone'],
            
            # Rule and application info
            'rule_name': security_rule,
            'application': application,
            'protocol': protocol['number'],
            'protocol_name': protocol['name'],
            
            # Session info
            'session_id': random.randint(10000, 1000000),
            'start_time': start_time,
            'elapsed_time': session_duration,
            'repeat_count': 1,
            
            # Traffic counters
            'bytes': bytes_sent + bytes_received,
            'bytes_sent': bytes_sent,
            'bytes_received': bytes_received,
            'packets': packets_sent + packets_received,
            'packets_sent': packets_sent,
            'packets_received': packets_received,
            
            # Additional fields
            'category': 'any',
            'sequence_number': random.randint(10000, 9999999),
            'generator': 'paloalto_traffic'
        }
        
        # Ensure the template directory exists
        template_dir = os.path.join('templates', 'paloalto', 'traffic')
        os.makedirs(template_dir, exist_ok=True)
        
        # Create template files if they don't exist
        for event in self.event_types:
            template_path = event['template']
            template_file = os.path.join('templates', template_path)
            if not os.path.exists(template_file):
                os.makedirs(os.path.dirname(template_file), exist_ok=True)
                with open(template_file, 'w') as f:
                    f.write('''{
  "receive_time": "{{ receive_time }}",
  "serial": "{{ serial }}",
  "type": "TRAFFIC",
  "subtype": "end",
  "time_generated": "{{ time_generated }}",
  "firewall_hostname": "{{ firewall_hostname }}",
  "virtual_system": "{{ virtual_system }}",
  "source": {
    "ip": "{{ src_ip }}",
    "port": {{ src_port }},
    "zone": "{{ src_zone }}"
  },
  "destination": {
    "ip": "{{ dst_ip }}",
    "port": {{ dst_port }},
    "zone": "{{ dst_zone }}"
  },
  "nat": {
    "source": {
      "ip": "{{ src_ip if flags == '0x400000' else random_ip() }}",
      "port": {{ random_port() if flags == '0x401000' else src_port }}
    },
    "destination": {
      "ip": "{{ dst_ip }}",
      "port": {{ dst_port }}
    }
  },
  "rule": {
    "name": "{{ rule_name }}",
    "id": {{ random_int(1000, 9999) }}
  },
  "application": "{{ application }}",
  "protocol": {
    "id": {{ protocol }},
    "name": "{{ protocol_name }}"
  },
  "session": {
    "id": {{ session_id }},
    "start_time": "{{ start_time }}",
    "elapsed_time": {{ elapsed_time }},
    "end_reason": "{{ session_end_reason }}",
    "repeat_count": {{ repeat_count }}
  },
  "action": "{{ action }}",
  "bytes": {
    "total": {{ bytes }},
    "sent": {{ bytes_sent }},
    "received": {{ bytes_received }}
  },
  "packets": {
    "total": {{ packets }},
    "sent": {{ packets_sent }},
    "received": {{ packets_received }}
  },
  "flags": "{{ flags }}",
  "category": "{{ category }}",
  "sequence_number": {{ sequence_number }},
  "threat_content_type": "{{ threat_content_type }}",
  "generator": "{{ generator }}"
}''')
                
                # Create metadata file for the template
                meta_path = os.path.splitext(template_file)[0] + '.meta.yaml'
                if not os.path.exists(meta_path):
                    with open(meta_path, 'w') as f:
                        yaml.dump({
                            'vendor': 'PaloAlto',
                            'product': 'Traffic',
                            'data_source': event['description'],
                            'description': f"PaloAlto Networks {event['description']} logs",
                            'format': 'JSON',
                            'frequency': 'high' if event['weight'] > 10 else 'medium',
                            'context': event.get('context', {})
                        }, f, default_flow_style=False)
        
        # Render the template
        try:
            return self.template_manager.render_template(
                event_type['template'],
                registry,
                context
            )
        except Exception as e:
            logger.error(f"Error rendering template for PaloAlto Traffic Log: {e}")
            return json.dumps({"ERROR": f"Failed to render PaloAlto Traffic Log: {e}"})