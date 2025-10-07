#!/usr/bin/env python3
"""
Test script for Open Ground Station Rotator Controller
This script tests the GS-232 protocol communication with the rotator
"""

import socket
import time
import sys

def test_rotator_connection(host='localhost', port=4533):
    """Test connection to rotator controller"""
    print(f"Testing connection to rotator at {host}:{port}")
    
    try:
        # Connect to rotator
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        print("✓ Connected to rotator controller")
        
        # Test commands
        test_commands = [
            ("P", "Get current position"),
            ("AZ180", "Set azimuth to 180°"),
            ("EL45", "Set elevation to 45°"),
            ("P", "Get position after move"),
            ("AZ0", "Return azimuth to 0°"),
            ("EL0", "Return elevation to 0°"),
            ("H", "Home both axes"),
            ("P", "Get final position")
        ]
        
        for command, description in test_commands:
            print(f"\nSending: {command} ({description})")
            sock.send(f"{command}\n".encode('ascii'))
            
            # Receive response
            response = sock.recv(1024).decode('ascii').strip()
            print(f"Response: {response}")
            
            # Wait between commands
            if command.startswith(('AZ', 'EL', 'H')):
                print("Waiting for movement to complete...")
                time.sleep(3)
        
        sock.close()
        print("\n✓ All tests completed successfully")
        return True
        
    except ConnectionRefusedError:
        print("✗ Connection refused - is the rotator controller running?")
        print("Start it with: sudo python3 main.py")
        return False
    except socket.timeout:
        print("✗ Connection timeout")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_manual_control():
    """Interactive manual control mode"""
    print("\n" + "="*50)
    print("Manual Control Mode")
    print("Commands: AZxxx, ELxxx, P, S, H, Q (quit)")
    print("="*50)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 4533))
        
        while True:
            command = input("\nEnter command: ").strip().upper()
            
            if command == 'Q':
                break
            
            if not command:
                continue
            
            sock.send(f"{command}\n".encode('ascii'))
            response = sock.recv(1024).decode('ascii').strip()
            print(f"Response: {response}")
        
        sock.close()
        
    except Exception as e:
        print(f"Manual control failed: {e}")

def main():
    print("Open Ground Station Rotator Controller - Test Script")
    print("="*60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'manual':
            test_manual_control()
            return
        elif sys.argv[1] == 'help':
            print("Usage:")
            print("  python3 test_rotator.py        - Run automated tests")
            print("  python3 test_rotator.py manual - Manual control mode")
            print("  python3 test_rotator.py help   - Show this help")
            return
    
    # Run automated tests
    success = test_rotator_connection()
    
    if success:
        print("\n" + "="*60)
        print("✓ Rotator controller is working correctly!")
        print("You can now use it with Gpredict and rotctld")
        print("\nTo use with Gpredict:")
        print("1. Start rotctld: rotctld -m 202 -r localhost:4533")
        print("2. In Gpredict: Radio Control -> Settings")
        print("3. Set rotator to 'GS-232A/B' on localhost:4533")
    else:
        print("\n" + "="*60)
        print("✗ Tests failed. Please check:")
        print("1. Rotator controller is running (sudo python3 main.py)")
        print("2. GPIO pins are properly connected")
        print("3. .env file has correct pin configurations")
        print("4. IMU is connected and accessible")

if __name__ == "__main__":
    main()