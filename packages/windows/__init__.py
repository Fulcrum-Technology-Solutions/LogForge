"""Windows Event Log package."""

import logging

from synth_logs.core.engine import Engine

logger = logging.getLogger(__name__)


def register(engine: Engine):
    """Register Windows Event Log generators with the engine.
    
    Args:
        engine: The engine to register with
    """
    logger.info("Registering Windows Event Log generators")
    
    # Import generators here to avoid circular imports
    from packages.windows.security import SecurityLogGenerator
    from packages.windows.system import SystemLogGenerator
    from packages.windows.application import ApplicationLogGenerator
    
    # Register generators with the engine
    engine.register_generator(SecurityLogGenerator())
    engine.register_generator(SystemLogGenerator())
    engine.register_generator(ApplicationLogGenerator())