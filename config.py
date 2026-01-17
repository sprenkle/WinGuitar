
# Note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Standard tuning: String 1 (high E) = MIDI 64, String 2 (B) = 59, String 3 (G) = 55, 
# String 4 (D) = 50, String 5 (A) = 45, String 6 (low E) = 40
OPEN_STRING_NOTES = [64, 59, 55, 50, 45, 40]  # Strings 1-6

# # MIDI notes that make up each chord
# CHORD_MIDI_NOTES = {
#     'A':   [64, 61, 57, 52, 45, 40],
#     'Am':  [64, 60, 57, 52, 45, 40],
#     'A7':  [64, 61, 55, 52, 45, 40],
#     'B':   [66, 63, 59, 54, 45, 40],
#     'Bm':  [66, 62, 59, 54, 45, 40],
#     'B7':  [66, 59, 57, 51, 47, 40],
#     'C':   [64, 60, 55, 52, 48, 40],
#     'Cm':  [64, 60, 55, 52, 48, 40],
#     'C7':  [64, 60, 58, 52, 48, 40],
#     'D':   [66, 62, 57, 50, 45, 40],
#     'Dm':  [65, 62, 57, 50, 45, 40],
#     'D7':  [66, 60, 57, 50, 45, 40],
#     'E':   [64, 59, 56, 52, 47, 40],
#     'Em':  [64, 59, 55, 52, 47, 40],
#     'E7':  [64, 59, 56, 50, 47, 40],
#     'F':   [65, 60, 57, 53, 45, 40],
#     'Fm':  [65, 60, 56, 53, 45, 40],
#     'F7':  [65, 60, 57, 51, 45, 40],
#     'G':   [67, 59, 55, 50, 47, 43],
#     'Gm':  [67, 62, 58, 50, 45, 40],
#     'G7':  [65, 59, 55, 50, 47, 43],
#     'D6/9': [64, 59, 55, 50, 47, 42],
#     'G/B':  [64, 59, 55, 50, 47, 42],
#     'Am7':  [64, 59, 55, 50, 47, 42],
#     'D7/F#': [64, 59, 55, 50, 47, 42],
#     'D5':    [66, 62, 57, 50, 45, 40],
#     'Dsus2': [66, 64, 57, 50, 45, 40],
# }

CHORD_MIDI_NOTES_FULL = {
    'A':   [64, 61, 57, 52, 45, None],
    'Am':  [64, 60, 57, 52, 45, None],
    'A7':  [64, 61, 55, 52, 45, None],
    'B':   [66, 63, 59, 54, None, None],
    'Bm':  [66, 62, 59, 54, None, None],
    'B7':  [66, 59, 57, 51, 47, None],
    'C':   [64, 60, 55, 52, 48, None],
    'Cm':  [64, 60, 55, 52, 48, None],
    'C7':  [64, 60, 58, 52, 48, None],
    'D':   [66, 62, 57, 50, None, None],
    'Dm':  [65, 62, 57, 50, None, None],
    'D7':  [66, 60, 57, 50, None, None],
    'E':   [64, 59, 56, 52, 47, None],
    'Em':  [64, 59, 55, 52, 47, None],
    'E7':  [64, 59, 56, 50, 47, None],
    'F':   [65, 60, 57, 53, 48, None],
    'Fm':  [65, 60, 56, 53, 48, None],
    'F7':  [65, 60, 57, 51, 48, None],
    'G':   [67, 59, 55, 50, 47, 43],
    'Gm':  [67, 62, 58, 50, None, None],
    'G7':  [65, 59, 55, 50, 47, 43],
    'D6/9': [64, 59, 55, 52, 47, 40],
    'D5':   [66, 62, 57, 50, None, None],
    'Dsus2': [66, 64, 57, 50, None, None],
}

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
