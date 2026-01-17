"""
Practice Library
Loads and manages chord collections from custom_chords.json and guitar configuration
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from target_chord import TargetChord


class PracticeLibrary:
    """Manages chord collections loaded from JSON configuration files"""
    
    def __init__(self, custom_chords_path: str = "custom_chords.json", 
                 guitar_config_path: str = "fenderstrat.json"):
        """
        Initialize the Practice Library
        
        Args:
            custom_chords_path: Path to custom_chords.json file
            guitar_config_path: Path to guitar configuration file with chord shapes
        """
        self.custom_chords_path = Path(custom_chords_path)
        self.guitar_config_path = Path(guitar_config_path)
        self.chord_shapes: Dict[str, List[int]] = {}
        self.collections: Dict[str, List[TargetChord]] = {}
        
        self._load_chord_shapes()
        self._load_collections()
    
    def _load_chord_shapes(self) -> None:
        """Load chord shapes from guitar configuration file"""
        try:
            with open(self.guitar_config_path, 'r') as f:
                config = json.load(f)
                self.chord_shapes = config.get("chord_shapes", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading guitar config: {e}")
            self.chord_shapes = {}
    
    def _load_collections(self) -> None:
        """Load chord collections from custom_chords.json"""
        try:
            with open(self.custom_chords_path, 'r') as f:
                data = json.load(f)
                
                for collection_name, chord_names in data:
                    target_chords = []
                    for chord_name in chord_names:
                        if chord_name in self.chord_shapes:
                            frets = self.chord_shapes[chord_name]
                            # Determine which strings should be struck (not -1)
                            strings_to_strike = [i for i, fret in enumerate(frets) if fret != -1]
                            target_chord = TargetChord(chord_name, frets, strings_to_strike)
                            target_chords.append(target_chord)
                    
                    if target_chords:
                        self.collections[collection_name] = target_chords
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading custom chords: {e}")
            self.collections = {}
    
    def get_collection(self, collection_name: str) -> Optional[List[TargetChord]]:
        """
        Get a specific chord collection by name
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            List of TargetChords or None if collection not found
        """
        return self.collections.get(collection_name)
    
    def get_all_collections(self) -> Dict[str, List[TargetChord]]:
        """
        Get all chord collections
        
        Returns:
            Dictionary of collection name to list of TargetChords
        """
        return self.collections.copy()
    
    def get_collection_names(self) -> List[str]:
        """
        Get all available collection names
        
        Returns:
            List of collection names
        """
        return list(self.collections.keys())
    
    def get_chord(self, chord_name: str) -> Optional[TargetChord]:
        """
        Get a specific chord by name
        
        Args:
            chord_name: Name of the chord
            
        Returns:
            TargetChord if found, None otherwise
        """
        for chords in self.collections.values():
            for chord in chords:
                if chord.name == chord_name:
                    return chord
        return None
    
    def collection_count(self) -> int:
        """
        Get the total number of collections
        
        Returns:
            Number of collections
        """
        return len(self.collections)
    
    def total_chords(self) -> int:
        """
        Get the total number of unique chords across all collections
        
        Returns:
            Total chord count
        """
        total = 0
        seen = set()
        for chords in self.collections.values():
            for chord in chords:
                if chord.name not in seen:
                    total += 1
                    seen.add(chord.name)
        return total
    
    def __repr__(self):
        return f"PracticeLibrary(collections={self.collection_count()}, total_chords={self.total_chords()})"
