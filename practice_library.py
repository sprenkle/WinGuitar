"""
Practice Library
Loads and manages chord collections from custom_chords.json and configuration
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from target_chord import TargetChord
from config import CHORD_SHAPES


class PracticeLibrary:
    """Manages chord collections loaded from JSON configuration files"""
    
    def __init__(self, custom_chords_path: str = None):
        """
        Initialize the Practice Library
        
        Args:
            custom_chords_path: Path to custom_chords.json file (defaults to script directory)
        """
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        
        # Use provided path or default to file in the script directory
        if custom_chords_path is None:
            custom_chords_path = script_dir / "custom_chords.json"
        else:
            custom_chords_path = Path(custom_chords_path)
        
        self.custom_chords_path = custom_chords_path
        self.chord_shapes: Dict[str, List[int]] = CHORD_SHAPES
        self.collections: Dict[str, List[TargetChord]] = {}
        
        self._load_collections()
    
    def _load_chord_shapes(self) -> None:
        """Load chord shapes from guitar configuration file"""
    
    def _load_collections(self) -> None:
        """Load chord collections from custom_chords.json"""
        try:
            with open(self.custom_chords_path, 'r') as f:
                data = json.load(f)
                print(f"[PracticeLibrary] Loaded {len(data)} collections from custom_chords.json")
                print(f"[PracticeLibrary] Using {len(self.chord_shapes)} chord shapes from config.py")
                
                for collection_name, chord_names in data:
                    target_chords = []
                    missing_chords = []
                    for chord_name in chord_names:
                        if chord_name in self.chord_shapes:
                            frets = self.chord_shapes[chord_name]
                            # Determine which strings should be struck (not -1)
                            strings_to_strike = [i for i, fret in enumerate(frets) if fret != -1]
                            target_chord = TargetChord(chord_name, frets, strings_to_strike)
                            target_chords.append(target_chord)
                        else:
                            missing_chords.append(chord_name)
                    
                    # Add collection even if some chords are missing
                    if target_chords:
                        self.collections[collection_name] = target_chords
                        if missing_chords:
                            print(f"Warning: Collection '{collection_name}' missing chord shapes for: {missing_chords}")
                    else:
                        print(f"Error: Collection '{collection_name}' has NO valid chords loaded. All requested: {chord_names}")
                
                print(f"[PracticeLibrary] Successfully loaded {len(self.collections)} collections: {list(self.collections.keys())}")
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
