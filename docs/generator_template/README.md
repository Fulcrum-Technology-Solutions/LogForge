# LogForge Generator Template

This is a template for creating new log generators for LogForge. Follow these steps to create your own custom generator package.

## Structure

A typical generator package has the following structure:

```
my_custom_generators/
├── __init__.py
├── setup.py
├── my_generators/
│   ├── __init__.py
│   └── my_generator.py
└── templates/
    └── vendor/
        └── product/
            ├── event_type1.json
            ├── event_type1.meta.yaml
            ├── event_type2.json
            └── event_type2.meta.yaml
```

## Implementation

### Generator Class

Create a class that inherits from `LogGenerator` and implements the required methods:

```python
from synth_logs.core.engine import LogGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.core.templates import TemplateManager

class MyCustomGenerator(LogGenerator):
    def __init__(self):
        # The name here will be used to activate the generator in the config
        super().__init__("my_custom_generator")
        
        # Initialize template manager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        template_dir = os.path.join(base_dir, 'templates')
        self.template_manager = TemplateManager([template_dir])
        
        # Define event types
        self.event_types = [
            {
                'template': 'vendor/product/event_type1.json',
                'description': 'First event type',
                'weight': 10,
                'time_patterns': ['business_hours', 'after_hours']
            },
            {
                'template': 'vendor/product/event_type2.json',
                'description': 'Second event type',
                'weight': 5,
                'time_patterns': ['business_hours']
            }
        ]
        
        # Set base frequency
        self.base_frequency = 1.0  # Events per second
    
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
        
        # Create the context for the template
        context = {
            # Add your context variables here
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'generator': 'my_custom_generator'
        }
        
        # Ensure template exists
        self._ensure_templates_exist()
        
        # Render the template
        try:
            return self.template_manager.render_template(
                event_type['template'],
                registry,
                context
            )
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return f"ERROR: Failed to render template: {e}"
    
    def _ensure_templates_exist(self):
        """Ensure that all templates exist, creating them if necessary."""
        # Create template directories
        for event in self.event_types:
            template_path = event['template']
            template_file = os.path.join('templates', template_path)
            if not os.path.exists(template_file):
                os.makedirs(os.path.dirname(template_file), exist_ok=True)
                
                # Write template file
                with open(template_file, 'w') as f:
                    f.write('{/* Add your template content here */}')
                
                # Write metadata file
                meta_path = os.path.splitext(template_file)[0] + '.meta.yaml'
                if not os.path.exists(meta_path):
                    with open(meta_path, 'w') as f:
                        yaml.dump({
                            'vendor': 'MyVendor',
                            'product': 'MyProduct',
                            'data_source': event['description'],
                            'description': f"My custom {event['description']} logs",
                            'format': 'JSON',
                            'frequency': 'high' if event['weight'] > 5 else 'medium'
                        }, f, default_flow_style=False)
```

### Registration

Register your generator using Python's entry points system in your `setup.py`:

```python
from setuptools import setup, find_packages

setup(
    name="my_custom_generators",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "synth_logs",
    ],
    entry_points={
        "synth_logs.generators": [
            "my_custom_generator=my_generators.my_generator:MyCustomGenerator",
        ],
    },
)
```

## Templates

Create templates for your log events in the format needed. Templates can be in any format supported by Jinja2 (XML, JSON, CSV, etc.).

Example JSON template:

```json
{
  "timestamp": "{{ timestamp }}",
  "level": "INFO",
  "message": "User {{ username }} performed action",
  "source": "my_application",
  "details": {
    "action": "login",
    "ip": "{{ ip_address }}"
  }
}
```

## Metadata

Each template should have a metadata file with the same name but with a `.meta.yaml` extension:

```yaml
vendor: MyVendor
product: MyProduct
data_source: User Login
description: User login events from my application
format: JSON
frequency: high
parameters:
  - name: username
    description: The username of the user
    required: true
  - name: ip_address
    description: IP address of the user
    required: true
```

## Installation

1. Create a distributable package:
   ```bash
   python setup.py sdist
   ```

2. Install your package:
   ```bash
   pip install -e .
   ```

## Usage

Once installed, LogForge will automatically discover your generator. You can activate it in the configuration file:

```yaml
active_generators:
  - my_custom_generator
```

Or use the interactive menu:

```bash
logforge configure --config config.yaml
```