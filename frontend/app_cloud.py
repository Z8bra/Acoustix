import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import pandas as pd
import plotly.express as px
from datetime import datetime
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Acoustix - Guitar Hero for Real Instruments",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .score-display {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .perfect { background-color: #00ff00; color: black; }
    .great { background-color: #00ccff; color: black; }
    .good { background-color: #ffff00; color: black; }
    .okay { background-color: #ff9900; color: black; }
    .miss { background-color: #ff0000; color: white; }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'note_history' not in st.session_state:
    st.session_state.note_history = []

def detect_pitch(audio_chunk, sample_rate=44100):
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
    freq = sample_rate / peak
    
    # Calculate confidence based on autocorrelation peak strength
    confidence = autocorr[peak] / autocorr[0] if autocorr[0] > 0 else 0
    
    return freq, confidence

def frequency_to_note(frequency):
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

def analyze_audio_file(file_path, instrument='guitar'):
    """Analyze an audio file for pitch detection"""
    try:
        # Load audio file
        audio, sr = librosa.load(file_path, sr=44100)
        
        # Process in chunks
        chunk_size = 2048
        results = []
        
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            if len(chunk) == chunk_size:
                frequency, confidence = detect_pitch(chunk)
                
                if frequency and confidence > 0.3:
                    note, cents = frequency_to_note(frequency)
                    if note:
                        results.append({
                            'time': i / sr,
                            'note': note,
                            'frequency': frequency,
                            'confidence': confidence,
                            'cents': cents
                        })
        
        return {
            'success': True,
            'duration': len(audio) / sr,
            'detected_notes': results,
            'total_notes': len(results)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Main UI
st.markdown('<h1 class="main-header">🎸 Acoustix Cloud 🎹</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem;">Guitar Hero for Real Instruments - Cloud Version</p>', unsafe_allow_html=True)

st.info("🌐 Cloud Version: Upload audio files to analyze your playing. For live recording, use the local version.")

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    instrument = st.selectbox(
        "Select Instrument",
        ["guitar", "piano"],
        index=0
    )
    
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.1,
        max_value=0.9,
        value=0.3,
        step=0.1
    )

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📁 Upload Audio File")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['wav', 'mp3', 'ogg', 'flac']
    )
    
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        
        if st.button("🎵 Analyze Audio", type="primary"):
            with st.spinner("Analyzing audio..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Analyze the audio
                    results = analyze_audio_file(tmp_file_path, instrument)
                    st.session_state.analysis_results = results
                    
                    if results['success']:
                        st.success(f"Analysis complete! Found {results['total_notes']} notes.")
                        
                        # Add to note history
                        for note in results['detected_notes'][:20]:  # Limit to first 20 notes
                            st.session_state.note_history.append({
                                'note': note['note'],
                                'timestamp': f"{note['time']:.2f}s",
                                'confidence': f"{note['confidence']:.2f}",
                                'frequency': f"{note['frequency']:.1f}Hz"
                            })
                    else:
                        st.error(f"Analysis failed: {results['error']}")
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
    
    # Display analysis results
    if st.session_state.analysis_results and st.session_state.analysis_results['success']:
        results = st.session_state.analysis_results
        
        st.subheader("📊 Analysis Results")
        st.metric("Duration", f"{results['duration']:.2f}s")
        st.metric("Notes Detected", results['total_notes'])
        
        # Display detected notes
        if results['detected_notes']:
            st.subheader("🎵 Detected Notes")
            notes_df = pd.DataFrame(results['detected_notes'][:50])  # Show first 50 notes
            st.dataframe(notes_df, use_container_width=True)
            
            # Note frequency chart
            if len(results['detected_notes']) > 0:
                note_counts = {}
                for note in results['detected_notes']:
                    note_name = note['note']
                    note_counts[note_name] = note_counts.get(note_name, 0) + 1
                
                if note_counts:
                    fig = px.bar(
                        x=list(note_counts.keys()),
                        y=list(note_counts.values()),
                        title="Note Frequency Distribution",
                        labels={'x': 'Note', 'y': 'Count'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.header("🏆 Session History")
    
    if st.session_state.note_history:
        st.subheader("Recent Notes")
        recent_notes = pd.DataFrame(st.session_state.note_history[-10:])
        st.dataframe(recent_notes, use_container_width=True)
        
        if st.button("🗑️ Clear History"):
            st.session_state.note_history = []
            st.rerun()
    else:
        st.info("No notes analyzed yet. Upload an audio file to begin!")
    
    # Instructions
    st.header("📖 How to Use")
    with st.expander("Instructions"):
        st.markdown("""
        ### Getting Started
        1. **Select your instrument** (guitar or piano) from the sidebar
        2. **Upload an audio file** (WAV, MP3, OGG, or FLAC)
        3. **Click "Analyze Audio"** to process your recording
        4. **View the results** - detected notes and statistics
        
        ### Tips
        - Use clear, high-quality recordings
        - Minimize background noise
        - Single notes work best for accurate detection
        - For live recording, use the local version of Acoustix
        
        ### Limitations
        - Cloud version supports file upload only (no live recording)
        - Processing time depends on file size
        - Best with individual note recordings rather than full songs
        """)

# Footer
st.markdown("---")
st.markdown('<p style="text-align: center; color: gray;">Made with ❤️ for musicians everywhere | Cloud Version</p>', unsafe_allow_html=True)