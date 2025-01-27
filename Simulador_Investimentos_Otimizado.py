import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Função de autenticação usando Streamlit Secrets
def autenticar_usuario(usuario, senha):
    usuario_valido = st.secrets["general"]["USUARIO"]
    senha_valida = st.secrets["general"]["SENHA"]
    return usuario == usuario_valido and senha == senha_valida

# Tela de login
def tela_login():
    st.set_page_config(page_title="Simulador de Investimentos", layout="centered")

    # Layout centralizado para o título
    title_col1, title_col2, title_col3 = st.columns([1, 2, 1])
    with title_col2:
        st.title("Bem-vindo ao Simulador de Investimentos")

    # Layout centralizado para login
    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    with login_col2:
        st.subheader("Login")
        usuario = st.text_input("Usuário:", placeholder="Digite seu usuário", key="usuario")
        senha = st.text_input("Senha:", type="password", placeholder="Digite sua senha", key="senha")
        login_btn = st.button("Entrar")

    return usuario, senha, login_btn

# Função para calcular períodos dinâmicos com edição manual
def gerar_tabela_dinamica(valor_investido, taxa_margem, total_impostos, valor_meta, ajustes):
    historico = []
    periodo = 0
    margem_liquida_acumulada = 0

    while margem_liquida_acumulada < valor_meta:
        # Ajustar manualmente taxas para períodos específicos
        if periodo in ajustes:
            taxa_margem_atual = ajustes[periodo].get("taxa_margem", taxa_margem)
            total_impostos_atual = ajustes[periodo].get("total_impostos", total_impostos)
        else:
            taxa_margem_atual = taxa_margem
            total_impostos_atual = total_impostos

        margem_bruta = valor_investido * taxa_margem_atual
        margem_liquida = margem_bruta - (margem_bruta * total_impostos_atual)
        margem_liquida_acumulada += margem_liquida

        historico.append({
            "Período": periodo + 1,
            "Valor Investido (R$)": valor_investido,
            "Taxa Margem (%)": taxa_margem_atual * 100,
            "Margem Bruta (R$)": margem_bruta,
            "Total Impostos (%)": total_impostos_atual * 100,
            "Margem Líquida (R$)": margem_liquida,
            "Margem Líquida Acumulada (R$)": margem_liquida_acumulada
        })

        # Atualizar o valor investido com base na margem líquida
        valor_investido += margem_liquida
        periodo += 1

    return pd.DataFrame(historico), periodo

# Lógica principal do simulador de investimentos
def app_principal():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Simulador de Investimentos")
    st.write("""
    Este simulador permite prever os ganhos de investimento com base em diferentes modelos matemáticos.
    Ajuste os parâmetros abaixo para simular os cenários desejados e entender as diferenças entre as estratégias.
    """)

    # Entrada do usuário
    nome_empresa = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    valor_investido = st.number_input("Valor Inicial Investido (R$):", min_value=0.0)
    taxa_margem_inicial = st.number_input("Taxa Inicial de Margem (%):", min_value=0.0, max_value=100.0) / 100
    total_impostos_inicial = st.number_input("Taxa Inicial de Impostos (%):", min_value=0.0, max_value=100.0) / 100
    valor_meta = st.number_input("Meta de Margem Líquida Total (R$):", min_value=0.0)

    # Configurar ajustes manuais
    st.subheader("Ajustes Manuais")
    ajustes = {}
    num_ajustes = st.number_input("Número de Períodos para Ajustar Manualmente:", min_value=0, max_value=100, step=1, value=0)

    for i in range(num_ajustes):
        st.write(f"Ajuste para o Período {i + 1}")
        periodo_ajustado = st.number_input(f"Selecione o Período para Ajustar (1 a {num_ajustes}):", min_value=1, max_value=num_ajustes, step=1, value=i+1)
        taxa_margem_ajustada = st.number_input(f"Taxa de Margem para o Período {periodo_ajustado} (%):", min_value=0.0, max_value=100.0, value=taxa_margem_inicial * 100) / 100
        total_impostos_ajustado = st.number_input(f"Taxa de Impostos para o Período {periodo_ajustado} (%):", min_value=0.0, max_value=100.0, value=total_impostos_inicial * 100) / 100
        ajustes[periodo_ajustado - 1] = {"taxa_margem": taxa_margem_ajustada, "total_impostos": total_impostos_ajustado}

    if st.button("Gerar Simulação"):
        tabela, total_meses = gerar_tabela_dinamica(valor_investido, taxa_margem_inicial, total_impostos_inicial, valor_meta, ajustes)

        # Adicionar informações de empresa à tabela
        tabela["Nome da Empresa"] = nome_empresa
        tabela["CNPJ"] = cnpj

        st.subheader("Resultados da Simulação")
        st.dataframe(tabela)

        st.write(f"**Total de Meses Necessários para Atingir a Meta:** {total_meses} meses")

        # Exibir gráficos
        st.subheader("Evolução dos Investimentos")
        st.line_chart(tabela.set_index("Período")[
            ["Valor Investido (R$)", "Margem Líquida (R$)", "Margem Líquida Acumulada (R$)"]
        ])

        # Botão para exportar tabela para Excel
        buffer = BytesIO()
        tabela.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)

        st.download_button(
            label="Exportar para Excel",
            data=buffer,
            file_name="Simulacao_Investimentos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Execução principal
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    usuario, senha, login_btn = tela_login()
    if login_btn:
        if autenticar_usuario(usuario, senha):
            st.session_state["autenticado"] = True
            from streamlit.runtime.scriptrunner import RerunException, RerunData
            raise RerunException(RerunData(None))
        else:
            st.error("Usuário ou senha inválidos. Por favor, tente novamente.")
else:
    app_principal()