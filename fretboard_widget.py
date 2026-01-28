"""Guitar fretboard display widget"""
import json
from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QPen
from PySide6.QtCore import Signal, QTimer, Qt, QSize
from guitar import GuitarState


class FretboardWidget(QFrame):
    """Custom widget to draw the guitar fretboard"""
    
    # Signal for thread-safe updates
    repaint_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(QSize(1600, 600))
        self.pressed_notes = set()  # MIDI notes currently pressed
        self.chord_name = None
        self.chord_frets = {}  # Fret positions for the selected chord
        self.strings_to_strike = []  # Indices of strings that should be struck (0-5)
        self.next_chord_frets = {}  # Fret positions for the next chord in queue
        self.next_chord_name = None  # Name of the next chord

        self.guitar_state = GuitarState()

        # Initialize config values (will be set by load_config)
        self.STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # Default
        self.NUM_FRETS = 24
        self.NUM_STRINGS = 6
        self.CHORD_PRESETS = {}

        # Initialize image and config
        self.guitar_image = QPixmap()
        self.has_image = False
        
        # Load JSON configuration (which will also load the image)
        self.config = None
        self.verticalA_positions = []
        self.verticalB_positions = []
        self.horizontal_positions = []
        self.load_config()
        
        # Feedback display
        self.feedback_text = ""  # "CORRECT" or "INCORRECT"
        self.feedback_color = "green"  # "green" or "red"
        
        # Show target display
        self.show_target = True  # Whether to display target chord frets
        
        # Show next chord display
        self.show_next_chord = True  # Whether to display next chord in queue
        
        # Show chord name display
        self.show_chord_name = True  # Whether to display the current chord name
        
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
            config_path = os.path.join(script_dir, 'aeroband.json')
            
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Load guitar parameters from config
            self.STANDARD_TUNING = self.config.get('standard_tuning', [40, 45, 50, 55, 59, 64])
            self.NUM_FRETS = self.config.get('number_of_frets', 24)
            self.NUM_STRINGS = self.config.get('number_of_strings', 6)
            
            # Build CHORD_PRESETS from chord_shapes in config
            chord_shapes = self.config.get('chord_shapes', {})
            self.CHORD_PRESETS = {name: {0: frets} for name, frets in chord_shapes.items()}
                
            # Extract fret and string positions from JSON
            image_config = self.config.get('image', {})
            self.verticalA_positions = image_config.get('verticalA_positions', [])
            self.verticalB_positions = image_config.get('verticalB_positions', [])
            self.horizontal_positions = image_config.get('horizontal_positions', [])
            
            # Load image using path from JSON
            image_path = image_config.get('image_path', 'aeroband.jpg')
            
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
            
            print(f"Loaded {len(self.CHORD_PRESETS)} chord presets from config")
            
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
        
    def set_guitar_state(self, guitar_state: GuitarState):
        """Set the current guitar state for display"""
        self.guitar_state = guitar_state
        self.update()
    
    def set_chord(self, chord_name, strings_to_strike=None):
        """Set the chord to display"""
        self.chord_name = chord_name
        self.strings_to_strike = strings_to_strike if strings_to_strike else []
        if chord_name in self.CHORD_PRESETS:
            self.chord_frets = self.CHORD_PRESETS[chord_name]
            self.guitar_state.clear_all()
        self.update()
    
    def set_feedback(self, text, color):
        """Set feedback text and color to display (CORRECT or INCORRECT)"""
        self.feedback_text = text
        self.feedback_color = color
        self.update()
    
    def set_show_target(self, show):
        """Set whether to show target chord frets and strings to strike"""
        self.show_target = show
        self.update()
    
    def set_next_chord(self, chord_name, frets):
        """Set the next chord in the practice queue to display in yellow"""
        self.next_chord_name = chord_name
        self.next_chord_frets = {0: frets} if frets else {}
        self.update()
    
    def set_show_next_chord(self, show):
        """Set whether to show the next chord in the practice queue"""
        self.show_next_chord = show
        self.update()
    
    def set_show_chord_name(self, show):
        """Set whether to show the current chord name"""
        self.show_chord_name = show
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
        
        # Draw title and chord name (centered)
        painter.setFont(QFont('Arial', 16, QFont.Bold))
        if (self.show_chord_name or self.feedback_text) and self.chord_name:
            title_text = f"Guitar Fretboard - {self.chord_name}"
        else:
            title_text = "Guitar Fretboard"
        painter.drawText(0, 10, width, 40, Qt.AlignCenter, title_text)
        
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
            
            scale_x = img_width / self.guitar_image.width() if self.guitar_image.width() > 0 else 1
            scale_y = img_height / self.guitar_image.height() if self.guitar_image.height() > 0 else 1
            
            # Draw chord dots (practice target) - light blue with transparency (only if show_target is True)
            if self.chord_frets and (self.show_target or self.feedback_text):
                painter.setBrush(QBrush(QColor(100, 150, 255, 180)))
                painter.setPen(QPen(QColor(50, 100, 200), 2))
                
                # chord_frets is {0: [fret0, fret1, fret2, fret3, fret4, fret5]}
                for root_pos, frets_array in self.chord_frets.items():
                    try:
                        # Iterate through each string (0-5) and get its fret position
                        for string_idx, fret in enumerate(frets_array):
                            if fret > 0 and string_idx < len(self.horizontal_positions) and fret < len(self.verticalA_positions) - 1:
                                # Get position from JSON
                                # vertical_positions[fret] gives Y, horizontal_positions[string_idx] gives X
                                y = img_y + self.verticalA_positions[string_idx] * scale_y
                                x = img_x + (self.horizontal_positions[fret] - 5) * scale_x
                                dot_size = 9 # Fixed size for chord dots
                                painter.drawEllipse(int(x - dot_size), int(y - dot_size), dot_size * 2, dot_size * 2)
                    except (IndexError, TypeError):
                        pass
            
            # Draw next chord dots (yellow) - shows the upcoming chord in the practice queue
            if self.next_chord_frets and self.show_next_chord:
                painter.setBrush(QBrush(QColor(255, 255, 0, 150)))  # Yellow with transparency
                painter.setPen(QPen(QColor(200, 200, 0), 2))
                
                # next_chord_frets is {0: [fret0, fret1, fret2, fret3, fret4, fret5]}
                for root_pos, frets_array in self.next_chord_frets.items():
                    try:
                        # Iterate through each string (0-5) and get its fret position
                        for string_idx, fret in enumerate(frets_array):
                            if fret > 0 and string_idx < len(self.horizontal_positions) and fret < len(self.verticalA_positions) - 1:
                                # Get position from JSON
                                y = img_y + self.verticalA_positions[string_idx] * scale_y
                                x = img_x + (self.horizontal_positions[fret] - 5) * scale_x
                                dot_size = 5  # Slightly smaller than current chord dots
                                painter.drawEllipse(int(x - dot_size), int(y - dot_size), dot_size * 2, dot_size * 2)
                    except (IndexError, TypeError):
                        pass
          


            # Draw pressed notes (active frets) - green if correct, red if wrong
            painter.setPen(QPen(QColor(200, 0, 0), 3))
            for string_idx in range(self.NUM_STRINGS):
                fret = self.guitar_state.get_fret_pressed(string_idx)
                if fret > 0:
                    y = img_y + self.verticalA_positions[string_idx] * scale_y
                    x = img_x + (self.horizontal_positions[fret] - 5)* scale_x
                    dot_size = 8
                    
                    # Check if this fret matches the target chord
                    is_correct = False
                    if self.chord_frets:
                        # Get the expected fret for this string from the chord
                        expected_fret = self.chord_frets.get(0, [])[string_idx] if 0 in self.chord_frets else -1
                        is_correct = (fret == expected_fret and expected_fret != -1)
                    
                    # Color green if correct chord fret, red if wrong
                    if is_correct:
                        painter.setBrush(QBrush(QColor(0, 255, 0, 200)))  # Green for correct
                    else:
                        painter.setBrush(QBrush(QColor(255, 0, 0, 200)))  # Red for wrong
                    
                    painter.drawEllipse(int(x - dot_size), int(y - dot_size), dot_size * 2, dot_size * 2)
                    
                    # Check if this pressed note matches any note in the next chord (only if show_next_chord is enabled)
                    if self.next_chord_frets and self.show_next_chord:
                        expected_next_fret = self.next_chord_frets.get(0, [])[string_idx] if 0 in self.next_chord_frets else -1
                        if fret == expected_next_fret and expected_next_fret > 0:
                            # Draw a smaller yellow circle to show it matches the next chord
                            painter.setBrush(QBrush(QColor(255, 255, 100, 220)))  # Bright yellow
                            painter.setPen(QPen(QColor(200, 200, 0), 1))
                            small_dot_size = 4
                            painter.drawEllipse(int(x - small_dot_size), int(y - small_dot_size), small_dot_size * 2, small_dot_size * 2)

            # Draw struck strings (active strings) - green
            painter.setBrush(QBrush(QColor(0, 200, 0, 180)))
            painter.setPen(QPen(QColor(0, 150, 0), 6))
            for string_idx in range(self.NUM_STRINGS):
                if self.guitar_state.is_string_struck(string_idx):
                    y1 = img_y + self.verticalA_positions[string_idx] * scale_y
                    y2 = img_y + self.verticalB_positions[string_idx] * scale_y
                    x0 = img_x + self.horizontal_positions[0] * scale_x 
                    x1 = img_x + self.horizontal_positions[-1] * scale_x
                    painter.drawLine(int(x0), int(y1), int(x1), int(y2))

            # Draw string strike indicators (marks on the left side of the fretboard) (shown if show_target is True or feedback is displayed)
            if self.chord_frets and (self.show_target or self.feedback_text):
                for string_idx in range(self.NUM_STRINGS):
                    y = img_y + (self.verticalA_positions[string_idx]  - 5) * scale_y 
                    x = img_x + (self.horizontal_positions[0]) * scale_x
                    
                    if self.chord_frets.get(0, [])[string_idx] == 0:
                        # Draw a checkmark for strings that should be struck
                        painter.setPen(QPen(QColor(0, 150, 0), 3))  # Green
                        painter.setFont(QFont('Arial', 14, QFont.Bold))
                        painter.drawText(int(x), int(y), 40, 20, Qt.AlignCenter, 'O')
                    elif self.chord_frets.get(0, [])[string_idx] == -1:
                        # Draw an X for strings that should NOT be struck (muted)
                        painter.setPen(QPen(QColor(200, 0, 0), 3))  # Red
                        painter.setFont(QFont('Arial', 14, QFont.Bold))
                        painter.drawText(int(x), int(y), 40, 20, Qt.AlignCenter, '✕')

            # Draw feedback (CORRECT/INCORRECT)
            if self.feedback_text:
                painter.setFont(QFont('Arial', 48, QFont.Bold))
                # Set color based on feedback
                if self.feedback_color == "green":
                    color = QColor(0, 200, 0)  # Green for CORRECT
                else:
                    color = QColor(255, 0, 0)  # Red for INCORRECT
                painter.setPen(color)
                # Draw feedback text at the top of the widget
                painter.drawText(0, 30, width, 80, Qt.AlignCenter, self.feedback_text)
                    
        except Exception as e:
            print(f"Error drawing guitar image: {e}")
        finally:
            painter.end()
    
    def _midi_to_note(self, midi_note):
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        note = notes[midi_note % 12]
        octave = (midi_note // 12) - 1
        return f"{note}{octave}"

if __name__ == '__main__':
    """Test the FretboardWidget by displaying a C note"""
    from PySide6.QtWidgets import QApplication
    import time
    
    app = QApplication([])
    
    widget = FretboardWidget()
    widget.setWindowTitle("Fretboard Widget Test - C Note")
    
    # Set E Major chord as the practice target
    widget.set_chord('E Major')
    
    guitar_state = GuitarState()
    # guitar_state.press_fret(0, 1)  # High E string open
    # guitar_state.press_fret(1, 2)  # High E string open
    # guitar_state.press_fret(3, 3)  # High E string open
    # guitar_state.press_fret(4, 4)  # High E string open
    # guitar_state.press_fret(5, 19)  # High E string open
    # guitar_state.strike_string(0, 3)    
    # guitar_state.strike_string(1, 22)    
    # guitar_state.strike_string(2, 19)    
    # guitar_state.strike_string(3, 22)    
    # guitar_state.strike_string(4, 19)    
    # guitar_state.strike_string(5, 19)    
    widget.set_guitar_state(guitar_state)

    widget.show()
    # time.sleep(5)
    # guitar_state.release_fret(0, 1)  # High E string open
    # guitar_state.release_fret(1, 2)  # High E string open
    # guitar_state.release_fret(3, 3)  # High E string open
    # guitar_state.release_fret(4, 4)  # High E string open
    # widget.show()




    # Exit when window is closed
    app.exec()