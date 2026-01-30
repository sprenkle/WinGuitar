
# Guitar Chord Shapes
# Format: chord_name -> [fret for string 0, fret for string 1, ..., fret for string 5]
# fret = -1 means muted/not played, 0 means open string
# Note: String indexing in the app is reversed from standard guitar convention
# String 0 = low E, String 5 = high E (due to MIDI handler reversal)
# So the arrays below are indexed from low E to high E
CHORD_SHAPES = {
    "A": [0, 0, 2, 2, 2, 0],
    "A7": [0, 0, 2, 0, 2, 0],
    "Am": [0, 0, 2, 2, 1, 0],
    "Am7": [0, 0, 2, 0, 1, 0],
    "B": [0, 0, 3, 3, 3, 1],
    "B7": [0, 2, 1, 2, 0, 2],
    "Bm": [2, 2, 4, 4, 3, 2],
    "C": [0, 3, 2, 0, 1, 0],
    "C7": [0, 3, 2, 3, 1, 0],
    "C Major": [0, 1, 0, 2, 3, -1],
    "D": [2, 2, 2, 0, -1, -1],
    "D5": [0, 0, 0, 2, 3, 2],
    "D6/9": [2, 2, 0, 0, 0, 0],
    "D7": [2, 2, 0, 2, 1, 2],
    "D7/F#": [2, 0, 0, 2, 1, 2],
    "Dm": [1, 3, 2, 0, -1, -1],
    "Dsus2": [0, 0, 0, 2, 3, 2],
    "E": [0, 2, 2, 1, 0, 0],
    "E7": [0, 2, 2, 1, 3, 0],
    "Em": [0, 2, 2, 0, 0, 0],
    "F": [1, 3, 3, 2, 1, 1],
    "F7": [1, 3, 1, 2, 1, 1],
    "Fm": [1, 3, 3, 1, 1, 1],
    "G": [3, 0, 0, 0, 2, 3],
    "G7": [3, 2, 0, 0, 0, 1],
    "G Major": [3, 0, 0, 0, 2, 3],
    "Gm": [3, 5, 5, 3, 3, 3],
    "G/B": [2, 2, 0, 0, 0, 3],
    "Ab": [0, 2, 2, 2, 0, -1],
    "Db": [2, 3, 2, 0, -1, -1],
    "Dbsus4": [3, 3, 2, 0, -1, -1],
    "Db/F": [-1, 3, 2, 0, 0, 2],
    "Eb": [0, 0, 1, 2, 2, 0]
}

# Standard tuning: String 0 (high E) = MIDI 64, String 5 (low E) = MIDI 40
# Reversed so index 0 is the thinnest/highest string (more intuitive)
OPEN_STRING_NOTES = [64, 59, 55, 50, 45, 40]  # Strings 0-5 (high to low)

# Generate CHORD_MIDI_NOTES_FULL from CHORD_SHAPES
CHORD_MIDI_NOTES_FULL = {}
for chord_name, frets in CHORD_SHAPES.items():
    midi_notes = []
    for string_idx, fret in enumerate(frets):
        if fret == -1:
            # Muted string
            midi_notes.append(None)
        elif fret == 0:
            # Open string
            midi_notes.append(OPEN_STRING_NOTES[string_idx])
        else:
            # Fretted string
            midi_notes.append(OPEN_STRING_NOTES[string_idx] + fret)
    CHORD_MIDI_NOTES_FULL[chord_name] = midi_notes

# Menu selection notes (22nd fret)
SELECTION_NOTES = [86, 81, 77, 72, 67, 62]

# BPM options for metronome
BPM_OPTIONS = [60, 80, 100, 120, 140, 160]


# Display colors (will be computed at runtime)
class Colors:
    BLACK = None
    WHITE = None
    GREEN = None
    RED = None
    BLUE = None
    YELLOW = None
    ORANGE = None
    
    @staticmethod
    def initialize(tft):
        """Initialize colors with the TFT driver"""
        Colors.BLACK = tft.color565(0, 0, 0)
        Colors.WHITE = tft.color565(255, 255, 255)
        Colors.GREEN = tft.color565(0, 255, 0)
        Colors.RED = tft.color565(255, 0, 0)
        Colors.BLUE = tft.color565(0, 0, 255)
        Colors.YELLOW = tft.color565(255, 255, 0)
        Colors.ORANGE = tft.color565(255, 165, 0)
        Colors.GREEN = tft.color565(0, 255, 0)
        Colors.RED = tft.color565(255, 0, 0)
        Colors.BLUE = tft.color565(0, 0, 255)
        Colors.YELLOW = tft.color565(255, 255, 0)
        Colors.ORANGE = tft.color565(255, 165, 0)
