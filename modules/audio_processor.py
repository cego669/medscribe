import os
import subprocess
from datetime import datetime
import streamlit as st

RECORDINGS_DIR = "gravacoes"
TRANSCRIPTIONS_DIR = "transcricoes"

def ensure_directories():
    """Ensures that the recordings and transcriptions directories exist."""
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

def clear_previous_files():
    """
    Deletes the last/all recording and transcription files to keep the environment clean.
    This runs when the user initiates a new recording session.
    """
    ensure_directories()
    
    # Clean recordings directory
    for file in os.listdir(RECORDINGS_DIR):
        file_path = os.path.join(RECORDINGS_DIR, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")
            
    # Clean transcriptions directory
    for file in os.listdir(TRANSCRIPTIONS_DIR):
        file_path = os.path.join(TRANSCRIPTIONS_DIR, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

def save_and_preprocess(audio_bytes: bytes, mime_type: str) -> str:
    """
    Saves raw audio bytes from the browser, processes them with FFmpeg 
    (applying highpass filter and loudness normalization), and returns the path to the 
    preprocessed WAV file.
    """
    ensure_directories()
    
    # Detect extension from mime-type (usually audio/webm or audio/wav)
    ext = "wav" if "wav" in mime_type else "webm"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    temp_raw_path = os.path.join(RECORDINGS_DIR, f"temp_{timestamp}.{ext}")
    final_wav_path = os.path.join(RECORDINGS_DIR, f"REC_{timestamp}.wav")
    
    # Save the raw browser audio bytes to a temp file
    with open(temp_raw_path, "wb") as f:
        f.write(audio_bytes)
        
    # Apply highpass filter (cut off low frequency rumble) and loudnorm (normalize loudness)
    audio_filter = "highpass=f=100,loudnorm"
    command = [
        'ffmpeg', '-y', '-v', 'error', '-i', temp_raw_path,
        '-ar', '16000', '-ac', '1', '-af', audio_filter,
        '-c:a', 'pcm_s16le', final_wav_path
    ]
    
    try:
        # Run FFmpeg to convert the raw audio to preprocessed clinic-ready audio
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        st.error(f"Erro no FFmpeg: O arquivo raw de áudio não pôde ser pré-processado. Verifique se o FFmpeg está instalado.")
        # If FFmpeg failed, keep the raw file or delete it
        if os.path.exists(temp_raw_path):
            os.remove(temp_raw_path)
        raise e
    finally:
        # Clean up the raw temp file
        if os.path.exists(temp_raw_path):
            os.remove(temp_raw_path)
            
    return final_wav_path
