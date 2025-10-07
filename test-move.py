#!/usr/bin/env python3
"""
Hardware Requirements:
- Raspberry Pi (any model with GPIO)
- TB6600 Stepper Motor Driver
- 6-wire Stepper Motor (center tap wires left unconnected)
- 24V DC Power Supply (5A recommended)
- 3.3V DC-DC Buck Converter

Wiring:
- DIR_PIN (GPIO 23) -> TB6600 DIR+ pin
- STEP_PIN (GPIO 24) -> TB6600 PUL+ pin  
- ENABLE_PIN (GPIO 25) -> TB6600 ENA+ pin
- GND -> TB6600 DIR-, PUL-, ENA- pins
- 3.3V from buck converter -> TB6600 DIR+, PUL+, ENA+ pins (through RPi GPIO)
"""

import RPi.GPIO as GPIO
import time
import os
from dotenv import load_dotenv
import signal
import sys

# Load environment variables
load_dotenv()

class StepperMotor:
    def __init__(self, dir_pin=None, step_pin=None, enable_pin=None):
        """
        Initialize the stepper motor controller
        
        Args:
            dir_pin (int): GPIO pin for direction control
            step_pin (int): GPIO pin for step pulses
            enable_pin (int): GPIO pin for enable/disable motor
        """
        # Load pins from environment or use defaults
        self.dir_pin = dir_pin or int(os.getenv('DIR_PIN', 23))
        self.step_pin = step_pin or int(os.getenv('STEP_PIN', 24))
        self.enable_pin = enable_pin or int(os.getenv('ENABLE_PIN', 25))
        
        # Motor state variables
        self.is_enabled = False
        self.current_position = 0
        self.steps_per_revolution = 200  # Standard for most stepper motors
        self.microstep_multiplier = 1    # Depends on TB6600 DIP switch settings
        
        # Speed settings (steps per second)
        self.min_speed = 1
        self.max_speed = 1000
        self.default_speed = 100
        
        # Setup GPIO
        self.setup_gpio()
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"Stepper Motor Controller Initialized")
        print(f"DIR Pin: {self.dir_pin}, STEP Pin: {self.step_pin}, ENABLE Pin: {self.enable_pin}")
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins as outputs
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        
        # Initialize pin states
        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.output(self.enable_pin, GPIO.HIGH)  # HIGH = disabled (TB6600 is active low)
        
        print("GPIO pins configured successfully")
    
    def enable_motor(self):
        """Enable the stepper motor"""
        GPIO.output(self.enable_pin, GPIO.LOW)  # TB6600 enable is active low
        self.is_enabled = True
        print("Motor enabled")
        time.sleep(0.1)  # Small delay for driver to stabilize
    
    def disable_motor(self):
        """Disable the stepper motor"""
        GPIO.output(self.enable_pin, GPIO.HIGH)  # TB6600 disable
        self.is_enabled = False
        print("Motor disabled")
    
    def set_direction(self, clockwise=True):
        """
        Set motor rotation direction
        
        Args:
            clockwise (bool): True for clockwise, False for counter-clockwise
        """
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
        time.sleep(0.001)  # Small delay for direction change
    
    def step_once(self, delay=0.001):
        """
        Execute a single step
        
        Args:
            delay (float): Delay between step pulse high and low (controls speed)
        """
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(delay)
    
    def move_steps(self, steps, speed=None, clockwise=True):
        """
        Move a specific number of steps
        
        Args:
            steps (int): Number of steps to move
            speed (float): Steps per second (None uses default)
            clockwise (bool): Direction of rotation
        """
        if not self.is_enabled:
            print("Motor is not enabled. Call enable_motor() first.")
            return
        
        if steps <= 0:
            print("Steps must be positive")
            return
        
        # Calculate delay from speed
        speed = speed or self.default_speed
        speed = max(self.min_speed, min(speed, self.max_speed))
        delay = 1.0 / (2.0 * speed)  # Half period for each high/low state
        
        # Set direction
        self.set_direction(clockwise)
        
        print(f"Moving {steps} steps {'clockwise' if clockwise else 'counter-clockwise'} at {speed} steps/sec")
        
        # Execute steps
        for i in range(steps):
            self.step_once(delay)
            
            # Update position tracking
            if clockwise:
                self.current_position += 1
            else:
                self.current_position -= 1
        
        print(f"Move complete. Current position: {self.current_position}")
    
    def move_degrees(self, degrees, speed=None):
        """
        Move a specific number of degrees
        
        Args:
            degrees (float): Degrees to rotate (positive = clockwise, negative = counter-clockwise)
            speed (float): Steps per second
        """
        # Calculate steps needed
        steps_needed = abs(int((degrees / 360.0) * self.steps_per_revolution * self.microstep_multiplier))
        clockwise = degrees > 0
        
        print(f"Moving {degrees} degrees ({steps_needed} steps)")
        self.move_steps(steps_needed, speed, clockwise)
    
    def move_revolutions(self, revolutions, speed=None):
        """
        Move a specific number of full revolutions
        
        Args:
            revolutions (float): Number of revolutions (positive = clockwise, negative = counter-clockwise)
            speed (float): Steps per second
        """
        degrees = revolutions * 360
        self.move_degrees(degrees, speed)
    
    def continuous_rotation(self, speed=None, clockwise=True, duration=None):
        """
        Rotate continuously until stopped
        
        Args:
            speed (float): Steps per second
            clockwise (bool): Direction of rotation
            duration (float): Duration in seconds (None = indefinite)
        """
        if not self.is_enabled:
            print("Motor is not enabled. Call enable_motor() first.")
            return
        
        speed = speed or self.default_speed
        speed = max(self.min_speed, min(speed, self.max_speed))
        delay = 1.0 / (2.0 * speed)
        
        self.set_direction(clockwise)
        
        print(f"Starting continuous rotation {'clockwise' if clockwise else 'counter-clockwise'}")
        print("Press Ctrl+C to stop")
        
        start_time = time.time()
        try:
            while True:
                if duration and (time.time() - start_time) >= duration:
                    break
                    
                self.step_once(delay)
                
                # Update position tracking
                if clockwise:
                    self.current_position += 1
                else:
                    self.current_position -= 1
                    
        except KeyboardInterrupt:
            print("\nContinuous rotation stopped by user")
    
    def home_motor(self, speed=None):
        """
        Simple homing routine - moves to position 0
        Note: This is a basic implementation. For real applications,
        you would typically use limit switches or encoders.
        """
        print("Homing motor...")
        steps_to_home = abs(self.current_position)
        if self.current_position > 0:
            self.move_steps(steps_to_home, speed, clockwise=False)
        elif self.current_position < 0:
            self.move_steps(steps_to_home, speed, clockwise=True)
        
        self.current_position = 0
        print("Motor homed to position 0")
    
    def get_position(self):
        """Get current motor position in steps"""
        return self.current_position
    
    def get_position_degrees(self):
        """Get current motor position in degrees"""
        return (self.current_position / (self.steps_per_revolution * self.microstep_multiplier)) * 360
    
    def set_microstep_multiplier(self, multiplier):
        """
        Set the microstep multiplier based on TB6600 DIP switch settings
        
        Common settings:
        - 1: Full step
        - 2: Half step  
        - 4: Quarter step
        - 8: Eighth step
        - 16: Sixteenth step
        """
        self.microstep_multiplier = multiplier
        print(f"Microstep multiplier set to {multiplier}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}. Shutting down...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up GPIO and disable motor"""
        print("Cleaning up...")
        self.disable_motor()
        GPIO.cleanup()
        print("GPIO cleanup complete")

def demo_movements():
    """Demonstration of various motor movements"""
    motor = StepperMotor()
    
    try:
        print("\n=== Stepper Motor Demo ===")
        
        # Enable motor
        motor.enable_motor()
        
        # Demo 1: Basic steps
        print("\n1. Moving 200 steps clockwise (1 revolution)")
        motor.move_steps(200, speed=100, clockwise=True)
        time.sleep(1)
        
        # Demo 2: Move by degrees
        print("\n2. Moving 90 degrees counter-clockwise")
        motor.move_degrees(-90, speed=150)
        time.sleep(1)
        
        # Demo 3: Full revolutions
        print("\n3. Moving 2 full revolutions clockwise")
        motor.move_revolutions(2, speed=200)
        time.sleep(1)
        
        # Demo 4: Variable speed demonstration
        print("\n4. Variable speed demonstration")
        speeds = [50, 100, 200, 400]
        for speed in speeds:
            print(f"   Moving 50 steps at {speed} steps/sec")
            motor.move_steps(50, speed=speed, clockwise=True)
            time.sleep(0.5)
        
        # Demo 5: Continuous rotation for 3 seconds
        print("\n5. Continuous rotation for 3 seconds")
        motor.continuous_rotation(speed=300, clockwise=True, duration=3)
        
        # Demo 6: Home the motor
        print("\n6. Homing motor")
        motor.home_motor(speed=200)
        
        print(f"\nFinal position: {motor.get_position()} steps ({motor.get_position_degrees():.1f} degrees)")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error during demo: {e}")
    finally:
        motor.cleanup()

def interactive_mode():
    """Interactive mode for manual motor control"""
    motor = StepperMotor()
    
    try:
        motor.enable_motor()
        
        print("\n=== Interactive Stepper Motor Control ===")
        print("Commands:")
        print("  s <steps> [speed] [direction] - Move steps (direction: cw/ccw)")
        print("  d <degrees> [speed] - Move degrees (+ = cw, - = ccw)")
        print("  r <revolutions> [speed] - Move revolutions")
        print("  c [speed] [direction] - Continuous rotation")
        print("  h [speed] - Home motor")
        print("  p - Show position")
        print("  e - Enable motor")
        print("  x - Disable motor")
        print("  m <multiplier> - Set microstep multiplier")
        print("  q - Quit")
        
        while True:
            try:
                cmd = input("\nEnter command: ").strip().lower().split()
                if not cmd:
                    continue
                
                if cmd[0] == 'q':
                    break
                elif cmd[0] == 's':  # Steps
                    steps = int(cmd[1])
                    speed = float(cmd[2]) if len(cmd) > 2 else None
                    direction = cmd[3] if len(cmd) > 3 else 'cw'
                    motor.move_steps(steps, speed, direction == 'cw')
                elif cmd[0] == 'd':  # Degrees
                    degrees = float(cmd[1])
                    speed = float(cmd[2]) if len(cmd) > 2 else None
                    motor.move_degrees(degrees, speed)
                elif cmd[0] == 'r':  # Revolutions
                    revolutions = float(cmd[1])
                    speed = float(cmd[2]) if len(cmd) > 2 else None
                    motor.move_revolutions(revolutions, speed)
                elif cmd[0] == 'c':  # Continuous
                    speed = float(cmd[1]) if len(cmd) > 1 else None
                    direction = cmd[2] if len(cmd) > 2 else 'cw'
                    motor.continuous_rotation(speed, direction == 'cw')
                elif cmd[0] == 'h':  # Home
                    speed = float(cmd[1]) if len(cmd) > 1 else None
                    motor.home_motor(speed)
                elif cmd[0] == 'p':  # Position
                    print(f"Position: {motor.get_position()} steps ({motor.get_position_degrees():.1f} degrees)")
                elif cmd[0] == 'e':  # Enable
                    motor.enable_motor()
                elif cmd[0] == 'x':  # Disable
                    motor.disable_motor()
                elif cmd[0] == 'm':  # Microstep
                    multiplier = int(cmd[1])
                    motor.set_microstep_multiplier(multiplier)
                else:
                    print("Unknown command")
                    
            except (ValueError, IndexError):
                print("Invalid command format")
            except KeyboardInterrupt:
                print("\nStopping current operation...")
                
    except KeyboardInterrupt:
        print("\nExiting interactive mode...")
    finally:
        motor.cleanup()

if __name__ == "__main__":
    print("Raspberry Pi Stepper Motor Control with TB6600 Driver")
    print("Choose mode:")
    print("1. Demo mode")
    print("2. Interactive mode")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == '1':
            demo_movements()
        elif choice == '2':
            interactive_mode()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    except Exception as e:
        print(f"Error: {e}")