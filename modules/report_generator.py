import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
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
    """Gera um arquivo .docx em memória, formatado e pronto para download."""
    doc = Document()
    
    # Configurar fonte padrão para o documento inteiro (Aparência mais clínica/profissional)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    # Título centralizado
    titulo = doc.add_heading('Nota Clínica - MedScribe', level=1)
    titulo.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    doc.add_paragraph() # Espaço após o título
    
    # Processar o texto gerado pela IA linha por linha
    linhas = texto_relatorio.split('\n')
    
    for linha in linhas:
        linha_limpa = linha.strip()
        
        # Ignorar linhas completamente vazias para evitar buracos no documento
        if not linha_limpa:
            continue
            
        # REGRA 1: Se a linha começa com "-" ou "*", transforma em Bullet Point nativo do Word
        if linha_limpa.startswith('- ') or linha_limpa.startswith('* '):
            texto_bullet = linha_limpa[2:] # Remove o símbolo do texto
            p = doc.add_paragraph(style='List Bullet')
            _adicionar_run_com_negrito(p, texto_bullet)
            
        # REGRA 2: Se a linha for curta e terminar com ":", trata como um subtítulo de seção
        elif linha_limpa.endswith(':') and len(linha_limpa) < 60:
            p = doc.add_paragraph()
            p.add_run(linha_limpa).bold = True
            
        # REGRA 3: Texto normal (Processando possíveis negritos do Markdown)
        else:
            p = doc.add_paragraph()
            _adicionar_run_com_negrito(p, linha_limpa)
            
    # Salvar no buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _adicionar_run_com_negrito(paragrafo, texto: str):
    """Função auxiliar para traduzir o **negrito** do Markdown para o Word."""
    if '**' in texto:
        partes = texto.split('**')
        for i, parte in enumerate(partes):
            run = paragrafo.add_run(parte)
            # O texto que estava entre ** sempre cai nos índices ímpares após o split
            if i % 2 != 0: 
                run.bold = True
    else:
        paragrafo.add_run(texto)