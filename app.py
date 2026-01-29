import streamlit as st
from fpdf import FPDF
import re
import tempfile

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerador de Relatórios", page_icon="📄")

st.title("📄 Gerador de Relatórios Faturamento")
st.write("Faça upload dos arquivos `.TXT` e baixe os PDFs.")

# --- CLASSE PDF MELHORADA ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'RELATÓRIO DE DADOS PROCESSADOS', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, self.safe_text(label), 0, 1, 'L', 1)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, self.safe_text(body))
        self.ln(3)
    
    def safe_text(self, text):
        # Esta função evita que o PDF trave com acentos
        return text.encode('latin-1', 'replace').decode('latin-1')

# --- EXTRAÇÃO DE DADOS ---
def extrair_dados(texto_completo):
    dados = {
        "nome": "NÃO ENCONTRADO",
        "valor": "0,00",
        "competencia": "N/D",
        "nascimento": "N/D",
        "codigo": "N/D"
    }

    try:
        # Datas
        datas = re.findall(r'\d{2}/\d{2,4}', texto_completo)
        for d in datas:
            if len(d) == 7: dados['competencia'] = d
            elif len(d) == 10 and '2026' not in d: dados['nascimento'] = d

        # Nome
        match_nome = re.search(r'[A-Z\s]{10,}', texto_completo)
        if match_nome: dados['nome'] = match_nome.group(0).strip()

        # Valor
        match_valor = re.search(r'0{5,}(\d+)', texto_completo)
        if match_valor:
            valor_bruto = int(match_valor.group(1))
            dados['valor'] = f"R$ {valor_bruto/100:,.2f}".replace('.', ',')

        # Código
        match_cod = re.search(r'[0-9]X[0-9A-Z]{3}', texto_completo)
        if match_cod: dados['codigo'] = match_cod.group(0)
    
    except Exception as e:
        return dados # Retorna o que conseguiu encontrar

    return dados

# --- LÓGICA DO APP ---
uploaded_files = st.file_uploader("Arraste seus arquivos TXT aqui", type=["txt"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            # Tenta ler o arquivo
            string_data = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            
            # Processa
            dados = extrair_dados(string_data)
            
            # Mostra Resultado
            st.success(f"Processado: {dados['nome']}")
            
            # Gera PDF
            pdf = PDF()
            pdf.add_page()
            pdf.chapter_title(f'Arquivo: {uploaded_file.name}')
            pdf.chapter_body(f"Extração automática.")
            
            pdf.chapter_title('Dados do Cliente')
            pdf.chapter_body(f"Nome: {dados['nome']}\nNasc: {dados['nascimento']}\nCod: {dados['codigo']}")
            
            pdf.chapter_title('Financeiro')
            pdf.chapter_body(f"Ref: {dados['competencia']}\nValor: {dados['valor']}")

            # Salva temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Baixar PDF ({dados['nome']})",
                        data=f,
                        file_name=f"Relatorio_{dados['nome']}.pdf",
                        mime="application/pdf"
                    )
        
        except Exception as e:
            st.error(f"Erro ao processar arquivo {uploaded_file.name}: {e}")
