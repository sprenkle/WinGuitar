"""
Target Chord
Represents a target chord with frets, name, and strings to be struck
"""

from typing import List


class TargetChord:
    """Represents a target chord with frets, name, and strings to be struck"""
    
    def __init__(self, name: str, frets: List[int], strings_to_strike: List[int]):
        """
        Initialize a TargetChord
        
        Args:
            name: The name of the chord (e.g., 'E Major')
            frets: List of fret positions for each string (e.g., [0, 2, 2, 1, 0, 0])
            strings_to_strike: List of string indices that should be struck (0-5)
        """
        self.name = name
        self.frets = frets
        self.strings_to_strike = strings_to_strike
    
    def __repr__(self):
        return f"TargetChord(name='{self.name}', frets={self.frets}, strings_to_strike={self.strings_to_strike})"
