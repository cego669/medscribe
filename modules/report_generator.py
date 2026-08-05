import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import streamlit as st
from docx import Document
from htmldocx import HtmlToDocx
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
    """Primeira Camada: Consome os prompts dos secrets e gera o conteúdo clínico (Seu prompt original)."""
    system_instruction = st.session_state.get("sys_prompt_edit", st.secrets.get("SYSTEM_PROMPT", ""))
    user_prompt = st.session_state.get("user_prompt_edit", st.secrets.get("USER_PROMPT", ""))
    
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

def formatar_para_html(texto_cru: str) -> str:
    """Segunda Camada: Pega a resposta clínica e a transforma em HTML estruturado."""
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 1. Puxa as regras de formatação dos secrets
    instrucao_formatacao = st.session_state.get("formatter_prompt_edit", st.secrets.get("FORMATTER_PROMPT", ""))
    
    # 2. Concatena as regras com o laudo gerado na primeira camada
    prompt_formatacao = f"{instrucao_formatacao}\n\nTEXTO ORIGINAL:\n{texto_cru}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_formatacao,
            config=types.GenerateContentConfig(
                temperature=0.0, # Temperatura 0 para manter fidelidade estrita
            ),
        )
        # Limpeza preventiva caso a IA coloque blocos de código
        html_limpo = response.text.replace("```html", "").replace("```", "").strip()
        return html_limpo
    except Exception as e:
        st.error(f"Erro na formatação HTML: {e}")
        return texto_cru # Em caso de erro na IA de formatação, devolve o texto cru para não perder o laudo

def criar_docx_em_memoria(texto_relatorio: str) -> io.BytesIO:
    """Usa htmldocx para converter o HTML da IA em um .docx real."""
    
    # 1. Passa o texto clínico pelo formatador de HTML
    html_content = formatar_para_html(texto_relatorio)
    
    # 2. Inicializa o parser e converte direto para um objeto do Word
    doc = Document()
    new_parser = HtmlToDocx()
    new_parser.add_html_to_document(html_content, doc)
    
    # 3. Salva em memória
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer