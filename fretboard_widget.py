"""Guitar fretboard display widget"""
import json
from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QPen
from PySide6.QtCore import Signal, QTimer, Qt, QSize


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
        self.setMinimumSize(QSize(1600, 1000))
        self.pressed_notes = set()  # MIDI notes currently pressed
        self.chord_name = None
        self.chord_frets = {}  # Fret positions for the selected chord
        
        # Initialize image and config
        self.guitar_image = QPixmap()
        self.has_image = False
        
        # Load JSON configuration (which will also load the image)
        self.config = None
        self.vertical_positions = []
        self.horizontal_positions = []
        self.load_config()
        
        # Setup timer for periodic repaint (thread-safe)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)  # Update every 50ms
    
    def load_config(self):
        """Load guitar configuration from JSON"""
        import os
        
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, 'fenderstrat.json')
            
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Extract fret and string positions from JSON
            image_config = self.config.get('image', {})
            self.vertical_positions = image_config.get('vertical_positions', [])
            self.horizontal_positions = image_config.get('horizontal_positions', [])
            
            # Load image using path from JSON
            image_path = image_config.get('image_path', 'fenderstrat.jpg')
            
            # Resolve image path relative to script directory
            if not os.path.isabs(image_path):
                image_path = os.path.join(script_dir, image_path)
            
            abs_path = os.path.abspath(image_path)
            print(f"Trying to load image from: {abs_path}")
            print(f"File exists: {os.path.exists(abs_path)}")
            
            self.guitar_image = QPixmap(abs_path)
            print(f"Image loaded, isNull: {self.guitar_image.isNull()}, size: {self.guitar_image.width()}x{self.guitar_image.height()}")
            
            if self.guitar_image.isNull():
                # Try fallback paths
                fallback_paths = ['images/fenderstrat.jpg', 'fenderstrat.jpg']
                for fallback in fallback_paths:
                    abs_fallback = os.path.join(script_dir, fallback) if not os.path.isabs(fallback) else fallback
                    abs_fallback = os.path.abspath(abs_fallback)
                    print(f"Trying fallback: {abs_fallback}")
                    self.guitar_image = QPixmap(abs_fallback)
                    if not self.guitar_image.isNull():
                        print(f"Loaded image from: {abs_fallback}")
                        self.has_image = True
                        break
                if self.guitar_image.isNull():
                    print(f"Warning: Could not load image from {image_path} or fallback paths")
                    self.has_image = False
            else:
                print(f"Loaded image from: {abs_path}")
                self.has_image = True
            
            print(f"Loaded config: {len(self.vertical_positions)} vertical positions, {len(self.horizontal_positions)} horizontal positions")
            
            # Update NUM_FRETS from config if available
            self.NUM_FRETS = self.config.get('number_of_frets', 24)
            self.NUM_STRINGS = self.config.get('number_of_strings', 6)
            
        except FileNotFoundError as e:
            print(f"Warning: fenderstrat.json not found - {e}")
            self.config = None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            self.config = None
        
        # Dynamic positioning - will be calculated in paintEvent
        self.img_x = 0
        self.img_y = 0
        self.img_width = 0
        self.img_height = 0
        self.string_positions = []
        self.fret_positions = []
        
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
        """Draw the fretboard with guitar image background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.fillRect(0, 0, width, height, QColor(240, 240, 240))
        
        # Draw title
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        painter.drawText(10, 25, f"Guitar Fretboard{' - ' + self.chord_name if self.chord_name else ''}")
        
        # Draw guitar image if available
        if self.has_image and not self.guitar_image.isNull():
            try:
                # Scale image to fit window (minimal margins - double the size)
                max_width = width - 20
                max_height = height - 60
                
                # Scale maintaining aspect ratio
                scaled_image = self.guitar_image.scaledToWidth(max_width, Qt.SmoothTransformation)
                
                # If scaled image is too tall, scale by height instead
                if scaled_image.height() > max_height:
                    scaled_image = self.guitar_image.scaledToHeight(max_height, Qt.SmoothTransformation)
                
                img_width = scaled_image.width()
                img_height = scaled_image.height()
                
                # Center the image horizontally, position below title
                img_x = (width - img_width) // 2
                img_y = (height - img_height) // 2 
                
                # Draw the image
                painter.drawPixmap(img_x, img_y, scaled_image)
                
                # Use JSON positions if available
                if self.config and self.vertical_positions and self.horizontal_positions:
                    # Scale JSON positions to match the scaled image
                    # JSON positions are based on original image, scale them proportionally
                    scale_x = img_width / self.guitar_image.width() if self.guitar_image.width() > 0 else 1
                    scale_y = img_height / self.guitar_image.height() if self.guitar_image.height() > 0 else 1
                    
                    # Draw chord dots (practice target) - light blue with transparency
                    if self.chord_frets:
                        painter.setBrush(QBrush(QColor(100, 150, 255, 180)))
                        painter.setPen(QPen(QColor(50, 100, 200), 2))
                        
                        # chord_frets is {0: [fret0, fret1, fret2, fret3, fret4, fret5]}
                        for root_pos, frets_array in self.chord_frets.items():
                            try:
                                # Iterate through each string (0-5) and get its fret position
                                for string_idx, fret in enumerate(frets_array):
                                    if fret > 0 and string_idx < len(self.horizontal_positions) and fret < len(self.vertical_positions):
                                        # Get position from JSON
                                        # vertical_positions[fret] gives Y, horizontal_positions[string_idx] gives X
                                        y = img_y + self.vertical_positions[5 - string_idx] * scale_y
                                        x = img_x + (self.horizontal_positions[fret - 1] - 5) * scale_x
                                        dot_size = 10 # Fixed size for chord dots
                                        painter.drawEllipse(int(x - dot_size), int(y - dot_size), dot_size * 2, dot_size * 2)
                            except (IndexError, TypeError):
                                pass
                    
                    # Draw pressed notes (active frets) - bright red
                    painter.setBrush(QBrush(QColor(255, 0, 0, 200)))
                    painter.setPen(QPen(QColor(200, 0, 0), 3))
                    
                    for note in self.pressed_notes:
                        try:
                            result = self.get_fret_for_note(note)
                            if result:
                                string_idx, fret = result
                                if string_idx < len(self.horizontal_positions) and fret < len(self.vertical_positions):
                                    # vertical_positions[fret] gives Y, horizontal_positions[string_idx] gives X
                                    y = img_y + self.horizontal_positions[string_idx] * scale_y
                                    y = img_y + self.vertical_positions[fret] * scale_y
                                    x = img_x + self.horizontal_positions[string_idx] * scale_x
                                    dot_size = int(img_width * 0.03)
                                    painter.drawEllipse(int(x - dot_size), int(y - dot_size), dot_size * 2, dot_size * 2)
                        except (IndexError, TypeError):
                            pass
                else:
                    print("No JSON positions available for drawing dots" )
                    # Fallback if no JSON config
                    painter.drawText(width // 2 - 200, height // 2, "JSON configuration not loaded")
                        
            except Exception as e:
                print(f"Error drawing guitar image: {e}")
        else:
            # Fallback if no image - draw simple fretboard
            painter.drawText(width // 2 - 100, height // 2, "No guitar image found")
    
    def _midi_to_note(self, midi_note):
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = notes[midi_note % 12]
        octave = (midi_note // 12) - 1
        return f"{note}{octave}"

if __name__ == '__main__':
    """Test the FretboardWidget by displaying a C note"""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication([])
    
    widget = FretboardWidget()
    widget.setWindowTitle("Fretboard Widget Test - C Note")
    
    # Set E Major chord as the practice target
    widget.set_chord('E Major')
    
    # Simulate pressing a C note (MIDI note 48 = C3)
    # C note is on multiple strings at different frets
    widget.add_pressed_note(48)  # C3
    
    widget.show()
    
    # Exit when window is closed
    app.exec()