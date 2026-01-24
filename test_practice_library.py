"""
Test suite for PracticeLibrary
Verifies that practices load correctly from custom_chords.json
"""

import unittest
from practice_library import PracticeLibrary


class TestPracticeLibrary(unittest.TestCase):
    """Tests for the PracticeLibrary class"""
    
    def setUp(self):
        """Initialize PracticeLibrary before each test"""
        self.library = PracticeLibrary()
    
    def test_load_collections(self):
        """Test that all collections load from custom_chords.json"""
        collections = self.library.get_collection_names()
        self.assertGreater(len(collections), 0, "No collections loaded")
        print(f"✓ Loaded {len(collections)} collections")
    
    def test_expected_collections(self):
        """Test that specific expected collections are loaded"""
        expected = [
            "Open D", "All D", "Open G", "G Major", "All Chords",
            "A Major & 7", "B Major & 7", "C Major & 7", 
            "D Major & 7", "E Major & 7", "F Major & 7", "G Major & 7"
        ]
        collections = self.library.get_collection_names()
        for collection_name in expected:
            self.assertIn(collection_name, collections, 
                         f"Expected collection '{collection_name}' not found")
        print(f"✓ All {len(expected)} expected collections present")
    
    def test_collection_has_chords(self):
        """Test that each collection has at least one chord"""
        for name in self.library.get_collection_names():
            chords = self.library.get_collection(name)
            self.assertIsNotNone(chords, f"Collection '{name}' returned None")
            self.assertGreater(len(chords), 0, f"Collection '{name}' has no chords")
        print(f"✓ All collections have chords")
    
    def test_chord_shapes_loaded(self):
        """Test that chord shapes are loaded from guitar config"""
        self.assertGreater(len(self.library.chord_shapes), 0, 
                          "No chord shapes loaded from guitar config")
        print(f"✓ Loaded {len(self.library.chord_shapes)} chord shapes")
    
    def test_get_collection_by_name(self):
        """Test retrieving specific collection by name"""
        all_chords = self.library.get_collection("All Chords")
        self.assertIsNotNone(all_chords)
        self.assertEqual(len(all_chords), 24, "All Chords collection should have 24 chords")
        print(f"✓ All Chords collection retrieved: {len(all_chords)} chords")
    
    def test_collection_details(self):
        """Test details of each collection"""
        print("\n✓ Collection Details:")
        for name in sorted(self.library.get_collection_names()):
            chords = self.library.get_collection(name)
            chord_names = [chord.name for chord in chords]
            print(f"  - {name}: {len(chords)} chords - {chord_names}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
