from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import asyncio
from typing import Dict, List
import time

from audio_processor import AudioProcessor
from note_recognizer import NoteRecognizer
from scoring_system import ScoringSystem

app = FastAPI(title="Acoustix API")

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for active sessions
active_sessions: Dict[str, Dict] = {}


@app.get("/")
async def root():
    return {"message": "Acoustix API - Guitar Hero for real instruments"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/session/start")
async def start_session(session_data: dict):
    """Start a new scoring session"""
    session_id = str(int(time.time() * 1000))
    
    session = {
        'id': session_id,
        'instrument': session_data.get('instrument', 'guitar'),
        'with_backing_track': session_data.get('with_backing_track', False),
        'audio_processor': AudioProcessor(),
        'note_recognizer': NoteRecognizer(),
        'scoring_system': ScoringSystem(),
        'started_at': time.time(),
        'is_active': True
    }
    
    active_sessions[session_id] = session
    
    return {
        'session_id': session_id,
        'status': 'started',
        'instrument': session['instrument'],
        'with_backing_track': session['with_backing_track']
    }


@app.post("/session/{session_id}/stop")
async def stop_session(session_id: str):
    """Stop a session and return final statistics"""
    if session_id not in active_sessions:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    
    session = active_sessions[session_id]
    session['is_active'] = False
    session['audio_processor'].stop_recording()
    
    stats = session['scoring_system'].get_statistics()
    score_breakdown = session['scoring_system'].get_score_breakdown()
    
    return {
        'session_id': session_id,
        'status': 'stopped',
        'statistics': stats,
        'score_breakdown': score_breakdown,
        'duration': time.time() - session['started_at']
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio processing and scoring"""
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    session = active_sessions[session_id]
    audio_processor = session['audio_processor']
    note_recognizer = session['note_recognizer']
    scoring_system = session['scoring_system']
    
    try:
        # Start audio recording
        audio_processor.start_recording()
        
        while session['is_active']:
            # Get audio chunk
            audio_chunk = audio_processor.get_audio_chunk(timeout=0.1)
            
            if audio_chunk is not None:
                # Process audio
                frequency, confidence = audio_processor.detect_pitch(audio_chunk)
                
                if frequency and confidence > 0.3:  # Confidence threshold
                    # Identify note based on instrument
                    if session['instrument'] == 'guitar':
                        note_info = note_recognizer.identify_guitar_note(frequency)
                    else:
                        note_info = note_recognizer.identify_piano_note(frequency)
                    
                    if note_info:
                        detected_note = note_info['note']
                        current_time = time.time()
                        
                        # Evaluate note
                        result = scoring_system.evaluate_note(
                            detected_note,
                            current_time,
                            frequency
                        )
                        
                        # Send result to client
                        await websocket.send_json({
                            'type': 'note_evaluation',
                            'timestamp': current_time,
                            'note': detected_note,
                            'frequency': frequency,
                            'confidence': confidence,
                            'result': result
                        })
                
                # Send periodic statistics
                stats = scoring_system.get_statistics()
                await websocket.send_json({
                    'type': 'statistics',
                    'timestamp': time.time(),
                    'statistics': stats
                })
            
            await asyncio.sleep(0.01)  # Small delay to prevent CPU overload
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
        await websocket.close(code=1011, reason=str(e))
    finally:
        audio_processor.stop_recording()


@app.post("/upload/audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload an audio file for processing"""
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Save temporarily
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Process the audio file
        audio_processor = AudioProcessor()
        audio_data = audio_processor.process_audio_file(file_path)
        
        # Analyze the audio
        note_recognizer = NoteRecognizer()
        
        # Get pitch detection results (simplified)
        results = []
        chunk_size = 2048
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            if len(chunk) == chunk_size:
                frequency, confidence = audio_processor.detect_pitch(chunk)
                if frequency and confidence > 0.3:
                    note_info = note_recognizer.identify_guitar_note(frequency)
                    if note_info:
                        results.append({
                            'time': i / audio_processor.sample_rate,
                            'note': note_info['note'],
                            'frequency': frequency,
                            'confidence': confidence
                        })
        
        # Clean up
        os.remove(file_path)
        
        return {
            'status': 'success',
            'file': file.filename,
            'duration': len(audio_data) / audio_processor.sample_rate,
            'detected_notes': results[:100]  # Limit to first 100 results
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/sessions")
async def get_sessions():
    """Get all active sessions"""
    return {
        'active_sessions': len(active_sessions),
        'sessions': [
            {
                'id': session['id'],
                'instrument': session['instrument'],
                'started_at': session['started_at'],
                'is_active': session['is_active']
            }
            for session in active_sessions.values()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)