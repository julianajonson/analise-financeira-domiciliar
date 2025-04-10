import streamlit as st
import pdfplumber
import os
import json 
from openai import OpenAI
import matplotlib.pyplot as plt
import pandas as pd
from graficos_utils import exibir_graficos, plota_graficos_categ
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
Você um assistente financeiro. 
Eu vou te mandar uma string do meu extrato financeiro. 
A sua função é diferenciar e extrair os valores gastos com 
as suas descrições, assim como os valores recebidos e suas descrições. 
Valores gastos tem como palavras chave (pagamento, enviado ou compra). 
Você vai me retornar em JSON.

Este é um exemplo de saída esperado:
{
    "gastos":[
    {
        "descrição": "descrição do gasto",
        "valor": valor do gasto
    }],
    "recebimentos":[
    {
        "descrição": "descrição do recebimento",
        "valor": "valor do recebimento"
    }]
}
"""
PROMPT2 = """"
    Aqui estão extratos bancários no formato JSON: {data_json}. 
    Utilize esses dados para categorizar cada transação em categorias de acordo com a descrição.
    As categorias devem ser divididas em  "alimentação", "saúde", "educação", "mercado", "lazer", "pet", e o que nao se encaixar nessas, inclua na categoria "outras". 
    Traga a chave como "transações"
    Por favor, mantenha o tipo de cada transação (gastos ou recebimentos) na resposta, e nao altere a descrição original dos dados. 
    A categoria dos recebimentos é "salário".
    """

def processa_extrato(uploaded_files):
    """
    Processa uma lista de arquivos de extrato em PDF.
    Para cada arquivo, extrai o texto completo e, em seguida, converte em
    DataFrames de total, gastos e recebimentos.

    Args:
        uploaded_files (list[file-like]): Lista de objetos de arquivo PDF enviados.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] ou None:
            - df_total: concatenação de gastos e recebimentos.
            - df_gastos: DataFrame apenas com as transações de gasto.
            - df_recebimentos: DataFrame apenas com as transações de recebimento.
            Se não houver arquivos válidos, retorna None.
    """
    extrato_completo = recebe_extrato(uploaded_files)
    df_total, df_gastos, df_recebimentos = le_extrato(extrato_completo)
    if not extrato_completo:
        st.error("Extrato vazio ou inválido!")
        return None
    else:
        return df_total, df_gastos, df_recebimentos

def recebe_extrato(uploaded_files):
    """
    Lê uma lista de arquivos PDF e extrai todo o texto concatenado.

    Args:
        uploaded_files (list[file-like]): Lista de objetos de arquivo PDF.

    Returns:
        Texto completo extraído de todos os PDFs."""
  
    if uploaded_files: 
        extrato_completo = ""
        for uploaded_file in uploaded_files:        
            with pdfplumber.open(uploaded_file) as pdf:
                extrato = ""
                with st.spinner(f"Processando {uploaded_file.name}..."):
                    paginas = pdf.pages  
                    for pagina in paginas:
                        st.write(f"Carregando Página {pagina.page_number}")  
                        extrato += pagina.extract_text()
                extrato_completo += extrato
        return extrato_completo
    
def le_extrato(extrato_completo: str):
    """Converte o texto do extrato em DataFrames de gastos e recebimentos
    usando um modelo de linguagem (GPT).

    Args:
        extrato_completo (str): Texto bruto extraído dos PDFs.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] ou None:
            - df_total: concatenação de gastos e recebimentos.
            - df_gastos: DataFrame de transações de gasto.
            - df_recebimentos: DataFrame de transações de recebimento.
            Se extrato_completo for vazio ou None, retorna None."""

    if extrato_completo:
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            temperature=0.0,
            response_format= {"type": "json_object"},
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": extrato_completo}
            ]
        )
        msg = completion.choices[0].message.content
        print(msg)
        data_gpt = json.loads(msg)

        # transformando em data frame 
        df_gastos = pd.DataFrame(data_gpt["gastos"])
        df_recebimentos = pd.DataFrame(data_gpt["recebimentos"])

        df_gastos["tipo"] = "gastos"
        df_recebimentos["tipo"] = "recebimentos"

        df_total = pd.concat([df_gastos, df_recebimentos], ignore_index=True)
        df_total = df_total.dropna(subset=['valor'])

        return df_total, df_gastos, df_recebimentos
    else:
        return None

def categoriza_extrato (data_json):
    """
    Classifica as transações de um extrato em categorias definidas
    usando um modelo de linguagem (GPT).

    Args:
        data_json (dict ou list): JSON com transações já extraídas.

    Returns:
        JSON retornado pelo modelo contendo as transações
        com a categoria atribuída.
    """
    if data_json:
        client = OpenAI()
        completion = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        temperature=0.0,
        response_format= {"type": "json_object"},
        messages=[
            {"role": "user", "content": PROMPT2},
            {"role": "user", "content": data_json}
        ]
    )
    msg = completion.choices[0].message.content
    data_gpt2 = json.loads(msg)
    print(data_gpt2)
    return data_gpt2

def categorias_agrupadas(data_gpt2):
    """
    Agrupa transações por categoria e soma seus valores, excluindo 'salário'.

    Args:
        data_gpt2 (dict ou list): JSON com transações categorizadas.

    Returns:
        pd.Series: Série Pandas com o total de gastos por categoria.
    """
    if data_gpt2:
        df_categoria = pd.DataFrame(data_gpt2)    
        df_normalized = pd.json_normalize(df_categoria['transações'])
        df_cat_gast = df_normalized[df_normalized['categoria'] != 'salário']
        df_agg = df_cat_gast.groupby('categoria')['valor'].sum()
    st.write("Transações Categorizadas:")

    return df_agg

 

#### INICIO DE EXECUÇÃO SCRIPT PRINCIPAL ######

st.title("Análise Financeira")

# Título da aplicação
st.title("Upload de múltiplos PDFs")

uploaded_files = st.file_uploader("Escolha seus PDFs", key = "uploader_1", accept_multiple_files = True, type= "pdf")
if uploaded_files:

    df_total, df_gastos, df_recebimentos = processa_extrato(uploaded_files)
    exibir_graficos(df_total, df_gastos)

    data_json = df_total.to_json(orient='records')
    data_gpt2= categoriza_extrato(data_json)
    df_agg = categorias_agrupadas(data_gpt2)
    plota_graficos_categ(df_agg)
