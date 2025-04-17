from transcriber import transcribe_audio
import os
import logging

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_transcription():
    # Use the test38.waptt.opus file from the current directory
    test_audio = "test38.waptt.opus"
    
    if not os.path.exists(test_audio):
        logger.error(f"Test audio file not found: {test_audio}")
        return
    
    try:
        logger.info(f"Starting transcription test with file: {test_audio}")
        logger.info(f"File size: {os.path.getsize(test_audio)} bytes")
        result = transcribe_audio(test_audio)
        
        print("\nTranscription Result:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        # Print the full traceback for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_transcription()