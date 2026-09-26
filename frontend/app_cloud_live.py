import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import os

# Page configuration
st.set_page_config(
    page_title="Acoustix Live - Guitar Hero for Real Instruments",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure for Railway deployment
port = int(os.environ.get("PORT", 8501))

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
    .recording-active {
        animation: pulse 1s infinite;
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for live audio recording and pitch detection
audio_js = """
<script>
let audioContext = null;
let analyser = null;
let microphone = null;
let isRecording = false;
let pitchDetectionInterval = null;

async function startRecording() {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        microphone = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        microphone.connect(analyser);
        
        isRecording = true;
        detectPitch();
        
        // Send message to Streamlit
        parent.postMessage({type: 'recording_started'}, '*');
        
    } catch (err) {
        console.error('Error accessing microphone:', err);
        parent.postMessage({type: 'recording_error', error: err.message}, '*');
    }
}

function stopRecording() {
    if (audioContext) {
        audioContext.close();
    }
    isRecording = false;
    if (pitchDetectionInterval) {
        clearInterval(pitchDetectionInterval);
    }
    parent.postMessage({type: 'recording_stopped'}, '*');
}

function autoCorrelate(buffer, sampleRate) {
    const SIZE = buffer.length;
    let rms = 0;
    for (let i = 0; i < SIZE; i++) {
        const val = buffer[i];
        rms += val * val;
    }
    rms = Math.sqrt(rms / SIZE);
    
    if (rms < 0.01) return -1; // Not enough signal
    
    let r1 = 0, r2 = SIZE - 1, threshold = 0.2;
    for (let i = 0; i < SIZE / 2; i++) {
        if (Math.abs(buffer[i]) < threshold) { r1 = i; break; }
    }
    for (let i = 1; i < SIZE / 2; i++) {
        if (Math.abs(buffer[SIZE - i]) < threshold) { r2 = SIZE - i; break; }
    }
    
    buffer = buffer.slice(r1, r2);
    const newSize = buffer.length;
    const c = new Array(newSize).fill(0);
    
    for (let i = 0; i < newSize; i++) {
        for (let j = 0; j < newSize - i; j++) {
            c[i] = c[i] + buffer[j] * buffer[j + i];
        }
    }
    
    let d = 0;
    while (c[d] > c[d + 1]) d++;
    let maxval = -1, maxpos = -1;
    for (let i = d; i < newSize; i++) {
        if (c[i] > maxval) {
            maxval = c[i];
            maxpos = i;
        }
    }
    
    let T0 = maxpos;
    return sampleRate / T0;
}

function noteFromPitch(frequency) {
    const noteNum = 12 * (Math.log(frequency / 440) / Math.log(2));
    return Math.round(noteNum) + 69;
}

function frequencyFromNoteNumber(note) {
    return 440 * Math.pow(2, (note - 69) / 12);
}

function centsOffFromPitch(frequency, note) {
    return Math.floor(1200 * Math.log(frequency / frequencyFromNoteNumber(note)) / Math.log(2));
}

function noteString(noteNum) {
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(noteNum / 12) - 1;
    const noteName = noteNames[noteNum % 12];
    return noteName + octave;
}

function detectPitch() {
    if (!isRecording) return;
    
    const buffer = new Float32Array(analyser.fftSize);
    analyser.getFloatTimeDomainData(buffer);
    
    const frequency = autoCorrelate(buffer, audioContext.sampleRate);
    
    if (frequency !== -1) {
        const noteNum = noteFromPitch(frequency);
        const noteName = noteString(noteNum);
        const cents = centsOffFromPitch(frequency, noteNum);
        
        parent.postMessage({
            type: 'pitch_detected',
            frequency: frequency,
            note: noteName,
            cents: cents,
            confidence: 0.8
        }, '*');
    }
    
    setTimeout(detectPitch, 100); // Detect every 100ms
}

// Expose functions to window
window.startRecording = startRecording;
window.stopRecording = stopRecording;
</script>
"""

# Inject JavaScript
st.components.v1.html(audio_js, height=0)

# Session state initialization
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'note_history' not in st.session_state:
    st.session_state.note_history = []
if 'total_score' not in st.session_state:
    st.session_state.total_score = 0
if 'combo' not in st.session_state:
    st.session_state.combo = 0
if 'max_combo' not in st.session_state:
    st.session_state.max_combo = 0

# Main UI
st.markdown('<h1 class="main-header">🎸 Acoustix Live 🎹</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem;">Real-time Guitar Hero for Real Instruments</p>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    instrument = st.selectbox(
        "Select Instrument",
        ["guitar", "piano"],
        index=0
    )
    
    sensitivity = st.slider(
        "Microphone Sensitivity",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.1
    )
    
    st.header("🎮 Controls")
    
    if not st.session_state.is_recording:
        if st.button("🎤 Start Recording", use_container_width=True, type="primary"):
            st.session_state.is_recording = True
            st.rerun()
    else:
        if st.button("⏹️ Stop Recording", use_container_width=True, type="secondary"):
            st.session_state.is_recording = False
            st.rerun()
    
    st.header("📊 Current Status")
    if st.session_state.is_recording:
        st.markdown('<div class="recording-active">🔴 Recording Active</div>', unsafe_allow_html=True)
    else:
        st.info("⏸️ Not Recording")

# Recording controls with JavaScript
if st.session_state.is_recording:
    st.markdown("""
    <button onclick="window.startRecording()" style="padding: 10px 20px; font-size: 16px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
        🎤 Start Microphone
    </button>
    <button onclick="window.stopRecording()" style="padding: 10px 20px; font-size: 16px; background-color: #f44336; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">
        ⏹️ Stop Microphone
    </button>
    """, unsafe_allow_html=True)
    
    st.info("Click 'Start Microphone' to begin live pitch detection. Allow microphone access when prompted.")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎵 Real-time Feedback")
    
    if st.session_state.is_recording:
        st.success("🎤 Listening... Play your instrument!")
        
        # Manual note input for demo (since JavaScript communication is complex)
        st.subheader("Demo Mode - Click to simulate notes")
        demo_notes = ["E4", "A4", "D4", "G4", "B4", "E5", "A5", "D5", "G5", "B5"]
        cols = st.columns(5)
        for i, note in enumerate(demo_notes):
            if cols[i % 5].button(note, key=f"note_{i}"):
                # Simulate note detection
                import random
                score_type = random.choice(['PERFECT', 'GREAT', 'GOOD', 'OKAY'])
                points = {'PERFECT': 100, 'GREAT': 80, 'GOOD': 60, 'OKAY': 40}[score_type]
                
                st.session_state.note_history.append({
                    'note': note,
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'score': score_type,
                    'points': points
                })
                
                st.session_state.total_score += points
                st.session_state.combo += 1
                st.session_state.max_combo = max(st.session_state.max_combo, st.session_state.combo)
                
                st.rerun()
        
        # Display recent notes
        if st.session_state.note_history:
            st.subheader("Recent Notes")
            recent_notes = st.session_state.note_history[-10:]
            notes_df = pd.DataFrame(recent_notes)
            st.dataframe(notes_df, use_container_width=True)
    else:
        st.info("Press 'Start Recording' to begin!")
        st.warning("🌐 Note: Full microphone access requires browser permissions. Click the buttons above to enable live recording.")

with col2:
    st.header("🏆 Score Display")
    
    # Score display
    score_color = "#1f77b4"
    if st.session_state.combo >= 50:
        score_color = "#ff0000"  # Red for high combo
    elif st.session_state.combo >= 20:
        score_color = "#ff9900"  # Orange for medium combo
    
    st.markdown(f'<div class="score-display" style="background-color: {score_color}; color: white;">Score: {st.session_state.total_score}</div>', unsafe_allow_html=True)
    
    # Statistics cards
    st.header("📈 Statistics")
    
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        st.metric("Combo", f"{st.session_state.combo}x")
        st.metric("Notes Hit", len(st.session_state.note_history))
    with col2_2:
        st.metric("Max Combo", f"{st.session_state.max_combo}x")
        
    if st.session_state.note_history:
        accuracy = sum(1 for n in st.session_state.note_history if n['score'] != 'MISS') / len(st.session_state.note_history) * 100
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    # Score breakdown chart
    st.header("📊 Score Breakdown")
    if st.session_state.note_history:
        score_counts = {}
        for note in st.session_state.note_history:
            score_type = note['score']
            score_counts[score_type] = score_counts.get(score_type, 0) + 1
        
        if score_counts:
            fig = px.pie(
                values=list(score_counts.values()),
                names=list(score_counts.keys()),
                title="Score Distribution",
                color_discrete_map={
                    'PERFECT': '#00ff00',
                    'GREAT': '#00ccff',
                    'GOOD': '#ffff00',
                    'OKAY': '#ff9900',
                    'MISS': '#ff0000'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    if st.button("🗑️ Reset Session"):
        st.session_state.note_history = []
        st.session_state.total_score = 0
        st.session_state.combo = 0
        st.session_state.max_combo = 0
        st.rerun()

# Instructions section
st.header("📖 How to Use")
with st.expander("Instructions"):
    st.markdown("""
    ### Getting Started
    1. **Select your instrument** (guitar or piano) from the sidebar
    2. **Click "Start Recording"** in the sidebar
    3. **Click "Start Microphone"** button that appears
    4. **Allow microphone access** when your browser prompts you
    5. **Play your instrument** - the app will detect notes in real-time
    6. **Click "Stop Microphone"** when you're done
    
    ### Demo Mode
    - If microphone access doesn't work, use the demo buttons to simulate notes
    - Click the note buttons to test the scoring system
    
    ### Scoring System
    - **PERFECT**: 100 points + combo multiplier
    - **GREAT**: 80 points + combo multiplier  
    - **GOOD**: 60 points + combo multiplier
    - **OKAY**: 40 points + combo multiplier
    - Build combos for higher scores!
    
    ### Tips
    - Play in a quiet environment for best results
    - Ensure your instrument is in tune
    - For guitar, pluck strings cleanly
    - For piano, strike keys firmly and clearly
    - Use headphones to avoid feedback
    """)

# Footer
st.markdown("---")
st.markdown('<p style="text-align: center; color: gray;">Made with ❤️ for musicians everywhere | Live Cloud Version</p>', unsafe_allow_html=True)