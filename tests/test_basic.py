#!/usr/bin/env python3
"""
Basic test script to verify Acoustix functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from audio_processor import AudioProcessor
from note_recognizer import NoteRecognizer
from scoring_system import ScoringSystem

def test_audio_processor():
    """Test basic audio processor functionality"""
    print("Testing AudioProcessor...")
    processor = AudioProcessor()
    
    # Test with synthetic audio data
    import numpy as np
    sample_rate = 44100
    duration = 0.1  # 100ms
    frequency = 440.0  # A4
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_chunk = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    # Test pitch detection
    detected_freq, confidence = processor.detect_pitch(audio_chunk)
    print(f"  Detected frequency: {detected_freq:.2f} Hz (expected: {frequency} Hz)")
    print(f"  Confidence: {confidence:.2f}")
    
    # Test note conversion
    note, cents = processor.frequency_to_note(detected_freq)
    print(f"  Detected note: {note} ({cents:+.1f} cents)")
    
    return True

def test_note_recognizer():
    """Test note recognizer functionality"""
    print("\nTesting NoteRecognizer...")
    recognizer = NoteRecognizer()
    
    # Test guitar note identification
    test_freq = 440.0  # A4
    guitar_note = recognizer.identify_guitar_note(test_freq)
    print(f"  Guitar note at {test_freq}Hz: {guitar_note}")
    
    # Test piano note identification
    piano_note = recognizer.identify_piano_note(test_freq)
    print(f"  Piano note at {test_freq}Hz: {piano_note}")
    
    return True

def test_scoring_system():
    """Test scoring system functionality"""
    print("\nTesting ScoringSystem...")
    scorer = ScoringSystem()
    
    # Add some expected notes
    scorer.add_expected_note("A4", 0.0)
    scorer.add_expected_note("B4", 0.5)
    scorer.add_expected_note("C5", 1.0)
    
    # Evaluate a note
    result = scorer.evaluate_note("A4", 0.02, 440.0)
    print(f"  Evaluation result: {result}")
    
    # Get statistics
    stats = scorer.get_statistics()
    print(f"  Statistics: {stats}")
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("Acoustix Basic Functionality Tests")
    print("=" * 50)
    
    try:
        # Run tests
        test_audio_processor()
        test_note_recognizer()
        test_scoring_system()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("=" * 50)
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())