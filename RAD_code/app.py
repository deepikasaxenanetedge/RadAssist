import streamlit as st
import requests
import tempfile
import os
from datetime import datetime

st.set_page_config(
    layout="wide",
    page_title="RAD-Assist ",
    page_icon="🩺",
    initial_sidebar_state="expanded"
)

if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None

st.markdown("""
    <style>
        /* Main background and text colors */
        body {
            background-color: #f0f2f6;
            color: #2b2b2b;
        }
        .stApp {
            background-color: #f0f2f6;
        }
        
        /* Container styling */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
            background-color: #f0f2f6;
        }
        
        /* Headers and labels */
        h1, h2, h3 {
            color: #2b2b2b !important;
            font-weight: 600 !important;
        }
        .stTextInput > label, .stTextArea > label, .stFileUploader > label {
            color: #2b2b2b !important;
            font-weight: 500;
        }
        
        /* Text areas and inputs */
        .stTextArea textarea {
            background-color: #ffffff;
            color: #2b2b2b;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            line-height: 1.5;
        }
        .stTextArea textarea:focus {
            border-color: #0984e3;
            box-shadow: 0 0 0 2px rgba(9, 132, 227, 0.2);
        }
        
        /* Buttons */
        .stButton button {
            background-color: #0984e3;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton button:hover {
            background-color: #0873c4;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        /* File uploader */
        .stFileUploader {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid #e0e0e0;
        }
        
        /* Columns and cards */
        .element-container {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
            border: 1px solid #e0e0e0;
        }
        
        /* Status messages */
        .stSuccess {
            background-color: #00b894;
            color: white;
        }
        .stError {
            background-color: #d63031;
            color: white;
        }
        .stWarning {
            background-color: #fdcb6e;
            color: #2d3436;
        }
        
        /* Progress bar */
        .stProgress > div > div > div {
            background-color: #0984e3;
        }

        /* Custom status box */
        .status-box {
            background-color: #ffffff;
            border-radius: 20px;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 4px solid #0984e3;
        }

        /* Radio buttons */
        .stRadio > div {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid #e0e0e0;
        }

        /* Date and time inputs */
        .stDateInput > div, .stTimeInput > div {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }

        /* Code blocks */
        .stCodeBlock {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)


st.title("🩺 RAD-Assist")


col1, col2, col3 = st.columns([1.2, 1.5, 1.5])


with col1:
    st.header("Audio Input")
    
   
    audio_file = st.file_uploader(
        "Upload Radiologist's Audio",
        type=["wav", "mp3", "m4a", "opus"],
        help="Supported formats: WAV, MP3, M4A, OPUS"
    )
    
    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")
        st.session_state.audio_file = audio_file

    if st.button("Transcribe", key="transcribe_btn"):
        if audio_file is not None:
            with st.spinner("Transcribing audio..."):
                
                progress_bar = st.progress(0)
                
                
                files = {"file": (audio_file.name, audio_file, "audio/wav")}
                try:
                    response = requests.post("http://127.0.0.1:8000/transcribe/", files=files)
                    progress_bar.progress(50)
                    
                    if response.status_code == 200:
                        st.session_state.transcription = response.json()["transcription"]
                        progress_bar.progress(100)
                        st.success("✅ Transcription Complete")
                    else:
                        st.error("❌ Failed to transcribe.")
                except Exception as e:
                    st.error(f"🚫 Error: {e}")
        else:
            st.warning("Please provide an audio input first.")


with col2:
    st.header("📝 Transcribed Text")
    transcript = st.session_state.get("transcription", "")
    st.text_area(
        "Transcript",
        transcript,
        height=300,
        key="transcript_area",
        help="The transcribed text will appear here"
    )
    
    
    if transcript:
        if st.button("Copy to Clipboard", key="copy_btn"):
            st.code(transcript, language="text")
            st.success("Text copied to clipboard!")

with col3:
    st.header("📋 Final Report")
    report_text = st.text_area(
        "Radiology Report",
        "",
        height=300,
        key="report_area",
        help="Edit and finalize your radiology report here"
    )
    
    
    col_a, col_b = st.columns(2)
    with col_a:
        report_date = st.date_input("Report Date", datetime.now())
    with col_b:
        report_time = st.time_input("Report Time", datetime.now())
    
    if st.button("🖨️ Submit Report", key="submit_btn"):
        if report_text:
            st.success("✅ Report submitted successfully!")
           
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(f"Date: {report_date}\n")
                f.write(f"Time: {report_time}\n\n")
                f.write(report_text)
            st.info(f"Report saved as: {filename}")
        else:
            st.warning("Please enter a report before submitting.")

