"""Example log generator for Logforge."""

import datetime
import logging
import os
import random
import yaml
from typing import Dict, Any, List

from synth_logs.core.engine import LogGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.core.templates import TemplateManager

logger = logging.getLogger(__name__)


class ExampleGenerator(LogGenerator):
    """Example generator that demonstrates how to create a custom log generator."""
    
    def __init__(self):
        """Initialize the generator."""
        super().__init__("example_generator")
        
        # Initialize template manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
        # Define the event types we can generate
        self.event_types = [
            {
                'template': 'example/webserver/access.json',
                'description': 'Web server access logs',
                'weight': 10,
                'time_patterns': ['business_hours', 'after_hours']
            },
            {
                'template': 'example/webserver/error.json',
                'description': 'Web server error logs',
                'weight': 3,
                'time_patterns': ['business_hours', 'after_hours']
            }
        ]
        
        # Define HTTP methods with weights
        self.http_methods = [
            {'method': 'GET', 'weight': 15},
            {'method': 'POST', 'weight': 5},
            {'method': 'PUT', 'weight': 2},
            {'method': 'DELETE', 'weight': 1},
            {'method': 'HEAD', 'weight': 1}
        ]
        
        # Define HTTP status codes with weights
        self.status_codes = [
            {'code': 200, 'weight': 15},
            {'code': 302, 'weight': 5},
            {'code': 404, 'weight': 3},
            {'code': 500, 'weight': 1}
        ]
        
        # Define common paths
        self.paths = [
            '/',
            '/index.html',
            '/about',
            '/contact',
            '/api/v1/users',
            '/api/v1/products',
            '/images/logo.png',
            '/css/style.css',
            '/js/main.js'
        ]
        
        # Base frequency - how many events per second on average
        self.base_frequency = 1.0  # Events per second
        
    def get_random_http_method(self) -> str:
        """Get a random HTTP method based on weights.
        
        Returns:
            A random HTTP method
        """
        weights = [item['weight'] for item in self.http_methods]
        method = random.choices(self.http_methods, weights=weights, k=1)[0]
        return method['method']
    
    def get_random_status_code(self) -> int:
        """Get a random HTTP status code based on weights.
        
        Returns:
            A random HTTP status code
        """
        weights = [item['weight'] for item in self.status_codes]
        status = random.choices(self.status_codes, weights=weights, k=1)[0]
        return status['code']
    
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
        """Generate a log entry.
        
        Args:
            registry: The entity registry to use for generating logs
            
        Returns:
            The generated log entry
        """
        # Select an event type based on weights
        weights = [event['weight'] for event in self.event_types]
        event_type = random.choices(self.event_types, weights=weights, k=1)[0]
        
        # Get a device and user from the registry, or create defaults
        device = registry.get_random_device()
        user = registry.get_random_user()
        
        client_ip = device.ip_address if device else self.template_manager.random_ip()
        username = user.username if user else f"user{random.randint(1, 1000)}"
        
        # Generate a timestamp
        timestamp = datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z')
        
        # Generate HTTP details
        http_method = self.get_random_http_method()
        path = random.choice(self.paths)
        status_code = self.get_random_status_code()
        
        # Generate response size
        if status_code == 200:
            response_size = random.randint(100, 10000)
        elif status_code == 302:
            response_size = random.randint(50, 500)
        elif status_code == 404:
            response_size = random.randint(50, 200)
        else:
            response_size = random.randint(200, 1000)
            
        # Generate user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        ]
        user_agent = random.choice(user_agents)
        
        # Prepare the context for the template
        context = {
            'client_ip': client_ip,
            'username': username,
            'timestamp': timestamp,
            'http_method': http_method,
            'path': path,
            'protocol': 'HTTP/1.1',
            'status_code': status_code,
            'response_size': response_size,
            'referer': 'https://example.com/',
            'user_agent': user_agent,
            'server_name': 'example-server',
            'generator': 'example_generator'
        }
        
        # Ensure the template directory exists
        template_dir = os.path.join('templates', 'example', 'webserver')
        os.makedirs(template_dir, exist_ok=True)
        
        # Create template files if they don't exist
        for event in self.event_types:
            template_path = event['template']
            template_file = os.path.join('templates', template_path)
            
            if not os.path.exists(template_file):
                os.makedirs(os.path.dirname(template_file), exist_ok=True)
                
                # Create the template file based on the event type
                if 'access' in template_path:
                    with open(template_file, 'w') as f:
                        f.write('''{
  "time": "{{ timestamp }}",
  "client_ip": "{{ client_ip }}",
  "remote_user": "{{ username }}",
  "request": "{{ http_method }} {{ path }} {{ protocol }}",
  "status": {{ status_code }},
  "bytes_sent": {{ response_size }},
  "referer": "{{ referer }}",
  "user_agent": "{{ user_agent }}",
  "server_name": "{{ server_name }}",
  "generator": "{{ generator }}"
}''')
                elif 'error' in template_path:
                    with open(template_file, 'w') as f:
                        f.write('''{
  "time": "{{ timestamp }}",
  "client_ip": "{{ client_ip }}",
  "server_name": "{{ server_name }}",
  "level": "ERROR",
  "message": "Error {{ status_code }} processing request {{ http_method }} {{ path }}",
  "module": "webserver.processor",
  "details": {
    "status": {{ status_code }},
    "request": "{{ http_method }} {{ path }} {{ protocol }}",
    "client": "{{ username }} ({{ client_ip }})"
  },
  "generator": "{{ generator }}"
}''')
                
                # Create metadata file
                meta_path = os.path.splitext(template_file)[0] + '.meta.yaml'
                if not os.path.exists(meta_path):
                    with open(meta_path, 'w') as f:
                        yaml.dump({
                            'vendor': 'Example',
                            'product': 'Webserver',
                            'data_source': event['description'],
                            'description': f"Example {event['description']} in JSON format",
                            'format': 'JSON',
                            'frequency': 'high' if event['weight'] > 5 else 'medium',
                            'parameters': [
                                {'name': 'client_ip', 'description': 'Client IP address', 'required': True},
                                {'name': 'username', 'description': 'Username', 'required': True},
                                {'name': 'timestamp', 'description': 'Timestamp', 'required': True},
                                {'name': 'http_method', 'description': 'HTTP method', 'required': True},
                                {'name': 'path', 'description': 'Request path', 'required': True},
                                {'name': 'status_code', 'description': 'HTTP status code', 'required': True}
                            ]
                        }, f, default_flow_style=False)
        
        # Render the template
        try:
            return self.template_manager.render_template(
                event_type['template'],
                registry,
                context
            )
        except Exception as e:
            logger.error(f"Error rendering template for Example Generator: {e}")
            return f"ERROR: Failed to render template: {e}"