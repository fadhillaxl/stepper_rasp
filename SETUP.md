# Open Ground Station Rotator Controller (OGRC) Setup Guide

This guide will help you set up the Open Ground Station Rotator Controller on your Raspberry Pi 4B.

## Hardware Requirements

### Essential Components
- **Raspberry Pi 4B** (4GB RAM recommended)
- **2x Stepper Motors** (NEMA34 recommended, 1.8°/step)
- **2x Stepper Drivers** (DM542, TMC5160, or similar)
- **WT901C-RS485 IMU** (9DOF sensor for position feedback)
- **RS485 to USB/TTL Adapter** (MAX485 based)
- **24V DC Power Supply** (10A minimum for motors)
- **Worm Gear System** (1:40 ratio recommended for stability)

### Wiring Connections

#### Azimuth Axis (Primary)
```
Raspberry Pi GPIO → DM542 Driver
GPIO 23 (AZ_DIR_PIN)    → DIR+
GPIO 24 (AZ_STEP_PIN)   → PUL+
GPIO 25 (AZ_ENABLE_PIN) → ENA+
GND                     → DIR-, PUL-, ENA-
```

#### Elevation Axis (Secondary)
```
Raspberry Pi GPIO → DM542 Driver
GPIO 26 (EL_DIR_PIN)    → DIR+
GPIO 27 (EL_STEP_PIN)   → PUL+
GPIO 22 (EL_ENABLE_PIN) → ENA+
GND                     → DIR-, PUL-, ENA-
```

#### WT901C-RS485 IMU
```
WT901C → RS485 Adapter → Raspberry Pi
VCC    → 5V            → 5V
GND    → GND           → GND
A+     → A+            → USB Port
B-     → B-            → (usually /dev/ttyUSB0)
```

## Software Installation

### 1. Prepare Raspberry Pi OS
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-dev git -y

# Enable GPIO and Serial
sudo raspi-config
# Navigate to: Interface Options → Enable GPIO and Serial
```

### 2. Clone and Setup Project
```bash
# Clone repository
git clone <your-repo-url> ~/stepper_rasp
cd ~/stepper_rasp

# Install Python dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x start_rotator.sh
chmod +x test_rotator.py
```

### 3. Configure Environment
```bash
# Edit .env file to match your GPIO connections
nano .env

# Verify motor configuration
nano motor_config.yaml
```

### 4. Test Hardware Connections
```bash
# Test individual motor movement
sudo python3 test-move.py

# Test complete rotator system
sudo python3 test_rotator.py
```

## Configuration

### GPIO Pin Configuration (.env)
The `.env` file contains all GPIO pin assignments:

```bash
# Azimuth Axis
AZ_DIR_PIN=23
AZ_STEP_PIN=24
AZ_ENABLE_PIN=25

# Elevation Axis
EL_DIR_PIN=26
EL_STEP_PIN=27
EL_ENABLE_PIN=22

# IMU Serial Port
IMU_PORT=/dev/ttyUSB0
```

### Motor Configuration (motor_config.yaml)
Key settings to verify:

```yaml
motor:
  steps_per_revolution: 200    # Standard for 1.8° motors
  gear_ratio: 40              # Worm gear ratio
  
driver:
  microstep_multiplier: 1     # Match DIP switch settings
  current_setting: 70         # 70% of max current
  
motion:
  default_speed: 100          # Steps per second
  max_speed: 1000
```

## Running the Rotator Controller

### Manual Start
```bash
# Start rotator controller
sudo ./start_rotator.sh

# The server will listen on TCP port 4533
# Compatible with Hamlib/rotctld protocol
```

### Automatic Startup (Systemd Service)
```bash
# Copy service file
sudo cp ogrc.service /etc/systemd/system/

# Edit paths in service file if needed
sudo nano /etc/systemd/system/ogrc.service

# Enable and start service
sudo systemctl enable ogrc.service
sudo systemctl start ogrc.service

# Check status
sudo systemctl status ogrc.service
```

## Integration with Gpredict

### Method 1: Direct Connection
1. Start the rotator controller: `sudo ./start_rotator.sh`
2. In Gpredict: **Radio Control** → **Settings**
3. Add new rotator:
   - **Name**: OGRC Rotator
   - **Host**: localhost
   - **Port**: 4533
   - **Type**: GS-232A/B

### Method 2: Via Hamlib rotctld
```bash
# Start rotator controller
sudo ./start_rotator.sh

# In another terminal, start rotctld
rotctld -m 202 -r localhost:4533 -s 115200

# Configure Gpredict to use rotctld
# Host: localhost, Port: 4533
```

## Testing and Verification

### Basic Functionality Test
```bash
# Run automated tests
sudo python3 test_rotator.py

# Manual control mode
sudo python3 test_rotator.py manual
```

### GS-232 Protocol Commands
You can test manually using telnet:

```bash
# Connect to rotator
telnet localhost 4533

# Commands:
AZ180    # Set azimuth to 180°
EL45     # Set elevation to 45°
P        # Get current position
S        # Stop movement
H        # Home both axes
```

### Expected Responses
```
Command: P
Response: AZ=180.0 EL=45.0

Command: AZ90
Response: OK

Command: H
Response: OK
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied (GPIO)
```bash
# Ensure running as root
sudo python3 main.py

# Or add user to gpio group
sudo usermod -a -G gpio $USER
```

#### 2. IMU Not Detected
```bash
# Check USB devices
lsusb

# Check serial ports
ls -la /dev/ttyUSB*

# Test IMU connection
sudo python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0', 115200); print('IMU OK')"
```

#### 3. Motors Not Moving
- Verify power supply (24V, sufficient current)
- Check DIP switch settings on drivers
- Verify GPIO connections
- Test with `test-move.py`

#### 4. Position Feedback Issues
- Calibrate IMU orientation
- Check RS485 wiring polarity
- Verify baud rate (115200)

### Log Files
```bash
# View real-time logs
tail -f rotator.log

# System service logs
sudo journalctl -u ogrc.service -f
```

## Performance Tuning

### Accuracy Improvements
1. **Mechanical**: Use higher gear ratios, reduce backlash
2. **Software**: Tune position tolerance in main.py
3. **IMU**: Regular calibration, vibration isolation

### Speed Optimization
1. Increase `max_speed` in motor_config.yaml
2. Adjust `default_speed` for tracking vs. slewing
3. Optimize microstepping settings

## Safety Features

- **Soft Limits**: Prevents over-rotation
- **Emergency Stop**: Immediate movement halt
- **Timeout Protection**: Prevents runaway conditions
- **Position Feedback**: Closed-loop error correction

## Maintenance

### Regular Checks
- IMU calibration accuracy
- Mechanical backlash
- Power supply voltage
- Log file rotation

### Updates
```bash
# Update software
cd ~/stepper_rasp
git pull
pip3 install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart ogrc.service
```

## Support

For issues and improvements:
1. Check log files for error messages
2. Verify hardware connections
3. Test with simplified configurations
4. Submit issues with full logs and configuration

---

**Happy Satellite Tracking! 🛰️**