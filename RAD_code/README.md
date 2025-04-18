# RAD-Assist: Medical Transcription and Text Processing

A system for transcribing medical audio recordings and processing the resulting text using NLP techniques.

## Features

- Speech-to-text conversion using Whisper model
- Text preprocessing using spaCy
- Medical entity recognition
- Web interface using Streamlit
- REST API using FastAPI

## Setup

1. Clone the repository:
```bash
git clone <your-repository-url>
cd RAD-assist
```

2. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. Run the application:

Start the backend server:
```bash
python main.py
```

For web interface (optional):
```bash
streamlit run app.py
```

For text preprocessing in terminal:
```bash
python textpreprocessing.py
# or
python text_processor.py
```

## Project Structure

- `main.py`: FastAPI backend server with Whisper model
- `app.py`: Streamlit web interface
- `textpreprocessing.py`: Text preprocessing utilities
- `text_processor.py`: Additional text processing features
- `transcribe.py`: Audio transcription functionality

## Requirements

- Python 3.8+
- spaCy
- FastAPI
- Streamlit
- Whisper
- Other dependencies listed in requirements.txt 