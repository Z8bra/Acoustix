import time
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class ScoreType(Enum):
    PERFECT = "PERFECT"
    GREAT = "GREAT"
    GOOD = "GOOD"
    OKAY = "OKAY"
    MISS = "MISS"


@dataclass
class NoteEvent:
    note: str
    expected_time: float
    detected_time: float = None
    detected_note: str = None
    score_type: ScoreType = None
    points: int = 0
    timing_difference: float = 0
    pitch_difference: float = 0


class ScoringSystem:
    def __init__(self):
        self.total_notes = 0
        self.hit_notes = 0
        self.total_score = 0
        self.max_score = 0
        self.combo = 0
        self.max_combo = 0
        self.note_events: List[NoteEvent] = []
        
        # Scoring thresholds (in milliseconds)
        self.timing_thresholds = {
            ScoreType.PERFECT: 30,
            ScoreType.GREAT: 60,
            ScoreType.GOOD: 100,
            ScoreType.OKAY: 150
        }
        
        # Scoring thresholds (in cents for pitch)
        self.pitch_thresholds = {
            ScoreType.PERFECT: 10,
            ScoreType.GREAT: 25,
            ScoreType.GOOD: 50,
            ScoreType.OKAY: 100
        }
        
        # Point values
        self.point_values = {
            ScoreType.PERFECT: 100,
            ScoreType.GREAT: 80,
            ScoreType.GOOD: 60,
            ScoreType.OKAY: 40,
            ScoreType.MISS: 0
        }
        
        # Combo multipliers
        self.combo_multipliers = {
            0: 1.0,
            10: 1.1,
            20: 1.2,
            30: 1.3,
            50: 1.5,
            100: 2.0
        }
    
    def add_expected_note(self, note: str, expected_time: float):
        """Add a note that should be played"""
        self.total_notes += 1
        self.max_score += 100  # Assume max 100 points per note
        note_event = NoteEvent(
            note=note,
            expected_time=expected_time
        )
        self.note_events.append(note_event)
    
    def evaluate_note(self, detected_note: str, detected_time: float, detected_frequency: float = None) -> Dict:
        """Evaluate a detected note against expected notes"""
        current_time = detected_time
        
        # Find the closest expected note in time
        closest_event = None
        min_time_diff = float('inf')
        
        for event in self.note_events:
            if event.score_type is None:  # Not yet evaluated
                time_diff = abs(current_time - event.expected_time)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_event = event
        
        if closest_event is None:
            return {
                'status': 'no_expected_note',
                'message': 'No expected notes remaining'
            }
        
        # Check if it's too late (more than 500ms past expected time)
        if min_time_diff > 0.5:
            return {
                'status': 'too_late',
                'message': 'Note played too late'
            }
        
        # Evaluate the note
        closest_event.detected_time = detected_time
        closest_event.detected_note = detected_note
        closest_event.timing_difference = min_time_diff * 1000  # Convert to ms
        
        # Check if the detected note matches the expected note
        note_match = detected_note == closest_event.note
        
        # Calculate pitch difference if frequency provided
        if detected_frequency:
            # This would need frequency of expected note
            closest_event.pitch_difference = 0  # Placeholder
        
        # Determine score type
        score_type = self._calculate_score_type(
            min_time_diff * 1000,  # timing in ms
            note_match,
            closest_event.pitch_difference
        )
        
        closest_event.score_type = score_type
        
        # Calculate points with combo multiplier
        base_points = self.point_values[score_type]
        multiplier = self._get_combo_multiplier()
        closest_event.points = int(base_points * multiplier)
        
        # Update statistics
        if score_type != ScoreType.MISS:
            self.hit_notes += 1
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
        else:
            self.combo = 0
        
        self.total_score += closest_event.points
        
        return {
            'status': 'evaluated',
            'score_type': score_type.value,
            'points': closest_event.points,
            'combo': self.combo,
            'max_combo': self.max_combo,
            'timing_difference': closest_event.timing_difference,
            'note_match': note_match,
            'expected_note': closest_event.note,
            'detected_note': detected_note
        }
    
    def _calculate_score_type(self, timing_diff: float, note_match: bool, pitch_diff: float) -> ScoreType:
        """Calculate score type based on timing and pitch accuracy"""
        if not note_match:
            return ScoreType.MISS
        
        # Check timing thresholds
        for score_type, threshold in self.timing_thresholds.items():
            if timing_diff <= threshold:
                # Also check pitch thresholds
                pitch_threshold = self.pitch_thresholds[score_type]
                if abs(pitch_diff) <= pitch_threshold:
                    return score_type
        
        return ScoreType.OKAY if timing_diff <= self.timing_thresholds[ScoreType.OKAY] else ScoreType.MISS
    
    def _get_combo_multiplier(self) -> float:
        """Get current combo multiplier"""
        multiplier = 1.0
        for combo_threshold, combo_mult in sorted(self.combo_multipliers.items()):
            if self.combo >= combo_threshold:
                multiplier = combo_mult
        return multiplier
    
    def get_statistics(self) -> Dict:
        """Get current scoring statistics"""
        accuracy = (self.hit_notes / self.total_notes * 100) if self.total_notes > 0 else 0
        score_percentage = (self.total_score / self.max_score * 100) if self.max_score > 0 else 0
        
        return {
            'total_score': self.total_score,
            'max_score': self.max_score,
            'accuracy': accuracy,
            'score_percentage': score_percentage,
            'combo': self.combo,
            'max_combo': self.max_combo,
            'total_notes': self.total_notes,
            'hit_notes': self.hit_notes,
            'missed_notes': self.total_notes - self.hit_notes
        }
    
    def reset(self):
        """Reset the scoring system"""
        self.total_notes = 0
        self.hit_notes = 0
        self.total_score = 0
        self.max_score = 0
        self.combo = 0
        self.max_combo = 0
        self.note_events = []
    
    def get_score_breakdown(self) -> List[Dict]:
        """Get breakdown of scores by type"""
        breakdown = {score_type.value: 0 for score_type in ScoreType}
        
        for event in self.note_events:
            if event.score_type:
                breakdown[event.score_type.value] += 1
        
        return [
            {'score_type': score_type, 'count': count}
            for score_type, count in breakdown.items()
        ]