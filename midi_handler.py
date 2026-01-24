"""MIDI input handling for both standard MIDI and Bluetooth LE (Aeroband)"""
import asyncio
import mido
from PySide6.QtCore import Signal, QObject

try:
    from bleak import BleakClient
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False


class MIDIHandler(QObject):
    """Handles MIDI input in a separate thread"""
    midi_note_received = Signal(int, int)  # string, fret
    midi_note_released = Signal(int)  # string, fret
    fret_pressed = Signal(int, int)  # string, fret
    fret_released = Signal(int, int)  # string, fret

    # Standard tuning MIDI notes (lowest to highest string)
    STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # E2, A2, D3, G3, B3, E4
    NUM_FRETS = 24
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.input_port = None
        self.use_ble = False
        self.ble_client = None
        self.loop = None
        
    def start_listening_ble(self, device_address):
        """Start listening to Aeroband via BLE"""
        if not BLEAK_AVAILABLE:
            print("Bleak not available")
            return False
        
        self.use_ble = True
        self.ble_client = BleakClient(device_address)
        self.running = True
        return True
    
    def listen(self):
        """Listen for MIDI messages (run in thread)"""
        if self.use_ble:
            self.listen_ble()
        else:
            self.listen_standard()
    
    def midi_to_note_name(self, midi_note):
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = notes[midi_note % 12]
        octave = (midi_note // 12) - 1
        return f"{note}{octave}"
    
    def midi_to_fret_info(self, string, midi_note):
        return midi_note - self.STANDARD_TUNING[string]  
    
    def listen_standard(self):
        """Listen for standard MIDI messages"""
        if not self.input_port:
            return
            
        try:
            for msg in self.input_port:
                if not self.running:
                    break
                
                if msg.type == 'note_on':
                    fret_info = self.midi_to_fret_info(msg.note)
                    note_name = self.midi_to_note_name(msg.note)
                    if fret_info:
                        string_idx, fret = fret_info
                        print(f"Note On: String {string_idx}, Fret {fret}, Note {note_name}")
                    self.midi_note_received.emit(msg.note, msg.velocity)
                elif msg.type == 'note_off':
                    fret_info = self.midi_to_fret_info(msg.note)
                    note_name = self.midi_to_note_name(msg.note)
                    if fret_info:
                        string_idx, fret = fret_info
                        print(f"Note Off: String {string_idx}, Fret {fret}, Note {note_name}")
                    self.midi_note_released.emit(msg.note)
        except Exception as e:
            print(f"MIDI listening error: {e}")
    
    def listen_ble(self):
        """Listen for Aeroband BLE MIDI messages"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._ble_connect_and_listen())
        except Exception as e:
            print(f"BLE listening error: {e}")
    
    async def _ble_connect_and_listen(self):
        """Connect to Aeroband and listen for MIDI"""
        MIDI_CHAR_UUID = "7772e5db-3868-4112-a1a9-f2669d106bf3"
        MIDI_SERVICE_UUID = "03b80e5a-ede8-4b33-a751-6ce34ec4c700"
        
        try:
            async with self.ble_client as client:
                print(f"Connected to Aeroband, waiting for MIDI data...")
                
                def midi_callback(sender, data):
                    """Parse MIDI over BLE data from Aeroband"""
                    if not data or len(data) < 3:
                        return
                    
                    try:
                        # BLE MIDI format has a 2-byte header, then MIDI messages
                        i = 2  # Skip header bytes
                        
                        while i < len(data):
                            midi_status = data[i]
                            command = midi_status & 0xF0
                            string = midi_status & 0x0F
                            
                            # Filter system messages
                            if command == 0xF0:  # System exclusive
                                i += 1
                                continue
                            # print(f"MIDI Status: {midi_status:02x}, Command: {command:02x}, String: {string}")
                            # 3-byte messages: Note On (0x90), Note Off (0x80), CC (0xB0), Polyphonic Pressure (0xA0)
                            if command in [0x80, 0x90, 0xA0, 0xB0]:
                                if i + 2 >= len(data):
                                    break

                                note = data[i + 1]

                                fret = self.midi_to_fret_info(string, note)

                                velocity = data[i + 2]
                                
                                if command == 0x90:  # Note On
                                    if velocity > 0:
                                        self.midi_note_received.emit(5-string, fret)
                                    else:
                                        # Note on with velocity 0 = note off
                                        self.midi_note_released.emit(string)
                                
                                elif command == 0x80:  # Note Off
                                    self.midi_note_released.emit(string)
                                elif command == 0xB0:  # Control Change
                                    fret_number = data[i+2]
                                    if data[i+1] & 0x01:
                                        self.fret_pressed.emit(string, fret_number)
                                    else:
                                        self.fret_released.emit(string, fret_number)

                                i += 3
                            
                            # 2-byte messages: Program Change (0xC0), Channel Pressure (0xD0)
                            elif command in [0xC0, 0xD0]:
                                if i + 1 >= len(data):
                                    break
                                i += 2
                            
                            else:
                                # Unknown message, skip
                                i += 1
                    
                    except Exception as e:
                        print(f"Error parsing MIDI: {e}")
                
                await client.start_notify(MIDI_CHAR_UUID, midi_callback)
                print("MIDI notifications started")
                
                # Keep listening
                while self.running:
                    await asyncio.sleep(0.1)
                
                try:
                    await client.stop_notify(MIDI_CHAR_UUID)
                except:
                    pass
                    
        except Exception as e:
            print(f"BLE connection error: {e}")
            self.running = False
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self.input_port:
            self.input_port.close()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except:
                pass
