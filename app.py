import os
import streamlit as st
from modules.auth import check_password, logout
from modules.audio_processor import clear_previous_files, save_and_preprocess
from modules.transcriber import transcribe_audio
from modules.report_generator import extrair_texto_pdf, gerar_nota_clinica, criar_docx_em_memoria
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Base Colors & Typography */
    :root {
        --primary: #0F766E; /* Deep Teal */
        --primary-light: #14B8A6;
        --secondary: #0F172A; /* Slate 900 */
        --surface: #FFFFFF;
        --background: #F8FAFC;
        --border: #E2E8F0;
        --text-main: #334155;
        --text-muted: #64748B;
    }
    
    /* Header design */
    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 40px 32px;
        border-radius: 12px;
        color: white;
        margin-bottom: 32px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        position: relative;
        overflow: hidden;
        border-left: 6px solid #14B8A6;
    }
    .app-header::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .app-header h1 {
        margin: 0;
        font-family: 'Inter', sans-serif;
        font-size: 36px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.5px;
    }
    .app-header p {
        margin: 10px 0 0 0;
        color: #94A3B8;
        font-size: 16px;
        font-weight: 400;
    }
    
    /* Custom style for Streamlit containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        padding: 0.5rem;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04) !important;
    }
    
    /* Streamlit Buttons styling to make them look premium */
    button[kind="primary"] {
        background-color: #0F766E !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: background-color 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        background-color: #0D9488 !important;
    }
    button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #334155 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        border-color: #CBD5E1 !important;
        background-color: #F8FAFC !important;
    }
    
    /* Transcription dialogue box styling */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin: 20px 0;
        padding: 24px;
        background-color: #F8FAFC;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        max-height: 500px;
        overflow-y: auto;
    }
    .chat-bubble {
        padding: 16px 20px;
        border-radius: 12px;
        max-width: 90%;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        line-height: 1.6;
        font-size: 15px;
        position: relative;
    }
    .bubble-1 {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 4px solid #22C55E;
        align-self: flex-start;
    }
    .bubble-2 {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-left: 4px solid #3B82F6;
        align-self: flex-start;
    }
    .bubble-generic {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #94A3B8;
        align-self: flex-start;
    }
    .bubble-meta {
        font-size: 12px;
        color: #64748B;
        margin-bottom: 8px;
        display: flex;
        gap: 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .bubble-speaker-1 {
        color: #166534;
    }
    .bubble-speaker-2 {
        color: #1E40AF;
    }
    .bubble-speaker-generic {
        color: #475569;
    }
    .bubble-text {
        color: #334155;
    }
    
    /* Uploaders and Expanders */
    .stFileUploader > div {
        border-radius: 12px;
    }
    
    /* Footer layout styling */
    .app-footer {
        text-align: center;
        padding: 24px;
        color: #94A3B8;
        font-size: 13px;
        margin-top: 48px;
        border-top: 1px solid #E2E8F0;
        font-weight: 500;
    }
    
    /* Make headers more clinical */
    h1, h2, h3, h4 {
        color: #0F172A;
        letter-spacing: -0.02em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Render login and stop if not authenticated
if not check_password():
    st.stop()

# Sidebar configuration with Navigation Menu
with st.sidebar:
    st.markdown("### 🩺 Portal Clínico")
    
    # Adicionado o menu de navegação aqui
    menu_selecionado = st.radio(
        "Navegação",
        ["🎙️ Gravação e Transcrição", "📄 Geração de Relatório"]
    )
    
    st.markdown("---")
    st.markdown("Bem-vindo ao sistema.")
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


# ==========================================
# PÁGINA 1: GRAVAÇÃO E TRANSCRIÇÃO (Seu código original)
# ==========================================
def pagina_gravacao():
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
        with st.container(border=True):
            st.markdown("### 📋 Diálogo da Consulta Processada")
            
            st.markdown("#### 🎧 Áudio Clínico Otimizado")
            with open(st.session_state["preprocessed_audio_path"], "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/wav")
                
            st.markdown("#### 💬 Transcrição de Vozes")
            
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    nome_orador1 = st.text_input("Nome do Orador 1", value="", placeholder="Ex: Dr. Carlos")
                with col2:
                    nome_orador2 = st.text_input("Nome do Orador 2", value="", placeholder="Ex: Paciente")
                    
            lbl_orador1 = nome_orador1.strip() if nome_orador1.strip() else "Orador 1"
            lbl_orador2 = nome_orador2.strip() if nome_orador2.strip() else "Orador 2"
            
            chat_html = '<div class="chat-container">'
            for line in st.session_state["transcription_text"].split("\n"):
                if not line.strip():
                    continue
                time_stamp, speaker, text_content = parse_line(line)
                
                if speaker and time_stamp:
                    if "SPEAKER_A" in speaker or "SPEAKER_0" in speaker:
                        chat_html += (
                            f'<div class="chat-bubble bubble-1">'
                            f'<div class="bubble-meta"><span class="bubble-speaker-1">{lbl_orador1}</span><span>⏱️ {time_stamp}</span></div>'
                            f'<div class="bubble-text">{text_content}</div>'
                            f'</div>'
                        )
                    elif "SPEAKER_B" in speaker or "SPEAKER_1" in speaker:
                        chat_html += (
                            f'<div class="chat-bubble bubble-2">'
                            f'<div class="bubble-meta"><span class="bubble-speaker-2">{lbl_orador2}</span><span>⏱️ {time_stamp}</span></div>'
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
            
            st.markdown(chat_html, unsafe_allow_html=True)
            
            col_audio, col_txt = st.columns(2)
            wav_filename = os.path.basename(st.session_state["preprocessed_audio_path"])
            txt_filename = os.path.basename(st.session_state["transcription_path"])
            
            with col_audio:
                with open(st.session_state["preprocessed_audio_path"], "rb") as audio_file:
                    st.download_button(
                        label="📥 Baixar Áudio (.wav)",
                        data=audio_file.read(),
                        file_name=wav_filename,
                        mime="audio/wav",
                        use_container_width=True,
                        type="primary"
                    )
                    
            with col_txt:
                with open(st.session_state["transcription_path"], "r", encoding="utf-8") as txt_file:
                    st.download_button(
                        label="📥 Baixar Transcrição (.txt)",
                        data=txt_file.read(),
                        file_name=txt_filename,
                        mime="text/plain",
                        use_container_width=True,
                        type="primary"
                    )
    else:
        st.info("Nenhuma consulta ativa no momento. Utilize o gravador acima para iniciar.")


# ==========================================
# PÁGINA 2: GERAÇÃO DE RELATÓRIO
# ==========================================
def pagina_geracao_relatorio():
    st.markdown("### 📄 Geração de Relatório Clínico")
    st.write("Faça o upload dos laudos em PDF e do áudio processado da consulta.")

    with st.container(border=True):
        pdfs_enviados = st.file_uploader("Upload de Exames/Laudos (PDF)", type=["pdf"], accept_multiple_files=True)
        
        usar_sessao = False
        if st.session_state.get("transcription_text"):
            usar_sessao = st.checkbox("Usar áudio e transcrição da gravação atual", value=True)
            
        audio_enviado = None
        if not usar_sessao:
            audio_enviado = st.file_uploader("Upload do Áudio da Consulta (.wav)", type=["wav", "mp3", "m4a"])

        if st.button("Gerar Relatório Clínico", type="primary", use_container_width=True):
            if not usar_sessao and not audio_enviado:
                st.warning("Por favor, envie o arquivo de áudio da consulta ou utilize a gravação atual.")
                return

            if usar_sessao:
                texto_transcricao = st.session_state["transcription_text"]
            else:
                with st.spinner("1/3 Transcrevendo o áudio..."):
                    # Como a função 'transcribe_audio' espera um caminho de arquivo,
                    # e o st.file_uploader entrega um objeto em memória (BytesIO),
                    # salvamos o arquivo temporariamente para a AssemblyAI processar.
                    temp_audio_path = os.path.join("gravacoes_temporarias", audio_enviado.name)
                    os.makedirs("gravacoes_temporarias", exist_ok=True)
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_enviado.getbuffer())
                    
                    texto_transcricao, _ = transcribe_audio(temp_audio_path)

            with st.spinner("2/3 Extraindo textos dos PDFs (via PyMuPDF e OCR)..."):
                texto_pdfs_combinado = ""
                for idx, pdf_file in enumerate(pdfs_enviados):
                    texto_extraido = extrair_texto_pdf(pdf_file.read())
                    texto_pdfs_combinado += f"\n--- Documento {idx+1} ---\n{texto_extraido}\n"

            with st.spinner("3/3 Analisando com Inteligência Artificial..."):
                st.session_state["relatorio_final"] = gerar_nota_clinica(texto_pdfs_combinado, texto_transcricao)
                st.success("✔️ Relatório gerado com sucesso!")
                
    if st.session_state.get("relatorio_final"):
        with st.container(border=True):
            st.markdown("#### Pré-visualização e Edição da Nota")
            st.info("Você pode editar o texto abaixo antes de baixar o documento. As alterações serão incluídas no arquivo final.")
            
            relatorio_editado = st.text_area(
                "Resultado", 
                value=st.session_state["relatorio_final"], 
                height=400, 
                label_visibility="collapsed"
            )
            
            with st.spinner("Preparando documento para download..."):
                docx_buffer = criar_docx_em_memoria(relatorio_editado)
            
            st.download_button(
                label="📥 Baixar Relatório (.docx)",
                data=docx_buffer,
                file_name="Nota_Clinica.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )


# ==========================================
# ROTEAMENTO (Controle de Exibição das Páginas)
# ==========================================
if menu_selecionado == "🎙️ Gravação e Transcrição":
    pagina_gravacao()
elif menu_selecionado == "📄 Geração de Relatório":
    pagina_geracao_relatorio()


# Simple professional footer
st.markdown(
    """
    <div class="app-footer">
        MedScribe — Sistema Restrito e Confidencial de Transcrição Clínica.
    </div>
    """,
    unsafe_allow_html=True
)