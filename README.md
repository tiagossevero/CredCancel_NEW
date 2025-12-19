# CRED-CANCEL v2.0

**Dashboard Avançado de Análise de Créditos Acumulados de ICMS e Detecção de Fraudes**

Sistema desenvolvido pela **Receita Estadual de Santa Catarina (SEFAZ-SC)** para monitoramento e análise de empresas com créditos acumulados de ICMS, detecção de atividades fraudulentas e suporte à decisão para cancelamento de Inscrição Estadual.

---

## Visão Geral

O CRED-CANCEL v2.0 é uma plataforma de analytics de nível empresarial que integra:
- Análise temporal dupla (12 meses recentes vs 60 meses históricos)
- Indicadores de enriquecimento de fraude
- Machine Learning para priorização de empresas
- Visualizações interativas para tomada de decisão

---

## Funcionalidades Principais

### 15 Páginas de Análise

| Página | Descrição |
|--------|-----------|
| **Dashboard Executivo** | Resumo executivo com KPIs principais |
| **Comparativo 12m vs 60m** | Análise período-a-período comparando dados de 12 e 60 meses |
| **Análise de Suspeitas** | Detecção de fraudes e análise de empresas suspeitas |
| **Ranking de Empresas** | Empresas ranqueadas por score, saldo, crescimento, etc. |
| **Análise Setorial** | Análise específica por setor (Têxtil, Metal-Mecânico, Tecnologia) |
| **Drill-Down Empresa** | Análise detalhada a nível de empresa individual |
| **Machine Learning** | Scoring baseado em ML para priorização |
| **Padrões de Abuso** | Identificação de comportamentos anômalos |
| **Empresas Inativas** | Empresas inativas com créditos acumulados |
| **Reforma Tributária** | Projeções de impacto da reforma tributária |
| **Empresas com Noteiras** | Detecção de relacionamentos com empresas de fachada |
| **Declarações Zeradas** | Análise de padrões de subfaturamento |
| **Alertas Automáticos** | Sistema de alertas inteligentes baseado em prioridade |
| **Guia de Cancelamento IE** | Guia para cancelamento de Inscrição Estadual |
| **Sobre o Sistema** | Documentação do sistema |

### Métricas e Indicadores

- **Score de Risco**: Cálculo para períodos de 12m e 60m
- **Classificação de Risco Combinado**: Integração de indicadores de fraude
- **Análise de Saldo**: Rastreamento de crescimento e evolução
- **Indicadores de Fraude**: Múltiplos sinais suspeitos por empresa
- **Detecção de Omissão**: DIME Normal e PGDAS Simplificado
- **Identificação de Estagnação**: Meses sem alterações

### Sistema de Filtros

- Classificações de risco (CRÍTICO, ALTO, MÉDIO, BAIXO)
- Saldo mínimo de crédito
- Período de estagnação (0-60 meses)
- Filtragem por GERFE (escritório regional)
- Filtros específicos de fraude

---

## Tecnologias Utilizadas

### Framework Principal
- **Streamlit** - Framework de aplicação web interativa

### Processamento de Dados
- **Python 3.8+** - Linguagem principal
- **Pandas** - Manipulação e análise de dados
- **NumPy** - Computação numérica

### Banco de Dados
- **Apache Impala** - Engine de consulta SQL distribuída
- **SQLAlchemy** - ORM e gerenciamento de conexões

### Visualização
- **Plotly Express** - Visualizações de dados interativas
- **Plotly Graph Objects** - Gráficos personalizados
- **Plotly Subplots** - Composição de múltiplos gráficos

### Segurança
- **hashlib** - Hashing de senhas
- **SSL/TLS** - Conexões seguras com banco de dados

---

## Pré-requisitos

- Python >= 3.8
- Acesso ao banco de dados Impala da SEFAZ-SC
- Credenciais LDAP válidas

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd CredCancel_NEW
```

### 2. Instale as dependências

```bash
pip install streamlit pandas numpy plotly sqlalchemy impyla
```

### 3. Configure as credenciais do Streamlit

Crie o arquivo `~/.streamlit/secrets.toml`:

```toml
[impala_credentials]
user = "seu_usuario"
password = "sua_senha"
```

### 4. Configure a senha da aplicação

Edite a linha 5 do arquivo `CRED (3).py`:

```python
SENHA = "sua_senha_desejada"
```

---

## Execução

```bash
streamlit run "CRED (3).py"
```

A aplicação estará disponível em: `http://localhost:8501`

---

## Estrutura do Projeto

```
CredCancel_NEW/
├── CRED (3).py                 # Aplicação principal Streamlit (~3.400 linhas)
├── CREDITO.ipynb               # Notebook de análise de dados (2.6 MB)
├── CREDITO-Exemplo (3).ipynb   # Notebook de exemplo/referência
├── CRED - SQL VALIDAR.ipynb    # Notebook de validação SQL
├── CRED-CANCEL.json            # Exportação de queries Hue/Impala
├── CANCEL (1).json             # Exportação de queries Hue/Impala
└── README.md                   # Este arquivo
```

---

## Configuração do Banco de Dados

### Conexão Impala

```python
IMPALA_HOST = 'bdaworkernode02.sef.sc.gov.br'
IMPALA_PORT = 21050
DATABASE = 'teste'
AUTH_MECHANISM = 'LDAP'
USE_SSL = True
```

### Tabelas Necessárias

| Tabela | Descrição |
|--------|-----------|
| `teste.credito_dime_completo` | Tabela principal de dados (12m e 60m) |
| `teste.credito_dime_textil` | Dados do setor têxtil |
| `teste.credito_dime_metalmec` | Dados do setor metal-mecânico |
| `teste.credito_dime_tech` | Dados do setor de tecnologia |
| `usr_sat_ods.vw_cad_contrib` | View do cadastro de contribuintes |

### Colunas Principais

A aplicação espera colunas para ambos os períodos (12 e 60 meses):

- `saldo_credor_atual`, `saldo_12m_atras`, `saldo_60m_atras`
- `score_risco_12m`, `score_risco_60m`
- `classificacao_risco_12m`, `classificacao_risco_60m`
- `score_risco_combinado_12m`, `score_risco_combinado_60m`
- Flags e indicadores de fraude (10+ campos de enriquecimento)

---

## Arquitetura

```
┌─────────────────────────────────────────┐
│   Aplicação Web Streamlit               │
│   (CRED (3).py)                         │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
   ┌───▼──────┐    ┌───▼─────────┐
   │Autenticação│  │  Filtros &  │
   │  por Senha │  │  Agregação  │
   └───────────┘   └─────────────┘
               │
       ┌───────▼────────────────────┐
       │ Camada de Processamento    │
       │ (Pandas, NumPy)            │
       └───────┬────────────────────┘
               │
       ┌───────▼────────────────────┐
       │ SQLAlchemy ORM             │
       │ + Conexão Impala           │
       └───────┬────────────────────┘
               │
       ┌───────▼────────────────────┐
       │ Banco de Dados Impala      │
       │ (LDAP Auth, SSL)           │
       └────────────────────────────┘
```

---

## Machine Learning

O sistema utiliza scoring multi-fator para priorização:

| Componente | Peso |
|------------|------|
| Score de Risco | 40% |
| Saldo de Crédito | 30% |
| Estagnação | 30% |

### Níveis de Alerta

- **BAIXO** - Monitoramento padrão
- **MÉDIO** - Atenção recomendada
- **ALTO** - Ação necessária
- **CRÍTICO** - Prioridade alta
- **EMERGENCIAL** - Ação imediata

---

## Notebooks de Apoio

| Notebook | Descrição |
|----------|-----------|
| `CREDITO.ipynb` | Pipeline de pré-processamento de dados (25K+ linhas) |
| `CREDITO-Exemplo (3).ipynb` | Padrões de análise e uso de exemplo |
| `CRED - SQL VALIDAR.ipynb` | Validação SQL e verificações de qualidade de dados |

---

## Desenvolvedor

**Tiago Severo**
AFRE - Agente Fiscal de Rendas Estaduais
Receita Estadual de Santa Catarina (SEFAZ-SC)

---

## Versão

- **Versão**: 2.0
- **Data de Lançamento**: Outubro 2025
- **Última Atualização**: Dezembro 2025

---

## Licença

Este software é de uso interno da Secretaria de Estado da Fazenda de Santa Catarina (SEFAZ-SC).
