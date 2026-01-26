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
                                QHBoxLayout, QLabel, QComboBox, QPushButton, QTabWidget, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSize, QCoreApplication, QThread, QMetaObject, Slot
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtWidgets import QFrame

from fretboard_widget import FretboardWidget
from midi_handler import MIDIHandler
from guitar import GuitarState
from ChordVerifier import ChordVerifier
from practice_library import PracticeLibrary

try:
    from bleak import BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("Warning: bleak not installed. Bluetooth support disabled.")


class GuitarFretboardApp(QMainWindow):
    # Signals for thread-safe communication from worker thread
    status_changed = Signal(str)  # Emits status text
    style_changed = Signal(str)   # Emits stylesheet
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Fretboard - Aeroband")
        
        # Detect screen size and fit window
        screen = QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()
        
        # Use 85% of available screen width and height with margins
        margin = 20
        width = 1000 #int(available_geometry.width() * 0.85)
        height = int(available_geometry.height() * 0.85)
        x = margin
        y = margin
        
        self.setGeometry(x, y, width, height)
        self.guitar_state = GuitarState()
        
        
        # MIDI handler
        self.midi_handler = MIDIHandler()
        self.midi_handler.midi_note_received.connect(self.on_note_pressed)
        self.midi_handler.midi_note_released.connect(self.on_note_released)
        self.midi_handler.fret_pressed.connect(self.on_fret_pressed)
        self.midi_handler.fret_released.connect(self.on_fret_released)
        
        # Device info
        self.ble_devices = {}
        self.aeroband_address = None
        self.aeroband_name = None
        
        # Practice mode state (initialize early, before UI creation)
        self.practice_chords = []   # List of chords to practice
        self.current_practice_idx = 0  # Current chord index
        self.practice_name = ""  # Current practice name
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create fretboard first so we can access its CHORD_PRESETS
        self.fretboard = FretboardWidget()
        
        # Control panel (simplified)
        control_layout = QHBoxLayout()
        
        # Practice selector (from PracticeLibrary)
        self.practice_library = PracticeLibrary()
        control_layout.addWidget(QLabel("Practice:"))
        self.practice_combo = QComboBox()
        self.practice_combo.currentTextChanged.connect(self.on_practice_changed)
        # Block signals while adding items to avoid triggering on_practice_changed with empty strings
        self.practice_combo.blockSignals(True)
        self.practice_combo.addItems(self.practice_library.get_collection_names())
        self.practice_combo.blockSignals(False)
        control_layout.addWidget(self.practice_combo)
        
        # Chord selector
        control_layout.addWidget(QLabel("Chord:"))
        self.chord_combo = QComboBox()
        self.chord_combo.addItems(['None'] + list(self.fretboard.CHORD_PRESETS.keys()))
        self.chord_combo.setCurrentText('E Major')
        self.chord_combo.currentTextChanged.connect(self.on_chord_changed)
        control_layout.addWidget(self.chord_combo)
        
        # Feedback checkbox
        self.feedback_checkbox = QCheckBox("Show Feedback")
        self.feedback_checkbox.setChecked(True)
        control_layout.addWidget(self.feedback_checkbox)
        
        # Show target checkbox
        self.show_target_checkbox = QCheckBox("Show Target")
        self.show_target_checkbox.setChecked(True)
        self.show_target_checkbox.stateChanged.connect(self.on_show_target_changed)
        control_layout.addWidget(self.show_target_checkbox)
        
        # Show next chord checkbox
        self.show_next_chord_checkbox = QCheckBox("Show Next Chord")
        self.show_next_chord_checkbox.setChecked(True)
        self.show_next_chord_checkbox.stateChanged.connect(self.on_show_next_chord_changed)
        control_layout.addWidget(self.show_next_chord_checkbox)
        
        # Show chord name checkbox
        self.show_chord_name_checkbox = QCheckBox("Show Chord Name")
        self.show_chord_name_checkbox.setChecked(True)
        self.show_chord_name_checkbox.stateChanged.connect(self.on_show_chord_name_changed)
        control_layout.addWidget(self.show_chord_name_checkbox)
        
        control_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Scanning for Aeroband...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        layout.addLayout(control_layout)
        
        # Add fretboard widget to layout
        layout.addWidget(self.fretboard)
        
        # Trigger initial chord display after fretboard is created
        self.on_chord_changed('E Major')
        
        # Manually trigger to load the first practice collection after fretboard is ready
        if self.practice_combo.count() > 0:
            self.on_practice_changed(self.practice_combo.currentText())
        
        # MIDI thread (use QThread to host the QObject)
        self.midi_thread = None
        
        # Connect signals to slots for thread-safe UI updates
        self.status_changed.connect(self.status_label.setText)
        self.style_changed.connect(self.status_label.setStyleSheet)
        
        # Auto-connect to Aeroband on startup
        QTimer.singleShot(500, self.auto_connect_aeroband)

        # Chord detection timer
        self.chord_timer = QTimer()
        self.chord_timer.setSingleShot(True)  # Timer fires once then stops
        self.chord_timer.timeout.connect(self.finished_chord)
        self.chord_timeout_ms = 250  # 250ms timeout
        self.verifier = ChordVerifier()
        
        # Feedback state
        self.feedback_text = ""  # "CORRECT" or "INCORRECT"
        self.feedback_color = "green"  # "green" or "red"
        self.should_advance_chord = False  # Flag to advance to next chord after feedback


    
    def _log(self, msg):
        """Log to file and console"""
        print(msg)
        try:
            with open('guitar_app.log', 'a') as f:
                f.write(msg + '\n')
        except:
            pass
    
    @Slot()
    def _start_midi_thread(self):
        """Start MIDI listening thread (must be called from main thread)"""
        if self.midi_handler.running:
            # If an existing thread exists, stop it first
            try:
                if self.midi_thread and isinstance(self.midi_thread, QThread):
                    self.midi_handler.stop()
                    self.midi_thread.quit()
                    self.midi_thread.wait(2000)
            except Exception:
                pass

            self.midi_thread = QThread()
            # Move the QObject to the QThread so its timers/signals are associated with a QThread
            self.midi_handler.moveToThread(self.midi_thread)
            # When thread starts, call the blocking listen() method (will run in this thread)
            self.midi_thread.started.connect(self.midi_handler.listen)
            self.midi_thread.start()

            # Emit signals (we're on main thread now)
            self.status_changed.emit(f"Connected: {self.aeroband_name}")
            self.style_changed.emit("color: green; font-weight: bold;")
            self._log("Successfully connected!")
        else:
            # MIDI handler failed to start
            self.status_changed.emit("Failed to connect")
            self.style_changed.emit("color: red; font-weight: bold;")
            self._log("Failed to start listening")
    
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
                # Emit signal from worker thread (thread-safe)
                self.status_changed.emit("Aeroband not found - retrying...")
                self._log("No Aeroband found, will retry in 5 seconds")
                # Schedule retry on the main thread
                QMetaObject.invokeMethod(self, "auto_connect_aeroband", Qt.ConnectionType.QueuedConnection)
                return
            
            self.aeroband_address = aeroband.address
            self.aeroband_name = aeroband.name  # Store for later use in _start_midi_thread
            self._log(f"Connecting to {aeroband.name} at {aeroband.address}")
            # Emit signal from worker thread (thread-safe)
            self.status_changed.emit(f"Connecting to {aeroband.name}...")
            
            # Start listening (call _start_midi_thread on main thread to set up QThread)
            if self.midi_handler.start_listening_ble(aeroband.address):
                # Schedule MIDI thread setup on the main thread (required for moveToThread)
                QMetaObject.invokeMethod(self, "_start_midi_thread", Qt.ConnectionType.QueuedConnection)
            else:
                # Emit signals from worker thread (thread-safe)
                self.status_changed.emit("Failed to connect")
                self.style_changed.emit("color: red; font-weight: bold;")
                self._log("Failed to start listening")
                
        except Exception as e:
            self._log(f"Error: {e}")
            # Emit signals from worker thread (thread-safe)
            self.status_changed.emit(f"Error: {str(e)[:30]}")
            self.style_changed.emit("color: red; font-weight: bold;")
            QMetaObject.invokeMethod(self, "auto_connect_aeroband", Qt.ConnectionType.QueuedConnection)
    
    def on_chord_changed(self, chord_name):
        """Handle chord selection change"""
        self._log(f"Chord changed to: {chord_name}")
        if chord_name == 'None':
            self.fretboard.set_chord(None)
        else:
            self.fretboard.set_chord(chord_name)
    
    def on_show_target_changed(self):
        """Handle show target checkbox change"""
        show_target = self.show_target_checkbox.isChecked()
        self.fretboard.set_show_target(show_target)
    
    def on_show_next_chord_changed(self):
        """Handle show next chord checkbox change"""
        show_next_chord = self.show_next_chord_checkbox.isChecked()
        self.fretboard.set_show_next_chord(show_next_chord)
    
    def on_show_chord_name_changed(self):
        """Handle show chord name checkbox change"""
        show_chord_name = self.show_chord_name_checkbox.isChecked()
        self.fretboard.set_show_chord_name(show_chord_name)
    
    def on_practice_changed(self, practice_name):
        """Handle practice selection change"""
        self._log(f"Practice changed to: {practice_name}")
        self.practice_name = practice_name
        
        # Load practice chords
        print(f"[DEBUG] Available collections: {self.practice_library.get_collection_names()}")
        print(f"[DEBUG] Requesting collection: '{practice_name}'")
        collection = self.practice_library.get_collection(practice_name)
        print(f"[DEBUG] Got collection: {collection}")
        self.practice_chords = collection or []
        print(f"[DEBUG] practice_chords populated with {len(self.practice_chords)} chords: {[c.name for c in self.practice_chords]}")
        self.current_practice_idx = 0
        self._load_next_practice_chord()
    
    def on_note_pressed(self, string, fret):
        """Handle MIDI note on"""
        print(f"Note Pressed: String {string}, Fret {fret}")
        # Reset the chord detection timer whenever a string is struck
        self.chord_timer.stop()
        self.chord_timer.start(self.chord_timeout_ms)

        self.guitar_state.strike_string(string, fret)
        self.guitar_state.press_fret(string, fret)
        print(f"Current Guitar State: {self.guitar_state.get_summary()}")
        self._state_changed()
    
    def on_note_released(self, string):
        """Handle MIDI note off"""
        print(f"Note Released: String {string}")
        self.guitar_state.release_string(string)  
        print(f"Current Guitar State: {self.guitar_state.get_summary()}")
        self._state_changed()
    
    def on_fret_pressed(self, string, fret):
        """Handle fret pressed event"""
        print(f"Fret Pressed: String {string}, Fret {fret}")
        self.guitar_state.press_fret(string, fret)
        self._state_changed()

    def on_fret_released(self, string, fret):
        """Handle fret released event"""
        print(f"Fret Released: String {string}, Fret {fret}")
        self.guitar_state.release_fret(string, fret)
        # Clear feedback when all frets are released
        if all(f == 0 for f in self.guitar_state.pressed_frets):
            # If we should advance to next chord, do it now
            if self.should_advance_chord:
                self.should_advance_chord = False
                self.current_practice_idx += 1
                self._load_next_practice_chord()
            self.feedback_text = ""
            self.feedback_color = "green"
        self._state_changed()

    def _state_changed(self):
        """Update fretboard display based on guitar state"""
        self.fretboard.set_guitar_state(self.guitar_state)
        # Pass feedback to fretboard if checkbox is enabled
        if self.feedback_checkbox.isChecked():
            self.fretboard.set_feedback(self.feedback_text, self.feedback_color)
        else:
            self.fretboard.set_feedback("", "green")
        self.fretboard.show()
    
    def _load_next_practice_chord(self):
        """Load the next chord in the practice sequence"""
        print(f"[DEBUG] _load_next_practice_chord: idx={self.current_practice_idx}, total={len(self.practice_chords)}")
        if self.current_practice_idx < len(self.practice_chords):
            target_chord = self.practice_chords[self.current_practice_idx]
            self._log(f"Practice [{self.current_practice_idx + 1}/{len(self.practice_chords)}]: {target_chord.name}")
            
            # Set the chord on the fretboard
            # We need to pass the frets in the format expected by set_chord
            # which is {0: [fret0, fret1, ...]}
            self.fretboard.chord_name = target_chord.name
            self.fretboard.chord_frets = {0: target_chord.frets}
            self.fretboard.strings_to_strike = target_chord.strings_to_strike
            
            # Set the next chord (if there is one) to display in yellow
            if self.current_practice_idx + 1 < len(self.practice_chords):
                next_chord = self.practice_chords[self.current_practice_idx + 1]
                self.fretboard.set_next_chord(next_chord.name, next_chord.frets)
            else:
                # No next chord - clear it
                self.fretboard.set_next_chord(None, [])
            
            self.fretboard.update()
            
            self.chord_combo.blockSignals(True)
            self.chord_combo.setCurrentText(target_chord.name)
            self.chord_combo.blockSignals(False)
        else:
            # Loop back to the beginning
            self._log(f"✓ Completed practice: {self.practice_name}! Restarting...")
            self.current_practice_idx = 0
            self._load_next_practice_chord()

    def finished_chord(self):
        """Called when chord playing is finished (250ms after last string struck)"""
        print("Chord finished!")
        print(f"Final chord state: {self.guitar_state.get_summary()}")
        
        # Get the current target chord
        if self.current_practice_idx < len(self.practice_chords):
            target_chord = self.practice_chords[self.current_practice_idx]
            current_chord_name = target_chord.name
            target_frets = target_chord.frets
            target_strings = target_chord.strings_to_strike
        else:
            current_chord_name = self.chord_combo.currentText()
            target_frets = None
            target_strings = None
        
        if current_chord_name != 'None' and target_frets is not None:
            strings_matched, frets_matched = self.verifier.verify(target_frets, target_strings, self.guitar_state)
            if frets_matched and strings_matched:
                print(f"✓ CORRECT: {current_chord_name} played perfectly!")
                self.feedback_text = "CORRECT"
                self.feedback_color = "green"
                # If feedback is not enabled, advance immediately
                # Otherwise, set flag to advance after frets are released
                if self.feedback_checkbox.isChecked():
                    self.should_advance_chord = True
                else:
                    self.current_practice_idx += 1
                    QTimer.singleShot(500, self._load_next_practice_chord)
            else:
                errors = self.verifier.get_errors()
                print(f"✗ INCORRECT: {current_chord_name}")
                for string_idx, error in errors.items():
                    print(f"  {error}")
                self.feedback_text = "INCORRECT"
                self.feedback_color = "red"

        self.guitar_state.clear_strings()
        self._state_changed()




    def closeEvent(self, event):
        """Clean up on close"""
        if self.midi_handler.running:
            self.midi_handler.stop()
            if self.midi_thread:
                try:
                    # If using QThread, quit and wait
                    if isinstance(self.midi_thread, QThread):
                        self.midi_thread.quit()
                        self.midi_thread.wait(2000)
                    else:
                        # Fallback: if a plain thread was used
                        self.midi_thread.join(timeout=2)
                except Exception:
                    pass
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
