import streamlit as st
import pandas as pd
import math
import io

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Painel Executivo - Torre de Recalque",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. CSS ESTILIZAÇÃO
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Remove margens padrão */
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important; 
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }
    footer {visibility: hidden;}

    /* Fundo Dark */
    .stApp {
        background-color: #0E1117;
    }

    /* CARD DO PRODUTO (VITRINE) */
    .product-card {
        background-color: #1E1E1E;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        border: 1px solid #333;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: transform 0.2s;
    }
    .product-card:hover {
        transform: translateY(-5px);
        border-color: #FF4B4B;
    }
    
    .card-img-container {
        background-color: #FFFFFF;
        height: 180px;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px;
        border-bottom: 3px solid #FF4B4B;
    }
    
    .card-content {
        padding: 15px;
        color: white;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }

    /* Tipografia */
    .big-kpi {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .desc-text {
        color: #AAA; 
        font-size: 0.85rem; 
        font-style: italic; 
        margin-bottom: 8px;
        line-height: 1.2;
    }

    .price-badge {
        background-color: #262730;
        color: #4CAF50;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        float: right;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. FUNÇÕES DE DADOS E LÓGICA
# -----------------------------------------------------------------------------

# Função Avançada de Descrição
def get_auto_description(nome_componente):
    nome = str(nome_componente).lower()
    if 'contator' in nome: return "Dispositivo para manobra de altas cargas elétricas."
    if 'disjuntor' in nome: return "Proteção essencial contra curtos e sobrecargas."
    if 'relé' in nome or 'rele' in nome: return "Monitoramento, temporização ou proteção térmica."
    if 'sinaleiro' in nome or 'led' in nome: return "Indicador visual de status (Ligado/Falha)."
    if 'botão' in nome or 'botao' in nome: return "Interface de comando manual para operador."
    if 'chave' in nome: return "Seletor de modo (Manual/Automático/Desligado)."
    if 'borne' in nome: return "Ponto de conexão para fiação segura."
    if 'inversor' in nome: return "Controle preciso de velocidade para motores."
    if 'clp' in nome or 'plc' in nome: return "Controlador Lógico: O cérebro da automação."
    if 'fonte' in nome: return "Converte tensão para alimentar o comando (24Vcc)."
    if 'cabo' in nome or 'fio' in nome: return "Condutor elétrico para potência ou comando."
    if 'trilho' in nome or 'canaleta' in nome: return "Acessório para montagem e organização."
    return "Componente eletroeletrônico do painel."

@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = None
        # Tenta Excel
        try:
            df = pd.read_excel(uploaded_file, header=1, engine='openpyxl')
        except:
            pass
        # Tenta CSV (Latin-1)
        if df is None:
            try:
                df = pd.read_csv(uploaded_file, header=1, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', quotechar='"')
            except:
                pass
        # Tenta CSV (UTF-8)
        if df is None:
            try:
                df = pd.read_csv(uploaded_file, header=1, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            except:
                st.error("❌ Formato inválido.")
                return pd.DataFrame()

        if df is not None:
            # Limpeza de Colunas
            df.columns = df.columns.astype(str).str.strip().str.replace('"', '').str.upper()
            df = df.loc[:, ~df.columns.str.contains('^UNNAMED')]
            
            # Garante colunas mínimas
            cols_check = ['COMPONENTE', 'MODELO', 'FABRICANTE', 'TAG', 'PREÇO UNID']
            for col in cols_check:
                if col not in df.columns and col != 'PREÇO UNID': 
                    df[col] = "-"

            # Tratamento de Preço
            price_col = 'PREÇO UNID'
            if 'PREÇO POR UNIDADE' in df.columns: price_col = 'PREÇO POR UNIDADE'
            if 'PREÇO UNIT' in df.columns: price_col = 'PREÇO UNIT'
            
            def clean_price_value(val):
                if isinstance(val, (int, float)): return float(val)
                val_str = str(val).strip().replace('R$', '').strip()
                if ',' in val_str:
                    val_str = val_str.replace('.', '').replace(',', '.')
                try:
                    return float(val_str)
                except:
                    return 0.0

            if price_col in df.columns:
                df['PREÇO_NUM'] = df[price_col].apply(clean_price_value).fillna(0.0)
            else:
                df['PREÇO_NUM'] = 0.0

            # Quantidade
            col_qtd = 'QUANTIDADE' if 'QUANTIDADE' in df.columns else 'QTD'
            if col_qtd in df.columns:
                df['QTD_NUM'] = pd.to_numeric(df[col_qtd], errors='coerce').fillna(0)
            else:
                df['QTD_NUM'] = 1

            # Totalização
            df['TOTAL_LINHA'] = df['QTD_NUM'] * df['PREÇO_NUM']
            
            # Imagem Placeholder
            if 'IMAGEM' not in df.columns:
                df['IMAGEM'] = "https://via.placeholder.com/300?text=Sem+Imagem"
            
            # APLICA A DESCRIÇÃO AUTOMÁTICA
            df['DESCRICAO'] = df['COMPONENTE'].apply(get_auto_description)

            return df
    return None

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Orçamento')
    return output.getvalue()

# -----------------------------------------------------------------------------
# 4. INTERFACE DO USUÁRIO
# -----------------------------------------------------------------------------

# --- LÓGICA DE UPLOAD ---
# 1. Sidebar sempre disponível
st.sidebar.title("🎛️ Configuração")
sidebar_file = st.sidebar.file_uploader("Carregar Arquivo", type=["csv", "xlsx"], key="sidebar_upl")

# 2. Definição do arquivo ativo
uploaded_file = sidebar_file

# 3. Se NÃO tiver arquivo, mostra a tela inicial (Upload Grande)
if uploaded_file is None:
    # Centralização vertical usando container vazio
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    with col_center2:
        st.markdown("""
        <div style="text-align:center;">
            <div style="font-size: 5rem;">⚡</div>
            <h1 style="color:white;">Painel Executivo</h1>
            <p style="color:#888;">Carregue sua planilha de orçamento para começar.</p>
        </div>
        """, unsafe_allow_html=True)
        
        main_file = st.file_uploader("Arraste ou clique para selecionar", type=["csv", "xlsx"], key="main_upl")
        
        if main_file is not None:
            uploaded_file = main_file

# --- DASHBOARD (SÓ RODA SE TIVER ARQUIVO) ---
if uploaded_file:
    df = load_data(uploaded_file)
    
    if df is not None and not df.empty:
        # --- HEADER KPIS ---
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div style='color:#888'>CUSTO TOTAL</div><div class='big-kpi'>R$ {df['TOTAL_LINHA'].sum():,.2f}</div>", unsafe_allow_html=True)
        c2.metric("Total de Peças", int(df['QTD_NUM'].sum()))
        c3.metric("Modelos Únicos", len(df))
        c4.metric("Principal Fabricante", df['FABRICANTE'].mode()[0] if not df.empty else "-")
        
        st.markdown("---")

        # --- SELETOR DE ABAS ---
        mode = st.radio("Visualização:", ["Vitrine Visual", "Tabela Analítica", "Detalhe Técnico"], horizontal=True)
        st.write("") # Espaçamento

        # ---------------------------------------------------------------------
        # MODO 1: VITRINE (CORRIGIDO)
        # ---------------------------------------------------------------------
        if mode == "Vitrine Visual":
            # Filtro
            all_fabs = list(df['FABRICANTE'].unique())
            sel_fabs = st.multiselect("Filtrar por Fabricante:", all_fabs, default=all_fabs)
            df_view = df[df['FABRICANTE'].isin(sel_fabs)]

            # Grid System
            cols_per_row = 4
            rows = math.ceil(len(df_view) / cols_per_row)

            for i in range(rows):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    idx = i * cols_per_row + j
                    if idx < len(df_view):
                        row = df_view.iloc[idx]
                        
                        # --- HTML CORRIGIDO AQUI ---
                        # Removi divs extras e simplifiquei a estrutura para evitar erros
                       # CÓDIGO EM LINHA ÚNICA (BLINDADO CONTRA ERROS)
                        html_card = f"""<div class="product-card"><div class="card-img-container"><img src="{row['IMAGEM']}" style="max-height:100%; max-width:100%; object-fit:contain;"></div><div class="card-content"><div><span class="price-badge">R$ {row['PREÇO_NUM']:,.2f}</span><strong style="font-size:1.1rem; display:block; margin-bottom:5px;">{row['COMPONENTE'][:25]}</strong></div><div class="desc-text">{row['DESCRICAO']}</div><div style="font-size:0.8rem; color:#888; margin-top:auto;">{row['FABRICANTE']} | {row['MODELO']}</div><div style="color:#FF4B4B; font-size:0.9rem; font-weight:bold; margin-top:5px;">Qtd: {int(row['QTD_NUM'])} un.</div></div></div>"""
                        
                        with cols[j]:
                            st.markdown(html_card, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # MODO 2: TABELA (COM DESCRIÇÃO)
        # ---------------------------------------------------------------------
        elif mode == "Tabela Analítica":
            st.caption("Visão geral financeira e técnica dos componentes.")
            
            df_tab = df[['TAG', 'COMPONENTE', 'DESCRICAO', 'FABRICANTE', 'QTD_NUM', 'PREÇO_NUM', 'TOTAL_LINHA']].copy()
            df_tab = df_tab.sort_values(by='TOTAL_LINHA', ascending=False)
            
            # Configuração da Tabela
            st.dataframe(
                df_tab,
                use_container_width=True,
                height=600,
                hide_index=True,
                column_config={
                    "TAG": st.column_config.TextColumn("Tag", width="small"),
                    "COMPONENTE": st.column_config.TextColumn("Componente", width="medium"),
                    "DESCRICAO": st.column_config.TextColumn("Função Técnica", width="large"),
                    "FABRICANTE": "Marca",
                    "QTD_NUM": st.column_config.NumberColumn("Qtd", format="%d"),
                    "PREÇO_NUM": st.column_config.NumberColumn("Unitário", format="R$ %.2f"),
                    "TOTAL_LINHA": st.column_config.ProgressColumn(
                        "Custo Total", 
                        format="R$ %.2f", 
                        min_value=0, 
                        max_value=float(df_tab['TOTAL_LINHA'].max())
                    )
                }
            )

        # ---------------------------------------------------------------------
        # MODO 3: DETALHE TÉCNICO (LAYOUT MELHORADO)
        # ---------------------------------------------------------------------
        elif mode == "Detalhe Técnico":
            lista_itens = df['COMPONENTE'].unique()
            sel_item = st.selectbox("Pesquisar Componente:", lista_itens)
            
            # Filtra o item
            dados_item = df[df['COMPONENTE'] == sel_item].iloc[0]
            
            st.markdown("<br>", unsafe_allow_html=True) # Espaço
            
            # Layout Assimétrico: Imagem (Esq) vs Dados (Dir)
            col_img, col_info = st.columns([1, 1.5], gap="large")
            
            with col_img:
                st.markdown(f"""
                <div style="background:white; border-radius:15px; padding:20px; display:flex; justify-content:center; align-items:center; height:400px; box-shadow: 0 5px 15px rgba(0,0,0,0.5);">
                    <img src="{dados_item['IMAGEM']}" style="max-height:100%; max-width:100%; object-fit:contain;">
                </div>
                """, unsafe_allow_html=True)
                
            with col_info:
                # Título
                st.markdown(f"<h1 style='margin-top:0; font-size:2.5rem; line-height:1.2;'>{dados_item['COMPONENTE']}</h1>", unsafe_allow_html=True)
                
                # Descrição Técnica Destacada
                st.markdown(f"""
                <div style="background:rgba(76, 175, 80, 0.1); border-left:4px solid #4CAF50; padding:15px; border-radius:4px; margin: 15px 0;">
                    <strong style="color:#4CAF50;">FUNÇÃO TÉCNICA:</strong><br>
                    <span style="font-size:1.1rem; color:#DDD;">{dados_item['DESCRICAO']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Dados Técnicos
                c_a, c_b = st.columns(2)
                with c_a:
                    st.markdown("**Fabricante:**")
                    st.info(dados_item['FABRICANTE'])
                with c_b:
                    st.markdown("**Modelo / Referência:**")
                    st.info(dados_item['MODELO'])
                
                st.markdown(f"**Tags de Projeto:** `{dados_item['TAG']}`")
                
                # Bloco de Custo
                st.markdown("---")
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:#262730; padding:20px; border-radius:10px; border:1px solid #444;">
                    <div>
                        <div style="color:#888; font-size:0.9rem;">Preço Unitário</div>
                        <div style="font-size:1.5rem; font-weight:bold;">R$ {dados_item['PREÇO_NUM']:,.2f}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#888; font-size:0.9rem;">Quantidade</div>
                        <div style="font-size:1.5rem; font-weight:bold; color:#FF4B4B;">x {int(dados_item['QTD_NUM'])}</div>
                    </div>
                    <div style="text-align:right; border-left:1px solid #555; padding-left:20px;">
                        <div style="color:#4CAF50; font-size:0.9rem;">TOTAL</div>
                        <div style="font-size:2rem; font-weight:900; color:#4CAF50;">R$ {dados_item['TOTAL_LINHA']:,.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)