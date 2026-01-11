"""
Windows MIDI Debug Script - Connects to Aeroband using BLE and displays all MIDI messages
Requires: pip install bleak
"""

import asyncio
from bleak import BleakClient, BleakScanner

# Aeroband UUIDs (standard MIDI service)
MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
MIDI_CHAR_UUID = "7772e5db-3868-4112-a1a9-f2669d106bf3"


class MIDIDebugger:
    def __init__(self):
        self.client = None
        self.note_names = {
            0: 'C-1', 1: 'C#-1', 2: 'D-1', 3: 'D#-1', 4: 'E-1', 5: 'F-1',
            6: 'F#-1', 7: 'G-1', 8: 'G#-1', 9: 'A-1', 10: 'A#-1', 11: 'B-1',
            12: 'C0', 13: 'C#0', 14: 'D0', 15: 'D#0', 16: 'E0', 17: 'F0',
            18: 'F#0', 19: 'G0', 20: 'G#0', 21: 'A0', 22: 'A#0', 23: 'B0',
            24: 'C1', 25: 'C#1', 26: 'D1', 27: 'D#1', 28: 'E1', 29: 'F1',
            30: 'F#1', 31: 'G1', 32: 'G#1', 33: 'A1', 34: 'A#1', 35: 'B1',
            36: 'C2', 37: 'C#2', 38: 'D2', 39: 'D#2', 40: 'E2', 41: 'F2',
            42: 'F#2', 43: 'G2', 44: 'G#2', 45: 'A2', 46: 'A#2', 47: 'B2',
            48: 'C3', 49: 'C#3', 50: 'D3', 51: 'D#3', 52: 'E3', 53: 'F3',
            54: 'F#3', 55: 'G3', 56: 'G#3', 57: 'A3', 58: 'A#3', 59: 'B3',
            60: 'C4', 61: 'C#4', 62: 'D4', 63: 'D#4', 64: 'E4', 65: 'F4',
            66: 'F#4', 67: 'G4', 68: 'G#4', 69: 'A4', 70: 'A#4', 71: 'B4',
            72: 'C5', 73: 'C#5', 74: 'D5', 75: 'D#5', 76: 'E5', 77: 'F5',
            78: 'F#5', 79: 'G5', 80: 'G#5', 81: 'A5', 82: 'A#5', 83: 'B5',
            84: 'C6', 85: 'C#6', 86: 'D6', 87: 'D#6', 88: 'E6', 89: 'F6',
            90: 'F#6', 91: 'G6', 92: 'G#6', 93: 'A6', 94: 'A#6', 95: 'B6',
            96: 'C7',
        }
        self.frets = [0, 0, 0, 0, 0, 0]
        self.message_count = 0

    def get_note_name(self, midi_note):
        """Get friendly note name from MIDI note number"""
        return self.note_names.get(midi_note, f'Unknown({midi_note})')

    async def scan_and_connect(self):
        """Scan for and connect to Aeroband guitar"""
        print("Scanning for Aeroband device...")
        
        devices = await BleakScanner.discover()
        aeroband_device = None
        
        for device in devices:
            print(f"Found: {device.name} ({device.address})")
            if device.name and ("aeroband" in device.name.lower() or "pocketdrum" in device.name.lower()):
                aeroband_device = device
                print(f"  -> Selected: {device.name}")
                break
        
        if not aeroband_device:
            print("Aeroband device not found!")
            return False
        
        print(f"\nConnecting to {aeroband_device.name}...")
        self.client = BleakClient(aeroband_device.address)
        
        try:
            await self.client.connect()
            print("Connected!")
            await self.list_services()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def list_services(self):
        """List all services and characteristics on the connected device"""
        print("\n=== DEVICE SERVICES & CHARACTERISTICS ===")
        
        services = self.client.services
        for service in services:
            print(f"\nService: {service.uuid}")
            print(f"  Description: {service.description}")
            
            for char in service.characteristics:
                print(f"  ├─ Characteristic: {char.uuid}")
                print(f"  │  Properties: {char.properties}")
                print(f"  │  Descriptors: {len(char.descriptors)}")
                
                # Check if this is likely the MIDI characteristic
                if "7772e5db" in str(char.uuid).lower():
                    print(f"  │  *** FOUND TARGET MIDI CHARACTERISTIC ***")
        
        print("\n")

    def notification_handler(self, sender, data):
        """Handle MIDI notifications from the device"""
        if not data or len(data) < 3:
            return
        
        # Parse BLE MIDI notification
        messages = self.parse_midi_messages(data)
        
        for msg in messages:
            command, string_num, fret_num, note, fret_pressed = msg
            
            self.message_count += 1
            self.frets[string_num] = fret_pressed
            
            action = "PRESS" if fret_pressed else "RELEASE"
            note_name = self.get_note_name(note)
            
            print(f"[{self.message_count:04d}] {action} - String:{string_num} Fret:{fret_num:2d} Note:{note_name:5s} (MIDI:{note:3d}) Cmd:{hex(command)}")
            print(f"       Fret States: {self.frets}")

    @staticmethod
    def parse_midi_messages(data):
        """Parse BLE MIDI notification and extract individual MIDI messages"""
        messages = []
        
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        
        if len(data) < 3:
            return messages
        
        # Debug: show raw bytes received
        hex_str = ' '.join('%02x' % b for b in data)
        print(f"[RAW DATA] Len={len(data)} Hex: {hex_str}")
        
        i = 2  # Skip BLE header and timestamp
        msg_count = 0
        
        while i < len(data):
            midi_status = data[i]
            command = midi_status & 0xF0
            if command == 0xb0:
                string_number = midi_status & 0x0F    
            else:
                string_number = 5 - (midi_status & 0x0F)
            
            print(f"[POS {i}] Status={hex(midi_status)} Cmd={hex(command)} String={string_number}")
            
            # 3-byte messages: Note On (0x90), Note Off (0x80), Polyphonic Pressure (0xA0), Control Change (0xB0)
            if (command == 0x80 or
                command == 0x90 or
                command == 0xA0 or 
                command == 0xB0):
                
                # Check we have enough bytes for a 3-byte message
                if i + 2 >= len(data):
                    print(f"  !! Incomplete 3-byte message at pos {i}")
                    break
                
                # Determine if fret pressed or released
                if command == 0x90:
                    fret_pressed = 1
                elif command == 0x80:
                    fret_pressed = 0
                else:
                    fret_pressed = data[i+1] & 0x01

                # Get fret number and note
                if command == 0xB0:
                    fret_number = data[i+2]
                    # For Windows version, we'll just use the fret number directly
                    # In production, you'd map this using the same logic as the Pico
                    note = 60 + fret_number  # Simple mapping for demo
                else:
                    note = data[i+1]
                    # Simple reverse calculation for demo
                    fret_number = note - 60 if note >= 60 else 0

                msg = [command, string_number, fret_number, note, fret_pressed]
                msg_count += 1
                print(f"  MSG[{msg_count}] Cmd={hex(command)} Str={string_number} Fret={fret_number} Note={note} Press={fret_pressed}")
                messages.append(msg)
                i += 3
            
            # 2-byte messages: Program Change (0xC0), Channel Pressure (0xD0)
            elif (command == 0xC0 or 
                  command == 0xD0):
                if i + 1 >= len(data):
                    print(f"  !! Incomplete 2-byte message at pos {i}")
                    break
                    
                msg = [command, string_number, 0, 0, 0]
                messages.append(msg)
                i += 2
            
            # System messages and other status bytes
            else:
                print(f"  !! Unknown status byte {hex(midi_status)} at pos {i}, skipping")
                i += 1
        
        print(f"[PARSED] Total {len(messages)} messages\n")
        return messages

    async def run(self):
        """Main debug loop"""
        print("=== WINDOWS AEROBAND MIDI DEBUG ===\n")
        
        if not await self.scan_and_connect():
            return
        
        print("\nListening for MIDI messages...")
        print("Press and release frets to see debug output.\n")
        
        try:
            # Subscribe to MIDI notifications
            await self.client.start_notify(MIDI_CHAR_UUID, self.notification_handler)
            
            # Keep running until user interrupts
            while True:
                await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\nDebug stopped by user")
        
        except Exception as e:
            print(f"\n\nError: {type(e).__name__}: {e}")
            if "was not found" in str(e):
                print("\n!!! CHARACTERISTIC NOT FOUND !!!")
                print("The MIDI characteristic UUID is not available on this device.")
                print("\nLooking for alternative characteristics...\n")
                
                # Print all characteristics for manual inspection
                services = self.client.services
                for service in services:
                    if "midi" in str(service.uuid).lower() or "03b80e5a" in str(service.uuid).lower():
                        print(f"\n>>> POTENTIAL MIDI SERVICE: {service.uuid}")
                        for char in service.characteristics:
                            print(f"    Characteristic: {char.uuid}")
                            print(f"    Properties: {char.properties}")
        
        finally:
            try:
                await self.client.stop_notify(MIDI_CHAR_UUID)
            except:
                pass
            await self.client.disconnect()
            print("Disconnected")


async def main():
    debugger = MIDIDebugger()
    await debugger.run()


if __name__ == '__main__':
    print("Windows Aeroband MIDI Debugger")
    print("================================")
    print("\nInstall dependencies with:")
    print("  pip install bleak")
    print("\nMake sure Bluetooth is enabled on your PC.\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
