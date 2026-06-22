import os
import streamlit as st
import assemblyai as aai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize AssemblyAI API Key (checks st.secrets first, then environment variables)
aai.settings.api_key = st.secrets.get("ASSEMBLYAI_API_KEY", os.getenv("ASSEMBLYAI_API_KEY", ""))
TRANSCRIPTIONS_DIR = "transcricoes"

def transcribe_audio(audio_path: str) -> tuple[str, str]:
    """
    Uploads the preprocessed audio file to AssemblyAI, performs diarization,
    saves the formatted transcript to a text file, and returns both the 
    transcript text and its file path.
    """
    if not aai.settings.api_key or aai.settings.api_key == "COLOQUE_SUA_CHAVE_AQUI":
        raise ValueError("Chave da API da AssemblyAI não configurada (.env ou secrets.toml).")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")

    # Determine paths
    base_name = os.path.basename(audio_path).replace(".wav", ".txt")
    output_txt_path = os.path.join(TRANSCRIPTIONS_DIR, base_name.replace("REC_", "TRANS_"))
    
    # AssemblyAI config tuned for clinical conversation (doctor/patient)
    config = aai.TranscriptionConfig(
        language_code="pt",
        speaker_labels=True,
        speakers_expected=2
    )
    
    transcriber = aai.Transcriber()
    
    # Process audio file through AssemblyAI
    transcript = transcriber.transcribe(audio_path, config=config)
    
    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"Erro na AssemblyAI: {transcript.error}")
        
    lines = []
    # Build text transcript with timestamped utterances and speaker ID
    for utterance in transcript.utterances:
        inicio = utterance.start / 1000.0
        fim = utterance.end / 1000.0
        spk = f"SPEAKER_{utterance.speaker}"
        texto = utterance.text
        
        line = f"[{inicio:.1f}s -> {fim:.1f}s] {spk}: {texto}"
        lines.append(line)
        
    transcript_text = "\n".join(lines)
    
    # Save transcription to local file
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(transcript_text + "\n")
        
    return transcript_text, output_txt_path
