# 🎸 Acoustix - Guitar Hero for Real Instruments 🎹

Acoustix is a revolutionary app that turns your real instrument practice into a game! Simply play your guitar or piano (acoustic or electric) and get scored in real-time, just like Guitar Hero but with actual instruments.

## Features

- **Real-time Pitch Detection**: Advanced audio processing detects the notes you play
- **Multi-instrument Support**: Works with both guitar and piano
- **Flexible Input**: Use your microphone or plug your instrument directly into your computer
- **Optional Backing Tracks**: Play along with music or go freestyle
- **Guitar Hero-style Scoring**: Get scored on timing and accuracy with combo multipliers
- **Cross-platform**: Web-based interface works on desktop and mobile devices

## Tech Stack

- **Backend**: Python with FastAPI
- **Audio Processing**: librosa, numpy, pyaudio
- **Frontend**: Streamlit for responsive web interface
- **Real-time Communication**: WebSocket for live scoring

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Microphone or audio interface

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd acoustix
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install PortAudio (required for PyAudio):
- **Mac**: `brew install portaudio`
- **Linux**: `sudo apt-get install portaudio19-dev`
- **Windows**: Usually included with PyAudio installer

## Usage

### Starting the Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Start the FastAPI server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### Starting the Frontend

1. In a new terminal, navigate to the frontend directory:
```bash
cd frontend
```

2. Start the Streamlit app:
```bash
streamlit run app.py
```

The web interface will be available at `http://localhost:8501`

### Using the App

1. Open your browser and navigate to `http://localhost:8501`
2. Select your instrument (guitar or piano)
3. Choose whether to use a backing track
4. Click "Start Recording"
5. Play your instrument!
6. Watch your score in real-time
7. Click "Stop Recording" to see your final statistics

## Architecture

### Backend Components

- **AudioProcessor**: Handles audio input from microphone and processes audio chunks
- **NoteRecognizer**: Identifies notes based on frequency for both guitar and piano
- **ScoringSystem**: Evaluates performance with timing and pitch accuracy scoring
- **FastAPI App**: RESTful API and WebSocket endpoints for real-time communication

### Frontend Components

- **Streamlit Interface**: Responsive web UI with real-time updates
- **Score Display**: Visual feedback for performance
- **Statistics Dashboard**: Detailed performance metrics and charts

## Scoring System

### Score Types

- **PERFECT**: Within 30ms timing and 10 cents pitch accuracy (100 points)
- **GREAT**: Within 60ms timing and 25 cents pitch accuracy (80 points)
- **GOOD**: Within 100ms timing and 50 cents pitch accuracy (60 points)
- **OKAY**: Within 150ms timing and 100 cents pitch accuracy (40 points)
- **MISS**: Outside thresholds or wrong note (0 points)

### Combo System

Build combos for higher scores:
- 10 notes: 1.1x multiplier
- 20 notes: 1.2x multiplier
- 30 notes: 1.3x multiplier
- 50 notes: 1.5x multiplier
- 100 notes: 2.0x multiplier

## API Endpoints

### REST API

- `POST /session/start` - Start a new scoring session
- `POST /session/{session_id}/stop` - Stop a session and get results
- `POST /upload/audio` - Upload audio file for processing
- `GET /sessions` - Get all active sessions

### WebSocket

- `WS /ws/{session_id}` - Real-time audio processing and scoring

## Project Structure

```
acoustix/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── audio_processor.py  # Audio input and processing
│   ├── note_recognizer.py  # Note identification
│   └── scoring_system.py   # Scoring logic
├── frontend/
│   └── app.py              # Streamlit web interface
├── assets/                 # Static assets (images, sounds)
├── data/                   # Sample data and backing tracks
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Future Enhancements

- [ ] Song library with pre-charted melodies
- [ ] Multiplayer mode
- [ ] Leaderboards
- [ ] Advanced practice modes (scales, arpeggios)
- [ ] Recording and playback features
- [ ] Mobile app version
- [ ] Integration with streaming services
- [ ] AI-powered performance feedback

## Troubleshooting

### Audio Input Issues

If you're having trouble with audio input:
- Ensure your microphone is properly connected
- Check system audio settings
- Try different audio input devices
- For electric instruments, use a proper audio interface

### Performance Issues

If the app is running slowly:
- Close other applications using audio
- Reduce audio chunk size in settings
- Use a wired network connection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with love for musicians everywhere
- Inspired by Guitar Hero and similar rhythm games
- Powered by amazing open-source audio processing libraries