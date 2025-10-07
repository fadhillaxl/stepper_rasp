# Raspberry Pi Stepper Motor Control with TB6600 Driver

A comprehensive Python project for controlling stepper motors using a Raspberry Pi and TB6600 stepper motor driver. This project is based on the [Instructables tutorial](https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/) <mcreference link="https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/" index="0">0</mcreference> and provides both basic and advanced motor control capabilities.

## Features

- **Comprehensive Motor Control**: Step-by-step movement, degree-based rotation, and continuous rotation
- **Variable Speed Control**: Configurable speed from 1 to 1000 steps per second
- **Position Tracking**: Real-time position monitoring in steps and degrees
- **Safety Features**: Proper GPIO cleanup, signal handling, and motor disable functionality
- **Interactive Mode**: Command-line interface for manual motor control
- **Demo Mode**: Automated demonstration of various motor movements
- **Microstep Support**: Configurable microstep multipliers for precision control
- **Environment Configuration**: GPIO pin configuration via .env file

## Hardware Requirements

### Essential Components
- **Raspberry Pi** (any model with GPIO pins)
- **TB6600 Stepper Motor Driver/Controller**
- **6-wire Stepper Motor** (center tap wires left unconnected)
- **24V DC Power Supply** (5A recommended)
- **3.3V DC-DC Buck Converter**
- **Breadboard or PCB** for connections
- **Jumper wires** and connectors

### TB6600 Driver Features <mcreference link="https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/" index="0">0</mcreference>
- Input voltage range: 9V to 40V DC
- Motor drive output: Up to 4A
- Built-in cooling fan and heat sink
- Easy configuration with DIP switches
- 3 removable connectors
- Small footprint and easy mounting

## Wiring Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raspberry Pi  │    │   TB6600 Driver  │    │  Stepper Motor  │
│                 │    │                  │    │                 │
│ GPIO 23 (DIR)   ├────┤ DIR+             │    │                 │
│ GPIO 24 (STEP)  ├────┤ PUL+             │    │                 │
│ GPIO 25 (ENA)   ├────┤ ENA+             │    │                 │
│ GND             ├────┤ DIR-, PUL-, ENA- │    │                 │
│                 │    │                  │    │                 │
│                 │    │ A+, A-           ├────┤ Coil A          │
│                 │    │ B+, B-           ├────┤ Coil B          │
│                 │    │                  │    │ (Center taps    │
│                 │    │ VCC, GND         │    │  not connected) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────┐
                       │ 24V 5A PSU   │
                       │              │
                       │ +24V ────────┤
                       │ GND  ────────┤
                       └──────────────┘
                              │
                       ┌──────────────┐
                       │ 3.3V Buck    │
                       │ Converter    │
                       │              │
                       │ 3.3V ────────┤ (to RPi GPIO power)
                       │ GND  ────────┤
                       └──────────────┘
```

### Pin Connections

| Raspberry Pi | TB6600 Driver | Function |
|--------------|---------------|----------|
| GPIO 23      | DIR+          | Direction Control |
| GPIO 24      | PUL+          | Step Pulse |
| GPIO 25      | ENA+          | Enable/Disable |
| GND          | DIR-, PUL-, ENA- | Ground |
| 3.3V (Buck)  | DIR+, PUL+, ENA+ | Signal Power |

### Power Connections

| Component | Connection | Notes |
|-----------|------------|-------|
| 24V PSU + | TB6600 VCC | Main motor power |
| 24V PSU - | TB6600 GND | Ground |
| 24V PSU + | Buck Converter Input | For 3.3V generation |
| Buck 3.3V | Signal power | **DO NOT use RPi 3.3V directly** |

## Safety Warnings ⚠️

<mcreference link="https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/" index="0">0</mcreference>

- **DO NOT** connect to live power sources while making connections
- **DO** use appropriate fuses and circuit breakers
- **DO** use a power switch to isolate the power supply
- **DO** properly terminate all wires with robust connections
- **DO NOT** use clips, frayed wires, or ill-fitting connectors
- **DO NOT** use electrical tape as an insulator
- **DO NOT** source signals directly from RPi 3.3V pins

## Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd stepper_rasp
```

### 2. Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r stepper_rasp/requirements.txt
```

### 4. Configure GPIO Pins
Edit the `.env` file in the `stepper_rasp` directory:
```bash
# GPIO pin configuration
DIR_PIN=23
STEP_PIN=24
ENABLE_PIN=25
```

## Usage

### Running the Main Script
```bash
cd stepper_rasp
python test-move.py
```

You'll be prompted to choose between:
1. **Demo Mode**: Automated demonstration of motor capabilities
2. **Interactive Mode**: Manual control via command-line interface

### Demo Mode
Demonstrates various motor movements including:
- Basic step movements
- Degree-based rotation
- Full revolutions
- Variable speed control
- Continuous rotation
- Homing functionality

### Interactive Mode Commands

| Command | Description | Example |
|---------|-------------|---------|
| `s <steps> [speed] [direction]` | Move specific steps | `s 200 100 cw` |
| `d <degrees> [speed]` | Move by degrees | `d 90 150` |
| `r <revolutions> [speed]` | Move full revolutions | `r 2 200` |
| `c [speed] [direction]` | Continuous rotation | `c 300 cw` |
| `h [speed]` | Home motor to position 0 | `h 200` |
| `p` | Show current position | `p` |
| `e` | Enable motor | `e` |
| `x` | Disable motor | `x` |
| `m <multiplier>` | Set microstep multiplier | `m 4` |
| `q` | Quit | `q` |

### Programming Examples

#### Basic Usage
```python
from test_move import StepperMotor

# Initialize motor
motor = StepperMotor()
motor.enable_motor()

# Move 200 steps clockwise at 100 steps/sec
motor.move_steps(200, speed=100, clockwise=True)

# Move 90 degrees counter-clockwise
motor.move_degrees(-90, speed=150)

# Move 2 full revolutions
motor.move_revolutions(2, speed=200)

# Clean up
motor.cleanup()
```

#### Advanced Control
```python
# Set microstep multiplier for higher precision
motor.set_microstep_multiplier(4)  # Quarter stepping

# Continuous rotation with timeout
motor.continuous_rotation(speed=300, clockwise=True, duration=5)

# Position tracking
print(f"Current position: {motor.get_position()} steps")
print(f"Current angle: {motor.get_position_degrees():.1f} degrees")

# Home the motor
motor.home_motor(speed=200)
```

## TB6600 DIP Switch Configuration

The TB6600 driver uses DIP switches to configure microstep resolution:

| SW1 | SW2 | SW3 | Microstep | Multiplier |
|-----|-----|-----|-----------|------------|
| OFF | OFF | OFF | Full Step | 1 |
| ON  | OFF | OFF | Half Step | 2 |
| OFF | ON  | OFF | 1/4 Step  | 4 |
| ON  | ON  | OFF | 1/8 Step  | 8 |
| ON  | ON  | ON  | 1/16 Step | 16 |

Update your code accordingly:
```python
motor.set_microstep_multiplier(4)  # For 1/4 step configuration
```

## Troubleshooting

### Motor Not Moving
- Check all wiring connections
- Verify power supply is connected and switched on
- Ensure motor is enabled: `motor.enable_motor()`
- Check GPIO pin configuration in `.env` file

### Motor Moving Erratically
- Verify 3.3V signal power is stable
- Check for loose connections
- Ensure proper grounding
- Verify microstep settings match DIP switches

### Permission Errors
```bash
# Add user to gpio group (Raspberry Pi OS)
sudo usermod -a -G gpio $USER
# Logout and login again
```

### GPIO Already in Use
```python
# Clean up GPIO before running
import RPi.GPIO as GPIO
GPIO.cleanup()
```

## Motor Specifications

For optimal performance, determine your motor's specifications:
- **Steps per revolution** (typically 200 for 1.8° motors)
- **Voltage rating**
- **Current rating**
- **Coil resistance**

Update the motor class accordingly:
```python
motor.steps_per_revolution = 200  # Adjust for your motor
```

## Project Structure

```
stepper_rasp/
├── stepper_rasp/
│   ├── .env                 # GPIO pin configuration
│   ├── requirements.txt     # Python dependencies
│   └── test-move.py        # Main stepper motor control script
├── venv/                   # Python virtual environment
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with actual hardware
5. Submit a pull request

## License

This project is open source. Please refer to the original [Instructables tutorial](https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/) for attribution.

## Acknowledgments

- Based on the excellent [Instructables tutorial](https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/) <mcreference link="https://www.instructables.com/Raspberry-Pi-Python-and-a-TB6600-Stepper-Motor-Dri/" index="0">0</mcreference>
- TB6600 driver documentation and community examples
- Raspberry Pi Foundation for GPIO libraries

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify hardware connections
3. Review the original Instructables tutorial
4. Open an issue in this repository

---

**Happy Stepping!** 🔧⚙️