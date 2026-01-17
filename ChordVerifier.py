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
        pass
    
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
            allow_muted_strings: If True, muted strings (fret 0) can be absent
            
        Returns:
            True if chord matches, False otherwise
        """
        if target_frets:
            return False
        
        missed_frets = False
        missed_strings = False
        # Check each string
        for string_idx in range(6):
            pressed_fret = self.guitar_state.get_fret_pressed(string_idx)
            string_struck = guitar_state.is_string_struck(string_idx)
            
            # Muted string (fret 0) - should not be struck
            if target_frets[string_idx] != pressed_fret:
                return False
            if target_strings[string_idx] != string_struck:     
                return False
        
        return True
    
    def get_accuracy(self) -> float:
        """
        Calculate accuracy as percentage (0.0 to 1.0)
        
        Returns:
            Percentage of correct strings (0.0 to 1.0)
        """
        if not self.target_frets:
            return 0.0
        
        correct_count = 0
        
        for string_idx in range(6):
            target_fret = self.target_frets[string_idx]
            pressed_frets = self.guitar_state.get_pressed_frets_on_string(string_idx)
            struck = self.guitar_state.is_string_struck(string_idx)
            
            if target_fret == 0:
                if not struck:
                    correct_count += 1
            elif target_fret == -1:
                if struck and len(pressed_frets) == 0:
                    correct_count += 1
            else:
                if struck and target_fret in pressed_frets:
                    correct_count += 1
        
        return correct_count / 6
    
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
            target_fret = self.target_frets[string_idx]
            pressed_frets = self.guitar_state.get_pressed_frets_on_string(string_idx)
            struck = self.guitar_state.is_string_struck(string_idx)
            
            if target_fret == 0:
                if struck:
                    errors[string_idx] = f"String {string_idx} should be muted"
            elif target_fret == -1:
                if not struck:
                    errors[string_idx] = f"String {string_idx} should be open (struck)"
                elif len(pressed_frets) > 0:
                    errors[string_idx] = f"String {string_idx} should be open but frets pressed: {pressed_frets}"
            else:
                if not struck:
                    errors[string_idx] = f"String {string_idx} should be struck"
                elif target_fret not in pressed_frets:
                    errors[string_idx] = f"String {string_idx} should be on fret {target_fret}, got {pressed_frets}"
        
        return errors