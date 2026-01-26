"""
Path processor plugin system for Sceptre CLI.

This module provides a plugin architecture that allows external packages to
register path processors that can transform or expand path arguments passed
to Sceptre CLI commands.

Path processors can implement features like:
- Wildcard/glob expansion
- Tag-based filtering
- Regex pattern matching
- Dynamic path generation

Plugins register themselves via entry points in their pyproject.toml:

    [project.entry-points."sceptre.cli.path_processors"]
    myprocessor = "my_package:register_plugin"

The register_plugin function should return a PathProcessor class (not instance).
"""

import logging
from typing import Dict, Type, Tuple, Optional, List
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


class PathProcessor:
    """
    Base class for path processors.
    
    Path processors can transform or expand path arguments before they are
    used by Sceptre commands.
    """
    
    def can_process(self, path: str) -> bool:
        """
        Check if this processor can handle the given path.
        
        :param path: The path string to check
        :return: True if this processor should handle the path
        """
        raise NotImplementedError("Subclasses must implement can_process()")
    
    def process(
        self,
        path: str,
        project_path: str,
        search_dir: str,
        command: str
    ) -> Tuple[str, bool, Optional[List[str]]]:
        """
        Process the path and return transformation results.
        
        :param path: The original path string
        :param project_path: The Sceptre project root path
        :param search_dir: The directory to search in (e.g., 'config')
        :param command: The command being executed (e.g., 'launch', 'delete')
        :return: Tuple of (processed_path, force_confirm, matched_files)
            - processed_path: The transformed path
            - force_confirm: Whether to force confirmation dialogs
            - matched_files: List of matched files (for display), or None
        """
        raise NotImplementedError("Subclasses must implement process()")


def get_registered_processors() -> Dict[str, Type[PathProcessor]]:
    """
    Discover and load all registered path processor plugins.
    
    Looks for entry points in the 'sceptre.cli.path_processors' group.
    Each entry point should reference a function that returns a PathProcessor class.
    
    :return: Dictionary mapping processor names to their classes
    """
    processors = {}
    
    try:
        # Get all entry points for path processors
        eps = entry_points()
        processor_entries = eps.select(group='sceptre.cli.path_processors')
        
        for entry_point in processor_entries:
            try:
                # Load the entry point (calls the register function)
                register_func = entry_point.load()
                processor_class = register_func()
                
                # Validate it's a proper PathProcessor subclass
                if not issubclass(processor_class, PathProcessor):
                    logger.warning(
                        f"Plugin '{entry_point.name}' did not return a PathProcessor subclass. Skipping."
                    )
                    continue
                
                processors[entry_point.name] = processor_class
                logger.debug(f"Registered path processor: {entry_point.name}")
                
            except Exception as e:
                logger.warning(
                    f"Failed to load path processor plugin '{entry_point.name}': {e}"
                )
                continue
    
    except Exception as e:
        logger.debug(f"Error discovering path processor plugins: {e}")
    
    return processors


def process_path(
    path: str,
    project_path: str,
    search_dir: str = "config",
    command: str = "generic"
) -> Tuple[str, bool, Optional[List[str]]]:
    """
    Process a path using registered path processors.
    
    Discovers all registered processors, checks which one can handle the path,
    and delegates processing to that processor. If no processor can handle it,
    returns the path unchanged.
    
    :param path: The path to process
    :param project_path: The Sceptre project root path
    :param search_dir: The directory to search in (default: 'config')
    :param command: The command being executed (default: 'generic')
    :return: Tuple of (processed_path, force_confirm, matched_files)
        - processed_path: The transformed path or original if no processor matched
        - force_confirm: Whether to force confirmation (False if no processor)
        - matched_files: List of matched files or None if no processor
    """
    processors = get_registered_processors()
    
    for name, processor_class in processors.items():
        try:
            # Instantiate the processor
            processor = processor_class()
            
            # Check if this processor can handle the path
            if processor.can_process(path):
                logger.debug(f"Using path processor: {name}")
                return processor.process(path, project_path, search_dir, command)
        
        except Exception as e:
            logger.warning(f"Error in path processor '{name}': {e}")
            continue
    
    # No processor matched, return path unchanged
    logger.debug("No path processor matched, using path as-is")
    return path, False, None
