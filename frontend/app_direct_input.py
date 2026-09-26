import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import os

# Page configuration
st.set_page_config(
    page_title="Acoustix Direct - Guitar Hero for Connected Instruments",
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
    .device-info {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for direct instrument input using Web Audio API
audio_js = """
<script>
let audioContext = null;
let audioInput = null;
let analyser = null;
let isRecording = false;
let pitchDetectionInterval = null;
let selectedDeviceId = null;

async function getAudioDevices() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        
        let deviceInfo = [];
        audioInputs.forEach((device, index) => {
            deviceInfo.push({
                index: index,
                deviceId: device.deviceId,
                label: device.label || `Microphone ${index + 1}`,
                groupId: device.groupId
            });
        });
        
        parent.postMessage({
            type: 'audio_devices',
            devices: deviceInfo
        }, '*');
        
        return deviceInfo;
    } catch (err) {
        console.error('Error getting audio devices:', err);
        parent.postMessage({type: 'device_error', error: err.message}, '*');
        return [];
    }
}

async function startRecording(deviceId = null) {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        const constraints = {
            audio: {
                deviceId: deviceId ? { exact: deviceId } : undefined,
                echoCancellation: false,
                noiseSuppression: false,
                autoGainControl: false
            }
        };
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        audioInput = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 4096; // Higher for better frequency resolution
        analyser.smoothingTimeConstant = 0.8;
        audioInput.connect(analyser);
        
        isRecording = true;
        detectPitch();
        
        parent.postMessage({type: 'recording_started', deviceId: deviceId}, '*');
        
    } catch (err) {
        console.error('Error accessing audio input:', err);
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
    
    if (frequency !== -1 && frequency > 50 && frequency < 2000) { // Valid frequency range for instruments
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
    
    setTimeout(detectPitch, 50); // Detect every 50ms for better responsiveness
}

// Expose functions to window
window.getAudioDevices = getAudioDevices;
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
if 'audio_devices' not in st.session_state:
    st.session_state.audio_devices = []
if 'selected_device' not in st.session_state:
    st.session_state.selected_device = None

# Main UI
st.markdown('<h1 class="main-header">🎸 Acoustix Direct Input 🎹</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem;">Guitar Hero for Connected Instruments - Plug in Your Instrument!</p>', unsafe_allow_html=True)

st.info("🎛️ Connect your instrument via USB, audio interface, or direct line-in like in Garage Band")

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    instrument = st.selectbox(
        "Select Instrument",
        ["guitar", "piano", "bass", "other"],
        index=0
    )
    
    input_gain = st.slider(
        "Input Gain",
        min_value=0.1,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Adjust sensitivity for your instrument input"
    )
    
    st.header("🎛️ Audio Input")
    
    # Device selection
    if st.button("🎤 Scan for Audio Devices"):
        st.markdown('<script>window.getAudioDevices();</script>', unsafe_allow_html=True)
        st.info("Scanning for audio devices...")
    
    if st.session_state.audio_devices:
        st.subheader("Available Audio Inputs")
        device_options = [f"{device['label']}" for device in st.session_state.audio_devices]
        selected_index = st.selectbox(
            "Select Your Instrument Input",
            range(len(device_options)),
            format_func=lambda i: device_options[i]
        )
        
        if selected_index is not None:
            st.session_state.selected_device = st.session_state.audio_devices[selected_index]['deviceId']
    
    st.header("🎮 Controls")
    
    if not st.session_state.is_recording:
        if st.button("🎤 Start Recording", use_container_width=True, type="primary"):
            if st.session_state.selected_device:
                device_id = f'"{st.session_state.selected_device}"'
                st.markdown(f'<script>window.startRecording({device_id});</script>', unsafe_allow_html=True)
                st.session_state.is_recording = True
                st.rerun()
            else:
                st.warning("Please select an audio device first")
    else:
        if st.button("⏹️ Stop Recording", use_container_width=True, type="secondary"):
            st.markdown('<script>window.stopRecording();</script>', unsafe_allow_html=True)
            st.session_state.is_recording = False
            st.rerun()
    
    st.header("📊 Current Status")
    if st.session_state.is_recording:
        st.markdown('<div class="recording-active">🔴 Recording Active</div>', unsafe_allow_html=True)
        if st.session_state.selected_device:
            st.info(f"🎛️ Input: {st.session_state.selected_device}")
    else:
        st.info("⏸️ Not Recording")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎛️ Instrument Input")
    
    st.markdown('<div class="device-info">', unsafe_allow_html=True)
    st.markdown("""
    ### How to Connect Your Instrument:
    
    **USB Instruments:**
    - Connect directly via USB cable
    - Select the USB input from the device list
    
    **Audio Interface:**
    - Connect instrument to audio interface
    - Connect interface to computer via USB
    - Select the interface input from device list
    
    **Direct Line-In:**
    - Use 1/4" to 3.5mm adapter
    - Plug into computer's line-in port
    - Select line-in from device list
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.is_recording:
        st.success("🎤 Listening for instrument input... Play your instrument!")
        
        # Manual note input for demo/testing
        st.subheader("Demo Mode - Test Scoring System")
        demo_notes = {
            "guitar": ["E2", "A2", "D3", "G3", "B3", "E4", "A4", "D4", "G4", "B4"],
            "piano": ["A0", "C1", "E1", "A1", "C2", "E2", "A2", "C3", "E3", "A3"],
            "bass": ["E1", "A1", "D2", "G2"],
            "other": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
        }
        
        instrument_notes = demo_notes.get(instrument, demo_notes["other"])
        cols = st.columns(5)
        for i, note in enumerate(instrument_notes):
            if cols[i % 5].button(note, key=f"note_{i}"):
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
        st.info("Select your audio input device and click 'Start Recording' to begin!")

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
    ### Getting Started with Direct Instrument Input
    
    **Step 1: Connect Your Instrument**
    - **USB Instruments**: Connect via USB cable (MIDI keyboards, USB guitars)
    - **Audio Interface**: Connect instrument to interface, then interface to computer
    - **Direct Line-In**: Use adapter to plug into computer's audio input
    
    **Step 2: Select Audio Input**
    - Click "Scan for Audio Devices"
    - Choose your instrument from the list
    - Adjust input gain if needed
    
    **Step 3: Start Recording**
    - Click "Start Recording"
    - Allow browser audio access
    - Play your instrument
    - Watch real-time scoring!
    
    **Step 4: Review Performance**
    - See your score build in real-time
    - Check accuracy and combo stats
    - Reset to try again
    
    ### Advantages of Direct Input
    - ✅ Better audio quality (digital signal)
    - ✅ No background noise
    - ✅ More accurate pitch detection
    - ✅ Works like Garage Band / professional DAWs
    - ✅ Consistent input for scoring
    
    ### Tips
    - Use a quality audio interface for best results
    - Set appropriate input levels (not too loud/quiet)
    - Keep your instrument in tune
    - Use clean, direct signal (no effects initially)
    """)

# Footer
st.markdown("---")
st.markdown('<p style="text-align: center; color: gray;">Made with ❤️ for musicians everywhere | Direct Instrument Input Version</p>', unsafe_allow_html=True)