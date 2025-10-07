#!/usr/bin/env python3
"""
Open Ground Station Rotator Controller (OGRC)
Main application for controlling azimuth and elevation rotator
Compatible with Hamlib/rotctld and Gpredict via GS-232 protocol

Hardware Requirements:
- Raspberry Pi 4B
- 2x Stepper Motors (NEMA34 recommended)
- 2x Stepper Drivers (DM542 or similar)
- WT901C-RS485 IMU sensor
- RS485 to USB/TTL adapter
- 24V DC Power Supply

Author: Open Source Ground Station Project
License: MIT
"""

import socket
import threading
import time
import serial
import struct
import math
import logging
import signal
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import RPi.GPIO as GPIO
from config_loader import MotorConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rotator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OGRC')

class StepperAxis:
    """Individual stepper motor axis control (Azimuth or Elevation)"""
    
    def __init__(self, name, dir_pin, step_pin, enable_pin, steps_per_degree=None):
        self.name = name
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        
        # Load configuration
        config = MotorConfig()
        motor_config = config.get_motor_config()
        driver_config = config.get_driver_config()
        
        # Calculate steps per degree
        steps_per_rev = motor_config.get('steps_per_revolution', 200)
        microstep = driver_config.get('microstep_multiplier', 1)
        gear_ratio = motor_config.get('gear_ratio', 40)  # Worm gear ratio
        
        self.steps_per_degree = steps_per_degree or (steps_per_rev * microstep * gear_ratio) / 360.0
        
        # Position tracking
        self.current_position = 0.0  # degrees
        self.target_position = 0.0   # degrees
        self.step_count = 0          # total steps moved
        
        # Motion parameters
        motion_config = config.get_motion_config()
        self.default_speed = motion_config.get('default_speed', 100)  # steps/sec
        self.max_speed = motion_config.get('max_speed', 1000)
        self.min_speed = motion_config.get('min_speed', 1)
        
        # Safety limits
        self.min_limit = 0.0 if name == "Azimuth" else 0.0
        self.max_limit = 360.0 if name == "Azimuth" else 90.0
        
        # State
        self.is_enabled = False
        self.is_moving = False
        self.homed = False
        
        # Setup GPIO
        self.setup_gpio()
        
        logger.info(f"{self.name} axis initialized - Steps/degree: {self.steps_per_degree:.2f}")
    
    def setup_gpio(self):
        """Initialize GPIO pins for this axis"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        
        # Initialize states
        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.output(self.enable_pin, GPIO.HIGH)  # Disabled initially
        
        logger.debug(f"{self.name} GPIO configured: DIR={self.dir_pin}, STEP={self.step_pin}, EN={self.enable_pin}")
    
    def enable(self):
        """Enable the stepper motor"""
        GPIO.output(self.enable_pin, GPIO.LOW)  # Active low
        self.is_enabled = True
        time.sleep(0.1)  # Stabilization delay
        logger.debug(f"{self.name} motor enabled")
    
    def disable(self):
        """Disable the stepper motor"""
        GPIO.output(self.enable_pin, GPIO.HIGH)
        self.is_enabled = False
        logger.debug(f"{self.name} motor disabled")
    
    def set_direction(self, clockwise=True):
        """Set rotation direction"""
        GPIO.output(self.dir_pin, GPIO.HIGH if clockwise else GPIO.LOW)
        time.sleep(0.001)  # Direction setup time
    
    def step_once(self, delay=0.001):
        """Execute single step pulse"""
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(delay)
    
    def move_to_position(self, target_degrees, speed=None):
        """Move to absolute position in degrees"""
        if not self.is_enabled:
            logger.warning(f"{self.name}: Motor not enabled")
            return False
        
        # Validate target position
        if target_degrees < self.min_limit or target_degrees > self.max_limit:
            logger.warning(f"{self.name}: Target {target_degrees}° outside limits [{self.min_limit}°, {self.max_limit}°]")
            return False
        
        self.target_position = target_degrees
        position_error = target_degrees - self.current_position
        
        if abs(position_error) < 0.1:  # Already at target
            return True
        
        steps_needed = int(abs(position_error) * self.steps_per_degree)
        clockwise = position_error > 0
        
        speed = speed or self.default_speed
        speed = max(self.min_speed, min(speed, self.max_speed))
        delay = 1.0 / (2.0 * speed)
        
        logger.info(f"{self.name}: Moving from {self.current_position:.2f}° to {target_degrees:.2f}° ({steps_needed} steps)")
        
        self.is_moving = True
        self.set_direction(clockwise)
        
        try:
            for i in range(steps_needed):
                if not self.is_moving:  # Allow interruption
                    break
                
                self.step_once(delay)
                
                # Update position tracking
                step_degrees = 1.0 / self.steps_per_degree
                if clockwise:
                    self.current_position += step_degrees
                    self.step_count += 1
                else:
                    self.current_position -= step_degrees
                    self.step_count -= 1
            
            self.is_moving = False
            logger.info(f"{self.name}: Move complete. Position: {self.current_position:.2f}°")
            return True
            
        except Exception as e:
            self.is_moving = False
            logger.error(f"{self.name}: Move failed - {e}")
            return False
    
    def stop(self):
        """Stop current movement"""
        self.is_moving = False
        logger.info(f"{self.name}: Movement stopped")
    
    def home(self):
        """Home the axis to 0 degrees"""
        logger.info(f"{self.name}: Homing...")
        if self.move_to_position(0.0, speed=50):
            self.current_position = 0.0
            self.step_count = 0
            self.homed = True
            logger.info(f"{self.name}: Homed successfully")
            return True
        return False

class WT901C_IMU:
    """WT901C-RS485 IMU sensor interface for position feedback"""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.yaw = 0.0      # Azimuth angle
        self.pitch = 0.0    # Elevation angle
        self.roll = 0.0     # Roll angle
        self.connected = False
        
        # Data parsing
        self.data_buffer = bytearray()
        
        self.connect()
    
    def connect(self):
        """Connect to IMU via RS485"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            self.connected = True
            logger.info(f"IMU connected on {self.port}")
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
        except Exception as e:
            logger.error(f"IMU connection failed: {e}")
            self.connected = False
    
    def _read_loop(self):
        """Continuous reading loop for IMU data"""
        while self.connected and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    self.data_buffer.extend(data)
                    self._parse_data()
                time.sleep(0.01)  # 100Hz reading rate
                
            except Exception as e:
                logger.error(f"IMU read error: {e}")
                break
    
    def _parse_data(self):
        """Parse WT901C data packets"""
        while len(self.data_buffer) >= 11:
            # Find packet header (0x55)
            header_idx = self.data_buffer.find(0x55)
            if header_idx == -1:
                self.data_buffer.clear()
                break
            
            # Remove data before header
            if header_idx > 0:
                self.data_buffer = self.data_buffer[header_idx:]
            
            if len(self.data_buffer) < 11:
                break
            
            packet_type = self.data_buffer[1]
            
            if packet_type == 0x53:  # Angle data packet
                try:
                    # Extract angle data (16-bit signed integers)
                    roll_raw = struct.unpack('<h', self.data_buffer[2:4])[0]
                    pitch_raw = struct.unpack('<h', self.data_buffer[4:6])[0]
                    yaw_raw = struct.unpack('<h', self.data_buffer[6:8])[0]
                    
                    # Convert to degrees (WT901C uses 32768 = 180°)
                    self.roll = roll_raw / 32768.0 * 180.0
                    self.pitch = pitch_raw / 32768.0 * 180.0
                    self.yaw = yaw_raw / 32768.0 * 180.0
                    
                    # Normalize yaw to 0-360°
                    if self.yaw < 0:
                        self.yaw += 360.0
                    
                except struct.error:
                    pass
            
            # Remove processed packet
            self.data_buffer = self.data_buffer[11:]
    
    def get_azimuth(self):
        """Get current azimuth (yaw) in degrees"""
        return self.yaw
    
    def get_elevation(self):
        """Get current elevation (pitch) in degrees"""
        return self.pitch
    
    def disconnect(self):
        """Disconnect from IMU"""
        self.connected = False
        if self.serial_conn:
            self.serial_conn.close()
        logger.info("IMU disconnected")

class GS232Server:
    """GS-232 protocol TCP server for Hamlib/rotctld compatibility"""
    
    def __init__(self, host='0.0.0.0', port=4533):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        # Initialize hardware
        self.setup_hardware()
        
        # Position tracking
        self.target_azimuth = 0.0
        self.target_elevation = 0.0
        
        # Closed-loop control
        self.feedback_enabled = True
        self.position_tolerance = 0.5  # degrees
        
        logger.info("GS-232 Server initialized")
    
    def setup_hardware(self):
        """Initialize stepper motors and IMU"""
        # Load GPIO pins from environment
        az_dir = int(os.getenv('AZ_DIR_PIN', 23))
        az_step = int(os.getenv('AZ_STEP_PIN', 24))
        az_enable = int(os.getenv('AZ_ENABLE_PIN', 25))
        
        el_dir = int(os.getenv('EL_DIR_PIN', 26))
        el_step = int(os.getenv('EL_STEP_PIN', 27))
        el_enable = int(os.getenv('EL_ENABLE_PIN', 22))
        
        # Initialize axes
        self.azimuth_axis = StepperAxis("Azimuth", az_dir, az_step, az_enable)
        self.elevation_axis = StepperAxis("Elevation", el_dir, el_step, el_enable)
        
        # Initialize IMU
        imu_port = os.getenv('IMU_PORT', '/dev/ttyUSB0')
        self.imu = WT901C_IMU(port=imu_port)
        
        # Enable motors
        self.azimuth_axis.enable()
        self.elevation_axis.enable()
        
        # Start feedback control loop
        self.feedback_thread = threading.Thread(target=self._feedback_loop, daemon=True)
        self.feedback_thread.start()
    
    def _feedback_loop(self):
        """Closed-loop position feedback using IMU"""
        while self.running:
            try:
                if self.feedback_enabled and self.imu.connected:
                    # Get actual positions from IMU
                    actual_az = self.imu.get_azimuth()
                    actual_el = self.imu.get_elevation()
                    
                    # Calculate position errors
                    az_error = self.target_azimuth - actual_az
                    el_error = self.target_elevation - actual_el
                    
                    # Handle azimuth wraparound
                    if az_error > 180:
                        az_error -= 360
                    elif az_error < -180:
                        az_error += 360
                    
                    # Apply corrections if error exceeds tolerance
                    if abs(az_error) > self.position_tolerance:
                        correction_az = self.azimuth_axis.current_position + az_error
                        self.azimuth_axis.move_to_position(correction_az, speed=50)
                    
                    if abs(el_error) > self.position_tolerance:
                        correction_el = self.elevation_axis.current_position + el_error
                        self.elevation_axis.move_to_position(correction_el, speed=50)
                
                time.sleep(0.1)  # 10Hz feedback rate
                
            except Exception as e:
                logger.error(f"Feedback loop error: {e}")
                time.sleep(1.0)
    
    def start_server(self):
        """Start the TCP server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"GS-232 Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    logger.info(f"Client connected from {address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Server socket error: {e}")
                        break
        
        except Exception as e:
            logger.error(f"Server start failed: {e}")
        finally:
            self.stop_server()
    
    def _handle_client(self, client_socket, address):
        """Handle individual client connection"""
        try:
            while self.running:
                data = client_socket.recv(1024).decode('ascii').strip()
                if not data:
                    break
                
                logger.debug(f"Received from {address}: {data}")
                response = self._process_command(data)
                
                if response:
                    client_socket.send(f"{response}\n".encode('ascii'))
                    logger.debug(f"Sent to {address}: {response}")
        
        except Exception as e:
            logger.error(f"Client {address} error: {e}")
        finally:
            client_socket.close()
            logger.info(f"Client {address} disconnected")
    
    def _process_command(self, command):
        """Process GS-232 protocol commands"""
        command = command.upper().strip()
        
        try:
            if command.startswith('AZ'):
                # Set azimuth: AZ123.5
                azimuth = float(command[2:])
                self.target_azimuth = azimuth
                threading.Thread(
                    target=self.azimuth_axis.move_to_position,
                    args=(azimuth,),
                    daemon=True
                ).start()
                return "OK"
            
            elif command.startswith('EL'):
                # Set elevation: EL45.0
                elevation = float(command[2:])
                self.target_elevation = elevation
                threading.Thread(
                    target=self.elevation_axis.move_to_position,
                    args=(elevation,),
                    daemon=True
                ).start()
                return "OK"
            
            elif command == 'P':
                # Get position
                if self.imu.connected:
                    az = self.imu.get_azimuth()
                    el = self.imu.get_elevation()
                else:
                    az = self.azimuth_axis.current_position
                    el = self.elevation_axis.current_position
                return f"AZ={az:.1f} EL={el:.1f}"
            
            elif command == 'S':
                # Stop all movement
                self.azimuth_axis.stop()
                self.elevation_axis.stop()
                return "OK"
            
            elif command == 'H':
                # Home both axes
                threading.Thread(target=self._home_all, daemon=True).start()
                return "OK"
            
            elif command == 'R':
                # Reset/restart
                self._reset_system()
                return "OK"
            
            else:
                return "ERROR"
        
        except ValueError:
            return "ERROR"
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return "ERROR"
    
    def _home_all(self):
        """Home both axes"""
        logger.info("Homing all axes...")
        self.elevation_axis.home()
        self.azimuth_axis.home()
        self.target_azimuth = 0.0
        self.target_elevation = 0.0
        logger.info("Homing complete")
    
    def _reset_system(self):
        """Reset system to initial state"""
        logger.info("Resetting system...")
        self.azimuth_axis.stop()
        self.elevation_axis.stop()
        time.sleep(0.5)
        self._home_all()
    
    def stop_server(self):
        """Stop the server and cleanup"""
        logger.info("Stopping server...")
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        # Disable motors
        self.azimuth_axis.disable()
        self.elevation_axis.disable()
        
        # Disconnect IMU
        self.imu.disconnect()
        
        # Cleanup GPIO
        GPIO.cleanup()
        
        logger.info("Server stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    if 'server' in globals():
        server.stop_server()
    sys.exit(0)

def main():
    """Main application entry point"""
    print("=" * 60)
    print("Open Ground Station Rotator Controller (OGRC)")
    print("Compatible with Hamlib/rotctld and Gpredict")
    print("=" * 60)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start server
        global server
        server = GS232Server()
        
        # Home axes on startup
        logger.info("Performing initial homing...")
        server._home_all()
        
        # Start server
        logger.info("Starting GS-232 server...")
        server.start_server()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        if 'server' in globals():
            server.stop_server()
        sys.exit(1)

if __name__ == "__main__":
    main()