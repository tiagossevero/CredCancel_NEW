# CRED-CANCEL v2.0

**Dashboard Avançado de Análise de Créditos Acumulados de ICMS e Detecção de Fraudes**

Sistema desenvolvido pela **Receita Estadual de Santa Catarina (SEFAZ-SC)** para monitoramento e análise de empresas com créditos acumulados de ICMS, detecção de atividades fraudulentas e suporte à decisão para cancelamento de Inscrição Estadual.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Execução](#execução)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Guia de Uso](#guia-de-uso)
- [Machine Learning e Scoring](#machine-learning-e-scoring)
- [Notebooks de Apoio](#notebooks-de-apoio)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Changelog](#changelog)
- [Desenvolvedor](#desenvolvedor)
- [Licença](#licença)

---

## Visão Geral

O **CRED-CANCEL v2.0** é uma plataforma de analytics de nível empresarial projetada para:

- **Análise Temporal Dupla**: Comparação de dados de 12 meses recentes vs 60 meses históricos
- **Detecção de Fraudes**: Identificação de padrões suspeitos e comportamentos anômalos
- **Machine Learning**: Priorização inteligente de empresas para fiscalização
- **Tomada de Decisão**: Suporte fundamentado para cancelamento de Inscrição Estadual
- **Monitoramento Contínuo**: Acompanhamento de créditos acumulados de ICMS

### Por que CRED-CANCEL?

O acúmulo irregular de créditos de ICMS pode indicar:
- Empresas de fachada (noteiras)
- Subfaturamento sistemático
- Omissão de declarações
- Fraudes tributárias organizadas

Este sistema permite identificar esses padrões de forma rápida e eficiente.

---

## Funcionalidades Principais

### 15 Páginas de Análise

| # | Página | Descrição |
|---|--------|-----------|
| 1 | **Dashboard Executivo** | Resumo executivo com KPIs principais e visão geral do sistema |
| 2 | **Comparativo 12m vs 60m** | Análise período-a-período comparando dados de 12 e 60 meses |
| 3 | **Análise de Suspeitas** | Detecção de fraudes e análise de empresas suspeitas |
| 4 | **Ranking de Empresas** | Empresas ranqueadas por score, saldo, crescimento, etc. |
| 5 | **Análise Setorial** | Análise específica por setor (Têxtil, Metal-Mecânico, Tecnologia) |
| 6 | **Drill-Down Empresa** | Análise detalhada a nível de empresa individual |
| 7 | **Machine Learning** | Scoring baseado em ML para priorização |
| 8 | **Padrões de Abuso** | Identificação de comportamentos anômalos e abusivos |
| 9 | **Empresas Inativas** | Empresas inativas com créditos acumulados |
| 10 | **Reforma Tributária** | Projeções de impacto da reforma tributária |
| 11 | **Empresas com Noteiras** | Detecção de relacionamentos com empresas de fachada |
| 12 | **Declarações Zeradas** | Análise de padrões de subfaturamento |
| 13 | **Alertas Automáticos** | Sistema de alertas inteligentes baseado em prioridade |
| 14 | **Guia de Cancelamento IE** | Guia para cancelamento de Inscrição Estadual |
| 15 | **Sobre o Sistema** | Documentação e informações do sistema |

### Métricas e Indicadores

| Métrica | Descrição |
|---------|-----------|
| **Score de Risco** | Cálculo para períodos de 12m e 60m |
| **Classificação de Risco Combinado** | Integração de indicadores de fraude |
| **Análise de Saldo** | Rastreamento de crescimento e evolução |
| **Indicadores de Fraude** | Múltiplos sinais suspeitos por empresa (10+ campos) |
| **Detecção de Omissão** | DIME Normal e PGDAS Simplificado |
| **Identificação de Estagnação** | Meses consecutivos sem alterações |

### Sistema de Filtros

O dashboard oferece filtros avançados para refinar a análise:

- **Classificação de Risco**: CRÍTICO, ALTO, MÉDIO, BAIXO
- **Saldo Mínimo**: Filtragem por valor mínimo de crédito
- **Período de Estagnação**: 0-60 meses sem movimentação
- **GERFE**: Escritório regional responsável
- **Filtros de Fraude**: Indicadores específicos de comportamentos suspeitos
- **Período de Análise**: Alternância entre 12 meses e 60 meses

---

## Tecnologias Utilizadas

### Framework Web
| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Streamlit | >= 1.28 | Interface web interativa |

### Processamento de Dados
| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Python | >= 3.8 | Linguagem principal |
| Pandas | >= 2.0 | Manipulação de dados |
| NumPy | >= 1.24 | Computação numérica |

### Banco de Dados
| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Apache Impala | - | Engine SQL distribuída |
| SQLAlchemy | >= 2.0 | ORM e conexões |
| Impyla | >= 0.18 | Driver Impala |

### Visualização
| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| Plotly Express | >= 5.18 | Gráficos interativos |
| Plotly Graph Objects | >= 5.18 | Visualizações customizadas |

### Segurança
| Tecnologia | Finalidade |
|------------|------------|
| hashlib | Hashing de senhas |
| SSL/TLS | Conexões criptografadas |
| LDAP | Autenticação corporativa |

---

## Pré-requisitos

### Sistema
- Python >= 3.8
- pip (gerenciador de pacotes Python)
- Acesso à rede interna da SEFAZ-SC

### Credenciais
- Credenciais LDAP válidas para acesso ao Impala
- Senha da aplicação (configurada pelo administrador)

### Conectividade
- Acesso ao servidor `bdaworkernode02.sef.sc.gov.br` porta `21050`

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd CredCancel_NEW
```

### 2. Crie um ambiente virtual (recomendado)

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install streamlit pandas numpy plotly sqlalchemy impyla thrift_sasl sasl
```

Ou crie um arquivo `requirements.txt`:

```text
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
sqlalchemy>=2.0.0
impyla>=0.18.0
thrift_sasl>=0.4.3
sasl>=0.3.1
```

E instale com:

```bash
pip install -r requirements.txt
```

### 4. Configure as credenciais do Streamlit

Crie o diretório e arquivo de secrets:

```bash
mkdir -p ~/.streamlit
```

Crie o arquivo `~/.streamlit/secrets.toml`:

```toml
[impala_credentials]
user = "seu_usuario_ldap"
password = "sua_senha_ldap"
```

### 5. Configure a senha da aplicação

Edite a linha 5 do arquivo `CRED (3).py`:

```python
SENHA = "sua_senha_desejada"
```

---

## Execução

### Iniciar a aplicação

```bash
streamlit run "CRED (3).py"
```

### Opções de execução

```bash
# Porta personalizada
streamlit run "CRED (3).py" --server.port 8080

# Permitir acesso externo
streamlit run "CRED (3).py" --server.address 0.0.0.0

# Modo headless (sem abrir navegador)
streamlit run "CRED (3).py" --server.headless true
```

### Acessar a aplicação

Abra no navegador: `http://localhost:8501`

1. Digite a senha configurada
2. Aguarde o carregamento dos dados
3. Utilize o menu lateral para navegar entre as páginas

---

## Estrutura do Projeto

```
CredCancel_NEW/
├── CRED (3).py                 # Aplicação principal Streamlit (~3.500 linhas)
│                               # - Autenticação
│                               # - 15 páginas de análise
│                               # - Processamento de dados
│                               # - Visualizações
│
├── CREDITO.ipynb               # Pipeline de pré-processamento (2.6 MB)
│                               # - Extração de dados do Impala
│                               # - Cálculo de indicadores
│                               # - Geração de datasets
│
├── CREDITO-Exemplo (3).ipynb   # Notebook de exemplos (144 KB)
│                               # - Casos de uso
│                               # - Padrões de análise
│
├── CRED - SQL VALIDAR.ipynb    # Validação SQL (128 KB)
│                               # - Verificação de qualidade
│                               # - Validação de dados
│
├── CRED-CANCEL.json            # Queries Hue/Impala (336 KB)
│                               # - 100+ consultas SQL
│                               # - Exportação do Hue
│
├── CANCEL (1).json             # Queries adicionais (189 KB)
│                               # - Consultas complementares
│
└── README.md                   # Este arquivo
```

---

## Configuração do Banco de Dados

### Conexão Impala

A conexão está configurada em `CRED (3).py` (linhas 223-245):

```python
IMPALA_HOST = 'bdaworkernode02.sef.sc.gov.br'
IMPALA_PORT = 21050
DATABASE = 'teste'
AUTH_MECHANISM = 'LDAP'
USE_SSL = True
```

### Tabelas Necessárias

| Tabela | Descrição | Uso |
|--------|-----------|-----|
| `teste.credito_dime_completo` | Tabela principal com dados 12m e 60m | Dashboard geral |
| `teste.credito_dime_textil` | Dados do setor têxtil | Análise setorial |
| `teste.credito_dime_metalmec` | Dados do setor metal-mecânico | Análise setorial |
| `teste.credito_dime_tech` | Dados do setor de tecnologia | Análise setorial |
| `usr_sat_ods.vw_cad_contrib` | View do cadastro de contribuintes | Dados cadastrais |

### Colunas Principais

#### Identificadores
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `nu_cnpj` | STRING | CNPJ da empresa |
| `nu_cnpj_grupo` | STRING | CNPJ do grupo econômico |
| `nm_contribuinte` | STRING | Nome/Razão social |
| `cd_gerfe` | STRING | Código da GERFE |

#### Saldos
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `saldo_credor_atual` | DECIMAL | Saldo de crédito atual |
| `saldo_12m_atras` | DECIMAL | Saldo há 12 meses |
| `saldo_60m_atras` | DECIMAL | Saldo há 60 meses |

#### Scores e Classificações
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `score_risco_12m` | DECIMAL | Score de risco (12 meses) |
| `score_risco_60m` | DECIMAL | Score de risco (60 meses) |
| `classificacao_risco_12m` | STRING | Classificação 12m |
| `classificacao_risco_60m` | STRING | Classificação 60m |
| `score_risco_combinado_12m` | DECIMAL | Score combinado 12m |
| `score_risco_combinado_60m` | DECIMAL | Score combinado 60m |

#### Indicadores de Fraude
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `flag_empresa_suspeita` | BOOLEAN | Empresa marcada como suspeita |
| `flag_declaracao_zerada` | BOOLEAN | Declarações com valor zero |
| `flag_omissao_dime` | BOOLEAN | Omissão de DIME |
| `flag_omissao_pgdas` | BOOLEAN | Omissão de PGDAS |
| `flag_noteira` | BOOLEAN | Relacionamento com noteiras |
| `qtd_periodos_iguais` | INT | Períodos sem alteração |
| `meses_estagnacao` | INT | Meses de estagnação |

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUÁRIO (Navegador Web)                      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CAMADA DE APRESENTAÇÃO                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Autenticação│  │   Sidebar   │  │     15 Páginas          │  │
│  │   por Senha │  │   Filtros   │  │     de Análise          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                         Streamlit Framework                      │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CAMADA DE PROCESSAMENTO                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Pandas    │  │   NumPy     │  │      Cálculo de         │  │
│  │ DataFrames  │  │ Operações   │  │      KPIs/Scores        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CAMADA DE VISUALIZAÇÃO                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 Plotly (Express + Graph Objects)         │    │
│  │  • Gráficos de Barras    • Treemaps    • Gauges         │    │
│  │  • Gráficos de Pizza     • Scatter     • Heatmaps       │    │
│  │  • Linhas Temporais      • Subplots    • Indicadores    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ SQLAlchemy  │  │   Impyla    │  │      Cache              │  │
│  │    ORM      │  │   Driver    │  │   (@st.cache_data)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │               Apache Impala (LDAP + SSL)                 │    │
│  │         bdaworkernode02.sef.sc.gov.br:21050              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Guia de Uso

### Fluxo de Trabalho Recomendado

```
1. Dashboard Executivo
   └── Visão geral e identificação de áreas críticas
           │
           ▼
2. Análise de Suspeitas / Alertas Automáticos
   └── Identificar empresas prioritárias
           │
           ▼
3. Drill-Down Empresa
   └── Análise detalhada da empresa selecionada
           │
           ▼
4. Guia de Cancelamento IE
   └── Procedimentos para ação fiscal
```

### Uso dos Filtros

1. **Selecione o Período de Análise**
   - 12 meses: dados recentes, ideal para monitoramento atual
   - 60 meses: dados históricos, ideal para identificar padrões

2. **Configure os Filtros de Risco**
   - Comece com CRÍTICO e ALTO para priorização
   - Expanda para MÉDIO conforme necessário

3. **Defina Saldo Mínimo**
   - Valores acima de R$ 1.000.000 para focar em casos relevantes

4. **Filtro de Estagnação**
   - Empresas com > 12 meses sem movimentação merecem atenção

### Interpretação dos Scores

| Score | Classificação | Ação Recomendada |
|-------|---------------|------------------|
| 0-25 | BAIXO | Monitoramento padrão |
| 26-50 | MÉDIO | Análise complementar |
| 51-75 | ALTO | Prioridade de verificação |
| 76-100 | CRÍTICO | Ação fiscal imediata |

---

## Machine Learning e Scoring

### Algoritmo de Priorização

O sistema utiliza um modelo de scoring multi-fator para priorização:

```
Score ML = (Score_Risco × 0.40) + (Score_Saldo × 0.30) + (Score_Estagnação × 0.30)
```

| Componente | Peso | Descrição |
|------------|------|-----------|
| Score de Risco | 40% | Baseado em indicadores de fraude |
| Score de Saldo | 30% | Normalizado pelo valor de crédito |
| Score de Estagnação | 30% | Baseado em meses sem movimentação |

### Níveis de Alerta

| Nível | Cor | Score | Ação |
|-------|-----|-------|------|
| BAIXO | Verde | 0-25 | Monitoramento regular |
| MÉDIO | Amarelo | 26-50 | Verificação periódica |
| ALTO | Laranja | 51-75 | Análise prioritária |
| CRÍTICO | Vermelho | 76-90 | Ação fiscal urgente |
| EMERGENCIAL | Vermelho escuro | 91-100 | Intervenção imediata |

### Indicadores de Fraude

O sistema analisa múltiplos sinais:

1. **Relacionamento com Noteiras**: Vínculo com empresas de fachada
2. **Declarações Zeradas**: Padrão de subfaturamento
3. **Omissão de DIME/PGDAS**: Falta de declarações obrigatórias
4. **Estagnação Prolongada**: Saldo inalterado por longos períodos
5. **Crescimento Anormal**: Aumento desproporcional de créditos
6. **Inatividade com Crédito**: Empresa parada com saldo elevado

---

## Notebooks de Apoio

### CREDITO.ipynb (Pipeline Principal)

**Tamanho**: 2.6 MB | **Células**: 200+

Responsável por:
- Extração de dados do Impala
- Cálculo de indicadores derivados
- Enriquecimento com flags de fraude
- Geração das tabelas finais

### CREDITO-Exemplo (3).ipynb (Exemplos)

**Tamanho**: 144 KB

Contém:
- Casos de uso demonstrativos
- Padrões de análise recomendados
- Exemplos de interpretação de dados

### CRED - SQL VALIDAR.ipynb (Validação)

**Tamanho**: 128 KB

Inclui:
- Queries de validação de dados
- Verificação de integridade
- Testes de qualidade

---

## Troubleshooting

### Problemas Comuns

#### Erro de conexão com Impala

```
Error: Could not connect to Impala
```

**Soluções**:
1. Verifique se está na rede da SEFAZ (ou VPN)
2. Confirme as credenciais em `~/.streamlit/secrets.toml`
3. Teste a conectividade: `telnet bdaworkernode02.sef.sc.gov.br 21050`

#### Senha incorreta

```
Senha incorreta. Tente novamente.
```

**Solução**: Verifique a senha configurada na linha 5 do `CRED (3).py`

#### Erro de importação de pacotes

```
ModuleNotFoundError: No module named 'impyla'
```

**Solução**:
```bash
pip install impyla thrift_sasl sasl
```

#### Timeout na carga de dados

```
TimeoutError: Data loading exceeded timeout
```

**Soluções**:
1. Verifique a conexão de rede
2. Tente limitar o período de análise
3. Utilize filtros mais restritivos

#### Gráficos não carregam

**Solução**: Limpe o cache do Streamlit:
```bash
streamlit cache clear
```

### Logs de Diagnóstico

Para ativar logs detalhados:

```bash
streamlit run "CRED (3).py" --logger.level=debug
```

---

## FAQ

### Perguntas Frequentes

**P: Qual a diferença entre análise de 12m e 60m?**

R: A análise de 12 meses foca em comportamentos recentes, ideal para monitoramento. A de 60 meses identifica padrões históricos e tendências de longo prazo.

**P: Como é calculado o Score de Risco?**

R: O score combina múltiplos fatores: indicadores de fraude, padrões de declaração, estagnação e relacionamentos suspeitos, normalizados em escala 0-100.

**P: Por que algumas empresas aparecem como CRÍTICO?**

R: Empresas classificadas como CRÍTICO apresentam múltiplos indicadores de risco simultâneos, como relação com noteiras, omissão de declarações e saldos estagnados.

**P: Posso exportar os dados?**

R: Sim, a maioria das tabelas possui botão de download para CSV/Excel.

**P: Com que frequência os dados são atualizados?**

R: Os dados são atualizados pelo pipeline `CREDITO.ipynb`, geralmente executado mensalmente após o fechamento das declarações.

**P: O sistema funciona offline?**

R: Não, é necessária conexão com o banco de dados Impala para funcionamento.

---

## Changelog

### v2.0 (Outubro 2025)
- Adição de análise dual (12m vs 60m)
- Novo sistema de scoring com ML
- 15 páginas de análise completas
- Integração com indicadores de fraude
- Interface renovada com Plotly

### v1.0 (Março 2025)
- Versão inicial
- Dashboard básico de créditos
- Análise de período único

---

## Desenvolvedor

**Tiago Severo**
- **Cargo**: AFRE - Agente Fiscal de Rendas Estaduais
- **Órgão**: Receita Estadual de Santa Catarina (SEFAZ-SC)
- **Projeto**: CRED-CANCEL - Sistema de Análise de Créditos e Detecção de Fraudes

---

## Versão

| Campo | Valor |
|-------|-------|
| **Versão** | 2.0 |
| **Data de Lançamento** | Outubro 2025 |
| **Última Atualização** | Dezembro 2025 |
| **Python** | >= 3.8 |
| **Streamlit** | >= 1.28 |

---

## Licença

Este software é de **uso interno exclusivo** da Secretaria de Estado da Fazenda de Santa Catarina (SEFAZ-SC).

**Restrições**:
- Proibida a distribuição externa
- Proibida a cópia sem autorização
- Uso restrito a servidores autorizados da SEFAZ-SC

---

**SEFAZ-SC** - Secretaria de Estado da Fazenda de Santa Catarina
