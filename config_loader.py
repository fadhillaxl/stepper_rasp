#!/usr/bin/env python3
"""
Configuration Loader for Stepper Motor Control
Loads settings from motor_config.yaml file
"""

import yaml
import os
from pathlib import Path

class MotorConfig:
    """Configuration loader and manager for stepper motor settings"""
    
    def __init__(self, config_file="motor_config.yaml"):
        """
        Initialize configuration loader
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / self.config_file
        
        if not config_path.exists():
            print(f"Warning: Configuration file {config_path} not found. Using defaults.")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                print(f"Configuration loaded from {config_path}")
                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration.")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Return default configuration if file is not available"""
        return {
            'motor': {
                'steps_per_revolution': 200,
                'step_angle': 1.8,
                'max_rpm': 300,
                'rated_voltage': 12,
                'rated_current': 1.5
            },
            'driver': {
                'microstep_multiplier': 1,
                'current_setting': 70,
                'max_output_current': 4.0,
                'enable_active_low': True
            },
            'motion': {
                'default_speed': 100,
                'min_speed': 1,
                'max_speed': 1000
            },
            'safety': {
                'operation_timeout': 300,
                'continuous_rotation_timeout': 60,
                'emergency_stop_enabled': True
            },
            'logging': {
                'level': 'INFO',
                'log_to_file': False,
                'log_motor_movements': True
            }
        }
    
    def get(self, section, key=None, default=None):
        """
        Get configuration value
        
        Args:
            section (str): Configuration section
            key (str): Configuration key (optional)
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if key is None:
            return self.config.get(section, default)
        
        section_config = self.config.get(section, {})
        return section_config.get(key, default)
    
    def get_motor_config(self):
        """Get motor-specific configuration"""
        return self.config.get('motor', {})
    
    def get_driver_config(self):
        """Get driver-specific configuration"""
        return self.config.get('driver', {})
    
    def get_motion_config(self):
        """Get motion control configuration"""
        return self.config.get('motion', {})
    
    def get_safety_config(self):
        """Get safety configuration"""
        return self.config.get('safety', {})
    
    def get_gpio_config(self):
        """Get GPIO configuration"""
        return self.config.get('gpio', {})
    
    def get_logging_config(self):
        """Get logging configuration"""
        return self.config.get('logging', {})
    
    def print_config(self):
        """Print current configuration"""
        print("\n=== Current Motor Configuration ===")
        for section, values in self.config.items():
            print(f"\n[{section.upper()}]")
            if isinstance(values, dict):
                for key, value in values.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {values}")

# Example usage
if __name__ == "__main__":
    config = MotorConfig()
    config.print_config()
    
    # Example of accessing specific values
    print(f"\nSteps per revolution: {config.get('motor', 'steps_per_revolution')}")
    print(f"Default speed: {config.get('motion', 'default_speed')}")
    print(f"Microstep multiplier: {config.get('driver', 'microstep_multiplier')}")