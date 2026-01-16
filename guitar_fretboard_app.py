"""
Guitar Fretboard MIDI Visualizer
Displays a guitar fretboard with dots for practice chords and highlights frets being pressed via MIDI
Supports both standard MIDI and Bluetooth LE (Aeroband)
Uses JSON configuration for fret positions
"""

import sys
import threading
import asyncio
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QComboBox, QPushButton, QTabWidget)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSize, QCoreApplication
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import QFrame

from fretboard_widget import FretboardWidget
from midi_handler import MIDIHandler

try:
    from bleak import BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Warning: bleak not installed. Bluetooth support disabled.")


class GuitarFretboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Fretboard - Aeroband")
        self.setGeometry(100, 100, 1200, 700)
        
        
        # MIDI handler
        self.midi_handler = MIDIHandler()
        self.midi_handler.midi_note_received.connect(self.on_note_pressed)
        self.midi_handler.midi_note_released.connect(self.on_note_released)
        
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
        
        # Trigger initial chord display after fretboard is created
        self.on_chord_changed('E Major')
        
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
