import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import streamlit as st
from docx import Document
from google import genai
from google.genai import types

def extrair_texto_pdf(arquivo_bytes) -> str:
    """Extrai texto do PDF em memória. Usa OCR se o texto nativo for insuficiente."""
    texto_completo = ""
    try:
        # Abre o PDF diretamente da memória
        doc = fitz.open(stream=arquivo_bytes, filetype="pdf")
        for pagina in doc:
            texto_pagina = pagina.get_text("text")
            
            # Se a página tiver menos de 100 caracteres, assume que é imagem/scan e aplica OCR
            if not texto_pagina or len(texto_pagina.strip()) < 100:
                pix = pagina.get_pixmap(dpi=300)
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                texto_completo += pytesseract.image_to_string(img, lang='por') + "\n"
            else:
                texto_completo += texto_pagina + "\n"
        doc.close()
    except Exception as e:
        st.error(f"Erro ao processar PDF: {e}")
    
    return texto_completo.strip()

def gerar_nota_clinica(texto_pdfs: str, texto_transcricao: str) -> str:
    """Consome os prompts dos secrets e envia para o Gemini."""
    system_instruction = st.secrets["SYSTEM_PROMPT"]
    user_prompt = st.secrets["USER_PROMPT"]
    
    prompt_final = f"{user_prompt}\n\nEis os documentos (Laudos/Exames):\n{texto_pdfs}\n\nEis a transcrição da consulta:\n{texto_transcricao}"
    
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_final,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=8192,
            ),
        )
        return response.text
    except Exception as e:
        st.error(f"Erro na comunicação com o Gemini: {e}")
        return ""

def criar_docx_em_memoria(texto_relatorio: str) -> io.BytesIO:
    """Gera um arquivo .docx em memória pronto para download."""
    doc = Document()
    doc.add_heading('Consulta', level=1)
    doc.add_paragraph(texto_relatorio)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer