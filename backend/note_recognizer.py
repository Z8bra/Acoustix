import numpy as np
from typing import List, Tuple, Dict


class NoteRecognizer:
    def __init__(self):
        # Guitar standard tuning frequencies
        self.guitar_strings = {
            'E2': 82.41,
            'A2': 110.00,
            'D3': 146.83,
            'G3': 196.00,
            'B3': 246.94,
            'E4': 329.63
        }
        
        # Piano note frequencies (A0 to C8)
        self.piano_notes = self._generate_piano_frequencies()
        
        # Guitar fretboard positions
        self.guitar_fretboard = self._generate_guitar_fretboard()
        
    def _generate_piano_frequencies(self):
        """Generate frequency map for all piano notes"""
        notes = {}
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # A4 = 440 Hz, MIDI note 69
        for octave in range(0, 9):
            for i, note_name in enumerate(note_names):
                midi_note = (octave + 1) * 12 + i
                if midi_note < 21 or midi_note > 108:  # A0 to C8 range
                    continue
                    
                frequency = 440.0 * (2 ** ((midi_note - 69) / 12))
                notes[f"{note_name}{octave}"] = frequency
                
        return notes
    
    def _generate_guitar_fretboard(self):
        """Generate guitar fretboard note positions"""
        fretboard = {}
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        for string, open_freq in self.guitar_strings.items():
            fretboard[string] = {}
            for fret in range(0, 25):  # 24 frets
                freq = open_freq * (2 ** (fret / 12))
                midi_note = 12 * np.log2(freq / 440.0) + 69
                note_num = int(round(midi_note))
                note_name = note_names[note_num % 12]
                octave = (note_num // 12) - 1
                fretboard[string][fret] = {
                    'note': f"{note_name}{octave}",
                    'frequency': freq
                }
                
        return fretboard
    
    def identify_guitar_note(self, frequency: float, tolerance: float = 0.5) -> Dict:
        """Identify guitar note from frequency"""
        if frequency is None or frequency <= 0:
            return None
        
        best_match = None
        min_diff = float('inf')
        
        for string, frets in self.guitar_fretboard.items():
            for fret, info in frets.items():
                diff = abs(frequency - info['frequency'])
                if diff < min_diff:
                    min_diff = diff
                    best_match = {
                        'note': info['note'],
                        'string': string,
                        'fret': fret,
                        'frequency': info['frequency'],
                        'difference': diff
                    }
        
        # Check if within tolerance (in cents)
        if best_match and min_diff > 0:
            cents = 1200 * np.log2(frequency / best_match['frequency'])
            if abs(cents) > tolerance * 100:
                return None
        
        return best_match
    
    def identify_piano_note(self, frequency: float, tolerance: float = 0.5) -> Dict:
        """Identify piano note from frequency"""
        if frequency is None or frequency <= 0:
            return None
        
        best_match = None
        min_diff = float('inf')
        
        for note, freq in self.piano_notes.items():
            diff = abs(frequency - freq)
            if diff < min_diff:
                min_diff = diff
                best_match = {
                    'note': note,
                    'frequency': freq,
                    'difference': diff
                }
        
        # Check if within tolerance
        if best_match and min_diff > 0:
            cents = 1200 * np.log2(frequency / best_match['frequency'])
            if abs(cents) > tolerance * 100:
                return None
        
        return best_match
    
    def detect_instrument_type(self, frequency_spectrum: np.ndarray) -> str:
        """Detect if the audio is more likely guitar or piano based on spectral characteristics"""
        # Simplified detection based on spectral characteristics
        # Guitar: more harmonic content, brighter
        # Piano: clearer fundamental, more even harmonics
        
        spectral_centroid = np.sum(frequency_spectrum * np.arange(len(frequency_spectrum))) / np.sum(frequency_spectrum)
        spectral_rolloff = self._calculate_spectral_rolloff(frequency_spectrum)
        
        # These thresholds would need calibration with real data
        if spectral_centroid > len(frequency_spectrum) * 0.3:
            return "guitar"
        else:
            return "piano"
    
    def _calculate_spectral_rolloff(self, spectrum: np.ndarray, rolloff_percent: float = 0.85) -> float:
        """Calculate spectral rolloff point"""
        total_energy = np.sum(spectrum)
        cumulative_energy = np.cumsum(spectrum)
        rolloff_threshold = rolloff_percent * total_energy
        rolloff_idx = np.where(cumulative_energy >= rolloff_threshold)[0]
        
        if len(rolloff_idx) > 0:
            return rolloff_idx[0] / len(spectrum)
        return 1.0
    
    def get_note_position(self, note: str, instrument: str) -> Dict:
        """Get playing position for a note on the instrument"""
        if instrument == "guitar":
            positions = []
            for string, frets in self.guitar_fretboard.items():
                for fret, info in frets.items():
                    if info['note'] == note:
                        positions.append({
                            'string': string,
                            'fret': fret,
                            'frequency': info['frequency']
                        })
            return {'positions': positions} if positions else None
        elif instrument == "piano":
            if note in self.piano_notes:
                return {
                    'note': note,
                    'frequency': self.piano_notes[note]
                }
        return None