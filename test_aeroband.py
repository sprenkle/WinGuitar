"""
Test script to debug Aeroband MIDI connection
"""

import sys
import asyncio
import threading
from bleak import BleakClient, BleakScanner

MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHAR_UUID = "7772e5db-3868-4112-a1a9-f2669d106bf3"

def log(msg):
    """Log to both console and file"""
    print(msg)
    with open('aeroband_test.log', 'a') as f:
        f.write(msg + '\n')

async def test_aeroband():
    """Test Aeroband connection and MIDI"""
    log("Starting Aeroband test...")
    
    # Scan for devices
    log("Scanning for devices...")
    devices = await BleakScanner.discover()
    
    log(f"Found {len(devices)} devices")
    
    aeroband = None
    for device in devices:
        log(f"Device: {device.name} ({device.address})")
        if device.name and 'aero' in device.name.lower():
            aeroband = device
            log(f"  -> Found Aeroband!")
    
    if not aeroband:
        log("No Aeroband found!")
        return
    
    # Connect
    log(f"Connecting to {aeroband.name}...")
    async with BleakClient(aeroband.address) as client:
        log("Connected!")
        
        # Start notifications
        def callback(sender, data):
            hex_data = ' '.join(f'{b:02x}' for b in data)
            log(f"MIDI DATA: {hex_data}")
        
        log("Starting notifications...")
        await client.start_notify(MIDI_CHAR_UUID, callback)
        
        log("Waiting for MIDI data (30 seconds)...")
        for i in range(30):
            await asyncio.sleep(1)
            log(f"  {i+1}/30")
        
        log("Done!")

# Clear log
open('aeroband_test.log', 'w').close()

# Run test
asyncio.run(test_aeroband())
