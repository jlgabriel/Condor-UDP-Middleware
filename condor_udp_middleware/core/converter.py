#!/usr/bin/env python3

"""
Unit Converter for Condor UDP Middleware
Handles conversion of units for different variables based on user preferences.

Part of the Condor UDP Middleware project.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logger = logging.getLogger('converter')


class UnitConverter:
    """
    Handles unit conversions for Condor simulator data.
    Converts between different unit systems based on user preferences.
    """
    
    def __init__(self, conversion_settings: Dict[str, str]):
        """
        Initialize the unit converter.
        
        Args:
            conversion_settings: Dictionary with conversion preferences
                                {"altitude": "feet", "speed": "knots", etc.}
        """
        self.conversion_settings = conversion_settings
        
        # Compiled regex for key=value pairs (reused from original parser)
        self.kv_pattern = re.compile(r'([a-zA-Z_]+)=([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)')
        
        # Define variable mappings and their conversion types
        self.variable_mappings = {
            # Altitude variables (meters by default in Condor)
            "altitude": "altitude",
            "height": "altitude", 
            "wheelheight": "altitude",
            
            # Speed variables (m/s by default in Condor)
            "airspeed": "speed",
            "vx": "speed",
            "vy": "speed", 
            "vz": "speed",
            
            # Vario variables (m/s by default in Condor)
            "vario": "vario",
            "evario": "vario",
            "nettovario": "vario",
            
            # Acceleration variables (m/s² by default in Condor)
            "ax": "acceleration",
            "ay": "acceleration",
            "az": "acceleration"
        }
        
        # Conversion factors
        self.conversion_factors = {
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
        
        # Statistics
        self.conversions_applied = 0
        self.variables_converted = set()
    
    def process_message(self, original_message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process a UDP message, applying unit conversions.
        
        Args:
            original_message: Original UDP message from Condor
            
        Returns:
            Tuple of (converted_message, conversion_info)
        """
        try:
            # Extract all key=value pairs
            pairs = self.kv_pattern.findall(original_message)
            if not pairs:
                return original_message, {"error": "No key=value pairs found"}
            
            # Convert to dictionary for processing
            data_dict = {key: self._convert_value(value) for key, value in pairs}
            
            # Apply conversions
            converted_dict, conversion_info = self._apply_conversions(data_dict)
            
            # Rebuild message in original format
            converted_message = self._rebuild_message(converted_dict)
            
            # Update statistics
            if conversion_info["conversions_applied"] > 0:
                self.conversions_applied += conversion_info["conversions_applied"]
                self.variables_converted.update(conversion_info["variables_converted"])
            
            return converted_message, conversion_info
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return original_message, {"error": str(e)}
    
    def _convert_value(self, value_str: str) -> float:
        """Convert string value to float."""
        try:
            return float(value_str)
        except ValueError:
            logger.warning(f"Could not convert value to float: {value_str}")
            return 0.0
    
    def _apply_conversions(self, data: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Apply unit conversions to data dictionary.
        
        Args:
            data: Dictionary of variable names to values
            
        Returns:
            Tuple of (converted_data, conversion_info)
        """
        converted_data = data.copy()
        conversion_info = {
            "conversions_applied": 0,
            "variables_converted": [],
            "conversions_detail": {}
        }
        
        # Skip if conversions are disabled
        if not self.conversion_settings.get("enabled", True):
            return converted_data, conversion_info
        
        for variable, value in data.items():
            # Check if this variable needs conversion
            if variable not in self.variable_mappings:
                continue
            
            conversion_type = self.variable_mappings[variable]
            target_unit = self.conversion_settings.get(conversion_type)
            
            if not target_unit:
                continue
            
            # Apply conversion based on type
            converted_value, conversion_applied = self._convert_variable(
                variable, value, conversion_type, target_unit
            )
            
            if conversion_applied:
                converted_data[variable] = converted_value
                conversion_info["conversions_applied"] += 1
                conversion_info["variables_converted"].append(variable)
                conversion_info["conversions_detail"][variable] = {
                    "original_value": value,
                    "converted_value": converted_value,
                    "conversion_type": conversion_type,
                    "target_unit": target_unit
                }
                
                logger.debug(f"Converted {variable}: {value} → {converted_value} ({target_unit})")
        
        return converted_data, conversion_info
    
    def _convert_variable(self, variable: str, value: float, conversion_type: str, target_unit: str) -> Tuple[float, bool]:
        """
        Convert a single variable to target unit.
        
        Args:
            variable: Variable name
            value: Original value
            conversion_type: Type of conversion (altitude, speed, vario, acceleration)
            target_unit: Target unit
            
        Returns:
            Tuple of (converted_value, was_converted)
        """
        try:
            if conversion_type == "altitude":
                return self._convert_altitude(value, target_unit)
            elif conversion_type == "speed":
                return self._convert_speed(value, target_unit)
            elif conversion_type == "vario":
                return self._convert_vario(value, target_unit)
            elif conversion_type == "acceleration":
                return self._convert_acceleration(value, target_unit)
            else:
                logger.warning(f"Unknown conversion type: {conversion_type}")
                return value, False
                
        except Exception as e:
            logger.error(f"Error converting {variable}: {e}")
            return value, False
    
    def _convert_altitude(self, value: float, target_unit: str) -> Tuple[float, bool]:
        """Convert altitude from meters to target unit."""
        if target_unit == "meters":
            return value, False  # No conversion needed
        elif target_unit == "feet":
            factor = self.conversion_factors["altitude"]["meters_to_feet"]
            return value * factor, True
        else:
            logger.warning(f"Unknown altitude unit: {target_unit}")
            return value, False
    
    def _convert_speed(self, value: float, target_unit: str) -> Tuple[float, bool]:
        """Convert speed from m/s to target unit."""
        if target_unit == "mps":
            return value, False  # No conversion needed
        elif target_unit == "kmh":
            factor = self.conversion_factors["speed"]["mps_to_kmh"]
            return value * factor, True
        elif target_unit == "knots":
            factor = self.conversion_factors["speed"]["mps_to_knots"]
            return value * factor, True
        else:
            logger.warning(f"Unknown speed unit: {target_unit}")
            return value, False
    
    def _convert_vario(self, value: float, target_unit: str) -> Tuple[float, bool]:
        """Convert vario from m/s to target unit."""
        if target_unit == "mps":
            return value, False  # No conversion needed
        elif target_unit == "fpm":
            factor = self.conversion_factors["vario"]["mps_to_fpm"]
            return value * factor, True
        else:
            logger.warning(f"Unknown vario unit: {target_unit}")
            return value, False
    
    def _convert_acceleration(self, value: float, target_unit: str) -> Tuple[float, bool]:
        """Convert acceleration from m/s² to target unit."""
        if target_unit == "mps2":
            return value, False  # No conversion needed
        elif target_unit == "fps2":
            factor = self.conversion_factors["acceleration"]["mps2_to_fps2"]
            return value * factor, True
        else:
            logger.warning(f"Unknown acceleration unit: {target_unit}")
            return value, False

    def _rebuild_message(self, data: Dict[str, float]) -> str:
        """
        Rebuild UDP message in original key=value format.
        Maintain high precision like Condor original.
        """
        pairs = []
        for key, value in data.items():
            if isinstance(value, float):
                # Usar alta precisión como Condor original
                pairs.append(f"{key}={value:.15g}")  # Hasta 15 dígitos significativos
            else:
                pairs.append(f"{key}={value}")

        return '\r\n'.join(pairs) + '\r\n'
    
    def update_settings(self, new_settings: Dict[str, str]) -> None:
        """
        Update conversion settings.
        
        Args:
            new_settings: New conversion settings
        """
        self.conversion_settings = new_settings.copy()
        logger.info(f"Conversion settings updated: {new_settings}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversion statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_conversions_applied": self.conversions_applied,
            "unique_variables_converted": len(self.variables_converted),
            "variables_converted": list(self.variables_converted),
            "current_settings": self.conversion_settings.copy(),
            "supported_variables": list(self.variable_mappings.keys())
        }
    
    def reset_statistics(self) -> None:
        """Reset conversion statistics."""
        self.conversions_applied = 0
        self.variables_converted.clear()
        logger.info("Conversion statistics reset")
    
    def get_convertible_variables(self, message: str) -> List[str]:
        """
        Get list of variables in message that can be converted.
        
        Args:
            message: UDP message to analyze
            
        Returns:
            List of convertible variable names
        """
        try:
            pairs = self.kv_pattern.findall(message)
            variables = [key for key, _ in pairs]
            convertible = [var for var in variables if var in self.variable_mappings]
            return convertible
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return []


# Example usage and testing:
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Test conversion settings
    test_settings = {
        "enabled": True,
        "altitude": "feet",
        "speed": "knots", 
        "vario": "fpm",
        "acceleration": "fps2"
    }
    
    # Create converter
    converter = UnitConverter(test_settings)
    
    # Test message (sample from Condor)
    test_message = """time=17.0000042330833
airspeed=30.5
altitude=117.328384399414
vario=-2.5
evario=-1.8
nettovario=-1.07
ax=-0.0140609405934811
ay=0.323577255010605
az=-8.06892871856689
height=10.5
wheelheight=0.5"""
    
    print("Original message:")
    print(test_message)
    print()
    
    # Process message
    converted_message, info = converter.process_message(test_message)
    
    print("Converted message:")
    print(converted_message)
    print()
    
    print("Conversion info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    # Show statistics
    stats = converter.get_statistics()
    print("Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Test convertible variables detection
    convertible = converter.get_convertible_variables(test_message)
    print(f"Convertible variables found: {convertible}")
