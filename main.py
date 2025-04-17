from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transcriber import transcribe_audio, check_ffmpeg
import shutil
import os
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  
        logging.FileHandler('backend.log')  
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application...")
    if not check_ffmpeg():
        logger.error("FFmpeg is not installed or not in PATH. The application may not work correctly.")
        raise RuntimeError("FFmpeg is required but not found. Please install FFmpeg and ensure it's in your PATH.")
    logger.info("FastAPI application started successfully")

@app.get("/health")
async def health_check():
    
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "ffmpeg_available": check_ffmpeg(),
        "whisper_model_loaded": True
    }

@app.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        
        file_location = f"temp_{file.filename}"
        logger.info(f"Saving file to: {file_location}")
        
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info("Starting transcription...")
        text = transcribe_audio(file_location)
        logger.info("Transcription completed successfully")
        
     
        os.remove(file_location)
        logger.info(f"Removed temporary file: {file_location}")
        
        return {"transcription": text}
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
