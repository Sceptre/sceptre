"""
Path processor plugin system for Sceptre CLI.

This module provides a plugin architecture for processing stack paths,
enabling extensions like wildcard pattern matching through installed plugins.
"""

import logging
from typing import List, Optional, Tuple, Type

try:
    from importlib.metadata import entry_points
except ImportError:
    # Python < 3.8
    from importlib_metadata import entry_points

logger = logging.getLogger(__name__)


class PathProcessor:
    """
    Base class for path processors.
    
    Path processors can transform or validate stack paths before they are
    passed to Sceptre's core functionality. This enables features like
    wildcard expansion, regex patterns, or custom path resolution.
    """
    
    name = "base"
    priority = 0
    
    def can_process(self, path: str) -> bool:
        """
        Check if this processor can handle the given path.
        
        :param path: The path to check
        :type path: str
        :returns: True if this processor can handle the path
        :rtype: bool
        """
        return False
    
    def process(
        self,
        path: str,
        project_path: str,
        config_path: str = "config"
    ) -> Tuple[str, Optional[List[str]]]:
        """
        Process the path and return the expanded command path.
        
        :param path: The path to process
        :type path: str
        :param project_path: The absolute path to the project root
        :type project_path: str
        :param config_path: The config directory name
        :type config_path: str
        :returns: Tuple of (processed_path, matched_files)
        :rtype: Tuple[str, Optional[List[str]]]
        """
        return path, None
    
    def should_force_confirmation(self, command_name: str) -> bool:
        """
        Determine if this processor should force confirmation for a command.
        
        :param command_name: The name of the command being executed
        :type command_name: str
        :returns: True if confirmation should be forced
        :rtype: bool
        """
        return False


class PathProcessorManager:
    """
    Manager for path processor plugins.
    
    This class discovers and loads path processor plugins via entry points,
    and provides methods to process paths using registered processors.
    """
    
    def __init__(self):
        """Initialize the path processor manager."""
        self._processors: List[PathProcessor] = []
        self._loaded = False
    
    def load_processors(self):
        """
        Load all registered path processor plugins.
        
        Discovers plugins via the 'sceptre.cli.path_processors' entry point
        group and instantiates them.
        """
        if self._loaded:
            return
        
        try:
            # Python 3.10+
            eps = entry_points(group='sceptre.cli.path_processors')
        except TypeError:
            # Python 3.8-3.9
            eps = entry_points().get('sceptre.cli.path_processors', [])
        
        for ep in eps:
            try:
                # Load the entry point (gets the register_plugin function)
                register_func = ep.load()
                
                # Call the registration function to get the processor class
                processor_class = register_func()
                
                # Instantiate the processor
                processor = processor_class()
                
                self._processors.append(processor)
                logger.debug(f"Loaded path processor plugin: {processor.name}")
                
            except Exception as e:
                logger.warning(f"Failed to load path processor plugin {ep.name}: {e}")
        
        # Sort processors by priority (highest first)
        self._processors.sort(key=lambda p: p.priority, reverse=True)
        
        self._loaded = True
        
        if self._processors:
            logger.info(f"Loaded {len(self._processors)} path processor plugin(s)")
    
    def process_path(
        self,
        path: str,
        project_path: str,
        config_path: str = "config",
        command_name: Optional[str] = None
    ) -> Tuple[str, bool, Optional[List[str]]]:
        """
        Process a path using registered processors.
        
        Iterates through registered processors (in priority order) and uses
        the first one that can handle the path.
        
        :param path: The path to process
        :type path: str
        :param project_path: The absolute path to the project root
        :type project_path: str
        :param config_path: The config directory name
        :type config_path: str
        :param command_name: The name of the command being executed (optional)
        :type command_name: Optional[str]
        :returns: Tuple of (processed_path, force_confirmation, matched_files)
        :rtype: Tuple[str, bool, Optional[List[str]]]
        """
        # Ensure processors are loaded
        self.load_processors()
        
        # Try each processor in priority order
        for processor in self._processors:
            if processor.can_process(path):
                logger.debug(f"Processing path with {processor.name} processor")
                
                # Process the path
                processed_path, matched_files = processor.process(
                    path, project_path, config_path
                )
                
                # Check if confirmation should be forced
                force_confirmation = False
                if command_name:
                    force_confirmation = processor.should_force_confirmation(command_name)
                
                return processed_path, force_confirmation, matched_files
        
        # No processor handled the path, return as-is
        return path, False, None


# Global instance
_manager = PathProcessorManager()


def process_path(
    path: str,
    project_path: str,
    config_path: str = "config",
    command_name: Optional[str] = None
) -> Tuple[str, bool, Optional[List[str]]]:
    """
    Process a path using registered path processors.
    
    This is the main entry point for path processing. It will automatically
    load and use any installed path processor plugins.
    
    :param path: The path to process
    :type path: str
    :param project_path: The absolute path to the project root
    :type project_path: str
    :param config_path: The config directory name (default: 'config')
    :type config_path: str
    :param command_name: The name of the command being executed (optional)
    :type command_name: Optional[str]
    :returns: Tuple of (processed_path, force_confirmation, matched_files)
    :rtype: Tuple[str, bool, Optional[List[str]]]
    
    Example:
        >>> path, force_confirm, files = process_path("dev/*.yaml", "/project")
        >>> # path might be "dev", files might be ["dev/vpc.yaml", "dev/app.yaml"]
    """
    return _manager.process_path(path, project_path, config_path, command_name)
