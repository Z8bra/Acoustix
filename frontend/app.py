import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

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
    .stat-card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f0f0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API configuration
import os
API_BASE_URL = os.environ.get("API_URL", "http://localhost:8000")

# Session state initialization
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'score_history' not in st.session_state:
    st.session_state.score_history = []
if 'note_history' not in st.session_state:
    st.session_state.note_history = []
if 'current_stats' not in st.session_state:
    st.session_state.current_stats = {}

def start_session(instrument, with_backing_track):
    """Start a new scoring session"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/session/start",
            json={
                "instrument": instrument,
                "with_backing_track": with_backing_track
            }
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data['session_id']
            st.session_state.is_recording = True
            st.session_state.score_history = []
            st.session_state.note_history = []
            return True, data
        else:
            return False, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def stop_session():
    """Stop the current session"""
    if st.session_state.session_id:
        try:
            response = requests.post(f"{API_BASE_URL}/session/{st.session_state.session_id}/stop")
            if response.status_code == 200:
                data = response.json()
                st.session_state.is_recording = False
                return True, data
            else:
                return False, response.json()
        except Exception as e:
            return False, {"error": str(e)}
    return False, {"error": "No active session"}

def get_statistics():
    """Get current session statistics"""
    if st.session_state.session_id:
        try:
            response = requests.get(f"{API_BASE_URL}/sessions")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    return {}

# Main UI
st.markdown('<h1 class="main-header">🎸 Acoustix 🎹</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem;">Guitar Hero for Real Instruments</p>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    instrument = st.selectbox(
        "Select Instrument",
        ["guitar", "piano"],
        index=0
    )
    
    with_backing_track = st.checkbox("Use Backing Track", value=False)
    
    st.header("🎮 Controls")
    
    if not st.session_state.is_recording:
        if st.button("🎤 Start Recording", use_container_width=True, type="primary"):
            success, result = start_session(instrument, with_backing_track)
            if success:
                st.success(f"Session started! ID: {result['session_id']}")
                st.rerun()
            else:
                st.error(f"Failed to start session: {result}")
    else:
        if st.button("⏹️ Stop Recording", use_container_width=True, type="secondary"):
            success, result = stop_session()
            if success:
                st.success("Session stopped!")
                st.rerun()
            else:
                st.error(f"Failed to stop session: {result}")
    
    st.header("📊 Current Status")
    if st.session_state.session_id:
        st.info(f"Session ID: {st.session_state.session_id}")
        st.info(f"Status: {'🔴 Recording' if st.session_state.is_recording else '⏸️ Stopped'}")
    else:
        st.warning("No active session")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎵 Real-time Feedback")
    
    if st.session_state.is_recording:
        st.info("🎤 Listening... Play your instrument!")
        
        # Placeholder for real-time updates
        # In a real implementation, this would use WebSocket connections
        placeholder = st.empty()
        
        # Simulate some activity for demo purposes
        if st.button("🎵 Simulate Note Detection"):
            demo_notes = ["E4", "A4", "D4", "G4", "B4", "E5"]
            import random
            detected_note = random.choice(demo_notes)
            st.session_state.note_history.append({
                'note': detected_note,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'score': random.choice(['PERFECT', 'GREAT', 'GOOD', 'OKAY', 'MISS'])
            })
            st.rerun()
        
        # Display recent notes
        if st.session_state.note_history:
            st.subheader("Recent Notes")
            notes_df = pd.DataFrame(st.session_state.note_history[-10:])  # Last 10 notes
            st.dataframe(notes_df, use_container_width=True)
    else:
        st.info("Press 'Start Recording' to begin!")
        
        # Upload audio file option
        st.header("📁 Upload Audio File")
        uploaded_file = st.file_uploader("Choose an audio file", type=['wav', 'mp3', 'ogg'])
        
        if uploaded_file:
            if st.button("📤 Process Audio File"):
                with st.spinner("Processing audio..."):
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/upload/audio", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Processed {result['file']}!")
                        st.json(result)
                    else:
                        st.error(f"Error processing file: {response.json()}")

with col2:
    st.header("🏆 Score Display")
    
    if st.session_state.session_id:
        # Display current statistics
        stats = get_statistics()
        if 'sessions' in stats and stats['sessions']:
            current_session = next((s for s in stats['sessions'] if s['id'] == st.session_state.session_id), None)
            if current_session:
                st.metric("Active Sessions", stats['active_sessions'])
    
    # Score display (placeholder for real implementation)
    score_card = st.container()
    with score_card:
        st.markdown('<div class="score-display" style="background-color: #1f77b4; color: white;">Score: 0</div>', unsafe_allow_html=True)
    
    # Statistics cards
    st.header("📈 Statistics")
    
    col2_1, col2_2 = st.columns(2)
    with col2_1:
        st.metric("Accuracy", "0%")
        st.metric("Combo", "0x")
    with col2_2:
        st.metric("Notes Hit", "0/0")
        st.metric("Max Combo", "0")
    
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

# Instructions section
st.header("📖 How to Use")
with st.expander("Instructions"):
    st.markdown("""
    ### Getting Started
    1. **Select your instrument** (guitar or piano) from the sidebar
    2. **Choose whether to use a backing track** or play freestyle
    3. **Click "Start Recording"** to begin the session
    4. **Play your instrument** - the app will detect notes and score your performance
    5. **Click "Stop Recording"** when you're done to see your final statistics
    
    ### Scoring System
    - **PERFECT**: Within 30ms timing and 10 cents pitch accuracy
    - **GREAT**: Within 60ms timing and 25 cents pitch accuracy  
    - **GOOD**: Within 100ms timing and 50 cents pitch accuracy
    - **OKAY**: Within 150ms timing and 100 cents pitch accuracy
    - **MISS**: Outside these thresholds or wrong note
    
    ### Tips
    - Play in a quiet environment for best results
    - Ensure your instrument is in tune
    - For guitar, pluck strings cleanly
    - For piano, strike keys firmly and clearly
    - Build combos for higher scores!
    """)

# Footer
st.markdown("---")
st.markdown('<p style="text-align: center; color: gray;">Made with ❤️ for musicians everywhere</p>', unsafe_allow_html=True)