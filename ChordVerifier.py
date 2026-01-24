"""
Chord Verification
Verifies if struck strings match a target chord
"""

from typing import Dict, List, Set
from guitar import GuitarState
from target_chord import TargetChord


class ChordVerifier:
    """Verifies if struck strings match a target chord"""
    
    # Standard tuning MIDI notes (lowest to highest string)
    STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # E2, A2, D3, G3, B3, E4
    
    
    def __init__(self):
        self.target_frets = None
        self.target_strings = None
        self.guitar_state = None
    
    def _get_target_frets(self, chord_name: str) -> List[int]:
        """Get the target fret positions for a chord"""
        if chord_name not in self.CHORD_PRESETS:
            return []
        
        chord_data = self.CHORD_PRESETS[chord_name]
        # Extract frets from {0: [fret0, fret1, ...]}
        for root_pos, frets_array in chord_data.items():
            return frets_array
        return []
    
    def verify(self, target_frets, target_strings, guitar_state) -> bool:
        """
        Verify if struck strings match the target chord
        
        Args:
            target_frets: List of fret positions for each string
            target_strings: List of string indices that should be struck
            guitar_state: Current guitar state
            
        Returns:
            True if chord matches, False otherwise
        """
        # Store for use by get_accuracy() and get_errors()
        self.target_frets = target_frets
        self.target_strings = target_strings
        self.guitar_state = guitar_state
        
        if not target_frets:
            return False
        
        # Check each string
        strings_matched = True
        frets_matched = True

        for string_idx in range(6):
            pressed_fret = guitar_state.get_fret_pressed(5-string_idx)
            string_struck = guitar_state.is_string_struck(5-string_idx)

            # Muted string (fret -1) - should not be struck
            if target_frets[string_idx] == -1:
                if string_struck:
                    strings_matched = False
            # Open string (fret 0) - should be struck if in target_strings
            elif target_frets[string_idx] == 0:
                if string_idx in target_strings and not string_struck:
                    strings_matched = False
                if string_idx not in target_strings and string_struck:
                    strings_matched = False
            # Fretted string - must match target fret
            else:
                if pressed_fret != target_frets[string_idx]:
                    print(f"String {string_idx} fret mismatch: expected {target_frets[string_idx]}, got {pressed_fret}")
                    frets_matched = False
                if string_idx in target_strings and not string_struck:
                    strings_matched = False
        
        # print(f"Chord Verification - Frets Matched: {frets_matched}, Strings Matched: {strings_matched}")   
        return (frets_matched, strings_matched)
    
   
    
    def get_errors(self) -> Dict[int, str]:
        """
        Get detailed errors for each string
        
        Returns:
            Dictionary mapping string index to error message
        """
        errors = {}
        
        if not self.target_frets:
            return errors
        
        for string_idx in range(6):
            t_index = string_idx
            target_fret = self.target_frets[5 - t_index]
            pressed_fret = self.guitar_state.get_fret_pressed(t_index)
            struck = self.guitar_state.is_string_struck(5-t_index)
            if target_fret == 0:
                if not struck:
                    errors[t_index] = f"String {t_index} should be struck open"
            elif target_fret == -1:
                if struck:
                    errors[t_index] = f"String {t_index} should not be struck"
            else:
                if not struck:
                    errors[t_index] = f"String {t_index} should be struck"
                elif pressed_fret != target_fret:
                    errors[t_index] = f"String {t_index} should be on fret {target_fret}, got {pressed_fret}"

        return errors