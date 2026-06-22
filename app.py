import os
import streamlit as st
from modules.auth import check_password, logout
from modules.audio_processor import clear_previous_files, save_and_preprocess
from modules.transcriber import transcribe_audio
from streamlit_mic_recorder import mic_recorder

# Set page settings and appearance
st.set_page_config(
    page_title="MedScribe - Transcritor de Consultas",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom premium CSS for professional aesthetics
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header design */
    .app-header {
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        padding: 35px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.15);
        position: relative;
        overflow: hidden;
    }
    .app-header::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50%;
        pointer-events: none;
    }
    .app-header h1 {
        margin: 0;
        font-family: 'Outfit', sans-serif;
        font-size: 32px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .app-header p {
        margin: 8px 0 0 0;
        opacity: 0.9;
        font-size: 15px;
        font-weight: 400;
    }
    
    /* Custom style for Streamlit containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #F1F5F9 !important;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 10px 20px -3px rgba(0, 0, 0, 0.06) !important;
        border-color: #E2E8F0 !important;
    }
    
    /* Transcription dialogue box styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin: 20px 0;
        padding: 20px;
        background-color: #F8FAFC;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        max-height: 450px;
        overflow-y: auto;
    }
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 12px;
        max-width: 90%;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        line-height: 1.6;
        font-size: 14.5px;
    }
    .bubble-1 {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        align-self: flex-start;
    }
    .bubble-2 {
        background-color: #ECFDF5;
        border-left: 4px solid #10B981;
        align-self: flex-start;
    }
    .bubble-generic {
        background-color: #F1F5F9;
        border-left: 4px solid #64748B;
        align-self: flex-start;
    }
    .bubble-meta {
        font-size: 11px;
        color: #64748B;
        margin-bottom: 6px;
        display: flex;
        gap: 12px;
        font-weight: 500;
    }
    .bubble-speaker-1 {
        color: #1E40AF;
        font-weight: 700;
    }
    .bubble-speaker-2 {
        color: #065F46;
        font-weight: 700;
    }
    .bubble-speaker-generic {
        color: #475569;
        font-weight: 700;
    }
    .bubble-text {
        color: #1E293B;
    }
    
    /* Footer layout styling */
    .app-footer {
        text-align: center;
        padding: 20px;
        color: #94A3B8;
        font-size: 12px;
        margin-top: 40px;
        border-top: 1px solid #F1F5F9;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Render login and stop if not authenticated
if not check_password():
    st.stop()

# Sidebar configuration
with st.sidebar:
    st.markdown("### 🩺 Portal Clínico")
    st.markdown("Bem-vindo ao sistema de transcrição de consultas.")
    st.info("O sistema divide a gravação automaticamente entre os oradores identificados (Orador 1 e Orador 2).")
    
    st.markdown("---")
    if st.button("Sair do Sistema", type="secondary", use_container_width=True):
        logout()

# Main Application Banner
st.markdown(
    """
    <div class="app-header">
        <h1>🩺 MedScribe</h1>
        <p>Assistente Digital para Transcrição de Consultas Clínicas</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize Session States for Audio and Transcripts
if "last_processed_audio_bytes" not in st.session_state:
    st.session_state["last_processed_audio_bytes"] = None
if "preprocessed_audio_path" not in st.session_state:
    st.session_state["preprocessed_audio_path"] = None
if "transcription_text" not in st.session_state:
    st.session_state["transcription_text"] = None
if "transcription_path" not in st.session_state:
    st.session_state["transcription_path"] = None

# Interface widgets for live recording
st.markdown("### 🎙️ Gravar Consulta")
st.write("Clique no botão abaixo para gravar a consulta. O áudio será processado e transcrevido automaticamente ao finalizar.")

# Use native container with border and background styling
with st.container(border=True):
    audio_data = mic_recorder(
        start_prompt="🔴 Iniciar Gravação",
        stop_prompt="⏹️ Finalizar e Processar",
        just_once=False,
        use_container_width=True,
        format="wav",
        key="mic_recorder_component"
    )

# Helper function to parse transcript lines into speaker tags and timestamps
def parse_line(line_str):
    try:
        if "]" in line_str and ":" in line_str:
            time_part, speaker_and_text = line_str.split("]", 1)
            time = time_part.replace("[", "").strip()
            speaker_part, text = speaker_and_text.split(":", 1)
            return time, speaker_part.strip(), text.strip()
    except Exception:
        pass
    return None, None, line_str

# Check if a new recording has been sent from the browser
if audio_data is not None:
    current_bytes = audio_data["bytes"]
    
    # Detect if it's a new audio session
    if current_bytes != st.session_state["last_processed_audio_bytes"]:
        # Rule: Deletes the last report and last audio file automatically
        clear_previous_files()
        
        # Reset local session states
        st.session_state["last_processed_audio_bytes"] = current_bytes
        st.session_state["preprocessed_audio_path"] = None
        st.session_state["transcription_text"] = None
        st.session_state["transcription_path"] = None
        
        # Step 1: Preprocess with FFmpeg
        with st.spinner("🧹 Limpando áudio e ajustando frequências (FFmpeg)..."):
            try:
                mime_type = audio_data.get("format", "audio/webm")
                final_wav = save_and_preprocess(current_bytes, mime_type)
                st.session_state["preprocessed_audio_path"] = final_wav
                st.success("✔️ Áudio pré-processado com sucesso!")
            except Exception as e:
                st.error(f"Falha ao pré-processar o áudio: {e}")
        
        # Step 2: Transcribe via AssemblyAI with Diarization
        if st.session_state["preprocessed_audio_path"]:
            with st.spinner("☁️ Analisando e identificando vozes (AssemblyAI)..."):
                try:
                    txt, txt_path = transcribe_audio(st.session_state["preprocessed_audio_path"])
                    st.session_state["transcription_text"] = txt
                    st.session_state["transcription_path"] = txt_path
                    st.success("✔️ Transcrição e identificação concluídas!")
                except Exception as e:
                    st.error(f"Falha na transcrição: {e}")
                    
        # Rerun to update state values and render downstream downloads
        st.rerun()

# Display Results Section if data is available
if st.session_state["preprocessed_audio_path"] and st.session_state["transcription_text"]:
    # Using a single native container for results
    with st.container(border=True):
        st.markdown("### 📋 Diálogo da Consulta Processada")
        
        # Display audio player for the doctor to listen to the optimized recording
        st.markdown("#### 🎧 Áudio Clínico Otimizado")
        with open(st.session_state["preprocessed_audio_path"], "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/wav")
            
        st.markdown("#### 💬 Transcrição de Vozes")
        
        # Construct the ENTIRE transcript box as a single HTML block
        # We write these strings as single-line elements to prevent leading indentation spaces 
        # from triggering markdown code block formatting in Streamlit's parser.
        chat_html = '<div class="chat-container">'
        for line in st.session_state["transcription_text"].split("\n"):
            if not line.strip():
                continue
            time_stamp, speaker, text_content = parse_line(line)
            
            if speaker and time_stamp:
                if "SPEAKER_A" in speaker or "SPEAKER_0" in speaker:
                    chat_html += (
                        f'<div class="chat-bubble bubble-1">'
                        f'<div class="bubble-meta"><span class="bubble-speaker-1">Orador 1</span><span>⏱️ {time_stamp}</span></div>'
                        f'<div class="bubble-text">{text_content}</div>'
                        f'</div>'
                    )
                elif "SPEAKER_B" in speaker or "SPEAKER_1" in speaker:
                    chat_html += (
                        f'<div class="chat-bubble bubble-2">'
                        f'<div class="bubble-meta"><span class="bubble-speaker-2">Orador 2</span><span>⏱️ {time_stamp}</span></div>'
                        f'<div class="bubble-text">{text_content}</div>'
                        f'</div>'
                    )
                else:
                    chat_html += (
                        f'<div class="chat-bubble bubble-generic">'
                        f'<div class="bubble-meta"><span class="bubble-speaker-generic">{speaker}</span><span>⏱️ {time_stamp}</span></div>'
                        f'<div class="bubble-text">{text_content}</div>'
                        f'</div>'
                    )
            else:
                chat_html += f'<div style="color: #64748B; font-style: italic; padding: 4px 8px;">{line}</div>'
                
        chat_html += '</div>'
        
        # Render the entire dialogue container in a single markdown block
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # Action buttons for downloading preprocessed outputs
        col_audio, col_txt = st.columns(2)
        wav_filename = os.path.basename(st.session_state["preprocessed_audio_path"])
        txt_filename = os.path.basename(st.session_state["transcription_path"])
        
        with col_audio:
            with open(st.session_state["preprocessed_audio_path"], "rb") as audio_file:
                st.download_button(
                    label="📥 Baixar Áudio Otimizado (.wav)",
                    data=audio_file.read(),
                    file_name=wav_filename,
                    mime="audio/wav",
                    use_container_width=True,
                    type="primary"
                )
                
        with col_txt:
            with open(st.session_state["transcription_path"], "r", encoding="utf-8") as txt_file:
                st.download_button(
                    label="📥 Baixar Relatório (.txt)",
                    data=txt_file.read(),
                    file_name=txt_filename,
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
else:
    # Empty State Info when no consultation has been processed in this session
    st.info("Nenhuma consulta ativa no momento. Utilize o gravador acima para iniciar.")

# Simple professional footer
st.markdown(
    """
    <div class="app-footer">
        MedScribe — Sistema Restrito e Confidencial de Transcrição Clínica.
    </div>
    """,
    unsafe_allow_html=True
)
