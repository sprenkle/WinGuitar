"""
Chord Queue
Manages a queue of target chords
"""

from typing import List, Optional
from target_chord import TargetChord


class ChordQueue:
    """Queue for managing a sequence of target chords"""
    
    def __init__(self):
        """Initialize an empty chord queue"""
        self._queue: List[TargetChord] = []
    
    def add(self, chord: TargetChord) -> None:
        """
        Add a chord to the end of the queue
        
        Args:
            chord: TargetChord to add
        """
        self._queue.append(chord)
    
    def pop(self) -> Optional[TargetChord]:
        """
        Remove and return the first chord in the queue
        
        Returns:
            TargetChord if queue is not empty, None otherwise
        """
        if self._queue:
            return self._queue.pop(0)
        return None
    
    def peek(self) -> Optional[TargetChord]:
        """
        Return the first chord without removing it
        
        Returns:
            TargetChord if queue is not empty, None otherwise
        """
        if self._queue:
            return self._queue[0]
        return None
    
    def is_empty(self) -> bool:
        """
        Check if the queue is empty
        
        Returns:
            True if queue is empty, False otherwise
        """
        return len(self._queue) == 0
    
    def size(self) -> int:
        """
        Get the number of chords in the queue
        
        Returns:
            Number of chords
        """
        return len(self._queue)
    
    def clear(self) -> None:
        """Remove all chords from the queue"""
        self._queue.clear()
    
    def get_all(self) -> List[TargetChord]:
        """
        Get a copy of all chords in the queue
        
        Returns:
            List of all TargetChords in queue
        """
        return self._queue.copy()
    
    def __repr__(self):
        return f"ChordQueue(size={self.size()}, chords={self._queue})"
