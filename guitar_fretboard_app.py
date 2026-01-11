"""
Guitar Fretboard MIDI Visualizer
Displays a guitar fretboard with dots for practice chords and highlights frets being pressed via MIDI
Supports both standard MIDI and Bluetooth LE (Aeroband)
"""

import sys
import threading
import asyncio
import mido
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QComboBox, QPushButton, QTabWidget)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSize, QCoreApplication
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import QFrame

try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Warning: bleak not installed. Bluetooth support disabled.")


class MIDIHandler(QObject):
    """Handles MIDI input in a separate thread"""
    midi_note_received = Signal(int, int)  # note, velocity
    midi_note_released = Signal(int)  # note
    
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
    
    def start_listening(self, port_name=None):
        """Start listening to MIDI input"""
        try:
            if port_name:
                self.input_port = mido.open_input(port_name)
            else:
                # Try to open default MIDI input
                available_inputs = mido.get_input_names()
                if available_inputs:
                    self.input_port = mido.open_input(available_inputs[0])
                else:
                    print("No MIDI inputs available")
                    return False
            
            self.running = True
            self.use_ble = False
            return True
        except Exception as e:
            print(f"Error opening MIDI input: {e}")
            return False
    
    def listen(self):
        """Listen for MIDI messages (run in thread)"""
        if self.use_ble:
            self.listen_ble()
        else:
            self.listen_standard()
    
    def listen_standard(self):
        """Listen for standard MIDI messages"""
        if not self.input_port:
            return
            
        try:
            for msg in self.input_port:
                if not self.running:
                    break
                
                if msg.type == 'note_on':
                    self.midi_note_received.emit(msg.note, msg.velocity)
                elif msg.type == 'note_off':
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
                            channel = midi_status & 0x0F
                            
                            # Filter system messages
                            if command == 0xF0:  # System exclusive
                                i += 1
                                continue
                            
                            # 3-byte messages: Note On (0x90), Note Off (0x80), CC (0xB0), Polyphonic Pressure (0xA0)
                            if command in [0x80, 0x90, 0xA0, 0xB0]:
                                if i + 2 >= len(data):
                                    break
                                
                                note = data[i + 1]
                                velocity = data[i + 2]
                                
                                if command == 0x90:  # Note On
                                    if velocity > 0:
                                        print(f"Note On: {note}, Velocity: {velocity}")
                                        self.midi_note_received.emit(note, velocity)
                                    else:
                                        # Note on with velocity 0 = note off
                                        print(f"Note Off: {note}")
                                        self.midi_note_released.emit(note)
                                
                                elif command == 0x80:  # Note Off
                                    print(f"Note Off: {note}")
                                    self.midi_note_released.emit(note)
                                
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


class FretboardWidget(QFrame):
    """Custom widget to draw the guitar fretboard"""
    
    # Standard tuning MIDI notes (lowest to highest string)
    STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # E2, A2, D3, G3, B3, E4
    NUM_FRETS = 24
    NUM_STRINGS = 6
    
    CHORD_PRESETS = {
        'E Major': {0: [0, 2, 2, 1, 0, 0]},
        'A Major': {0: [0, 0, 2, 2, 2, 0]},
        'D Major': {0: [2, 3, 2, 0, 0, 0]},
        'G Major': {0: [3, 2, 0, 0, 0, 3]},
        'C Major': {0: [0, 3, 2, 0, 1, 0]},
        'F Major': {0: [1, 3, 3, 2, 1, 1]},
        'Em': {0: [0, 2, 2, 0, 1, 0]},
        'Am': {0: [0, 0, 2, 2, 1, 0]},
        'Dm': {0: [2, 3, 2, 0, 0, 0]},
        'Gm': {0: [3, 5, 5, 3, 3, 3]},
    }
    
    # Signal for thread-safe updates
    repaint_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(1000, 600))
        self.pressed_notes = set()  # MIDI notes currently pressed
        self.chord_name = None
        self.chord_frets = {}  # Fret positions for the selected chord
        
        # Setup timer for periodic repaint (thread-safe)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)  # Update every 50ms
        
    def set_pressed_notes(self, notes):
        """Update which MIDI notes are currently pressed"""
        self.pressed_notes = notes
    
    def add_pressed_note(self, note):
        """Add a pressed note"""
        self.pressed_notes.add(note)
    
    def remove_pressed_note(self, note):
        """Remove a pressed note"""
        self.pressed_notes.discard(note)
    
    def set_chord(self, chord_name):
        """Set the chord to display"""
        self.chord_name = chord_name
        if chord_name in self.CHORD_PRESETS:
            self.chord_frets = self.CHORD_PRESETS[chord_name]
        self.update()
    
    def get_fret_for_note(self, midi_note):
        """Convert MIDI note to (string, fret) position"""
        for string_idx, open_note in enumerate(self.STANDARD_TUNING):
            if open_note <= midi_note <= open_note + self.NUM_FRETS:
                fret = midi_note - open_note
                return (string_idx, fret)
        return None
    
    def paintEvent(self, event):
        """Draw the fretboard"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Padding and dimensions
        left_margin = 80
        top_margin = 40
        string_spacing = (height - 2 * top_margin) / (self.NUM_STRINGS - 1)
        fret_width = (width - 2 * left_margin) / self.NUM_FRETS
        
        # Draw title
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        painter.drawText(10, 20, f"Guitar Fretboard{' - ' + self.chord_name if self.chord_name else ''}")
        
        # Draw fret numbers
        painter.setFont(QFont('Arial', 10))
        for fret in range(self.NUM_FRETS + 1):
            x = left_margin + fret * fret_width
            painter.drawText(x - 10, top_margin - 20, 20, 20, Qt.AlignCenter, str(fret))
        
        # Draw strings (horizontal lines)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        for string_idx in range(self.NUM_STRINGS):
            y = top_margin + string_idx * string_spacing
            painter.drawLine(left_margin, y, width - left_margin, y)
            
            # Draw string label
            note_name = self._midi_to_note(self.STANDARD_TUNING[string_idx])
            painter.drawText(5, y - 10, 70, 20, Qt.AlignRight | Qt.AlignVCenter, note_name)
        
        # Draw frets (vertical lines)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for fret in range(1, self.NUM_FRETS + 1):
            x = left_margin + fret * fret_width
            painter.drawLine(x, top_margin, x, height - top_margin)
        
        # Draw fret markers (dots on the side)
        marker_frets = [3, 5, 7, 9, 12, 15, 17, 19, 21]
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        marker_x = width - left_margin + 30
        for fret in marker_frets:
            if fret <= self.NUM_FRETS:
                y = top_margin + (self.NUM_STRINGS - 1) / 2 * string_spacing
                painter.drawEllipse(int(marker_x - 4), int(y - 4), 8, 8)
        
        # Draw chord dots (practice target)
        if self.chord_frets:
            painter.setBrush(QBrush(QColor(100, 150, 255)))
            painter.setPen(QPen(QColor(50, 100, 200), 2))
            
            for string_idx, frets in self.chord_frets.items():
                if string_idx < len(frets):
                    fret = frets[string_idx]
                    if fret > 0:  # 0 = open string (no dot)
                        y = top_margin + string_idx * string_spacing
                        x = left_margin + fret * fret_width
                        painter.drawEllipse(int(x - 12), int(y - 12), 24, 24)
        
        # Draw pressed notes (active frets)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(QPen(QColor(200, 0, 0), 2))
        
        for note in self.pressed_notes:
            result = self.get_fret_for_note(note)
            if result:
                string_idx, fret = result
                y = top_margin + string_idx * string_spacing
                x = left_margin + fret * fret_width
                painter.drawEllipse(int(x - 15), int(y - 15), 30, 30)
    
    def _midi_to_note(self, midi_note):
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = notes[midi_note % 12]
        octave = (midi_note // 12) - 1
        return f"{note}{octave}"


class GuitarFretboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Fretboard - Aeroband")
        self.setGeometry(100, 100, 1200, 700)
        
        # Setup logging
        with open('guitar_app.log', 'w') as f:
            f.write("=== Guitar Fretboard App Started ===\n")
        
        # MIDI handler
        self.midi_handler = MIDIHandler()
        self.midi_handler.midi_note_received.connect(self.on_note_pressed)
        self.midi_handler.midi_note_released.connect(self.on_note_released)
        
        self._log("MIDI handler created and signals connected")
        
        # Device info
        self.ble_devices = {}
        self.aeroband_address = None
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Control panel (simplified)
        control_layout = QHBoxLayout()
        
        # Chord selector
        control_layout.addWidget(QLabel("Practice Chord:"))
        self.chord_combo = QComboBox()
        self.chord_combo.addItems(['None'] + list(FretboardWidget.CHORD_PRESETS.keys()))
        self.chord_combo.setCurrentText('E Major')
        self.chord_combo.currentTextChanged.connect(self.on_chord_changed)
        control_layout.addWidget(self.chord_combo)
        
        control_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Scanning for Aeroband...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        layout.addLayout(control_layout)
        
        # Fretboard widget
        self.fretboard = FretboardWidget()
        layout.addWidget(self.fretboard)
        
        # MIDI thread
        self.midi_thread = None
        
        # Auto-connect to Aeroband on startup
        QTimer.singleShot(500, self.auto_connect_aeroband)
    
    def _log(self, msg):
        """Log to file and console"""
        print(msg)
        try:
            with open('guitar_app.log', 'a') as f:
                f.write(msg + '\n')
        except:
            pass
    
    def auto_connect_aeroband(self):
        """Automatically scan for and connect to Aeroband"""
        self._log("Auto-connecting to Aeroband...")
        self.status_label.setText("Scanning for Aeroband...")
        
        # Scan in background thread
        threading.Thread(target=self._scan_and_connect, daemon=True).start()
    
    def _scan_and_connect(self):
        """Background thread to scan and connect"""
        try:
            self._log("Starting BLE scan...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            devices = loop.run_until_complete(BleakScanner.discover())
            
            self._log(f"Found {len(devices)} devices")
            
            aeroband = None
            for device in devices:
                self._log(f"  Device: {device.name} ({device.address})")
                # Look for Aeroband devices
                if device.name and ('aeroband' in device.name.lower() or 'guitar' in device.name.lower()):
                    aeroband = device
                    self._log(f"    -> Found Aeroband!")
                    break
            
            if not aeroband:
                self.status_label.setText("Aeroband not found - retrying...")
                self._log("No Aeroband found, will retry in 5 seconds")
                QTimer.singleShot(5000, self.auto_connect_aeroband)
                return
            
            self.aeroband_address = aeroband.address
            self._log(f"Connecting to {aeroband.name} at {aeroband.address}")
            self.status_label.setText(f"Connecting to {aeroband.name}...")
            
            # Start listening
            if self.midi_handler.start_listening_ble(aeroband.address):
                self.midi_thread = threading.Thread(target=self.midi_handler.listen, daemon=True)
                self.midi_thread.start()
                self.status_label.setText(f"Connected: {aeroband.name}")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self._log("Successfully connected!")
            else:
                self.status_label.setText("Failed to connect")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self._log("Failed to start listening")
                
        except Exception as e:
            self._log(f"Error: {e}")
            self.status_label.setText(f"Error: {str(e)[:30]}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QTimer.singleShot(5000, self.auto_connect_aeroband)
    
    def on_chord_changed(self, chord_name):
        """Handle chord selection change"""
        self._log(f"Chord changed to: {chord_name}")
        if chord_name == 'None':
            self.fretboard.set_chord(None)
        else:
            self.fretboard.set_chord(chord_name)
    
    def on_note_pressed(self, note, velocity):
        """Handle MIDI note on"""
        self.fretboard.add_pressed_note(note)
    
    def on_note_released(self, note):
        """Handle MIDI note off"""
        self.fretboard.remove_pressed_note(note)
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.midi_handler.running:
            self.midi_handler.stop()
            if self.midi_thread:
                self.midi_thread.join(timeout=2)
        event.accept()
    
    def on_device_type_changed(self, device_type):
        """Handle device type change"""
        pass
    
    def update_midi_inputs(self):
        """Update the list of available MIDI inputs"""
        pass
    
    def scan_ble_devices(self):
        """Scan for Aeroband BLE devices"""
        pass
    
    def _scan_ble(self):
        """Background BLE scan"""
        pass
    
    def connect_device(self):
        """Connect to selected device"""
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GuitarFretboardApp()
    window.show()
    sys.exit(app.exec())
