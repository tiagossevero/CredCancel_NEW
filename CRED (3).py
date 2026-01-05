import streamlit as st
import hashlib

# DEFINA A SENHA AQUI
SENHA = "tsevero456"  # ← TROQUE para cada projeto

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("<div style='text-align: center; padding: 50px;'><h1>🔐 Acesso Restrito</h1></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            senha_input = st.text_input("Digite a senha:", type="password", key="pwd_input")
            if st.button("Entrar", use_container_width=True):
                if senha_input == SENHA:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta")
        st.stop()

check_password()


# =============================================================================
# 1. IMPORTS E CONFIGURAÇÕES INICIAIS
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import warnings
import ssl

# Configuração SSL
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="CRED-CANCEL v2.0 - Análise de Créditos ICMS",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. FUNÇÃO AUXILIAR PARA FORMATAR CNPJ
# =============================================================================

def formatar_cnpj(cnpj):
    """
    Garante que CNPJ tenha 14 dígitos, preenchendo zeros à esquerda.
    Retorna também versão formatada (00.000.000/0000-00).
    """
    cnpj_14 = limpar_cnpj(cnpj)
    
    if cnpj_14 is None:
        return None, None
    
    # Formata: 00.000.000/0000-00
    cnpj_formatado = f"{cnpj_14[:2]}.{cnpj_14[2:5]}.{cnpj_14[5:8]}/{cnpj_14[8:12]}-{cnpj_14[12:14]}"
    
    return cnpj_14, cnpj_formatado
    
# =============================================================================
# 2. FUNÇÃO AUXILIAR PARA OBTER COLUNAS CORRETAS
# =============================================================================

def get_col_name(base_name, periodo='12m'):
    """
    Retorna o nome da coluna correto baseado no período.
    
    Args:
        base_name: Nome base da coluna (ex: 'score_risco', 'media_credito')
        periodo: '12m', '60m' ou 'comparativo'
    
    Returns:
        String com nome correto da coluna
    """
    # Mapa de colunas que mudaram
    colunas_periodo = {
        'score_risco': f'score_risco_{periodo}',
        'classificacao_risco': f'classificacao_risco_{periodo}',
        'score_risco_combinado': f'score_risco_combinado_{periodo}',
        'classificacao_risco_combinado': f'classificacao_risco_combinado_{periodo}',
        'valor_igual_total_periodos': f'valor_igual_total_periodos_{periodo}',
        'qtde_ultimos_meses_iguais': 'qtde_ultimos_12m_iguais',  # Sempre 12m
        'media_credito': f'media_credito_{periodo}',
        'min_credito': f'min_credito_{periodo}',
        'max_credito': f'max_credito_{periodo}',
        'desvio_padrao_credito': f'desvio_padrao_credito_{periodo}',
        'qtde_meses_declarados': f'qtde_meses_declarados_{periodo}',
        'crescimento_saldo_percentual': f'crescimento_saldo_percentual_{periodo}',
        'crescimento_saldo_absoluto': f'crescimento_saldo_absoluto_{periodo}',
        'vl_credito_presumido': f'vl_credito_presumido_{periodo}',
        'qtde_tipos_cp': f'qtde_tipos_cp_{periodo}',
        'saldo_atras': f'saldo_{periodo}_atras'
    }
    
    # Se não está no mapa, retorna o nome original
    return colunas_periodo.get(base_name, base_name)
    
# =============================================================================
# 3. ESTILOS CSS CUSTOMIZADOS
# =============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1565c0;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    /* ESTILO DOS GRÁFICOS (PLOTLY) */
    div[data-testid="stPlotlyChart"] {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        background-color: #ffffff;
    }
    
    /* ESTILO DOS KPIs - BORDA PRETA */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #2c3e50;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetric"] > label {
        font-weight: 600;
        color: #2c3e50;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-critico {
        background-color: #ffebee;
        border-left: 5px solid #c62828;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-alto {
        background-color: #fff3e0;
        border-left: 5px solid #ef6c00;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-positivo {
        background-color: #e8f5e9;
        border-left: 5px solid #2e7d32;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-extremo {
        background-color: #3d0000;
        border-left: 5px solid #ff0000;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stDataFrame {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 4. FUNÇÕES DE CONEXÃO E CARREGAMENTO
# =============================================================================

IMPALA_HOST = 'bdaworkernode02.sef.sc.gov.br'
IMPALA_PORT = 21050
DATABASE = 'teste'

IMPALA_USER = st.secrets.get("impala_credentials", {}).get("user", "tsevero")
IMPALA_PASSWORD = st.secrets.get("impala_credentials", {}).get("password", "")

@st.cache_resource
def get_impala_engine():
    """Cria engine de conexão Impala."""
    try:
        engine = create_engine(
            f'impala://{IMPALA_HOST}:{IMPALA_PORT}/{DATABASE}',
            connect_args={
                'user': IMPALA_USER,
                'password': IMPALA_PASSWORD,
                'auth_mechanism': 'LDAP',
                'use_ssl': True
            }
        )
        return engine
    except Exception as e:
        st.sidebar.error(f"Erro na conexão: {str(e)[:100]}")
        return None

def limpar_cnpj(cnpj):
    """
    Limpa e padroniza CNPJ para 14 dígitos.
    Trata problemas de float, notação científica e zeros.
    """
    if pd.isna(cnpj) or cnpj is None:
        return None
    
    # Se for float ou int, converter para string sem notação científica
    if isinstance(cnpj, (int, float)):
        # Usar format para evitar notação científica
        cnpj_str = format(int(cnpj), 'd')
    else:
        cnpj_str = str(cnpj)
    
    # Remover .0 se existir (caso venha como "12345678000190.0")
    if '.' in cnpj_str:
        cnpj_str = cnpj_str.split('.')[0]
    
    # Remover tudo que não é dígito
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj_str))
    
    # Se estiver vazio, retornar None
    if not cnpj_limpo:
        return None
    
    # Se tiver mais de 14 dígitos, provavelmente tem lixo no final
    # CNPJs válidos têm no máximo 14 dígitos
    if len(cnpj_limpo) > 14:
        cnpj_limpo = cnpj_limpo[:14]
    
    # Preencher zeros à esquerda até 14 dígitos
    cnpj_14 = cnpj_limpo.zfill(14)
    
    return cnpj_14
    
@st.cache_data(ttl=3600)
def carregar_dados_creditos(_engine):
    """Carrega dados das tabelas DIME - VERSÃO OTIMIZADA."""
    dados = {}
    
    if _engine is None:
        return {}
    
    try:
        with _engine.connect() as conn:
            st.sidebar.success("Conexão Impala OK!")
    except Exception as e:
        st.sidebar.error(f"Falha na conexão: {str(e)[:100]}")
        return {}
    
    # ✅ COLUNAS ESSENCIAIS - Reduz de 100+ para ~35 colunas
    colunas_essenciais = """
        nu_cnpj, nm_razao_social, nm_fantasia, nm_sit_cadastral, 
        nm_gerfe, de_cnae, nu_cnpj_grupo,
        saldo_credor_atual, saldo_12m_atras, saldo_60m_atras,
        score_risco_12m, score_risco_60m,
        score_risco_combinado_12m, score_risco_combinado_60m,
        classificacao_risco_12m, classificacao_risco_60m,
        classificacao_risco_combinado_12m, classificacao_risco_combinado_60m,
        qtde_ultimos_12m_iguais,
        crescimento_saldo_percentual_12m, crescimento_saldo_percentual_60m,
        media_credito_12m, media_credito_60m,
        desvio_padrao_credito_12m, desvio_padrao_credito_60m,
        vl_credito_presumido_12m, vl_credito_presumido_60m,
        flag_empresa_suspeita, qtde_indicios_fraude, sn_cancelado_inex_inativ,
        score_suspeita, cd_situacao_suspeita, qt_motivos,
        flag_tem_declaracoes_zeradas, flag_tem_omissoes,
        qt_clientes_noteiras, qt_fornecedoras_noteiras,
        periodos_zerados_normal, periodos_zerados_simples,
        periodos_omissos_normal, periodos_omissos_simples,
        flag_omissao_dime_normal, flag_omissao_pgdas_simples
    """
    
    st.sidebar.write("Carregando dados:")
    
    # ✅ CARREGAR TABELA PRINCIPAL COM FILTRO
    try:
        st.sidebar.write("📊 Carregando credito_dime_completo...")
        
        query = f"""
            SELECT {colunas_essenciais}
            FROM {DATABASE}.credito_dime_completo
            WHERE saldo_credor_atual > 0
               OR flag_empresa_suspeita = 1
               OR qtde_indicios_fraude > 0
        """
        
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Limpar CNPJs
        if 'nu_cnpj' in df.columns:
            df['nu_cnpj'] = df['nu_cnpj'].apply(limpar_cnpj)
            df['nu_cnpj_formatado'] = df['nu_cnpj'].apply(
                lambda x: f"{x[:2]}.{x[2:5]}.{x[5:8]}/{x[8:12]}-{x[12:14]}" if x and len(x) == 14 else x
            )
        
        if 'nu_cnpj_grupo' in df.columns:
            df['nu_cnpj_grupo'] = df['nu_cnpj_grupo'].apply(limpar_cnpj)
        
        dados['completo'] = df
        st.sidebar.success(f"  ✓ {len(df):,} empresas carregadas")
        
    except Exception as e:
        st.sidebar.error(f"❌ Erro: {str(e)[:100]}")
        dados['completo'] = pd.DataFrame()
    
    # ✅ TABELAS SETORIAIS: NÃO CARREGAR AUTOMATICAMENTE
    # Serão carregadas sob demanda na página de análise setorial
    dados['textil'] = pd.DataFrame()
    dados['metalmec'] = pd.DataFrame()
    dados['tech'] = pd.DataFrame()
    
    st.sidebar.write("---")
    st.sidebar.write(f"📋 Total: {len(dados.get('completo', [])):,} registros")
    
    return dados

@st.cache_data(ttl=3600)
def carregar_dados_setorial(_engine, setor):
    """Carrega dados de um setor específico sob demanda."""
    
    tabelas_setor = {
        'textil': 'credito_dime_textil',
        'metalmec': 'credito_dime_metalmec',
        'tech': 'credito_dime_tech'
    }
    
    flags_setor = {
        'textil': 'flag_setor_textil',
        'metalmec': 'flag_setor_metalmec',
        'tech': 'flag_setor_tech'
    }
    
    if setor not in tabelas_setor:
        return pd.DataFrame()
    
    try:
        query = f"""
            SELECT *
            FROM {DATABASE}.{tabelas_setor[setor]}
            WHERE {flags_setor[setor]} = 1
        """
        
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower().strip() for col in df.columns]
        
        if 'nu_cnpj' in df.columns:
            df['nu_cnpj'] = df['nu_cnpj'].apply(limpar_cnpj)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar setor {setor}: {str(e)[:100]}")
        return pd.DataFrame()
        
# =============================================================================
# 5. FUNÇÕES DE PROCESSAMENTO E CÁLCULOS
# =============================================================================

def calcular_kpis_gerais(df, periodo='12m'):
    """Calcula KPIs principais do sistema."""
    if df.empty:
        return {k: 0 for k in ['total_empresas', 'total_grupos', 'saldo_total', 
                                'score_medio', 'score_combinado_medio', 'criticos', 'altos',
                                'congelados_12m', 'crescimento_medio', 'cp_total',
                                'empresas_suspeitas', 'empresas_canceladas', 
                                'empresas_5plus_indicios']}
    
    # ✅ Obter nomes corretos das colunas
    col_score = get_col_name('score_risco', periodo)
    col_classificacao = get_col_name('classificacao_risco', periodo)
    col_crescimento = get_col_name('crescimento_saldo_percentual', periodo)
    col_cp = get_col_name('vl_credito_presumido', periodo)
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    
    kpis = {
        'total_empresas': df['nu_cnpj'].nunique(),
        'total_grupos': df['nu_cnpj_grupo'].nunique() if 'nu_cnpj_grupo' in df.columns else 0,
        'saldo_total': float(df['saldo_credor_atual'].sum()),
        'score_medio': float(df[col_score].mean()) if col_score in df.columns else 0,
        'criticos': len(df[df[col_classificacao] == 'CRÍTICO']) if col_classificacao in df.columns else 0,
        'altos': len(df[df[col_classificacao] == 'ALTO']) if col_classificacao in df.columns else 0,
        'congelados_12m': len(df[df['qtde_ultimos_12m_iguais'] >= 12]),
        'crescimento_medio': float(df[col_crescimento].mean()) if col_crescimento in df.columns else 0,
        'cp_total': float(df[col_cp].sum()) if col_cp in df.columns else 0
    }
    
    # Score combinado
    if col_score_comb in df.columns:
        kpis['score_combinado_medio'] = float(df[col_score_comb].mean())
    else:
        kpis['score_combinado_medio'] = 0
    
    # Campos de enriquecimento (não mudaram)
    if 'flag_empresa_suspeita' in df.columns:
        kpis['empresas_suspeitas'] = len(df[df['flag_empresa_suspeita'] == 1])
    else:
        kpis['empresas_suspeitas'] = 0
    
    if 'sn_cancelado_inex_inativ' in df.columns:
        kpis['empresas_canceladas'] = len(df[df['sn_cancelado_inex_inativ'] == 1])
    else:
        kpis['empresas_canceladas'] = 0
    
    if 'qtde_indicios_fraude' in df.columns:
        kpis['empresas_5plus_indicios'] = len(df[df['qtde_indicios_fraude'] >= 5])
    else:
        kpis['empresas_5plus_indicios'] = 0
    
    return kpis

def calcular_estatisticas_setoriais(dados, filtros, engine):
    """Calcula estatísticas dos 3 setores - carrega sob demanda."""
    setores = []
    
    periodo = filtros.get('periodo', '12m')
    col_score = get_col_name('score_risco', periodo)
    col_class = get_col_name('classificacao_risco', periodo)
    
    for setor_key, setor_nome, flag_col in [
        ('textil', 'TÊXTIL', 'flag_setor_textil'),
        ('metalmec', 'METAL-MECÂNICO', 'flag_setor_metalmec'),
        ('tech', 'TECNOLOGIA', 'flag_setor_tech')
    ]:
        # ✅ Carregar sob demanda se não estiver em cache
        df = dados.get(setor_key, pd.DataFrame())
        
        if df.empty:
            with st.spinner(f"Carregando dados {setor_nome}..."):
                df = carregar_dados_setorial(engine, setor_key)
                dados[setor_key] = df  # Atualiza o cache local
        
        if df.empty:
            continue
        
        # Filtrar por flag do setor
        if flag_col in df.columns:
            df_ativo = df[df[flag_col] == 1]
        else:
            df_ativo = df
        
        if df_ativo.empty:
            continue
        
        setor_info = {
            'Setor': setor_nome,
            'Empresas': df_ativo['nu_cnpj'].nunique(),
            'Saldo Total': float(df_ativo['saldo_credor_atual'].sum()),
            'Score Médio': float(df_ativo[col_score].mean()) if col_score in df_ativo.columns else 0,
            'Críticos': len(df_ativo[df_ativo[col_class] == 'CRÍTICO']) if col_class in df_ativo.columns else 0,
            'Congelados 12m+': len(df_ativo[df_ativo['qtde_ultimos_12m_iguais'] >= 12])
        }
        
        if 'flag_empresa_suspeita' in df_ativo.columns:
            setor_info['Suspeitas'] = len(df_ativo[df_ativo['flag_empresa_suspeita'] == 1])
        
        setores.append(setor_info)
    
    return pd.DataFrame(setores)

def calcular_score_ml(df, periodo='12m', peso_score=0.4, peso_saldo=0.3, peso_estagnacao=0.3):
    """Calcula score de Machine Learning para priorização."""
    df = df.copy()
    
    col_score = get_col_name('score_risco', periodo)
    
    df['score_norm'] = (df[col_score] / df[col_score].max() * 100) if col_score in df.columns else 0
    df['saldo_norm'] = (df['saldo_credor_atual'] / df['saldo_credor_atual'].max() * 100)
    df['estagnacao_norm'] = (df['qtde_ultimos_12m_iguais'] / 13 * 100)
    
    df['score_ml'] = (
        df['score_norm'] * peso_score +
        df['saldo_norm'] * peso_saldo +
        df['estagnacao_norm'] * peso_estagnacao
    )
    
    df['nivel_alerta_ml'] = pd.cut(
        df['score_ml'],
        bins=[0, 30, 50, 70, 85, 100],
        labels=['BAIXO', 'MÉDIO', 'ALTO', 'CRÍTICO', 'EMERGENCIAL']
    )
    
    return df

# =============================================================================
# 6. FUNÇÕES DE FILTROS
# =============================================================================

def criar_filtros_sidebar(dados):
    """Cria painel de filtros na sidebar."""
    filtros = {}
    
    # CONTEXTO DA ANÁLISE
    with st.sidebar.expander("🎯 Contexto da Análise", expanded=True):
        st.markdown("**Selecione o objetivo da análise:**")
        
        contexto = st.radio(
            "Tipo de Análise:",
            [
                "📋 Cancelamento de IE",
                "💰 Verificação de Saldos Credores",
                "🔄 Ambos (Cancelamento + Saldos)"
            ],
            index=0,
            help="Define o foco da análise e adapta os indicadores e filtros"
        )
        
        if "Cancelamento" in contexto and "Ambos" not in contexto:
            filtros['contexto'] = 'cancelamento'
            st.info("🎯 **Foco:** Identificar empresas para cancelamento de IE")
        elif "Saldos" in contexto and "Ambos" not in contexto:
            filtros['contexto'] = 'saldos_credores'
            st.success("💰 **Foco:** Analisar saldos credores acumulados")
        else:
            filtros['contexto'] = 'ambos'
            st.warning("🔄 **Foco:** Análise combinada")
        
        if filtros['contexto'] == 'cancelamento':
            st.caption("✓ Empresas inativas ou sem movimentação")
            st.caption("✓ CNAEs indevidos")
            st.caption("✓ Omissão de declarações")
        elif filtros['contexto'] == 'saldos_credores':
            st.caption("✓ Créditos acumulados sem débitos")
            st.caption("✓ Crescimento anormal de saldos")
            st.caption("✓ Empresas com estagnação")
        else:
            st.caption("✓ Análise completa de todos os indicadores")

    # ✅ NOVO: SELETOR DE PERÍODO DE ANÁLISE
    with st.sidebar.expander("📅 Período de Análise", expanded=True):
        st.markdown("**Selecione o período base para análise:**")
        
        periodo_analise = st.radio(
            "Análise baseada em:",
            [
                "📊 12 meses (Recente)",
                "📈 60 meses (Histórico)",
                "🔄 Comparativo (12m vs 60m)"
            ],
            index=0,
            help="Define qual período será usado para scores e indicadores"
        )
        
        if "12 meses" in periodo_analise:
            filtros['periodo'] = '12m'
            st.info("🎯 **Período:** Out/2024 a Set/2025")
        elif "60 meses" in periodo_analise:
            filtros['periodo'] = '60m'
            st.success("📊 **Período:** Set/2020 a Set/2025")
        else:
            filtros['periodo'] = 'comparativo'
            st.warning("🔄 **Modo:** Análise comparativa dos dois períodos")
    
    with st.sidebar.expander("Filtros Globais", expanded=True):
        
        filtros['classificacoes'] = st.multiselect(
            "Classificações de Risco",
            ['CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO'],
            default=['CRÍTICO', 'ALTO', 'MÉDIO', 'BAIXO']
        )
        
        filtros['saldo_minimo'] = st.number_input(
            "Saldo Credor Mínimo (R$)",
            min_value=0,
            max_value=10000000,
            value=0,
            step=10000,
            format="%d"
        )
        
        filtros['meses_iguais_min'] = st.slider(
            "Meses Estagnados (mínimo)",
            min_value=0,
            max_value=60,
            value=0
        )
        
        df_completo = dados.get('completo', pd.DataFrame())
        if not df_completo.empty and 'nm_gerfe' in df_completo.columns:
            gerfes = ['TODAS'] + sorted(df_completo['nm_gerfe'].dropna().unique().tolist())
            filtros['gerfe'] = st.selectbox("GERFE", gerfes)
        
        st.divider()
        
        st.subheader("⚠️ Filtros de Fraude")
        
        filtros['apenas_suspeitas'] = st.checkbox("Apenas empresas suspeitas", value=False)
        filtros['apenas_canceladas'] = st.checkbox("Apenas canceladas/inexistentes", value=False)
        filtros['min_indicios'] = st.slider("Indícios de fraude (mínimo)", 0, 15, 0)
        filtros['apenas_zeradas'] = st.checkbox("Com declarações zeradas", value=False)
        filtros['apenas_omissas'] = st.checkbox("Com omissões", value=False)
        
        st.divider()
        
        st.subheader("Visualização")
        filtros['tema'] = st.selectbox(
            "Tema dos Gráficos",
            ["plotly", "plotly_white", "plotly_dark"],
            index=1
        )
        
        filtros['mostrar_valores'] = st.checkbox("Mostrar valores nos gráficos", value=True)
    
    return filtros

def aplicar_filtros(df, filtros):
    """Aplica filtros no DataFrame."""
    if df.empty:
        return df
    
    df_filtrado = df.copy()
    
    # ✅ Obter período
    periodo = filtros.get('periodo', '12m')
    col_class = get_col_name('classificacao_risco', periodo)
    col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
    
    # Filtros básicos
    if filtros.get('classificacoes') and len(filtros['classificacoes']) < 4:
        if col_class in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[col_class].isin(filtros['classificacoes'])]
    
    if filtros.get('saldo_minimo', 0) > 0:
        df_filtrado = df_filtrado[df_filtrado['saldo_credor_atual'] >= filtros['saldo_minimo']]
    
    if filtros.get('meses_iguais_min', 0) > 0:
        df_filtrado = df_filtrado[df_filtrado['qtde_ultimos_12m_iguais'] >= filtros['meses_iguais_min']]
    
    if filtros.get('gerfe') and filtros['gerfe'] != 'TODAS':
        df_filtrado = df_filtrado[df_filtrado['nm_gerfe'] == filtros['gerfe']]
    
    # Filtros de enriquecimento
    if filtros.get('apenas_suspeitas') and 'flag_empresa_suspeita' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['flag_empresa_suspeita'] == 1]
    
    if filtros.get('apenas_canceladas') and 'sn_cancelado_inex_inativ' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['sn_cancelado_inex_inativ'] == 1]
    
    if filtros.get('min_indicios', 0) > 0 and 'qtde_indicios_fraude' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['qtde_indicios_fraude'] >= filtros['min_indicios']]
    
    if filtros.get('apenas_zeradas') and 'flag_tem_declaracoes_zeradas' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['flag_tem_declaracoes_zeradas'] == 1]
    
    if filtros.get('apenas_omissas') and 'flag_tem_omissoes' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['flag_tem_omissoes'] == 1]
    
    # Filtros contextuais
    contexto = filtros.get('contexto', 'ambos')
    
    if contexto == 'cancelamento':
        df_filtrado['flag_cancelamento'] = (
            (df_filtrado['qtde_ultimos_12m_iguais'] >= 6) |
            (df_filtrado.get('flag_tem_omissoes', 0) == 1) |
            (df_filtrado.get('flag_tem_declaracoes_zeradas', 0) == 1) |
            (df_filtrado.get('sn_cancelado_inex_inativ', 0) == 1)
        )
        
    elif contexto == 'saldos_credores':
        df_filtrado['flag_saldo_suspeito'] = (
            ((df_filtrado['saldo_credor_atual'] > 50000) & 
             (df_filtrado['qtde_ultimos_12m_iguais'] >= 6)) |
            ((df_filtrado[col_cresc] > 200) if col_cresc in df_filtrado.columns else False) |
            (df_filtrado['saldo_credor_atual'] > 500000)
        )
    
    return df_filtrado

def get_contexto_info(contexto):
    """Retorna informações sobre o contexto selecionado."""
    info = {
        'cancelamento': {
            'icon': '📋',
            'title': 'Análise para Cancelamento de IE',
            'description': 'Identificação de empresas candidatas ao cancelamento de Inscrição Estadual',
            'criterios': [
                'Empresas com 6+ meses sem movimentação',
                'Omissão de declarações obrigatórias',
                'Declarações zeradas consecutivas',
                'CNAE não sujeito ao ICMS',
                'Empresas canceladas/inexistentes'
            ],
            'color': '#ef6c00'
        },
        'saldos_credores': {
            'icon': '💰',
            'title': 'Análise de Saldos Credores',
            'description': 'Verificação de créditos acumulados e padrões suspeitos',
            'criterios': [
                'Saldo credor alto e estagnado (6+ meses)',
                'Crescimento anormal de saldo (>200%)',
                'Saldos muito elevados (>R$ 500K)',
                'Baixa variação com alto crédito',
                'Crédito presumido suspeito'
            ],
            'color': '#2e7d32'
        },
        'ambos': {
            'icon': '🔄',
            'title': 'Análise Combinada',
            'description': 'Avaliação completa: Cancelamento + Saldos Credores',
            'criterios': [
                'Todos os critérios de cancelamento',
                'Todos os critérios de saldos credores',
                'Análise integrada de risco',
                'Priorização por impacto fiscal'
            ],
            'color': '#1976d2'
        }
    }
    return info.get(contexto, info['ambos'])

# =============================================================================
# 7. PÁGINAS DO DASHBOARD
# =============================================================================

def pagina_dashboard_executivo(dados, filtros):
    """Dashboard executivo principal."""
    contexto = filtros.get('contexto', 'ambos')
    periodo = filtros.get('periodo', '12m')
    contexto_info = get_contexto_info(contexto)
    
    # ✅ Mostrar período selecionado
    if periodo == '12m':
        periodo_label = "📊 Análise: Últimos 12 meses (Out/2024 a Set/2025)"
        periodo_color = "#1976d2"
    elif periodo == '60m':
        periodo_label = "📈 Análise: Últimos 60 meses (Set/2020 a Set/2025)"
        periodo_color = "#2e7d32"
    else:
        periodo_label = "🔄 Análise: Comparativo 12m vs 60m"
        periodo_color = "#ef6c00"
    
    st.markdown(
        f"<div style='background: {periodo_color}; color: white; padding: 10px; "
        f"border-radius: 5px; margin-bottom: 10px; text-align: center;'>"
        f"<b>{periodo_label}</b>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Header com contexto
    st.markdown(
        f"<h1 class='main-header'>{contexto_info['icon']} {contexto_info['title']}</h1>", 
        unsafe_allow_html=True
    )
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados. Verifique a conexão.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    
    # ✅ KPIs com período correto
    kpis = calcular_kpis_gerais(df_filtrado, periodo)
    
    st.subheader("📊 Indicadores Principais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Empresas Monitoradas", f"{kpis['total_empresas']:,}",
                 help="Total de empresas com saldo credor de ICMS na base de dados, após aplicação dos filtros selecionados")

    with col2:
        st.metric("Grupos Econômicos", f"{kpis['total_grupos']:,}",
                 help="Quantidade de grupos econômicos distintos identificados pelo CNPJ raiz das empresas")

    with col3:
        st.metric("Saldo Credor Total", f"R$ {kpis['saldo_total']/1e9:.2f}B",
                 help="Soma de todos os saldos credores de ICMS acumulados pelas empresas filtradas")

    with col4:
        st.metric("Score Médio", f"{kpis['score_medio']:.1f}",
                 help="Média do score de risco calculado para as empresas. Quanto maior, maior o risco de irregularidade")

    with col5:
        st.metric("Casos Críticos", f"{kpis['criticos']:,}", delta=f"{kpis['altos']:,} altos",
                 help="Empresas classificadas como CRÍTICO (maior risco). O delta mostra quantas estão classificadas como ALTO")
    
    # Segunda linha - KPIs CONTEXTUAIS
    st.subheader(f"{contexto_info['icon']} Indicadores Contextuais")
    
    if contexto == 'cancelamento':
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            qtd_6m_parado = len(df_filtrado[df_filtrado['qtde_ultimos_12m_iguais'] >= 6])
            st.metric("6+ Meses Parado", f"{qtd_6m_parado:,}",
                     delta=f"{qtd_6m_parado/kpis['total_empresas']*100:.1f}%" if kpis['total_empresas'] > 0 else "0%",
                     delta_color="inverse",
                     help="Empresas com saldo credor inalterado por 6 ou mais meses consecutivos, indicando possível inatividade operacional")

        with col2:
            if 'flag_tem_omissoes' in df_filtrado.columns:
                qtd_omissas = len(df_filtrado[df_filtrado['flag_tem_omissoes'] == 1])
                st.metric("Com Omissões", f"{qtd_omissas:,}", delta_color="inverse",
                         help="Empresas que possuem omissão de declarações obrigatórias (DIME ou PGDAS)")
            else:
                st.metric("Com Omissões", "N/A", help="Dados de omissões não disponíveis na base atual")

        with col3:
            if 'flag_tem_declaracoes_zeradas' in df_filtrado.columns:
                qtd_zer = len(df_filtrado[df_filtrado['flag_tem_declaracoes_zeradas'] == 1])
                st.metric("Decl. Zeradas", f"{qtd_zer:,}", delta_color="inverse",
                         help="Empresas que apresentaram declarações com valores zerados, podendo indicar subfaturamento")
            else:
                st.metric("Decl. Zeradas", "N/A", help="Dados de declarações zeradas não disponíveis na base atual")

        with col4:
            if 'sn_cancelado_inex_inativ' in df_filtrado.columns:
                qtd_canc = len(df_filtrado[df_filtrado['sn_cancelado_inex_inativ'] == 1])
                st.metric("Canceladas/Inex", f"{qtd_canc:,}", delta_color="inverse",
                         help="Empresas com situação cadastral cancelada, inexistente ou inativa que mantêm saldo credor")
            else:
                st.metric("Canceladas/Inex", "N/A", help="Dados de situação cadastral não disponíveis na base atual")

        with col5:
            if 'flag_cancelamento' in df_filtrado.columns:
                candidatas = len(df_filtrado[df_filtrado['flag_cancelamento'] == True])
                st.metric("Candidatas ao Cancel.", f"{candidatas:,}",
                         delta=f"{candidatas/kpis['total_empresas']*100:.1f}%" if kpis['total_empresas'] > 0 else "0%",
                         help="Empresas que atendem aos critérios para cancelamento de IE: 6+ meses paradas, omissões ou declarações zeradas")
            else:
                st.metric("Candidatas ao Cancel.", "N/A", help="Flag de cancelamento não calculada")
    
    elif contexto == 'saldos_credores':
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            alto_estag = len(df_filtrado[
                (df_filtrado['saldo_credor_atual'] > 50000) &
                (df_filtrado['qtde_ultimos_12m_iguais'] >= 6)
            ])
            st.metric("Alto Saldo + Estagnado", f"{alto_estag:,}", delta_color="inverse",
                     help="Empresas com saldo credor acima de R$ 50.000 e sem movimentação há 6+ meses. Indica possível acumulação indevida")

        with col2:
            col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
            if col_cresc in df_filtrado.columns:
                cresc_anorm = len(df_filtrado[df_filtrado[col_cresc] > 200])
                st.metric("Crescimento >200%", f"{cresc_anorm:,}", delta_color="inverse",
                         help="Empresas cujo saldo credor cresceu mais de 200% no período analisado. Crescimento anormal pode indicar fraude")
            else:
                st.metric("Crescimento >200%", "N/A", help="Dados de crescimento não disponíveis")

        with col3:
            muito_alto = len(df_filtrado[df_filtrado['saldo_credor_atual'] > 500000])
            saldo_muito_alto = df_filtrado[df_filtrado['saldo_credor_atual'] > 500000]['saldo_credor_atual'].sum()
            st.metric("Saldo >R$ 500K", f"{muito_alto:,}",
                     delta=f"R$ {saldo_muito_alto/1e6:.1f}M",
                     help="Empresas com saldo credor superior a R$ 500.000. O delta mostra o valor total acumulado por essas empresas")

        with col4:
            col_desvio = get_col_name('desvio_padrao_credito', periodo)
            col_media = get_col_name('media_credito', periodo)
            if col_desvio in df_filtrado.columns and col_media in df_filtrado.columns:
                baixa_var = len(df_filtrado[
                    (df_filtrado[col_desvio] < 1000) &
                    (df_filtrado[col_media] > 50000)
                ])
                st.metric("Baixa Variação", f"{baixa_var:,}", delta_color="inverse",
                         help="Empresas com desvio padrão < R$ 1.000 e média > R$ 50.000. Padrão suspeito de valores constantes")
            else:
                st.metric("Baixa Variação", "N/A", help="Dados de variação não disponíveis")

        with col5:
            if 'flag_saldo_suspeito' in df_filtrado.columns:
                suspeitos = len(df_filtrado[df_filtrado['flag_saldo_suspeito'] == True])
                st.metric("Saldos Suspeitos", f"{suspeitos:,}",
                         delta=f"{suspeitos/kpis['total_empresas']*100:.1f}%" if kpis['total_empresas'] > 0 else "0%",
                         help="Empresas que atendem a critérios de saldo suspeito: alto+estagnado, crescimento >200% ou saldo >R$ 500K")
            else:
                st.metric("Saldos Suspeitos", "N/A", help="Flag de saldo suspeito não calculada")
    
    else:  # ambos
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            qtd_6m = len(df_filtrado[df_filtrado['qtde_ultimos_12m_iguais'] >= 6])
            st.metric("6+ Meses Parado", f"{qtd_6m:,}",
                     help="Empresas com saldo credor inalterado por 6 ou mais meses consecutivos")

        with col2:
            alto_estag = len(df_filtrado[
                (df_filtrado['saldo_credor_atual'] > 50000) &
                (df_filtrado['qtde_ultimos_12m_iguais'] >= 6)
            ])
            st.metric("Alto + Estagnado", f"{alto_estag:,}",
                     help="Empresas com saldo > R$ 50.000 e sem movimentação há 6+ meses")

        with col3:
            if 'flag_tem_omissoes' in df_filtrado.columns:
                qtd_om = len(df_filtrado[df_filtrado['flag_tem_omissoes'] == 1])
                st.metric("Com Omissões", f"{qtd_om:,}",
                         help="Empresas com omissão de declarações obrigatórias")
            else:
                st.metric("Com Omissões", "N/A", help="Dados não disponíveis")

        with col4:
            col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
            if col_cresc in df_filtrado.columns:
                cresc = len(df_filtrado[df_filtrado[col_cresc] > 200])
                st.metric("Crescimento >200%", f"{cresc:,}",
                         help="Empresas cujo saldo credor cresceu mais de 200% no período")
            else:
                st.metric("Crescimento >200%", "N/A", help="Dados não disponíveis")

        with col5:
            if 'flag_cancelamento' in df_filtrado.columns and 'flag_saldo_suspeito' in df_filtrado.columns:
                prioritarios = len(df_filtrado[
                    (df_filtrado['flag_cancelamento'] == True) |
                    (df_filtrado['flag_saldo_suspeito'] == True)
                ])
                st.metric("Prioritários", f"{prioritarios:,}",
                         delta=f"{prioritarios/kpis['total_empresas']*100:.1f}%" if kpis['total_empresas'] > 0 else "0%",
                         help="Empresas que são candidatas ao cancelamento OU possuem saldos suspeitos")
            else:
                st.metric("Prioritários", "N/A", help="Flags não calculadas")
    
    # Terceira linha - Indicadores de Fraude
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    if col_score_comb in df.columns:
        st.subheader("🚨 Indicadores de Fraude (v2.0)")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Score Combinado Médio", f"{kpis['score_combinado_medio']:.1f}",
                     help="Média do score combinado que integra múltiplos indicadores de risco e fraude. Valores > 70 indicam alto risco")

        with col2:
            perc_susp = (kpis['empresas_suspeitas'] / kpis['total_empresas'] * 100) if kpis['total_empresas'] > 0 else 0
            st.metric("Empresas Suspeitas", f"{kpis['empresas_suspeitas']:,}",
                     delta=f"{perc_susp:.1f}%", delta_color="inverse",
                     help="Empresas marcadas como suspeitas pelo sistema de IA, baseado em padrões de comportamento anômalo")

        with col3:
            st.metric("Canceladas/Inex", f"{kpis['empresas_canceladas']:,}", delta_color="inverse",
                     help="Empresas com situação cadastral cancelada ou inexistente que ainda mantêm saldo credor")

        with col4:
            st.metric("5+ Indícios Fraude", f"{kpis['empresas_5plus_indicios']:,}", delta_color="inverse",
                     help="Empresas que apresentam 5 ou mais indícios de fraude detectados pelo sistema")

        with col5:
            if kpis['empresas_suspeitas'] > 0 and 'flag_empresa_suspeita' in df_filtrado.columns:
                saldo_susp = df_filtrado[df_filtrado['flag_empresa_suspeita'] == 1]['saldo_credor_atual'].sum()
                st.metric("Saldo Suspeitas", f"R$ {saldo_susp/1e6:.1f}M",
                         help="Soma dos saldos credores de todas as empresas marcadas como suspeitas")
            else:
                st.metric("Saldo Suspeitas", "R$ 0.0M", help="Nenhuma empresa suspeita encontrada")
    
    st.divider()
    
    # Critérios do contexto atual
    with st.expander(f"📋 Critérios de Análise - {contexto_info['title']}", expanded=False):
        st.markdown("**Critérios aplicados neste contexto:**")
        for criterio in contexto_info['criterios']:
            st.markdown(f"✓ {criterio}")
    
    st.divider()
    
    # Gráficos principais
    st.subheader("📊 Análises Visuais")
    
    col1, col2 = st.columns(2)
    
    col_class = get_col_name('classificacao_risco', periodo)
    
    with col1:
        if col_class in df_filtrado.columns:
            dist_risco = df_filtrado[col_class].value_counts().reset_index()
            dist_risco.columns = ['Classificação', 'Quantidade']
            
            fig_risco = px.pie(
                dist_risco,
                values='Quantidade',
                names='Classificação',
                title=f'Distribuição por Risco ({periodo.upper()})',
                template=filtros['tema'],
                color='Classificação',
                color_discrete_map={
                    'CRÍTICO': '#c62828',
                    'ALTO': '#ef6c00',
                    'MÉDIO': '#fbc02d',
                    'BAIXO': '#388e3c'
                },
                hole=0.4
            )
            st.plotly_chart(fig_risco, use_container_width=True, key="grafico_dist_risco_principal")
    
    with col2:
        if col_class in df_filtrado.columns:
            saldo_risco = df_filtrado.groupby(col_class)['saldo_credor_atual'].sum().reset_index()
            saldo_risco.columns = ['Classificação', 'Saldo']
            
            fig_saldo = px.bar(
                saldo_risco,
                x='Classificação',
                y='Saldo',
                title=f'Saldo Credor por Nível de Risco ({periodo.upper()})',
                template=filtros['tema'],
                color='Classificação',
                color_discrete_map={
                    'CRÍTICO': '#c62828',
                    'ALTO': '#ef6c00',
                    'MÉDIO': '#fbc02d',
                    'BAIXO': '#388e3c'
                }
            )
            fig_saldo.update_yaxes(title_text="Saldo Credor (R$)")
            st.plotly_chart(fig_saldo, use_container_width=True, key="grafico_saldo_risco_principal")
    
    # Gráficos contextuais
    if contexto == 'cancelamento' or contexto == 'ambos':
        col1, col2 = st.columns(2)
        
        with col1:
            df_filtrado['faixa_meses'] = pd.cut(
                df_filtrado['qtde_ultimos_12m_iguais'],
                bins=[0, 6, 12, 24, 36, 48, 60], 
                labels=['0-6m', '7-12m', '13-24m', '25-36m', '37-48m', '49-60m']
            )
            
            dist_meses = df_filtrado['faixa_meses'].value_counts().reset_index()
            dist_meses.columns = ['Faixa', 'Quantidade']
            
            fig = px.bar(
                dist_meses,
                x='Faixa',
                y='Quantidade',
                title='📋 Distribuição por Tempo Estagnado (Cancelamento)',
                template=filtros['tema'],
                color='Quantidade',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True, key="grafico_meses_estagnado")
        
        with col2:
            if 'flag_cancelamento' in df_filtrado.columns:
                candidatas_data = pd.DataFrame({
                    'Status': ['Candidatas', 'Não Candidatas'],
                    'Quantidade': [
                        len(df_filtrado[df_filtrado['flag_cancelamento'] == True]),
                        len(df_filtrado[df_filtrado['flag_cancelamento'] == False])
                    ]
                })
                
                fig = px.pie(
                    candidatas_data,
                    values='Quantidade',
                    names='Status',
                    title='📋 Empresas Candidatas ao Cancelamento',
                    template=filtros['tema'],
                    color_discrete_sequence=['#ef6c00', '#4caf50']
                )
                st.plotly_chart(fig, use_container_width=True, key="grafico_candidatas_cancelamento")
    
    if contexto == 'saldos_credores' or contexto == 'ambos':
        col1, col2 = st.columns(2)
        
        col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
        
        with col1:
            if col_cresc in df_filtrado.columns:
                df_filtrado['faixa_cresc'] = pd.cut(
                    df_filtrado[col_cresc],
                    bins=[-1000, 0, 50, 100, 200, 10000],
                    labels=['Negativo', '0-50%', '51-100%', '101-200%', '>200%']
                )
                
                dist_cresc = df_filtrado['faixa_cresc'].value_counts().reset_index()
                dist_cresc.columns = ['Faixa', 'Quantidade']
                
                fig = px.bar(
                    dist_cresc,
                    x='Faixa',
                    y='Quantidade',
                    title=f'💰 Distribuição por Crescimento de Saldo ({periodo.upper()})',
                    template=filtros['tema'],
                    color='Quantidade',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig, use_container_width=True, key="grafico_crescimento_saldo")
        
        with col2:
            if 'flag_saldo_suspeito' in df_filtrado.columns:
                suspeitos_data = pd.DataFrame({
                    'Status': ['Saldos Suspeitos', 'Saldos Normais'],
                    'Quantidade': [
                        len(df_filtrado[df_filtrado['flag_saldo_suspeito'] == True]),
                        len(df_filtrado[df_filtrado['flag_saldo_suspeito'] == False])
                    ]
                })
                
                fig = px.pie(
                    suspeitos_data,
                    values='Quantidade',
                    names='Status',
                    title='💰 Classificação de Saldos Credores',
                    template=filtros['tema'],
                    color_discrete_sequence=['#c62828', '#2e7d32']
                )
                st.plotly_chart(fig, use_container_width=True, key="grafico_saldos_suspeitos")
    
    # Score Combinado
    if col_score_comb in df_filtrado.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            df_filtrado['faixa_score_comb'] = pd.cut(
                df_filtrado[col_score_comb],
                bins=[0, 30, 50, 70, 100, 120, 200],
                labels=['BAIXO', 'MÉDIO', 'ALTO', 'CRÍTICO', 'MUITO CRÍTICO', 'EXTREMO']
            )
            
            dist_score = df_filtrado['faixa_score_comb'].value_counts().reset_index()
            dist_score.columns = ['Faixa', 'Quantidade']
            
            fig = px.bar(
                dist_score,
                x='Faixa',
                y='Quantidade',
                title=f'Distribuição por Score Combinado ({periodo.upper()})',
                template=filtros['tema'],
                color='Quantidade',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True, key="grafico_score_combinado")
        
        with col2:
            if 'flag_empresa_suspeita' in df_filtrado.columns:
                matriz_data = []
                for susp in [0, 1]:
                    for faixa in ['< 50K', '50K-100K', '100K-500K', '500K-1M', '1M+']:
                        df_temp = df_filtrado[df_filtrado['flag_empresa_suspeita'] == susp]
                        
                        if faixa == '< 50K':
                            df_temp = df_temp[df_temp['saldo_credor_atual'] < 50000]
                        elif faixa == '50K-100K':
                            df_temp = df_temp[(df_temp['saldo_credor_atual'] >= 50000) & (df_temp['saldo_credor_atual'] < 100000)]
                        elif faixa == '100K-500K':
                            df_temp = df_temp[(df_temp['saldo_credor_atual'] >= 100000) & (df_temp['saldo_credor_atual'] < 500000)]
                        elif faixa == '500K-1M':
                            df_temp = df_temp[(df_temp['saldo_credor_atual'] >= 500000) & (df_temp['saldo_credor_atual'] < 1000000)]
                        else:
                            df_temp = df_temp[df_temp['saldo_credor_atual'] >= 1000000]
                        
                        matriz_data.append({
                            'Status': 'SUSPEITA' if susp == 1 else 'NORMAL',
                            'Faixa': faixa,
                            'Qtde': len(df_temp),
                            'Saldo': df_temp['saldo_credor_atual'].sum()
                        })
                
                df_matriz = pd.DataFrame(matriz_data)
                
                fig = px.scatter(
                    df_matriz,
                    x='Faixa',
                    y='Status',
                    size='Qtde',
                    color='Saldo',
                    title='Matriz: Suspeitas x Saldo',
                    template=filtros['tema'],
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True, key="grafico_matriz_risco")
    
    # Scatter - Score vs Saldo
    st.subheader("Matriz de Risco: Score vs Saldo Credor")
    
    col_score = get_col_name('score_risco', periodo)
    
    if col_score in df_filtrado.columns and col_class in df_filtrado.columns:
        df_scatter = df_filtrado.nlargest(500, col_score)
        
        fig_scatter = px.scatter(
            df_scatter,
            x=col_score,
            y='saldo_credor_atual',
            color=col_class,
            size='qtde_ultimos_12m_iguais',
            hover_data=['nm_razao_social', 'nm_gerfe'],
            title=f'Top 500 Empresas por Score ({periodo.upper()})',
            template=filtros['tema'],
            color_discrete_map={
                'CRÍTICO': '#c62828',
                'ALTO': '#ef6c00',
                'MÉDIO': '#fbc02d',
                'BAIXO': '#388e3c'
            },
            log_y=True
        )
        fig_scatter.update_layout(height=600)
        st.plotly_chart(fig_scatter, use_container_width=True, key="scatter_score_vs_saldo")

def pagina_comparativo_periodos(dados, filtros):
    """Análise comparativa entre 12 e 60 meses."""
    st.markdown("<h1 class='main-header'>🔄 Análise Comparativa: 12m vs 60m</h1>", 
                unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    
    st.markdown("""
    <div class='info-box'>
    <b>Objetivo:</b> Comparar indicadores de risco entre análise de curto prazo (12 meses) 
    e longo prazo (60 meses) para identificar padrões recentes vs históricos.
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs Comparativos
    st.subheader("📊 Indicadores Comparativos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 12 Meses (Recente)")
        kpis_12 = calcular_kpis_gerais(df_filtrado, '12m')
        st.metric("Score Médio", f"{kpis_12['score_medio']:.1f}",
                 help="Score médio de risco calculado nos últimos 12 meses (Out/2024 a Set/2025)")
        st.metric("Críticos", f"{kpis_12['criticos']:,}",
                 help="Quantidade de empresas classificadas como CRÍTICO no período de 12 meses")
        st.metric("Score Comb. Médio", f"{kpis_12['score_combinado_medio']:.1f}",
                 help="Média do score combinado (risco + fraude) nos últimos 12 meses")

    with col2:
        st.markdown("### 📈 60 Meses (Histórico)")
        kpis_60 = calcular_kpis_gerais(df_filtrado, '60m')
        st.metric("Score Médio", f"{kpis_60['score_medio']:.1f}",
                 help="Score médio de risco calculado nos últimos 60 meses (Set/2020 a Set/2025)")
        st.metric("Críticos", f"{kpis_60['criticos']:,}",
                 help="Quantidade de empresas classificadas como CRÍTICO no período de 60 meses")
        st.metric("Score Comb. Médio", f"{kpis_60['score_combinado_medio']:.1f}",
                 help="Média do score combinado (risco + fraude) nos últimos 60 meses")

    with col3:
        st.markdown("### 🔄 Variação")
        var_score = kpis_60['score_medio'] - kpis_12['score_medio']
        var_crit = kpis_60['criticos'] - kpis_12['criticos']
        var_comb = kpis_60['score_combinado_medio'] - kpis_12['score_combinado_medio']

        st.metric("Δ Score", f"{var_score:+.1f}",
                 help="Diferença entre score 60m e 12m. Valor positivo indica piora do risco histórico")
        st.metric("Δ Críticos", f"{var_crit:+,}",
                 help="Diferença na quantidade de empresas críticas entre períodos")
        st.metric("Δ Score Comb.", f"{var_comb:+.1f}",
                 help="Diferença no score combinado entre períodos")
    
    st.divider()
    
    # Gráfico Comparativo
    st.subheader("📊 Distribuição por Classificação")
    
    if 'classificacao_risco_12m' in df_filtrado.columns and 'classificacao_risco_60m' in df_filtrado.columns:
        dist_12 = df_filtrado['classificacao_risco_12m'].value_counts().reset_index()
        dist_12.columns = ['Classificação', 'Qtde_12m']
        
        dist_60 = df_filtrado['classificacao_risco_60m'].value_counts().reset_index()
        dist_60.columns = ['Classificação', 'Qtde_60m']
        
        dist_comp = dist_12.merge(dist_60, on='Classificação', how='outer').fillna(0)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=dist_comp['Classificação'],
            y=dist_comp['Qtde_12m'],
            name='12 meses',
            marker_color='#1976d2'
        ))
        
        fig.add_trace(go.Bar(
            x=dist_comp['Classificação'],
            y=dist_comp['Qtde_60m'],
            name='60 meses',
            marker_color='#2e7d32'
        ))
        
        fig.update_layout(
            title='Comparativo: Classificações de Risco',
            barmode='group',
            template=filtros['tema']
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Top 50 com divergência
    st.subheader("🎯 Top 50 Empresas com Maior Divergência")
    
    if 'classificacao_risco_12m' in df_filtrado.columns and 'classificacao_risco_60m' in df_filtrado.columns:
        df_filtrado['divergencia_classificacao'] = (
            df_filtrado['classificacao_risco_12m'] != df_filtrado['classificacao_risco_60m']
        ).astype(int)
        
        if 'score_risco_12m' in df_filtrado.columns and 'score_risco_60m' in df_filtrado.columns:
            df_filtrado['diferenca_score'] = abs(
                df_filtrado['score_risco_60m'] - df_filtrado['score_risco_12m']
            )
            
            df_diverg = df_filtrado[df_filtrado['divergencia_classificacao'] == 1].nlargest(50, 'diferenca_score')
            
            if not df_diverg.empty:
                colunas = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe',
                           'classificacao_risco_12m', 'classificacao_risco_60m',
                           'score_risco_12m', 'score_risco_60m', 'diferenca_score',
                           'saldo_credor_atual']
                
                df_display = df_diverg[[col for col in colunas if col in df_diverg.columns]].copy()
                df_display.insert(0, 'Rank', range(1, len(df_display) + 1))
                
                st.dataframe(
                    df_display.style.format({
                        'score_risco_12m': '{:.1f}',
                        'score_risco_60m': '{:.1f}',
                        'diferenca_score': '{:.1f}',
                        'saldo_credor_atual': 'R$ {:,.2f}'
                    }),
                    use_container_width=True,
                    height=600
                )
            else:
                st.info("Nenhuma empresa com divergência significativa encontrada.")

def pagina_analise_suspeitas(dados, filtros):
    """NOVA PÁGINA v2.0 - Análise de Empresas Suspeitas."""
    st.markdown("<h1 class='main-header'>🚨 Análise de Suspeitas e Fraudes</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    if 'flag_empresa_suspeita' not in df.columns:
        st.warning("⚠️ Dados de enriquecimento (v2.0) não disponíveis nesta tabela.")
        st.info("Execute primeiro os scripts SQL de enriquecimento para criar a tabela credito_dime_completo com os novos campos.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    periodo = filtros.get('periodo', '12m')
    
    st.markdown("""
    <div class='info-box'>
    <b>Objetivo:</b> Identificar empresas com indicadores de fraude, suspeitas fiscais, 
    cancelamento/inexistência e padrões anômalos de declaração.
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs de Fraude
    st.subheader("📊 Panorama de Fraudes")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        qtd_susp = len(df_filtrado[df_filtrado['flag_empresa_suspeita'] == 1])
        st.metric("Empresas Suspeitas", f"{qtd_susp:,}",
                 help="Total de empresas identificadas como suspeitas pelo sistema de IA fiscal")

    with col2:
        qtd_canc = len(df_filtrado[df_filtrado.get('sn_cancelado_inex_inativ', 0) == 1])
        st.metric("Canceladas/Inexistentes", f"{qtd_canc:,}",
                 help="Empresas com situação cadastral cancelada, inexistente ou inativa na Receita")

    with col3:
        qtd_ind5 = len(df_filtrado[df_filtrado.get('qtde_indicios_fraude', 0) >= 5])
        st.metric("5+ Indícios", f"{qtd_ind5:,}",
                 help="Empresas com 5 ou mais indícios de fraude detectados, requerem investigação prioritária")

    with col4:
        qtd_zer = len(df_filtrado[df_filtrado.get('flag_tem_declaracoes_zeradas', 0) == 1])
        st.metric("Com Decl. Zeradas", f"{qtd_zer:,}",
                 help="Empresas que apresentaram declarações com valores zerados em algum período")

    with col5:
        qtd_omi = len(df_filtrado[df_filtrado.get('flag_tem_omissoes', 0) == 1])
        st.metric("Com Omissões", f"{qtd_omi:,}",
                 help="Empresas que deixaram de entregar declarações obrigatórias")
    
    # SEÇÃO CORRIGIDA: Detalhamento de Omissões DIME/PGDAS
    st.divider()
    st.subheader("📋 Detalhamento de Omissões (v2.0)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        qtd_omi_dime_n = len(df_filtrado[df_filtrado.get('flag_omissao_dime_normal', 0) == 1])
        st.metric("Omissão DIME (Normal)", f"{qtd_omi_dime_n:,}",
                 help="Empresas do regime Normal com omissão de DIME")
    
    with col2:
        qtd_omi_pgdas_s = len(df_filtrado[df_filtrado.get('flag_omissao_pgdas_simples', 0) == 1])
        st.metric("Omissão PGDAS (Simples)", f"{qtd_omi_pgdas_s:,}",
                 help="Empresas do Simples Nacional com omissão de PGDAS")
    
    st.divider()
    
    # Distribuição por Indícios
    st.subheader("📈 Distribuição por Indícios de Fraude")
    
    if 'qtde_indicios_fraude' in df_filtrado.columns:
        df_filtrado['faixa_indicios'] = pd.cut(
            df_filtrado['qtde_indicios_fraude'],
            bins=[-1, 0, 2, 4, 6, 9, 100],
            labels=['Sem indícios', '1-2', '3-4', '5-6', '7-9', '10+']
        )
        
        col_score_comb = get_col_name('score_risco_combinado', periodo)
        
        dist_ind = df_filtrado.groupby('faixa_indicios', observed=True).agg({
            'nu_cnpj': 'count',
            'saldo_credor_atual': 'sum',
            col_score_comb: 'mean' if col_score_comb in df_filtrado.columns else lambda x: 0
        }).reset_index()
        
        dist_ind.columns = ['Faixa', 'Qtde', 'Saldo', 'Score Médio']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                dist_ind,
                x='Faixa',
                y='Qtde',
                title='Empresas por Faixa de Indícios',
                template=filtros['tema'],
                color='Qtde',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                dist_ind,
                x='Faixa',
                y='Saldo',
                title='Saldo por Faixa de Indícios',
                template=filtros['tema'],
                color='Saldo',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Top 50 Suspeitas
    st.subheader("🎯 Top 50 Empresas Mais Suspeitas")
    
    df_susp = df_filtrado[df_filtrado['flag_empresa_suspeita'] == 1]
    
    if df_susp.empty:
        st.info("ℹ️ Nenhuma empresa suspeita encontrada com os filtros aplicados.")
        return
    
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    if col_score_comb in df_susp.columns:
        df_susp = df_susp.nlargest(50, col_score_comb)
    else:
        df_susp = df_susp.head(50)
    
    # COLUNAS CORRIGIDAS: Removidas as flags impossíveis
    colunas_display = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe', 'de_cnae',
                       col_score_comb, 'score_suspeita', 'saldo_credor_atual',
                       'qtde_indicios_fraude', 'cd_situacao_suspeita', 'sn_cancelado_inex_inativ',
                       'qtde_ultimos_12m_iguais', 'qt_clientes_noteiras', 'qt_fornecedoras_noteiras',
                       'flag_omissao_dime_normal', 'flag_omissao_pgdas_simples']
    
    df_display = df_susp[[col for col in colunas_display if col in df_susp.columns]].copy()
    df_display.insert(0, 'Rank', range(1, len(df_display) + 1))
    
    format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
    if col_score_comb in df_display.columns:
        format_dict[col_score_comb] = '{:.1f}'
    if 'score_suspeita' in df_display.columns:
        format_dict['score_suspeita'] = '{:.1f}'
    
    st.dataframe(
        df_display.style.format(format_dict),
        use_container_width=True,
        height=600
    )
    
    # Empresas com Múltiplos Alertas - CORRIGIDO
    st.divider()
    st.subheader("⚠️ Empresas com Múltiplos Sinais de Alerta")
    
    df_filtrado['qtde_alertas'] = (
        df_filtrado.get('flag_empresa_suspeita', 0).fillna(0) +
        df_filtrado.get('flag_tem_declaracoes_zeradas', 0).fillna(0) +
        df_filtrado.get('flag_tem_omissoes', 0).fillna(0) +
        df_filtrado.get('sn_cancelado_inex_inativ', 0).fillna(0) +
        (df_filtrado.get('qtde_indicios_fraude', 0) >= 5).astype(int) +
        (df_filtrado['qtde_ultimos_12m_iguais'] >= 12).astype(int) +
        df_filtrado.get('flag_omissao_dime_normal', 0).fillna(0) +
        df_filtrado.get('flag_omissao_pgdas_simples', 0).fillna(0)
    )
    
    col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
    if col_cresc in df_filtrado.columns:
        df_filtrado['qtde_alertas'] = df_filtrado['qtde_alertas'] + (df_filtrado[col_cresc] > 500).astype(int)
    
    df_mult = df_filtrado[df_filtrado['qtde_alertas'] >= 3].nlargest(30, 'qtde_alertas')
    
    if not df_mult.empty:
        colunas_mult = ['nu_cnpj', 'nm_razao_social', 'qtde_alertas', col_score_comb,
                       'saldo_credor_atual', 'flag_empresa_suspeita', 'qtde_indicios_fraude',
                       'sn_cancelado_inex_inativ']
        
        df_mult_display = df_mult[[col for col in colunas_mult if col in df_mult.columns]].copy()
        
        format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
        if col_score_comb in df_mult_display.columns:
            format_dict[col_score_comb] = '{:.1f}'
        
        st.dataframe(
            df_mult_display.style.format(format_dict),
            use_container_width=True,
            height=500
        )
        
def pagina_ranking_empresas(dados, filtros):
    """Ranking e análise de empresas."""
    st.markdown("<h1 class='main-header'>Ranking de Empresas Críticas</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    periodo = filtros.get('periodo', '12m')
    
    st.subheader("Configurações do Ranking")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        criterios_base = ['Saldo Credor', 'Meses Estagnados']
        
        # Adicionar critérios do período
        criterios_base.insert(0, f'Score de Risco ({periodo})')
        col_score_comb = get_col_name('score_risco_combinado', periodo)
        if col_score_comb in df.columns:
            criterios_base.insert(1, f'Score Combinado ({periodo})')
        
        col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
        if col_cresc in df.columns:
            criterios_base.append(f'Crescimento % ({periodo})')
        
        if 'qtde_indicios_fraude' in df.columns:
            criterios_base.append('Indícios de Fraude')
        
        criterio = st.selectbox("Ordenar por", criterios_base, index=0)
    
    with col2:
        top_n = st.slider("Top N empresas", 10, 100, 50, 10)
    
    with col3:
        ordem = st.radio("Ordem", ['Decrescente', 'Crescente'], index=0)
    
    with col4:
        exportar = st.checkbox("Habilitar exportação", value=False)
    
    # Mapear critério
    mapa_criterio = {
        f'Score de Risco ({periodo})': get_col_name('score_risco', periodo),
        f'Score Combinado ({periodo})': get_col_name('score_risco_combinado', periodo),
        'Saldo Credor': 'saldo_credor_atual',
        f'Crescimento % ({periodo})': get_col_name('crescimento_saldo_percentual', periodo),
        'Meses Estagnados': 'qtde_ultimos_12m_iguais',
        'Indícios de Fraude': 'qtde_indicios_fraude'
    }
    
    col_ordenacao = mapa_criterio.get(criterio, 'saldo_credor_atual')
    
    if col_ordenacao not in df_filtrado.columns:
        st.warning(f"⚠️ Coluna {criterio} não disponível nos dados.")
        return
    
    ascending = (ordem == 'Crescente')
    
    ranking = df_filtrado.sort_values(col_ordenacao, ascending=ascending).head(top_n)
    
    colunas_ranking = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe', 'de_cnae',
                       get_col_name('score_risco', periodo), get_col_name('classificacao_risco', periodo),
                       'saldo_credor_atual', 'qtde_ultimos_12m_iguais']
    
    col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
    if col_cresc in ranking.columns:
        colunas_ranking.append(col_cresc)
    
    col_cp = get_col_name('vl_credito_presumido', periodo)
    if col_cp in ranking.columns:
        colunas_ranking.append(col_cp)
    
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    if col_score_comb in ranking.columns:
        colunas_ranking.insert(5, col_score_comb)
    
    if 'flag_empresa_suspeita' in ranking.columns:
        colunas_ranking.append('flag_empresa_suspeita')
    if 'qtde_indicios_fraude' in ranking.columns:
        colunas_ranking.append('qtde_indicios_fraude')
    
    ranking_display = ranking[[col for col in colunas_ranking if col in ranking.columns]].copy()
    
    ranking_display.insert(0, 'Posição', range(1, len(ranking_display) + 1))
    
    st.subheader(f"Top {top_n} Empresas - {criterio}")
    
    format_dict = {
        'saldo_credor_atual': 'R$ {:,.2f}',
        get_col_name('score_risco', periodo): '{:.1f}'
    }
    
    if col_cresc in ranking_display.columns:
        format_dict[col_cresc] = '{:+.1f}%'
    if col_cp in ranking_display.columns:
        format_dict[col_cp] = 'R$ {:,.2f}'
    if col_score_comb in ranking_display.columns:
        format_dict[col_score_comb] = '{:.1f}'
    
    st.dataframe(
        ranking_display.style.format(format_dict),
        use_container_width=True,
        height=600
    )
    
    # Gráfico do ranking
    col_class = get_col_name('classificacao_risco', periodo)
    if col_class in ranking_display.columns:
        fig_ranking = px.bar(
            ranking_display.head(20),
            x=col_ordenacao,
            y='nm_razao_social',
            orientation='h',
            title=f'Top 20: {criterio}',
            template=filtros['tema'],
            color=col_class,
            color_discrete_map={
                'CRÍTICO': '#c62828',
                'ALTO': '#ef6c00',
                'MÉDIO': '#fbc02d',
                'BAIXO': '#388e3c'
            }
        )
        
        fig_ranking.update_layout(height=700)
        st.plotly_chart(fig_ranking, use_container_width=True)
    
    if exportar:
        st.download_button(
            label="Baixar Ranking (CSV)",
            data=ranking_display.to_csv(index=False, encoding='utf-8-sig', sep=';').encode('utf-8-sig'),
            file_name=f"ranking_empresas_{periodo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

def pagina_analise_setorial(dados, filtros):
    """Análise comparativa dos 3 setores."""
    st.markdown("<h1 class='main-header'>Análise Setorial Comparativa</h1>", unsafe_allow_html=True)
    
    periodo = filtros.get('periodo', '12m')

    # ✅ Passar engine para carregar sob demanda
    engine = get_impala_engine()
    stats_setores = calcular_estatisticas_setoriais(dados, filtros, engine)
    
    if stats_setores.empty:
        st.error("Dados setoriais não carregados.")
        return
    
    st.info(f"📊 Análise baseada em: **{periodo.upper()}**")
    
    st.subheader("Comparativo entre Setores")
    
    st.dataframe(
        stats_setores.style.format({
            'Saldo Total': 'R$ {:,.2f}',
            'Score Médio': '{:.1f}'
        }),
        use_container_width=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            stats_setores,
            x='Setor',
            y='Empresas',
            title='Empresas Ativas por Setor',
            template=filtros['tema'],
            color='Setor'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            stats_setores,
            x='Setor',
            y='Saldo Total',
            title='Saldo Credor Total por Setor',
            template=filtros['tema'],
            color='Setor'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if 'Suspeitas' in stats_setores.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                stats_setores,
                x='Setor',
                y='Suspeitas',
                title='Empresas Suspeitas por Setor',
                template=filtros['tema'],
                color='Suspeitas',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                stats_setores,
                x='Setor',
                y='Congelados 12m+',
                title='Empresas Congeladas por Setor',
                template=filtros['tema'],
                color='Congelados 12m+',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig, use_container_width=True)

def pagina_drill_down_empresa(dados, filtros):
    """Análise detalhada de empresa específica."""
    st.markdown("<h1 class='main-header'>Drill-Down por Empresa</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    periodo = filtros.get('periodo', '12m')
    
    st.subheader("Seleção da Empresa")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        opcao_busca = st.radio("Buscar por:", ['Nome', 'CNPJ'], horizontal=True)
        
        if opcao_busca == 'Nome':
            empresas_lista = df_filtrado[['nu_cnpj', 'nm_razao_social']].drop_duplicates()
            empresas_lista = empresas_lista.sort_values('nm_razao_social')
            
            if empresas_lista.empty:
                st.warning("Nenhuma empresa disponível com os filtros aplicados.")
                return
            
            empresa_selecionada = st.selectbox(
                "Selecione a empresa:",
                empresas_lista['nu_cnpj'].tolist(),
                format_func=lambda x: f"{empresas_lista[empresas_lista['nu_cnpj']==x]['nm_razao_social'].iloc[0]}"
            )
        else:
            cnpj_input = st.text_input("Digite o CNPJ (apenas números):", max_chars=14, 
                                      help="Digite apenas os 14 números do CNPJ, sem pontos, traços ou barras")
            
            if cnpj_input:
                cnpj_limpo = ''.join(filter(str.isdigit, cnpj_input))
                
                if len(cnpj_limpo) > 14:
                    st.warning(f"⚠️ CNPJ deve ter no máximo 14 dígitos. Você digitou {len(cnpj_limpo)} dígitos.")
                    empresa_selecionada = None
                else:
                    empresa_selecionada = cnpj_limpo.zfill(14)
                    cnpj_formatado = f"{empresa_selecionada[:2]}.{empresa_selecionada[2:5]}.{empresa_selecionada[5:8]}/{empresa_selecionada[8:12]}-{empresa_selecionada[12:14]}"
                    st.info(f"🔍 Buscando por: {cnpj_formatado}")
            else:
                empresa_selecionada = None
    
    if not empresa_selecionada:
        st.info("Selecione uma empresa para análise.")
        return
    
    df_empresa = df[df['nu_cnpj'].astype(str).str.zfill(14) == str(empresa_selecionada).zfill(14)]
    
    if df_empresa.empty:
        df_empresa = df[df['nu_cnpj'].astype(str).str.replace(r'\D', '', regex=True) == str(empresa_selecionada)]
    
    if df_empresa.empty:
        st.error(f"❌ CNPJ {empresa_selecionada} não encontrado na base de dados.")
        st.info("💡 Dica: Verifique se o CNPJ está correto e se a empresa possui créditos acumulados.")
        
        with st.expander("🔍 Pesquisar empresas disponíveis"):
            busca_parcial = st.text_input("Digite parte da razão social:", key="busca_parcial")
            if busca_parcial:
                empresas_similares = df[df['nm_razao_social'].str.contains(busca_parcial, case=False, na=False)][['nu_cnpj', 'nm_razao_social']].head(10)
                if not empresas_similares.empty:
                    st.dataframe(empresas_similares, use_container_width=True)
                else:
                    st.warning("Nenhuma empresa encontrada com esse termo.")
        return
    
    empresa_info = df_empresa.iloc[0]

    # Cabeçalho com botão de copiar
    col_titulo, col_btn = st.columns([4, 1])
    
    with col_titulo:
        st.markdown(f"### {empresa_info['nm_razao_social']}")
    
    with col_btn:
        cnpj_formatado = empresa_info.get('nu_cnpj_formatado', empresa_info['nu_cnpj'])
        if st.button("📋 Copiar CNPJ", key="btn_copy_cnpj"):
            st.code(empresa_info['nu_cnpj'], language=None)
            st.success("✅ CNPJ copiado!")
    
    # Informações básicas da empresa
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**CNPJ:** `{cnpj_formatado}`")
        st.caption(f"**CNAE:** {empresa_info.get('de_cnae', 'N/A')}")
    
    with col2:
        st.caption(f"**Situação:** {empresa_info.get('nm_sit_cadastral', 'N/A')}")
        st.caption(f"**GERFE:** {empresa_info.get('nm_gerfe', 'N/A')}")
    
    with col3:
        st.caption(f"**Grupo:** {empresa_info.get('nu_cnpj_grupo', 'N/A')}")
    
    st.divider()
    
    st.info(f"📊 Análise baseada em: **{periodo.upper()}**")
    
    st.subheader("Indicadores da Empresa")

    col1, col2, col3, col4, col5 = st.columns(5)

    col_score = get_col_name('score_risco', periodo)
    col_class = get_col_name('classificacao_risco', periodo)
    col_cresc = get_col_name('crescimento_saldo_percentual', periodo)

    with col1:
        if col_score in empresa_info.index:
            score = empresa_info[col_score]
            st.metric(f"Score Risco ({periodo})", f"{score:.1f}",
                     help="Pontuação de risco da empresa. Quanto maior, maior a probabilidade de irregularidade")

    with col2:
        if col_class in empresa_info.index:
            st.metric("Classificação", empresa_info[col_class],
                     help="Classificação de risco: CRÍTICO (maior risco), ALTO, MÉDIO ou BAIXO")

    with col3:
        st.metric("Saldo Credor", f"R$ {empresa_info['saldo_credor_atual']/1e6:.2f}M",
                 help="Saldo credor de ICMS acumulado pela empresa no período atual")

    with col4:
        st.metric("Meses Estagnados", f"{int(empresa_info['qtde_ultimos_12m_iguais'])}",
                 help="Quantidade de meses consecutivos em que o saldo credor permaneceu inalterado")

    with col5:
        if col_cresc in empresa_info.index:
            st.metric(f"Crescimento ({periodo})", f"{empresa_info[col_cresc]:+.1f}%",
                     help="Percentual de crescimento/redução do saldo credor no período analisado")
    
    # Indicadores de Fraude
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    if col_score_comb in empresa_info.index:
        st.divider()
        st.subheader("🚨 Indicadores de Fraude (v2.0)")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(f"Score Combinado ({periodo})", f"{empresa_info[col_score_comb]:.1f}",
                     help="Score que combina indicadores de risco com sinais de fraude. Valores > 100 indicam situação crítica")

        with col2:
            flag_susp = "SIM" if empresa_info.get('flag_empresa_suspeita', 0) == 1 else "NÃO"
            st.metric("Empresa Suspeita", flag_susp,
                     help="Indica se a empresa foi marcada como suspeita pelo sistema de inteligência artificial fiscal")

        with col3:
            st.metric("Indícios Fraude", f"{int(empresa_info.get('qtde_indicios_fraude', 0))}",
                     help="Quantidade de indícios de fraude detectados para esta empresa. 5+ requer investigação prioritária")

        with col4:
            flag_canc = "SIM" if empresa_info.get('sn_cancelado_inex_inativ', 0) == 1 else "NÃO"
            st.metric("Cancelada/Inex", flag_canc,
                     help="Indica se a empresa está com situação cadastral cancelada, inexistente ou inativa")

        with col5:
            st.metric("Score Suspeita", f"{empresa_info.get('score_suspeita', 0):.1f}",
                     help="Pontuação específica de suspeita atribuída pela análise de IA. Quanto maior, mais suspeita")
        
        # Alertas visuais
        if empresa_info.get('flag_empresa_suspeita', 0) == 1:
            st.markdown(
                f"<div class='alert-critico'>"
                f"<b>⚠️ ALERTA CRÍTICO:</b> Empresa marcada como suspeita<br>"
                f"Código Situação: {empresa_info.get('cd_situacao_suspeita', 'N/A')}<br>"
                f"Motivos: {int(empresa_info.get('qt_motivos', 0))}"
                f"</div>",
                unsafe_allow_html=True
            )
        
        if empresa_info.get('sn_cancelado_inex_inativ', 0) == 1:
            st.markdown(
                f"<div class='alert-extremo'>"
                f"<b>🔴 ALERTA EXTREMO:</b> Empresa CANCELADA ou INEXISTENTE"
                f"</div>",
                unsafe_allow_html=True
            )
        
        if empresa_info.get('qtde_indicios_fraude', 0) >= 5:
            st.markdown(
                f"<div class='alert-alto'>"
                f"<b>⚠️ ALERTA ALTO:</b> {int(empresa_info['qtde_indicios_fraude'])} indícios de fraude detectados"
                f"</div>",
                unsafe_allow_html=True
            )

        # SEÇÃO CORRIGIDA: Detalhamento de Omissões
        if any([
            empresa_info.get('flag_omissao_dime_normal'),
            empresa_info.get('flag_omissao_pgdas_simples')
        ]):
            st.divider()
            st.subheader("📋 Detalhamento de Omissões (v2.0)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**DIME (Regime Normal):**")
                omi_dime_n = "SIM" if empresa_info.get('flag_omissao_dime_normal', 0) == 1 else "NÃO"
                st.caption(f"Omissão: {omi_dime_n}")
            
            with col2:
                st.markdown("**PGDAS (Simples Nacional):**")
                omi_pgdas_s = "SIM" if empresa_info.get('flag_omissao_pgdas_simples', 0) == 1 else "NÃO"
                st.caption(f"Omissão: {omi_pgdas_s}")
            
            # Alerta se tiver omissões em múltiplos tipos
            tipos_omissao = sum([
                empresa_info.get('flag_omissao_dime_normal', 0) == 1,
                empresa_info.get('flag_omissao_pgdas_simples', 0) == 1
            ])
            
            if tipos_omissao >= 2:
                st.markdown(
                    f"<div class='alert-alto'>"
                    f"<b>⚠️ ATENÇÃO:</b> Omissões em {tipos_omissao} tipos diferentes de declaração"
                    f"</div>",
                    unsafe_allow_html=True
                )
        
        # Informações adicionais
        col1, col2 = st.columns(2)

        with col1:
            total_noteiras = empresa_info.get('qt_clientes_noteiras', 0) + empresa_info.get('qt_fornecedoras_noteiras', 0)
            st.metric("Total Noteiras", f"{int(total_noteiras)}",
                     help="Quantidade total de empresas noteiras (clientes + fornecedores) com relacionamento comercial")
            st.caption(f"Clientes: {int(empresa_info.get('qt_clientes_noteiras', 0))} | Fornecedores: {int(empresa_info.get('qt_fornecedoras_noteiras', 0))}")

        with col2:
            if empresa_info.get('flag_tem_declaracoes_zeradas', 0) == 1 or empresa_info.get('flag_tem_omissoes', 0) == 1:
                total_zer = empresa_info.get('periodos_zerados_normal', 0) + empresa_info.get('periodos_zerados_simples', 0)
                total_omi = empresa_info.get('periodos_omissos_normal', 0) + empresa_info.get('periodos_omissos_simples', 0)
                st.metric("Irregularidades Declaratórias", f"{int(total_zer + total_omi)}",
                         help="Total de períodos com declarações zeradas ou omissas (DIME + PGDAS)")
                st.caption(f"Zerados: {int(total_zer)} | Omissos: {int(total_omi)}")

def pagina_machine_learning(dados, filtros):
    """Sistema de Machine Learning."""
    st.markdown("<h1 class='main-header'>Sistema de Machine Learning</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    periodo = filtros.get('periodo', '12m')
    
    st.info(f"📊 Modelo baseado em: **{periodo.upper()}**")
    
    st.subheader("Configuração do Modelo de Scoring")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        peso_score = st.slider("Peso: Score de Risco", 0, 100, 40, 5)
    
    with col2:
        peso_saldo = st.slider("Peso: Impacto Financeiro", 0, 100, 30, 5)
    
    with col3:
        peso_estagnacao = st.slider("Peso: Estagnação", 0, 100, 30, 5)
    
    soma_pesos = peso_score + peso_saldo + peso_estagnacao
    if soma_pesos > 0:
        peso_score_norm = peso_score / soma_pesos
        peso_saldo_norm = peso_saldo / soma_pesos
        peso_estagnacao_norm = peso_estagnacao / soma_pesos
    else:
        peso_score_norm = peso_saldo_norm = peso_estagnacao_norm = 1/3
    
    st.info(f"Pesos normalizados: Score={peso_score_norm:.2f}, Saldo={peso_saldo_norm:.2f}, Estagnação={peso_estagnacao_norm:.2f}")
    
    if st.button("Executar Modelo de ML", type="primary"):
        with st.spinner("Processando modelo..."):
            df_ml = calcular_score_ml(
                df_filtrado,
                periodo=periodo,
                peso_score=peso_score_norm,
                peso_saldo=peso_saldo_norm,
                peso_estagnacao=peso_estagnacao_norm
            )
        
        st.success("Modelo executado com sucesso!")
        
        st.subheader("Distribuição de Alertas ML")
        
        dist_alertas = df_ml['nivel_alerta_ml'].value_counts().reset_index()
        dist_alertas.columns = ['Nível', 'Quantidade']
        dist_alertas['Percentual'] = (dist_alertas['Quantidade'] / len(df_ml) * 100)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            for _, row in dist_alertas.iterrows():
                nivel = row['Nível']
                qtd = row['Quantidade']
                perc = row['Percentual']
                
                saldo_nivel = df_ml[df_ml['nivel_alerta_ml'] == nivel]['saldo_credor_atual'].sum()
                
                if nivel == 'EMERGENCIAL':
                    st.markdown(
                        f"<div class='alert-extremo'>"
                        f"<b>{nivel}</b>: {qtd:,} ({perc:.1f}%)<br>"
                        f"Saldo: R$ {saldo_nivel/1e6:.1f}M"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                elif nivel == 'CRÍTICO':
                    st.markdown(
                        f"<div class='alert-critico'>"
                        f"<b>{nivel}</b>: {qtd:,} ({perc:.1f}%)<br>"
                        f"Saldo: R$ {saldo_nivel/1e6:.1f}M"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                elif nivel == 'ALTO':
                    st.markdown(
                        f"<div class='alert-alto'>"
                        f"<b>{nivel}</b>: {qtd:,} ({perc:.1f}%)<br>"
                        f"Saldo: R$ {saldo_nivel/1e6:.1f}M"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.info(f"**{nivel}**: {qtd:,} ({perc:.1f}%) | Saldo: R$ {saldo_nivel/1e6:.1f}M")
        
        with col2:
            fig = px.pie(
                dist_alertas,
                values='Quantidade',
                names='Nível',
                title='Distribuição por Nível de Alerta ML',
                template=filtros['tema'],
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.subheader("Top 50 Empresas Prioritárias (ML)")
        
        top_ml = df_ml.nlargest(50, 'score_ml')
        
        col_class = get_col_name('classificacao_risco', periodo)
        
        colunas_ml = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe',
                      'score_ml', 'nivel_alerta_ml']
        if col_class in top_ml.columns:
            colunas_ml.append(col_class)
        colunas_ml.extend(['saldo_credor_atual', 'qtde_ultimos_12m_iguais'])
        
        top_ml_display = top_ml[[col for col in colunas_ml if col in top_ml.columns]].copy()
        
        top_ml_display.insert(0, 'Rank', range(1, len(top_ml_display) + 1))
        
        st.dataframe(
            top_ml_display.style.format({
                'score_ml': '{:.1f}',
                'saldo_credor_atual': 'R$ {:,.2f}'
            }),
            use_container_width=True,
            height=600
        )

def pagina_padroes_abuso(dados, filtros):
    """Análise de padrões de abuso de crédito."""
    st.markdown("<h1 class='main-header'>⚠️ Padrões de Abuso de Crédito</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    periodo = filtros.get('periodo', '12m')
    
    st.info(f"📊 Análise baseada em: **{periodo.upper()}**")
    
    st.markdown("""
    <div class='info-box'>
    <b>Objetivo:</b> Identificar empresas que fazem créditos sem correspondentes débitos, 
    acumulando saldos credores indevidos há anos.
    </div>
    """, unsafe_allow_html=True)
    
    df_analise = df.copy()
    
    col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
    col_desvio = get_col_name('desvio_padrao_credito', periodo)
    col_media = get_col_name('media_credito', periodo)
    
    # 1. Empresas que SÓ acumulam
    if col_cresc in df_analise.columns:
        df_analise['so_acumula'] = (
            (df_analise[col_cresc] > 0) & 
            (df_analise['saldo_credor_atual'] > 10000)
        )
    else:
        df_analise['so_acumula'] = False
    
    # 2. Empresas com saldo alto e estagnado
    df_analise['estagnado_alto'] = (
        (df_analise['qtde_ultimos_12m_iguais'] >= 6) & 
        (df_analise['saldo_credor_atual'] > 50000)
    )
    
    # 3. Crescimento anormal
    if col_cresc in df_analise.columns:
        df_analise['crescimento_anormal'] = df_analise[col_cresc] > 500
    else:
        df_analise['crescimento_anormal'] = False
    
    # 4. Baixa variação com saldo alto
    if col_desvio in df_analise.columns and col_media in df_analise.columns:
        df_analise['baixa_variacao'] = (
            (df_analise[col_desvio] < 1000) & 
            (df_analise[col_media] > 50000)
        )
    else:
        df_analise['baixa_variacao'] = False
    
    padroes = {
        'Só Acumula (crescimento contínuo)': df_analise['so_acumula'].sum(),
        'Estagnado com Saldo Alto': df_analise['estagnado_alto'].sum(),
        'Crescimento Anormal (>500%)': df_analise['crescimento_anormal'].sum(),
        'Baixa Variação + Saldo Alto': df_analise['baixa_variacao'].sum()
    }
    
    st.subheader("📊 Resumo de Padrões Suspeitos")

    col1, col2, col3, col4 = st.columns(4)

    tooltips_padroes = {
        'Só Acumula (crescimento contínuo)': "Empresas que apenas acumulam crédito (crescimento positivo) sem utilização, com saldo > R$ 10.000",
        'Estagnado com Saldo Alto': "Empresas com saldo > R$ 50.000 e sem movimentação há 6+ meses. Padrão típico de acumulação irregular",
        'Crescimento Anormal (>500%)': "Empresas com crescimento de saldo credor superior a 500% no período. Indica comportamento atípico",
        'Baixa Variação + Saldo Alto': "Empresas com desvio padrão < R$ 1.000 mas média > R$ 50.000. Valores artificialmente constantes"
    }

    items = list(padroes.items())
    for idx, (padrao, qtd) in enumerate(items):
        with [col1, col2, col3, col4][idx]:
            st.metric(padrao, f"{qtd:,}", help=tooltips_padroes.get(padrao, ""))
    
    df_padroes = pd.DataFrame(list(padroes.items()), columns=['Padrão', 'Quantidade'])
    
    fig = px.bar(
        df_padroes,
        x='Quantidade',
        y='Padrão',
        orientation='h',
        title='Quantidade de Empresas por Padrão Suspeito',
        template=filtros['tema'],
        color='Quantidade',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🎯 Top 50 Empresas com Múltiplos Padrões Suspeitos")
    
    df_analise['qtd_padroes'] = (
        df_analise['so_acumula'].astype(int) +
        df_analise['estagnado_alto'].astype(int) +
        df_analise['crescimento_anormal'].astype(int) +
        df_analise['baixa_variacao'].astype(int)
    )
    
    df_multiplos = df_analise[df_analise['qtd_padroes'] >= 2].nlargest(50, 'qtd_padroes')
    
    col_class = get_col_name('classificacao_risco', periodo)
    
    colunas_mult = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe',
                    'saldo_credor_atual', 'qtd_padroes', 'qtde_ultimos_12m_iguais']
    
    if col_cresc in df_multiplos.columns:
        colunas_mult.insert(5, col_cresc)
    if col_class in df_multiplos.columns:
        colunas_mult.append(col_class)
    
    df_mult_display = df_multiplos[[col for col in colunas_mult if col in df_multiplos.columns]].copy()
    
    format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
    if col_cresc in df_mult_display.columns:
        format_dict[col_cresc] = '{:+.1f}%'
    
    st.dataframe(
        df_mult_display.style.format(format_dict),
        use_container_width=True,
        height=600
    )
    
    st.divider()
    st.subheader("🚨 Alertas Críticos")
    
    col1, col2 = st.columns(2)
    
    col_saldo_atras = get_col_name('saldo_atras', periodo)
    
    with col1:
        if col_saldo_atras in df_analise.columns:
            zerou_voltou = df_analise[
                (df_analise[col_saldo_atras] < 1000) & 
                (df_analise['saldo_credor_atual'] > 50000)
            ]
        else:
            zerou_voltou = pd.DataFrame()
        
        st.markdown(
            f"<div class='alert-critico'>"
            f"<b>Zerou Saldo e Voltou a Acumular</b><br>"
            f"{len(zerou_voltou):,} empresas<br>"
            f"Saldo total: R$ {zerou_voltou['saldo_credor_atual'].sum()/1e6:.1f}M"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        if col_cresc in df_analise.columns:
            explosivo = df_analise[
                (df_analise[col_cresc] > 1000) &
                (df_analise['saldo_credor_atual'] > 100000)
            ]
        else:
            explosivo = pd.DataFrame()
        
        st.markdown(
            f"<div class='alert-critico'>"
            f"<b>Crescimento Explosivo (>1000%)</b><br>"
            f"{len(explosivo):,} empresas<br>"
            f"Saldo total: R$ {explosivo['saldo_credor_atual'].sum()/1e6:.1f}M"
            f"</div>",
            unsafe_allow_html=True
        )

def pagina_empresas_inativas(dados, filtros):
    """Análise de empresas inativas com saldo credor."""
    st.markdown("<h1 class='main-header'>🔍 Empresas Inativas com Saldo Credor</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    st.markdown("""
    <div class='info-box'>
    <b>Problema:</b> Muitas empresas inativas mantêm saldos credores há anos, 
    sem movimentação de débitos. Com a reforma tributária, poderão solicitar ressarcimento.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='alert-alto'>
    <b>⚠️ Nota Técnica:</b> A coluna qtde_ultimos_12m_iguais está limitada a 13 meses (últimos 12 + atual).
    Para análises de períodos maiores, usamos a comparação direta de saldos entre períodos (12m e 60m atrás).
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("⚙️ Configurar Critérios de Inatividade")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        criterio_inatividade = st.selectbox(
            "Critério de Inatividade",
            [
                "Saldo idêntico há 12 meses",
                "Saldo idêntico há 60 meses", 
                "Variação < R$ 100 em 12m",
                "Variação < R$ 100 em 60m",
                "Variação < 1% em 12m",
                "Variação < 1% em 60m",
                "Sem movimento 6+ meses (últimos 12m)",
                "Sem movimento 12+ meses (últimos 12m)"
            ],
            index=0,
            help="Escolha como identificar empresas inativas"
        )
    
    with col2:
        saldo_minimo = st.number_input("Saldo mínimo (R$)", 0, 1000000, 10000, 10000)
    
    with col3:
        incluir_baixo_risco = st.checkbox("Incluir baixo risco", value=True)
    
    # ✅ NOVA LÓGICA: Aplicar filtro baseado no critério escolhido
    if criterio_inatividade == "Saldo idêntico há 12 meses":
        df_inativas = df[
            (df['saldo_credor_atual'] == df['saldo_12m_atras']) &
            (df['saldo_credor_atual'] >= saldo_minimo)
        ].copy()
        desc_criterio = "Empresas com saldo **exatamente igual** há 12 meses"
        
    elif criterio_inatividade == "Saldo idêntico há 60 meses":
        df_inativas = df[
            (df['saldo_credor_atual'] == df['saldo_60m_atras']) &
            (df['saldo_credor_atual'] >= saldo_minimo) &
            (df['saldo_60m_atras'].notna())
        ].copy()
        desc_criterio = "Empresas com saldo **exatamente igual** há 60 meses (5 anos!)"
        
    elif criterio_inatividade == "Variação < R$ 100 em 12m":
        df_inativas = df[
            (abs(df['saldo_credor_atual'] - df['saldo_12m_atras']) < 100) &
            (df['saldo_credor_atual'] >= saldo_minimo)
        ].copy()
        desc_criterio = "Empresas com variação **menor que R$ 100** em 12 meses"
        
    elif criterio_inatividade == "Variação < R$ 100 em 60m":
        df_inativas = df[
            (abs(df['saldo_credor_atual'] - df['saldo_60m_atras']) < 100) &
            (df['saldo_credor_atual'] >= saldo_minimo) &
            (df['saldo_60m_atras'].notna())
        ].copy()
        desc_criterio = "Empresas com variação **menor que R$ 100** em 60 meses"
        
    elif criterio_inatividade == "Variação < 1% em 12m":
        df_inativas = df[
            (abs(df['saldo_credor_atual'] - df['saldo_12m_atras']) / df['saldo_12m_atras'].replace(0, 1) < 0.01) &
            (df['saldo_credor_atual'] >= saldo_minimo) &
            (df['saldo_12m_atras'] > 0)
        ].copy()
        desc_criterio = "Empresas com variação **menor que 1%** em 12 meses"
        
    elif criterio_inatividade == "Variação < 1% em 60m":
        df_inativas = df[
            (abs(df['saldo_credor_atual'] - df['saldo_60m_atras']) / df['saldo_60m_atras'].replace(0, 1) < 0.01) &
            (df['saldo_credor_atual'] >= saldo_minimo) &
            (df['saldo_60m_atras'] > 0)
        ].copy()
        desc_criterio = "Empresas com variação **menor que 1%** em 60 meses"
        
    elif criterio_inatividade == "Sem movimento 6+ meses (últimos 12m)":
        df_inativas = df[
            (df['qtde_ultimos_12m_iguais'] >= 6) &
            (df['saldo_credor_atual'] >= saldo_minimo)
        ].copy()
        desc_criterio = "Empresas **sem alteração no saldo** por 6+ meses consecutivos"
        
    else:  # "Sem movimento 12+ meses (últimos 12m)"
        df_inativas = df[
            (df['qtde_ultimos_12m_iguais'] >= 12) &
            (df['saldo_credor_atual'] >= saldo_minimo)
        ].copy()
        desc_criterio = "Empresas **completamente congeladas** há 12+ meses"
    
    periodo = filtros.get('periodo', '12m')
    col_class = get_col_name('classificacao_risco', periodo)
    
    if not incluir_baixo_risco and col_class in df_inativas.columns:
        df_inativas = df_inativas[df_inativas[col_class] != 'BAIXO']
    
    # Mostrar critério aplicado
    st.info(f"📋 **Critério:** {desc_criterio}")
    
    st.subheader("📊 Indicadores de Inatividade")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Empresas Inativas", f"{len(df_inativas):,}",
                 help="Total de empresas que atendem ao critério de inatividade selecionado")

    with col2:
        saldo_total_inativo = df_inativas['saldo_credor_atual'].sum()
        st.metric("Saldo Total", f"R$ {saldo_total_inativo/1e6:.1f}M",
                 help="Soma dos saldos credores de todas as empresas classificadas como inativas")

    with col3:
        media_saldo = df_inativas['saldo_credor_atual'].mean() if len(df_inativas) > 0 else 0
        st.metric("Saldo Médio", f"R$ {media_saldo/1e3:.1f}K",
                 help="Média do saldo credor por empresa inativa")

    with col4:
        taxa_inatividade = len(df_inativas) / len(df) * 100 if len(df) > 0 else 0
        st.metric("Taxa Inatividade", f"{taxa_inatividade:.1f}%",
                 help="Percentual de empresas inativas em relação ao total da base")
    
    # Adicionar comparação entre períodos
    if len(df_inativas) > 0:
        st.divider()
        st.subheader("🔄 Comparação Temporal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Variação 12 meses
            df_inativas['var_12m'] = abs(df_inativas['saldo_credor_atual'] - df_inativas['saldo_12m_atras'])
            media_var_12m = df_inativas['var_12m'].mean()
            st.metric("Variação Média 12m", f"R$ {media_var_12m:,.2f}",
                     help="Média da variação absoluta do saldo credor nos últimos 12 meses para empresas inativas")

            zeradas_12m = len(df_inativas[df_inativas['var_12m'] == 0])
            st.caption(f"✓ {zeradas_12m:,} empresas com variação zero")

        with col2:
            # Variação 60 meses
            if 'saldo_60m_atras' in df_inativas.columns:
                df_inativas['var_60m'] = abs(df_inativas['saldo_credor_atual'] - df_inativas['saldo_60m_atras'])
                media_var_60m = df_inativas['var_60m'].mean()
                st.metric("Variação Média 60m", f"R$ {media_var_60m:,.2f}",
                         help="Média da variação absoluta do saldo credor nos últimos 60 meses para empresas inativas")

                zeradas_60m = len(df_inativas[df_inativas['var_60m'] == 0])
                st.caption(f"✓ {zeradas_60m:,} empresas com variação zero")
    
    st.divider()
    
    st.subheader("📋 Distribuição por Situação Cadastral")
    
    dist_situacao = df_inativas['nm_sit_cadastral'].value_counts().reset_index()
    dist_situacao.columns = ['Situação', 'Quantidade']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(
            dist_situacao,
            values='Quantidade',
            names='Situação',
            title='Situação Cadastral das Inativas',
            template=filtros['tema']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        por_gerfe = df_inativas.groupby('nm_gerfe')['saldo_credor_atual'].agg(['count', 'sum']).reset_index()
        por_gerfe.columns = ['GERFE', 'Quantidade', 'Saldo Total']
        por_gerfe = por_gerfe.nlargest(10, 'Saldo Total')
        
        fig = px.bar(
            por_gerfe,
            x='Saldo Total',
            y='GERFE',
            orientation='h',
            title='Top 10 GERFEs - Saldo Inativo',
            template=filtros['tema']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("📝 Lista de Empresas Inativas (Top 100)")
    
    colunas_lista = ['nu_cnpj', 'nm_razao_social', 'nm_sit_cadastral', 'nm_gerfe',
                     'saldo_credor_atual', 'saldo_12m_atras', 'saldo_60m_atras']
    
    if 'var_12m' in df_inativas.columns:
        colunas_lista.append('var_12m')
    if 'var_60m' in df_inativas.columns:
        colunas_lista.append('var_60m')
    
    if 'qtde_ultimos_12m_iguais' in df_inativas.columns:
        colunas_lista.append('qtde_ultimos_12m_iguais')
    
    if col_class in df_inativas.columns:
        colunas_lista.append(col_class)
    
    if 'flag_empresa_suspeita' in df_inativas.columns:
        colunas_lista.append('flag_empresa_suspeita')
    if 'qtde_indicios_fraude' in df_inativas.columns:
        colunas_lista.append('qtde_indicios_fraude')
    
    df_lista = df_inativas.nlargest(100, 'saldo_credor_atual')[[col for col in colunas_lista if col in df_inativas.columns]].copy()
    
    format_dict = {
        'saldo_credor_atual': 'R$ {:,.2f}',
        'saldo_12m_atras': 'R$ {:,.2f}',
        'saldo_60m_atras': 'R$ {:,.2f}'
    }
    if 'var_12m' in df_lista.columns:
        format_dict['var_12m'] = 'R$ {:,.2f}'
    if 'var_60m' in df_lista.columns:
        format_dict['var_60m'] = 'R$ {:,.2f}'
    
    st.dataframe(
        df_lista.style.format(format_dict),
        use_container_width=True,
        height=600
    )
    
    if st.button("📥 Exportar Lista Completa (CSV)"):
        colunas_export = ['nu_cnpj', 'nm_razao_social', 'nm_sit_cadastral', 'nm_gerfe', 'de_cnae',
                         'saldo_credor_atual', 'saldo_12m_atras', 'saldo_60m_atras']
        
        if 'var_12m' in df_inativas.columns:
            colunas_export.append('var_12m')
        if 'var_60m' in df_inativas.columns:
            colunas_export.append('var_60m')
        if 'qtde_ultimos_12m_iguais' in df_inativas.columns:
            colunas_export.append('qtde_ultimos_12m_iguais')
        
        col_score = get_col_name('score_risco', periodo)
        if col_score in df_inativas.columns:
            colunas_export.append(col_score)
        if col_class in df_inativas.columns:
            colunas_export.append(col_class)
        
        if 'flag_empresa_suspeita' in df_inativas.columns:
            colunas_export.append('flag_empresa_suspeita')
        if 'qtde_indicios_fraude' in df_inativas.columns:
            colunas_export.append('qtde_indicios_fraude')
        
        csv = df_inativas[[col for col in colunas_export if col in df_inativas.columns]].to_csv(
            index=False, encoding='utf-8-sig', sep=';'
        )
        
        st.download_button(
            label="Baixar CSV",
            data=csv.encode('utf-8-sig'),
            file_name=f"empresas_inativas_{criterio_inatividade.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

def pagina_reforma_tributaria(dados, filtros):
    """Análise de impacto da reforma tributária."""
    st.markdown("<h1 class='main-header'>📊 Impacto da Reforma Tributária</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    st.markdown("""
    <div class='info-box'>
    <b>Contexto:</b> Com a reforma tributária, empresas com saldos credores de ICMS poderão 
    solicitar ressarcimento (à vista ou parcelado) e compensação com IBS a partir de 01/01/2027.
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("💰 Valores em Risco de Compensação/Ressarcimento")
    
    col1, col2 = st.columns(2)
    
    periodo = filtros.get('periodo', '12m')
    col_class = get_col_name('classificacao_risco', periodo)
    
    with col1:
        st.markdown("### 🔴 Cenário Pessimista (100%)")
        st.caption("Todas as empresas solicitam ressarcimento")

        total_risco = df['saldo_credor_atual'].sum()
        st.metric("Valor Total em Risco", f"R$ {total_risco/1e9:.2f} Bilhões",
                 help="Soma de todos os saldos credores que poderiam ser objeto de ressarcimento ou compensação com IBS")

        if col_class in df.columns:
            criticos_alto = df[df[col_class].isin(['CRÍTICO', 'ALTO'])]['saldo_credor_atual'].sum()
            st.metric("Apenas Críticos/Alto", f"R$ {criticos_alto/1e9:.2f} Bilhões",
                     help="Soma dos saldos credores apenas de empresas classificadas como CRÍTICO ou ALTO risco")

    with col2:
        st.markdown("### 🟡 Cenário Realista (30-50%)")
        st.caption("Estimativa: 30-50% solicitarão ressarcimento")

        cenario_min = total_risco * 0.3
        cenario_max = total_risco * 0.5

        st.metric("Cenário Mínimo (30%)", f"R$ {cenario_min/1e9:.2f} Bilhões",
                 help="Projeção conservadora: 30% das empresas solicitarão ressarcimento dos créditos")
        st.metric("Cenário Máximo (50%)", f"R$ {cenario_max/1e9:.2f} Bilhões",
                 help="Projeção moderada: 50% das empresas solicitarão ressarcimento dos créditos")
    
    st.divider()
    
    st.subheader("🎯 Empresas com Comportamento Suspeito pós-2023")
    
    col_cresc = get_col_name('crescimento_saldo_percentual', periodo)
    
    if col_cresc in df.columns:
        df_preparando = df[
            (df[col_cresc] > 200) &
            (df['saldo_credor_atual'] > 50000)
        ].copy()
    else:
        df_preparando = pd.DataFrame()
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Empresas Suspeitas", f"{len(df_preparando):,}",
                 help="Empresas com crescimento > 200% e saldo > R$ 50.000, potencialmente se preparando para a reforma")

    with col2:
        if not df_preparando.empty:
            st.metric("Saldo Suspeito", f"R$ {df_preparando['saldo_credor_atual'].sum()/1e6:.1f}M",
                     help="Soma dos saldos credores das empresas com comportamento suspeito pós-2023")
        else:
            st.metric("Saldo Suspeito", "R$ 0.0M", help="Nenhuma empresa com comportamento suspeito identificada")

    with col3:
        if not df_preparando.empty and col_cresc in df_preparando.columns:
            cresc_medio = df_preparando[col_cresc].mean()
            st.metric("Crescimento Médio", f"{cresc_medio:.0f}%",
                     help="Média do crescimento percentual do saldo credor das empresas suspeitas")
        else:
            st.metric("Crescimento Médio", "0%", help="Dados de crescimento não disponíveis")
    
    st.subheader("📈 Evolução do Risco ao Longo do Tempo")
    
    meses = pd.date_range('2023-01', '2027-01', freq='MS')
    valores = []
    base = total_risco
    
    for i, mes in enumerate(meses):
        if mes.year < 2027:
            fator = 1 + (i * 0.02)
            valores.append(base * fator)
        else:
            valores.append(valores[-1])
    
    df_timeline = pd.DataFrame({
        'Data': meses,
        'Valor em Risco': valores
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_timeline['Data'],
        y=df_timeline['Valor em Risco'] / 1e9,
        mode='lines+markers',
        name='Projeção de Risco',
        line=dict(color='red', width=3),
        fill='tozeroy'
    ))
    
    fig.add_shape(
        type="line",
        x0=pd.Timestamp('2027-01-01'),
        x1=pd.Timestamp('2027-01-01'),
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="orange", width=2, dash="dash")
    )
    
    fig.add_annotation(
        x=pd.Timestamp('2027-01-01'),
        y=1.05,
        yref="paper",
        text="Início Compensação IBS",
        showarrow=False,
        font=dict(color="orange")
    )
    
    fig.update_layout(
        title="Projeção de Valores em Risco (Bilhões R$)",
        xaxis_title="Período",
        yaxis_title="Valor (Bilhões R$)",
        template=filtros['tema'],
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🏆 Top 50 Empresas por Impacto na Reforma")
    
    colunas_top = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe',
                   'saldo_credor_atual', 'qtde_ultimos_12m_iguais']
    
    if col_cresc in df.columns:
        colunas_top.append(col_cresc)
    if col_class in df.columns:
        colunas_top.append(col_class)
    
    if 'flag_empresa_suspeita' in df.columns:
        colunas_top.append('flag_empresa_suspeita')
    if 'qtde_indicios_fraude' in df.columns:
        colunas_top.append('qtde_indicios_fraude')
    
    df_top_reforma = df.nlargest(50, 'saldo_credor_atual')[[col for col in colunas_top if col in df.columns]].copy()
    
    format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
    if col_cresc in df_top_reforma.columns:
        format_dict[col_cresc] = '{:+.1f}%'
    
    st.dataframe(
        df_top_reforma.style.format(format_dict),
        use_container_width=True,
        height=600
    )

def pagina_noteiras(dados, filtros):
    """NOVA PÁGINA v2.0 - Análise de Empresas com Noteiras."""
    st.markdown("<h1 class='main-header'>🏢 Análise de Empresas com Noteiras</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    if 'qt_clientes_noteiras' not in df.columns:
        st.warning("⚠️ Dados de noteiras não disponíveis nesta tabela.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    
    st.markdown("""
    <div class='info-box'>
    <b>Objetivo:</b> Identificar empresas que mantêm relacionamento comercial com muitas empresas 
    noteiras (clientes ou fornecedores), o que pode indicar operações fraudulentas.
    </div>
    """, unsafe_allow_html=True)
    
    df_filtrado['total_noteiras'] = (
        df_filtrado['qt_clientes_noteiras'].fillna(0) + 
        df_filtrado['qt_fornecedoras_noteiras'].fillna(0)
    )
    
    df_noteiras = df_filtrado[df_filtrado['total_noteiras'] >= 5].copy()
    
    st.subheader("📊 Panorama de Noteiras")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Empresas com 5+ Noteiras", f"{len(df_noteiras):,}",
                 help="Total de empresas que possuem relacionamento comercial com 5 ou mais empresas noteiras")

    with col2:
        st.metric("Saldo Total", f"R$ {df_noteiras['saldo_credor_atual'].sum()/1e6:.1f}M",
                 help="Soma dos saldos credores das empresas com relacionamento com noteiras")

    with col3:
        media_not = df_noteiras['total_noteiras'].mean() if len(df_noteiras) > 0 else 0
        st.metric("Média Noteiras", f"{media_not:.1f}",
                 help="Média de empresas noteiras (clientes + fornecedores) por empresa analisada")

    with col4:
        if 'flag_empresa_suspeita' in df_noteiras.columns:
            susp = len(df_noteiras[df_noteiras['flag_empresa_suspeita'] == 1])
            st.metric("Suspeitas", f"{susp:,}",
                     help="Quantidade de empresas com noteiras que também estão marcadas como suspeitas pelo sistema")
    
    st.divider()
    
    st.subheader("📈 Distribuição por Quantidade de Noteiras")
    
    df_noteiras['faixa_noteiras'] = pd.cut(
        df_noteiras['total_noteiras'],
        bins=[4, 10, 20, 50, 100, 1000],
        labels=['5-10', '11-20', '21-50', '51-100', '100+']
    )
    
    dist_not = df_noteiras.groupby('faixa_noteiras', observed=True).agg({
        'nu_cnpj': 'count',
        'saldo_credor_atual': 'sum'
    }).reset_index()
    
    dist_not.columns = ['Faixa', 'Qtde', 'Saldo']
    
    if 'flag_empresa_suspeita' in df_noteiras.columns:
        susp_count = df_noteiras.groupby('faixa_noteiras', observed=True)['flag_empresa_suspeita'].sum().reset_index()
        susp_count.columns = ['Faixa', 'Suspeitas']
        dist_not = dist_not.merge(susp_count, on='Faixa', how='left')
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            dist_not,
            x='Faixa',
            y='Qtde',
            title='Empresas por Faixa de Noteiras',
            template=filtros['tema'],
            color='Qtde',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'Suspeitas' in dist_not.columns:
            fig = px.bar(
                dist_not,
                x='Faixa',
                y='Suspeitas',
                title='Empresas Suspeitas por Faixa',
                template=filtros['tema'],
                color='Suspeitas',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🎯 Top 50 Empresas com Mais Noteiras")
    
    periodo = filtros.get('periodo', '12m')
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    
    colunas_not = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe', 'de_cnae',
                   'qt_clientes_noteiras', 'qt_fornecedoras_noteiras', 'total_noteiras',
                   'saldo_credor_atual']
    
    if col_score_comb in df_noteiras.columns:
        colunas_not.append(col_score_comb)
    
    if 'flag_empresa_suspeita' in df_noteiras.columns:
        colunas_not.append('flag_empresa_suspeita')
    if 'qtde_indicios_fraude' in df_noteiras.columns:
        colunas_not.append('qtde_indicios_fraude')
    if 'sn_cancelado_inex_inativ' in df_noteiras.columns:
        colunas_not.append('sn_cancelado_inex_inativ')
    
    df_top_not = df_noteiras.nlargest(50, 'total_noteiras')[[col for col in colunas_not if col in df_noteiras.columns]].copy()
    df_top_not.insert(0, 'Rank', range(1, len(df_top_not) + 1))
    
    format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
    if col_score_comb in df_top_not.columns:
        format_dict[col_score_comb] = '{:.1f}'
    
    st.dataframe(
        df_top_not.style.format(format_dict),
        use_container_width=True,
        height=600
    )

def pagina_declaracoes_zeradas(dados, filtros):
    """NOVA PÁGINA v2.0 - Análise de Declarações Zeradas e Omissões."""
    st.markdown("<h1 class='main-header'>📋 Análise de Declarações Zeradas e Omissões</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    if 'periodos_zerados_normal' not in df.columns:
        st.warning("⚠️ Dados de declarações zeradas não disponíveis nesta tabela.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    
    st.markdown("""
    <div class='info-box'>
    <b>Objetivo:</b> Identificar empresas com padrão de declarações zeradas ou omissões 
    frequentes, que podem indicar subfaturamento ou operações irregulares.
    </div>
    """, unsafe_allow_html=True)
    
    df_filtrado['total_zerados'] = (
        df_filtrado['periodos_zerados_normal'].fillna(0) + 
        df_filtrado['periodos_zerados_simples'].fillna(0)
    )
    
    df_filtrado['total_omissos'] = (
        df_filtrado['periodos_omissos_normal'].fillna(0) + 
        df_filtrado['periodos_omissos_simples'].fillna(0)
    )
    
    df_zeradas = df_filtrado[
        (df_filtrado['total_zerados'] >= 1) | (df_filtrado['total_omissos'] >= 1)
    ].copy()
    
    st.subheader("📊 Panorama de Declarações")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Com Zeradas", f"{len(df_zeradas[df_zeradas['total_zerados'] >= 1]):,}",
                 help="Empresas que apresentaram pelo menos uma declaração com valores zerados")

    with col2:
        st.metric("Com Omissões", f"{len(df_zeradas[df_zeradas['total_omissos'] >= 1]):,}",
                 help="Empresas que deixaram de entregar pelo menos uma declaração obrigatória")

    with col3:
        media_zer = df_zeradas['total_zerados'].mean() if len(df_zeradas) > 0 else 0
        st.metric("Média Zerados", f"{media_zer:.1f}",
                 help="Média de períodos com declarações zeradas por empresa")

    with col4:
        saldo_tot = df_zeradas['saldo_credor_atual'].sum()
        st.metric("Saldo Total", f"R$ {saldo_tot/1e6:.1f}M",
                 help="Soma dos saldos credores de empresas com declarações zeradas ou omissas")
    
    # SEÇÃO CORRIGIDA: Detalhamento de Omissões por Tipo
    st.divider()
    st.subheader("📋 Detalhamento de Omissões (v2.0)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        qtd_omi_dime_n = len(df_zeradas[df_zeradas.get('flag_omissao_dime_normal', 0) == 1])
        perc_dime_n = (qtd_omi_dime_n / len(df_zeradas) * 100) if len(df_zeradas) > 0 else 0
        st.metric("Omissão DIME (Normal)", f"{qtd_omi_dime_n:,}", delta=f"{perc_dime_n:.1f}%",
                 help="Empresas do regime Normal com indício de omissão DIME")
    
    with col2:
        qtd_omi_pgdas_s = len(df_zeradas[df_zeradas.get('flag_omissao_pgdas_simples', 0) == 1])
        perc_pgdas_s = (qtd_omi_pgdas_s / len(df_zeradas) * 100) if len(df_zeradas) > 0 else 0
        st.metric("Omissão PGDAS (Simples)", f"{qtd_omi_pgdas_s:,}", delta=f"{perc_pgdas_s:.1f}%",
                 help="Empresas do Simples Nacional com indício de omissão PGDAS")
    
    # GRÁFICO CORRIGIDO: Distribuição de Omissões por Tipo
    if any([qtd_omi_dime_n, qtd_omi_pgdas_s]):
        st.subheader("📊 Distribuição de Omissões por Tipo")
        
        df_dist_omi = pd.DataFrame({
            'Tipo': ['DIME (Normal)', 'PGDAS (Simples)'],
            'Quantidade': [qtd_omi_dime_n, qtd_omi_pgdas_s]
        })
        
        fig = px.bar(
            df_dist_omi,
            x='Tipo',
            y='Quantidade',
            title='Empresas com Omissões por Tipo de Declaração',
            template=filtros['tema'],
            color='Quantidade',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🎯 Matriz: Zeradas vs Omissões")
    
    matriz_data = []
    for fz in ['0', '1-5', '6-11', '12+']:
        for fo in ['0', '1-2', '3-5', '6+']:
            df_temp = df_filtrado.copy()
            
            if fz == '0':
                df_temp = df_temp[df_temp['total_zerados'] == 0]
            elif fz == '1-5':
                df_temp = df_temp[(df_temp['total_zerados'] >= 1) & (df_temp['total_zerados'] <= 5)]
            elif fz == '6-11':
                df_temp = df_temp[(df_temp['total_zerados'] >= 6) & (df_temp['total_zerados'] <= 11)]
            else:
                df_temp = df_temp[df_temp['total_zerados'] >= 12]
            
            if fo == '0':
                df_temp = df_temp[df_temp['total_omissos'] == 0]
            elif fo == '1-2':
                df_temp = df_temp[(df_temp['total_omissos'] >= 1) & (df_temp['total_omissos'] <= 2)]
            elif fo == '3-5':
                df_temp = df_temp[(df_temp['total_omissos'] >= 3) & (df_temp['total_omissos'] <= 5)]
            else:
                df_temp = df_temp[df_temp['total_omissos'] >= 6]
            
            matriz_data.append({
                'Zeradas': fz,
                'Omissões': fo,
                'Qtde': len(df_temp),
                'Saldo': df_temp['saldo_credor_atual'].sum()
            })
    
    df_matriz = pd.DataFrame(matriz_data)
    
    fig = px.scatter(
        df_matriz,
        x='Zeradas',
        y='Omissões',
        size='Qtde',
        color='Saldo',
        hover_data=['Qtde', 'Saldo'],
        title='Matriz: Declarações Zeradas x Omissões',
        template=filtros['tema'],
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("📝 Top 50 Empresas com Mais Irregularidades")
    
    df_zeradas['total_irregularidades'] = df_zeradas['total_zerados'] + df_zeradas['total_omissos']
    
    periodo = filtros.get('periodo', '12m')
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    
    # COLUNAS CORRIGIDAS
    colunas_zer = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe',
                   'total_zerados', 'total_omissos', 'total_irregularidades',
                   'saldo_credor_atual',
                   'flag_omissao_dime_normal', 'flag_omissao_pgdas_simples']
    
    if col_score_comb in df_zeradas.columns:
        colunas_zer.append(col_score_comb)
    
    if 'flag_empresa_suspeita' in df_zeradas.columns:
        colunas_zer.append('flag_empresa_suspeita')
    if 'qtde_indicios_fraude' in df_zeradas.columns:
        colunas_zer.append('qtde_indicios_fraude')
    
    df_top_zer = df_zeradas.nlargest(50, 'total_irregularidades')[[col for col in colunas_zer if col in df_zeradas.columns]].copy()
    df_top_zer.insert(0, 'Rank', range(1, len(df_top_zer) + 1))
    
    format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
    if col_score_comb in df_top_zer.columns:
        format_dict[col_score_comb] = '{:.1f}'
    
    st.dataframe(
        df_top_zer.style.format(format_dict),
        use_container_width=True,
        height=600
    )

def pagina_alertas_automaticos(dados, filtros):
    """NOVA PÁGINA v2.0 - Sistema de Alertas Automáticos."""
    st.markdown("<h1 class='main-header'>🚨 Sistema de Alertas Automáticos</h1>", unsafe_allow_html=True)
    
    df = dados.get('completo', pd.DataFrame())
    
    if df.empty:
        st.error("Dados não carregados.")
        return
    
    df_filtrado = aplicar_filtros(df, filtros)
    periodo = filtros.get('periodo', '12m')
    
    st.markdown("""
    <div class='info-box'>
    <b>Objetivo:</b> Sistema automatizado de geração de alertas priorizados para 
    empresas que apresentam múltiplos indicadores de risco.
    </div>
    """, unsafe_allow_html=True)
    
    col_score_comb = get_col_name('score_risco_combinado', periodo)
    
    # Função para gerar alertas
    def classificar_alerta(row):
        score_comb = row.get(col_score_comb, row.get(get_col_name('score_risco', periodo), 0))
        cancelada = row.get('sn_cancelado_inex_inativ', 0)
        suspeita = row.get('flag_empresa_suspeita', 0)
        indicios = row.get('qtde_indicios_fraude', 0)
        saldo = row.get('saldo_credor_atual', 0)
        
        if cancelada == 1 and saldo > 100000:
            return 'CRÍTICO: Cancelada com Alto Crédito', 1
        elif suspeita == 1 and indicios >= 10:
            return 'CRÍTICO: 10+ Indícios', 1
        elif score_comb >= 120:
            return 'CRÍTICO: Score 120+', 1
        elif indicios >= 7 and saldo > 500000:
            return 'CRÍTICO: 7+ Indícios + Alto Crédito', 1
        elif suspeita == 1 and row.get('flag_tem_declaracoes_zeradas', 0) == 1 and row.get('flag_tem_omissoes', 0) == 1:
            return 'ALTO: Suspeita + Zeradas + Omissões', 2
        elif score_comb >= 100:
            return 'ALTO: Score 100-119', 2
        elif (row.get('qt_clientes_noteiras', 0) + row.get('qt_fornecedoras_noteiras', 0)) >= 15:
            return 'ALTO: 15+ Noteiras', 2
        elif row.get('qtde_ultimos_12m_iguais', 0) >= 12 and row.get('score_suspeita', 0) > 80:
            return 'ALTO: Congelado 12m + Score Alto', 2
        elif indicios >= 5:
            return 'MÉDIO: 5+ Indícios', 3
        else:
            return 'BAIXO: Monitoramento', 4
    
    df_alertas = df_filtrado.copy()
    df_alertas[['tipo_alerta', 'prioridade']] = df_alertas.apply(
        lambda row: pd.Series(classificar_alerta(row)), axis=1
    )
    
    # Dashboard
    st.subheader("📊 Dashboard de Alertas")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        crit = len(df_alertas[df_alertas['prioridade'] == 1])
        st.metric("CRÍTICOS", f"{crit:,}", delta_color="inverse",
                 help="Alertas de máxima prioridade: canceladas com alto crédito, 10+ indícios, score 120+ ou 7+ indícios com saldo > R$ 500K")

    with col2:
        altos = len(df_alertas[df_alertas['prioridade'] == 2])
        st.metric("ALTOS", f"{altos:,}", delta_color="inverse",
                 help="Alertas de alta prioridade: score 100-119, 15+ noteiras, congelado 12m com score alto")

    with col3:
        medios = len(df_alertas[df_alertas['prioridade'] == 3])
        st.metric("MÉDIOS", f"{medios:,}",
                 help="Alertas de média prioridade: 5+ indícios de fraude")

    with col4:
        baixos = len(df_alertas[df_alertas['prioridade'] == 4])
        st.metric("BAIXOS", f"{baixos:,}",
                 help="Alertas de baixa prioridade: empresas para monitoramento contínuo")
    
    # Distribuição por tipo
    dist_alertas = df_alertas['tipo_alerta'].value_counts().reset_index()
    dist_alertas.columns = ['Tipo', 'Quantidade']
    
    fig = px.bar(
        dist_alertas,
        x='Quantidade',
        y='Tipo',
        orientation='h',
        title='Distribuição por Tipo de Alerta',
        template=filtros['tema'],
        color='Quantidade',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("🎯 Top 100 Alertas Prioritários")
    
    col_score = get_col_name('score_risco', periodo)
    
    df_top = df_alertas.sort_values(['prioridade', col_score_comb if col_score_comb in df_alertas.columns else col_score], 
                                     ascending=[True, False]).head(100)
    
    colunas_alert = ['nu_cnpj', 'nm_razao_social', 'nm_gerfe',
                     'tipo_alerta', 'prioridade', 'saldo_credor_atual']
    
    if col_score_comb in df_top.columns:
        colunas_alert.insert(5, col_score_comb)
    if 'flag_empresa_suspeita' in df_top.columns:
        colunas_alert.append('flag_empresa_suspeita')
    if 'qtde_indicios_fraude' in df_top.columns:
        colunas_alert.append('qtde_indicios_fraude')
    if 'sn_cancelado_inex_inativ' in df_top.columns:
        colunas_alert.append('sn_cancelado_inex_inativ')
    
    df_display = df_top[[col for col in colunas_alert if col in df_top.columns]].copy()
    df_display.insert(0, 'ID', range(1, len(df_display) + 1))
    
    format_dict = {'saldo_credor_atual': 'R$ {:,.2f}'}
    if col_score_comb in df_display.columns:
        format_dict[col_score_comb] = '{:.1f}'
    
    st.dataframe(
        df_display.style.format(format_dict),
        use_container_width=True,
        height=600
    )
    
    # Exportar
    if st.button("📥 Exportar Alertas (CSV)"):
        csv = df_top[[col for col in colunas_alert if col in df_top.columns]].to_csv(
            index=False, encoding='utf-8-sig', sep=';'
        )
        
        st.download_button(
            label="Baixar CSV",
            data=csv.encode('utf-8-sig'),
            file_name=f"alertas_{periodo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

def pagina_guia_cancelamento(dados, filtros):
    """Exibe o Guia de Cancelamento de IE."""
    st.markdown("<h1 class='main-header'>📖 Guia de Cancelamento de Inscrição Estadual</h1>", unsafe_allow_html=True)
    
    try:
        import os
        
        possible_paths = [
            'static/guia.html',
            './static/guia.html',
            os.path.join(os.path.dirname(__file__), 'static', 'guia.html'),
            'guia.html'
        ]
        
        html_content = None
        used_path = None
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                used_path = path
                break
        
        if html_content:
            st.success(f"✅ Guia carregado com sucesso!")
            
            import streamlit.components.v1 as components
            
            components.html(html_content, height=800, scrolling=True)
            
        else:
            st.error("❌ Arquivo guia.html não encontrado!")
            st.info("📁 Certifique-se de que o arquivo está em uma das seguintes localizações:")
            for path in possible_paths:
                st.code(path)
            
            st.warning("💡 **Solução:** Coloque o arquivo guia.html na pasta 'static' no mesmo diretório do seu app.py")
            
    except Exception as e:
        st.error(f"Erro ao carregar o guia: {str(e)}")
        st.exception(e)

def pagina_sobre(dados, filtros):
    """Página sobre o sistema."""
    st.markdown("<h1 class='main-header'>Sobre o Sistema CRED-CANCEL v2.0</h1>", unsafe_allow_html=True)
    
    texto_sobre = """
    ## Sistema de Análise de Créditos ICMS Acumulados
    
    ### Versão 2.0 - Com Análise 12 e 60 Meses + Enriquecimento
    
    #### Descrição
    
    O Sistema CRED-CANCEL é uma ferramenta desenvolvida pela Receita Estadual de Santa Catarina para 
    monitoramento e análise de créditos acumulados de ICMS, agora com camada avançada de 
    detecção de fraudes, suspeitas fiscais e análise temporal expandida.
    
    #### Funcionalidades v2.0
    
    - **Análise Temporal Dual**: Comparação entre 12 meses (recente) e 60 meses (histórico)
    - **Análise Comparativa**: Identificação de divergências entre períodos
    - **Análise de Suspeitas**: Empresas marcadas como suspeitas com scores de IA
    - **Indícios de Fraude**: Múltiplos indicadores de fraude por empresa
    - **Cancelamentos**: Empresas canceladas ou inexistentes com crédito
    - **Declarações Zeradas**: Análise de padrões de subfaturamento
    - **Noteiras**: Identificação de relacionamento com empresas noteiras
    - **Score Combinado**: Pontuação integrando todos os indicadores de risco
    - **Alertas Automáticos**: Sistema de priorização inteligente
    - **Machine Learning**: Modelo de scoring para priorização de ações
    - **Análise Setorial**: Têxtil, Metal-Mecânico e Tecnologia
    - **Padrões de Abuso**: Identificação de comportamentos anômalos
    - **Empresas Inativas**: Monitoramento de saldos sem movimentação
    - **Reforma Tributária**: Projeção de impactos financeiros
    
    #### Novidades da Versão 2.0
    
    - 📊 Análise de 12 e 60 meses (Out/2024-Set/2025 vs Set/2020-Set/2025)
    - 🔄 Modo comparativo entre períodos
    - 📈 Identificação de padrões temporais
    - 🚨 Sistema de alertas automáticos por prioridade
    - 🎯 Score combinado considerando enriquecimento
    - 📋 Análise de declarações zeradas e omissões
    - 🏢 Detecção de relacionamento com noteiras
    - ⚠️ Múltiplos indícios de fraude por empresa
    - 🔍 Filtros avançados de fraude na sidebar
    - 📊 Mais de 13 páginas de análise
    
    ### Desenvolvimento
    
    **Versão:** 2.0 (com Análise 12/60 Meses + Enriquecimento)  
    **Data:** Outubro 2025
    """
    
    st.markdown(texto_sobre)
    
    st.subheader("Estatísticas da Base Atual")
    
    df = dados.get('completo', pd.DataFrame())
    
    if not df.empty:
        kpis = calcular_kpis_gerais(df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Empresas", f"{kpis['total_empresas']:,}",
                     help="Total de empresas com saldo credor de ICMS na base de dados")

        with col2:
            st.metric("Saldo Total", f"R$ {kpis['saldo_total']/1e9:.2f}B",
                     help="Soma de todos os saldos credores de ICMS acumulados")

        with col3:
            st.metric("Empresas Suspeitas", f"{kpis['empresas_suspeitas']:,}",
                     help="Total de empresas identificadas como suspeitas pelo sistema de IA")

        with col4:
            st.metric("Atualização", datetime.now().strftime('%d/%m/%Y'),
                     help="Data e hora da última atualização dos dados exibidos")

# =============================================================================
# 8. FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """Função principal do dashboard."""
    
    st.sidebar.title("Sistema CRED-CANCEL v2.0")
    st.sidebar.caption("Análise de Créditos ICMS - 12 e 60 Meses")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Menu de Navegação")
    
    paginas = [
        "Dashboard Executivo",
        "🔄 Comparativo 12m vs 60m",
        "🚨 Análise de Suspeitas",
        "Ranking de Empresas",
        "Análise Setorial",
        "Drill-Down Empresa",
        "Machine Learning",
        "⚠️ Padrões de Abuso",
        "🔍 Empresas Inativas",
        "📊 Reforma Tributária",
        "🏢 Empresas com Noteiras",
        "📋 Declarações Zeradas",
        "🚨 Alertas Automáticos",
        "📖 Guia de Cancelamento IE",
        "Sobre o Sistema"
    ]
    
    pagina_selecionada = st.sidebar.radio(
        "Selecione:",
        paginas,
        label_visibility="collapsed"
    )
    
    engine = get_impala_engine()
    
    if engine is None:
        st.error("Não foi possível conectar ao banco de dados.")
        return
    
    with st.spinner('Carregando dados...'):
        dados = carregar_dados_creditos(engine)
    
    if not dados or dados.get('completo', pd.DataFrame()).empty:
        st.error("Falha no carregamento dos dados.")
        return
    
    df_principal = dados.get('completo', pd.DataFrame())
    if not df_principal.empty:
        st.sidebar.success(f"{len(df_principal):,} registros carregados")
        
        kpis = calcular_kpis_gerais(df_principal)
        
        info_text = f"{kpis['total_empresas']:,} empresas\n\nR$ {kpis['saldo_total']/1e9:.2f}B total\n\n{kpis['criticos']:,} casos críticos"
        
        if kpis['empresas_suspeitas'] > 0:
            info_text += f"\n\n{kpis['empresas_suspeitas']:,} suspeitas"
        
        st.sidebar.info(info_text)
    
    filtros = criar_filtros_sidebar(dados)
    
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("Informações"):
        st.caption(f"**Versão:** 2.0 (12m + 60m)")
        st.caption(f"**Atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.caption(f"**Dev:** Tiago Severo - AFRE")
    
    funcoes = {
        "Dashboard Executivo": pagina_dashboard_executivo,
        "🔄 Comparativo 12m vs 60m": pagina_comparativo_periodos,
        "🚨 Análise de Suspeitas": pagina_analise_suspeitas,
        "Ranking de Empresas": pagina_ranking_empresas,
        "Análise Setorial": pagina_analise_setorial,
        "Drill-Down Empresa": pagina_drill_down_empresa,
        "Machine Learning": pagina_machine_learning,
        "⚠️ Padrões de Abuso": pagina_padroes_abuso,
        "🔍 Empresas Inativas": pagina_empresas_inativas,
        "📊 Reforma Tributária": pagina_reforma_tributaria,
        "🏢 Empresas com Noteiras": pagina_noteiras,
        "📋 Declarações Zeradas": pagina_declaracoes_zeradas,
        "🚨 Alertas Automáticos": pagina_alertas_automaticos,
        "📖 Guia de Cancelamento IE": pagina_guia_cancelamento,
        "Sobre o Sistema": pagina_sobre
    }
    
    try:
        funcoes[pagina_selecionada](dados, filtros)
    except Exception as e:
        st.error(f"Erro ao carregar a página: {str(e)}")
        st.exception(e)
    
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #666;'>"
        f"Sistema CRED-CANCEL v2.0 | SEF/SC | "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
        f"</div>",
        unsafe_allow_html=True
    )

# =============================================================================
# 9. EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    main()