import whisper
import tempfile
import os
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend.log')
    ]
)
logger = logging.getLogger(__name__)

model = whisper.load_model("small")
logger.info("Whisper model loaded successfully")

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("FFmpeg is available")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("FFmpeg is not installed or not in PATH")
        return False

def preprocess_audio(input_path: str) -> str:
    """
    Preprocess audio file using FFmpeg to ensure compatibility with Whisper.
    Converts audio to 16kHz mono WAV format.
    """
    if not check_ffmpeg():
        logger.warning("FFmpeg is not installed or not in PATH. Using original file without preprocessing.")
        return input_path

    logger.info(f"Preprocessing audio file: {input_path}")
    
    # Create a temporary file with a unique name
    temp_output = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_output.close()  # Close the file so FFmpeg can access it
    
    try:
        # Get absolute paths
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(temp_output.name)
        
        # Create the FFmpeg command with progress information
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file without asking
            '-i', f'"{input_path}"',
            '-ac', '1',  # mono
            '-ar', '16000',  # 16kHz sample rate
            '-loglevel', 'info',  # Changed from error to info to see progress
            '-progress', 'pipe:1',  # Show progress
            f'"{output_path}"'
        ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        # Run the command with shell=True and capture output
        process = subprocess.Popen(
            ' '.join(cmd),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Read output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"FFmpeg: {output.strip()}")
        
        # Check for errors
        _, stderr = process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, stderr=stderr)
        
        if stderr:
            logger.warning(f"FFmpeg warnings: {stderr}")
        
        logger.info(f"Audio preprocessing completed. Output saved to: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if isinstance(e.stderr, str) else e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg error: {error_msg}")
        if os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        if os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise

def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file using Whisper."""
    logger.info(f"Starting transcription for file: {file_path}")
    temp_file = None
    try:
        # Preprocess the audio file
        temp_file = preprocess_audio(file_path)
        if not temp_file:
            raise Exception("Audio preprocessing failed")
            
        # Load Whisper model
        logger.info("Loading Whisper model...")
        model = whisper.load_model("small")
        logger.info("Whisper model loaded successfully")
        
        # Transcribe the audio
        logger.info(f"Starting transcription of file: {temp_file}")
        result = model.transcribe(temp_file,language="en")
        logger.info("Transcription completed successfully")
        
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            logger.info(f"Temporary file cleaned up: {temp_file}")
            
        return result["text"]
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg processing failed: {e.stderr.decode() if e.stderr else str(e)}")
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        raise
