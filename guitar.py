"""
Guitar State Management
Tracks the current state of the guitar including pressed frets, struck strings, and note information
"""

from dataclasses import dataclass, field
from typing import Dict, Set, List
from enum import Enum


class StringName(Enum):
    """Standard guitar string names"""
    E_LOW = 0
    A = 1
    D = 2
    G = 3
    B = 4
    E_HIGH = 5


@dataclass
class FretPress:
    """Represents a fret being pressed on a string"""
    string: int  # 0-5 (low E to high E)
    fret: int
    midi_note: int
    
    def __hash__(self):
        return hash((self.string, self.fret, self.midi_note))


class GuitarState:
    """Manages the current state of the guitar"""
    
    def __init__(self, num_strings: int = 6):
        self.pressed_frets = [0] * num_strings   # string -> set of frets
        self.strings_struck = [0] * num_strings        
    
    def press_fret(self, string: int, fret: int) -> None:
        """Record a fret being pressed"""
        if 0 <= string < 6 and fret >= 0:
            self.pressed_frets[string] = fret
    
    def release_fret(self, string: int, fret: int) -> None:
        """Record a fret being released"""
        if 0 <= string < 6 and fret >= 0:
            self.pressed_frets[string] = 0
    
    def strike_string(self, string: int, fret: int) -> None:
        """Record a string being struck"""
        if 0 <= string < 6:
            self.strings_struck[string] = fret
    
    def release_string(self, string: int) -> None:
        """Record a string being released after being struck"""
        # if 0 <= string < 6:
        #     self.strings_struck[string] = 0
        pass

    
    def clear_all(self) -> None:
        """Clear all pressed frets and struck strings"""
        self.pressed_frets = [0] * 6
        self.strings_struck = [None] * 6
        self.struck_strings.clear()
    
    
    def is_string_struck(self, string: int) -> bool:
        """Check if a string is currently struck"""
        return self.strings_struck[string] > 0
    
    def get_fret_pressed(self, string: int) -> int:
        """Check if a fret is currently pressed on a string"""
        return self.pressed_frets[string]
    
    def get_summary(self) -> Dict:
        """Get a summary of the current guitar state"""
        return {
            'pressed_frets': {str(s): list(f) for s, f in self.pressed_frets.items()},
            'pressed_notes': sorted(list(self.pressed_notes)),
            'struck_strings': sorted(list(self.struck_strings)),
            'active_chord': self.active_chord
        }