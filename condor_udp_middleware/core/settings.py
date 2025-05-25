#!/usr/bin/env python3

"""
Settings for Condor UDP Middleware
Configuration management including unit conversion preferences.

Part of the Condor UDP Middleware project.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import dataclasses
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger('settings')


@dataclass
class NetworkSettings:
    """Network configuration settings"""
    input_port: int = 55278  # Port to receive data from Condor
    output_host: str = "127.0.0.1"  # Target host for converted data
    output_port: int = 55300  # Target port for converted data
    buffer_size: int = 65535  # UDP buffer size


@dataclass
class UnitConversionSettings:
    """Unit conversion preferences"""
    altitude: str = "meters"     # "meters", "feet"
    speed: str = "mps"          # "mps", "kmh", "knots"
    vario: str = "mps"          # "mps", "fpm"
    acceleration: str = "mps2"   # "mps2", "fps2"
    enabled: bool = True         # Master enable/disable for conversions


@dataclass
class LogSettings:
    """Logging settings"""
    level: str = "INFO"
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    max_log_files: int = 5
    max_log_size_mb: int = 10


@dataclass
class UISettings:
    """User interface settings"""
    theme: str = "system"  # "system", "light", "dark"
    auto_start: bool = False  # Auto-start middleware on launch
    start_minimized: bool = False  # Start minimized
    recent_configs: List[str] = field(default_factory=list)


@dataclass
class MiddlewareAppSettings:
    """Main application settings container"""
    network: NetworkSettings = field(default_factory=NetworkSettings)
    conversions: UnitConversionSettings = field(default_factory=UnitConversionSettings)
    logging: LogSettings = field(default_factory=LogSettings)
    ui: UISettings = field(default_factory=UISettings)
    version: str = "1.0.0"
    first_run: bool = True


class SettingsEncoder(json.JSONEncoder):
    """Custom JSON encoder for dataclasses"""
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


class MiddlewareSettings:
    """
    Settings manager for Condor UDP Middleware.
    Handles loading, saving, and accessing application settings.
    """
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        # Default settings
        self.settings = MiddlewareAppSettings()
        
        # Configuration file path
        if config_file:
            self.config_file = config_file
        else:
            # Default to user's home directory
            self.config_file = os.path.join(
                str(Path.home()), 
                '.condor_udp_middleware', 
                'config.json'
            )
            
        # Load settings
        self.load()
    
    def load(self, config_file: Optional[str] = None) -> bool:
        """
        Load settings from file.
        
        Args:
            config_file: Override configuration file path
            
        Returns:
            bool: True if settings were loaded successfully
        """
        if config_file:
            self.config_file = config_file
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Check if file exists
            if not os.path.exists(self.config_file):
                logger.info(f"Configuration file not found at {self.config_file}")
                self._create_default_config()
                return True
            
            # Load from file
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                
            # Update settings with loaded data
            self._update_from_dict(data)
            
            logger.info(f"Settings loaded from {self.config_file}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return False
            
        except IOError as e:
            logger.error(f"Error reading config file: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            return False
    
    def save(self, config_file: Optional[str] = None) -> bool:
        """
        Save settings to file.
        
        Args:
            config_file: Override configuration file path
            
        Returns:
            bool: True if settings were saved successfully
        """
        if config_file:
            self.config_file = config_file
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2, cls=SettingsEncoder)
                
            logger.info(f"Settings saved to {self.config_file}")
            return True
            
        except IOError as e:
            logger.error(f"Error writing config file: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error saving config: {e}")
            return False
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Save default settings
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2, cls=SettingsEncoder)
                
            logger.info(f"Default configuration created at {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error creating default config: {e}")
    
    def _update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update settings from dictionary.
        
        Args:
            data: Dictionary with settings data
        """
        # Helper function to recursively update dataclasses
        def update_dataclass(obj, data_dict):
            for key, value in data_dict.items():
                if hasattr(obj, key):
                    current_value = getattr(obj, key)
                    # If it's a dataclass and value is a dict, update recursively
                    if dataclasses.is_dataclass(current_value) and isinstance(value, dict):
                        update_dataclass(current_value, value)
                    # For lists with default factory, handle specially
                    elif isinstance(current_value, list) and isinstance(value, list):
                        setattr(obj, key, value)
                    # Direct value assignment for everything else
                    else:
                        # Only set if types are compatible
                        target_type = type(current_value)
                        try:
                            if target_type is bool and isinstance(value, int):
                                # Convert int to bool (0=False, non-zero=True)
                                setattr(obj, key, bool(value))
                            elif value is None or isinstance(value, target_type):
                                # Direct assignment for same type or None
                                setattr(obj, key, value)
                            else:
                                # Try to convert to target type
                                setattr(obj, key, target_type(value))
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert {key}={value} to {target_type}")
        
        # Update main settings object
        update_dataclass(self.settings, data)
        
        # No longer first run after loading settings
        self.settings.first_run = False
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get a setting value.
        
        Args:
            section: Section name (network, conversions, logging, ui)
            key: Setting key (if None, returns entire section)
            
        Returns:
            Setting value or None if not found
        """
        try:
            if hasattr(self.settings, section):
                section_obj = getattr(self.settings, section)
                if key is None:
                    return section_obj
                elif hasattr(section_obj, key):
                    return getattr(section_obj, key)
        except Exception as e:
            logger.error(f"Error getting setting {section}.{key}: {e}")
        
        return None

    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a setting value.

        Args:
            section: Section name (network, conversions, logging, ui)
            key: Setting key
            value: New value

        Returns:
            bool: True if setting was changed
        """
        try:
            if hasattr(self.settings, section):
                section_obj = getattr(self.settings, section)
                if hasattr(section_obj, key):
                    # Handle special cases for Optional fields
                    if section == 'logging' and key == 'log_file_path':
                        if value is None:
                            setattr(section_obj, key, None)
                        else:
                            setattr(section_obj, key, str(value))
                        return True

                    # Get current value and handle type conversion
                    current_value = getattr(section_obj, key)
                    
                    if current_value is None:
                        # For None fields, handle type hints
                        try:
                            annotations = section_obj.__class__.__annotations__
                            if key in annotations:
                                type_hint = annotations[key]
                                import typing
                                origin = getattr(type_hint, "__origin__", None)
                                args = getattr(type_hint, "__args__", None)

                                if origin is typing.Union and type(None) in args:
                                    # It's Optional[type]
                                    real_type = next((t for t in args if t is not type(None)), str)
                                    if real_type is str and value is not None:
                                        setattr(section_obj, key, str(value))
                                        return True
                        except Exception:
                            pass
                        
                        # Fallback: set as-is
                        setattr(section_obj, key, value)
                        return True

                    # For non-None values, do type conversion
                    target_type = type(current_value)
                    
                    if target_type is bool and isinstance(value, int):
                        typed_value = bool(value)
                    elif value is None:
                        typed_value = None
                    elif isinstance(value, target_type):
                        typed_value = value
                    else:
                        try:
                            typed_value = target_type(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Cannot convert {key}={value} to {target_type}")
                            typed_value = value

                    setattr(section_obj, key, typed_value)
                    return True

            return False

        except Exception as e:
            logger.error(f"Unexpected error setting {section}.{key}: {e}")
            return False
    
    def get_conversion_units(self) -> Dict[str, List[str]]:
        """
        Get available units for each conversion type.
        
        Returns:
            dict: Dictionary mapping conversion types to available units
        """
        return {
            "altitude": ["meters", "feet"],
            "speed": ["mps", "kmh", "knots"],
            "vario": ["mps", "fpm"],
            "acceleration": ["mps2", "fps2"]
        }
    
    def get_conversion_factors(self) -> Dict[str, Dict[str, float]]:
        """
        Get conversion factors for unit conversions.
        
        Returns:
            dict: Nested dictionary with conversion factors
        """
        return {
            "altitude": {
                "meters_to_feet": 3.28084,
                "feet_to_meters": 0.3048
            },
            "speed": {
                "mps_to_kmh": 3.6,
                "mps_to_knots": 1.94384,
                "kmh_to_mps": 0.277778,
                "kmh_to_knots": 0.539957,
                "knots_to_mps": 0.514444,
                "knots_to_kmh": 1.852
            },
            "vario": {
                "mps_to_fpm": 196.85,
                "fpm_to_mps": 0.00508
            },
            "acceleration": {
                "mps2_to_fps2": 3.28084,
                "fps2_to_mps2": 0.3048
            }
        }
    
    def apply_logging_settings(self) -> None:
        """Apply logging settings to the Python logging system."""
        try:
            # Get logging settings
            log_level = self.settings.logging.level
            log_to_file = self.settings.logging.log_to_file
            log_file_path = self.settings.logging.log_file_path

            # Convert level string to logging level
            level_map = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL
            }
            level = level_map.get(log_level, logging.INFO)

            # Use centralized logging configuration
            from condor_udp_middleware.core.log_config import configure_logging

            # Configure logging system
            configure_logging(
                level=level,
                log_to_file=log_to_file,
                log_file_path=log_file_path,
                max_log_files=self.settings.logging.max_log_files,
                max_log_size_mb=self.settings.logging.max_log_size_mb
            )

            logger.info(f"Logging level set to {log_level}")
        except Exception as e:
            logger.error(f"Error applying logging settings: {e}")
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate settings for consistency and correctness.
        
        Returns:
            dict: Dictionary of validation errors by section
        """
        errors = {}
        
        # Validate network settings
        network_errors = []
        if self.settings.network.input_port <= 0 or self.settings.network.input_port > 65535:
            network_errors.append("Input port must be between 1 and 65535")
        if self.settings.network.output_port <= 0 or self.settings.network.output_port > 65535:
            network_errors.append("Output port must be between 1 and 65535")
        if self.settings.network.input_port == self.settings.network.output_port:
            network_errors.append("Input and output ports cannot be the same")
        if not self.settings.network.output_host:
            network_errors.append("Output host cannot be empty")
        if network_errors:
            errors["network"] = network_errors
        
        # Validate conversion settings
        conversion_errors = []
        available_units = self.get_conversion_units()
        
        if self.settings.conversions.altitude not in available_units["altitude"]:
            conversion_errors.append(f"Invalid altitude unit: {self.settings.conversions.altitude}")
        if self.settings.conversions.speed not in available_units["speed"]:
            conversion_errors.append(f"Invalid speed unit: {self.settings.conversions.speed}")
        if self.settings.conversions.vario not in available_units["vario"]:
            conversion_errors.append(f"Invalid vario unit: {self.settings.conversions.vario}")
        if self.settings.conversions.acceleration not in available_units["acceleration"]:
            conversion_errors.append(f"Invalid acceleration unit: {self.settings.conversions.acceleration}")
            
        if conversion_errors:
            errors["conversions"] = conversion_errors
        
        # Validate logging settings
        logging_errors = []
        if self.settings.logging.log_to_file and not self.settings.logging.log_file_path:
            logging_errors.append("Log file path must be specified when logging to file")
        if self.settings.logging.max_log_files <= 0:
            logging_errors.append("Maximum log files must be positive")
        if self.settings.logging.max_log_size_mb <= 0:
            logging_errors.append("Maximum log size must be positive")
        if logging_errors:
            errors["logging"] = logging_errors
        
        return errors


# Example usage:
if __name__ == "__main__":
    # Create settings manager
    settings = MiddlewareSettings()
    
    # Print current settings
    print("Current Settings:")
    settings_dict = dataclasses.asdict(settings.settings)
    for section, section_settings in settings_dict.items():
        if isinstance(section_settings, dict):
            print(f"\n[{section}]")
            for key, value in section_settings.items():
                print(f"  {key} = {value}")
        else:
            print(f"\n{section} = {section_settings}")
    
    # Test conversion factors
    print("\nConversion Factors:")
    factors = settings.get_conversion_factors()
    for category, conversions in factors.items():
        print(f"\n{category}:")
        for conversion, factor in conversions.items():
            print(f"  {conversion}: {factor}")
    
    # Validate settings
    validation_errors = settings.validate()
    if validation_errors:
        print("\nValidation Errors:")
        for section, errors in validation_errors.items():
            print(f"[{section}]")
            for error in errors:
                print(f"  - {error}")
    else:
        print("\nSettings are valid.")
    
    # Save settings
    settings.save()
