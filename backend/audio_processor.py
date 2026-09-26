import numpy as np
import librosa
import pyaudio
import soundfile as sf
from scipy import signal
import threading
import queue
import time


class AudioProcessor:
    def __init__(self, sample_rate=44100, chunk_size=2048):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self.p = None
        
    def start_recording(self):
        """Start recording audio from microphone"""
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        self.is_recording = True
        self.stream.start_stream()
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio callback status: {status}")
        
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        self.audio_queue.put(audio_data)
        return (None, pyaudio.paContinue)
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
    
    def get_audio_chunk(self, timeout=0.1):
        """Get audio chunk from queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def process_audio_file(self, file_path):
        """Process an audio file for pitch detection"""
        audio, sr = librosa.load(file_path, sr=self.sample_rate)
        return audio
    
    def detect_pitch(self, audio_chunk):
        """Detect pitch using autocorrelation"""
        if len(audio_chunk) < 2:
            return None, None
        
        # Autocorrelation
        autocorr = np.correlate(audio_chunk, audio_chunk, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find the first peak after the first dip
        d = np.diff(autocorr)
        start = np.where(d > 0)[0][0] if len(np.where(d > 0)[0]) > 0 else 0
        
        peak = np.argmax(autocorr[start:]) + start
        if peak == 0:
            return None, None
        
        # Calculate frequency
        freq = self.sample_rate / peak
        
        # Calculate confidence based on autocorrelation peak strength
        confidence = autocorr[peak] / autocorr[0] if autocorr[0] > 0 else 0
        
        return freq, confidence
    
    def frequency_to_note(self, frequency):
        """Convert frequency to musical note"""
        if frequency is None or frequency <= 0:
            return None, 0
        
        # A4 = 440 Hz, note number 69 in MIDI
        note_number = 12 * np.log2(frequency / 440.0) + 69
        note_number = int(round(note_number))
        
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        
        cents = 1200 * np.log2(frequency / 440.0) - (note_number - 69) * 100
        
        return f"{note_name}{octave}", cents
    
    def detect_chord(self, audio_chunk):
        """Detect chord from audio (simplified)"""
        # Perform FFT
        fft = np.fft.fft(audio_chunk)
        freqs = np.fft.fftfreq(len(audio_chunk), 1/self.sample_rate)
        magnitude = np.abs(fft)
        
        # Find prominent frequencies
        peak_indices = signal.find_peaks(magnitude[:len(magnitude)//2], height=np.max(magnitude)*0.1)[0]
        prominent_freqs = freqs[peak_indices]
        prominent_freqs = prominent_freqs[prominent_freqs > 0]
        
        # Convert to notes
        notes = []
        for freq in prominent_freqs:
            note, _ = self.frequency_to_note(freq)
            if note:
                notes.append(note)
        
        return notes
    
    def analyze_timing(self, audio_chunk, target_bpm=120):
        """Analyze timing against expected BPM"""
        # Simplified timing analysis
        # In a full implementation, this would compare note onset times to expected grid
        return {
            'detected_onset': time.time(),
            'target_bpm': target_bpm,
            'timing_score': 0.0  # Placeholder
        }