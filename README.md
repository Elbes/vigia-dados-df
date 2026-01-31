# VigiaDados DF

Projeto desenvolvido para o **1º Hackathon em Controle Social – Desafio Participa DF**, na categoria **Acesso à Informação**.

O **VigiaDados DF** tem como objetivo apoiar a Administração Pública na **proteção de dados pessoais e dados sensíveis**, identificando automaticamente pedidos de acesso à informação que apresentem **risco de exposição indevida**, em conformidade com a **Lei Geral de Proteção de Dados Pessoais (LGPD – Lei nº 13.709/2018)**.

A solução atua como um **mecanismo preventivo**, auxiliando a triagem inicial de pedidos, **sem substituir a decisão humana**, garantindo **explicabilidade, auditabilidade e governança**.

Link do vídeo de demonstração: https://youtu.be/pWZZ_9EpD7A
---

## Problema

Órgãos públicos recebem diariamente um grande volume de pedidos de acesso à informação.  
A análise exclusivamente manual desses pedidos pode resultar em:

- Exposição indevida de dados pessoais ou sensíveis;
- Classificação equivocada de informações como públicas;
- Risco jurídico, administrativo e institucional;
- Sobrecarga operacional das equipes responsáveis pela triagem.

---

## Objetivo da Solução

Atuar como um **filtro automatizado de apoio à decisão**, alertando servidores públicos quando um pedido contém indícios de dados protegidos pela LGPD.

O VigiaDados DF busca:

- Identificar automaticamente **dados pessoais explícitos**;
- Detectar **dados sensíveis**, conforme definido pela LGPD;
- Sinalizar pedidos que exigem **revisão humana obrigatória**;
- Priorizar **alta sensibilidade (recall)**, reduzindo falsos negativos;
- Garantir **explicabilidade, transparência e rastreabilidade** das decisões.

---

## Visão Geral da Solução

A solução adota uma **arquitetura determinística e linguística**, com separação clara de responsabilidades:

- **Regras explícitas (Regex)** → detecção direta, conservadora e auditável;
- **Heurística linguística (spaCy / NLP clássico)** → interpretação contextual;
- **Camada de orquestração (Laravel)** → integração, regras de negócio e governança.

Essa abordagem é especialmente adequada ao contexto do edital, pois **evita decisões opacas**, não utiliza modelos generativos e permite **controle institucional total**.

---

## bordagem Técnica

### Camada 1 — Regras Determinísticas (Regex)

Utiliza expressões regulares extensivas para identificar padrões explícitos de dados pessoais e administrativos, como:

- CPF e CNPJ (com validação de dígito verificador);
- E-mails e telefones;
- Documentos pessoais (RG, CNH, passaporte, títulos);
- Matrículas, inscrições e identificadores administrativos;
- Endereços;
- Dados financeiros e bancários;
- Processos e protocolos administrativos.

**Características:**

- Decisão conservadora;
- Alta sensibilidade (recall);
- Totalmente explicável e auditável;
- Fundamentada em regras jurídicas claras.

---

### Camada 2 — Heurística Linguística com spaCy

Utiliza **Processamento de Linguagem Natural clássico (NLP)**, sem aprendizado automático em produção, para identificar:

#### 🔹 Dados pessoais
- Nomes de pessoas (NER – `PER`);
- Menções indiretas a identificação pessoal.

#### 🔹 Dados sensíveis (LGPD – Art. 5º, II)
- Saúde (ex: “sou portador de…”);
- Religião;
- Raça / etnia;
- Outros contextos sensíveis quando explicitamente declarados.

São utilizados:

- spaCy NER (`pt_core_news_lg`);
- `EntityRuler` para padrões linguísticos controlados;
- `Matcher` para detecção de contexto sensível;
- Regex integrada ao pipeline spaCy;
- Validações adicionais para redução de falsos positivos.

**Não há treinamento automático de modelos**.  
O pipeline é **determinístico, reproduzível e auditável**.

---

## Uso de Inteligência Artificial

A Inteligência Artificial é utilizada de forma:

- Não generativa;
- Sem aprendizado automático em produção;
- Totalmente explicável;
- Com controle humano garantido.

**Não são utilizados:**

- LLMs;
- Modelos generativos;
- Classificadores estatísticos opacos.

A solução está alinhada às **boas práticas de IA Responsável no setor público**.

---

## Evidências e Explicabilidade

Cada análise retorna, além da decisão final:

- **Tipos de dados detectados**;
- **Origem da decisão** (regex, spaCy, matcher);
- **Evidências textuais** (trechos detectados);
- **Nível de confiança estimado**;
- **Ação sugerida** (revisão ou publicação).

Esses elementos permitem **auditoria técnica, jurídica e administrativa**.

---

## Arquitetura da Aplicação

Arquitetura distribuída com separação clara de responsabilidades:

### Python / FastAPI (ML Service)
Responsável por:

- Análise textual;
- Detecção de dados pessoais e sensíveis;
- Execução do pipeline linguístico (Regex + spaCy);
- Exposição de API.

### PHP / Laravel (API Institucional)
Responsável por:

- Orquestração da requisição;
- Validação de entrada;
- Tratamento de exceções;
- Regras de negócio;
- Definição da ação sugerida ao usuário.

Essa abordagem segue o princípio de **Separação de Responsabilidades (SoC)**, favorecendo manutenção, escalabilidade e integração futura com o ecossistema do Participa DF.

### Por que usar PHP com Laravel + Python
Embora toda a solução pudesse ser implementada exclusivamente em Python, a escolha por uma arquitetura híbrida traz vantagens práticas no contexto governamental:

Com Laravel:
- Python é utilizado onde é mais eficiente: análise textual e processamento semântico;
- Laravel atua como camada de integração, segurança, governança e compatibilidade com sistemas existentes.

---

## Tecnologias Utilizadas

- Python 3.10
- FastAPI
- spaCy (`pt_core_news_lg`)
- Docker
- Docker Compose
- PHP 8.2
- Laravel 10

---

## Execução com Docker (Recomendado)

### Pré-requisitos
- Docker
- Docker Compose

### Subir a aplicação
```
git clone https://github.com/Elbes/vigia-dados-df.git
cd vigia-dados-df
docker compose build
docker compose up
```

### Serviços Disponíveis
| Serviço              | Endereço                                                     |
| -------------------- | ------------------------------------------------------------ |
| API Laravel          | [http://localhost:8001](http://localhost:8001)               |
| ML Service (FastAPI) | [http://localhost:8000/docs](http://localhost:8000/docs)     |
| Healthcheck ML       | [http://localhost:8000/health](http://localhost:8000/health) |

### Exemplo de Requisição

```
curl -X POST http://localhost:8001/api/analisar \
  -H "Content-Type: application/json" \
  -d '{"texto":"Meu nome é João Silva e meu CPF é 123.456.789-00"}'
```

### Resposta Esperada

```
{
  "contem_dados_pessoais": true,
  "contem_dados_sensiveis": false,
  "tipos_detectados": ["cpf_cnpj", "nome_pessoa"],
  "origem_decisao": ["regex", "spacy"],
  "confianca": 0.95,
  "evidencias": [
    "Nome detectado: João Silva",
    "Dado pessoal: CPF_CNPJ"
  ],
  "acao_sugerida": "Revisão antes da publicação"
}
```

### Estrutura do Projeto

```
vigia-dados-df/
├── README.md
├── docker-compose.yml
├── ml-service/
│   ├── main.py              # API FastAPI (execução)
│   ├── detector.py          # Decisão final e JSON - Lógica de análise
│   ├── spacy_pipeline.py    # Regex + NER + heurísticas
│   ├── evaluate.py          # Avaliação OFFLINE (auditoria)
│   ├── validacoes.py        # funções de validações
│   ├── requirements.txt     # API FastAPI (execução)
│   └── Dockerfile           # CONFIG DOCKER
├── api-laravel/             # Interface/API em PHP
│   ├── app/Http/Controllers/
│   │   └── AnaliseController.php  # Controller laravel
│   ├── routes/
│   │   └── api.php          # rotas
│   └── composer.json        # Dependências PHP
└── data/                    # Base de dados
    └── AMOSTRA_e-SIC.xlsx   # Amostra fornecida
```

## Diagrama de Decisão (Lógico)
```
Texto do Pedido (e-SIC)
        │
        ▼
┌─────────────────────────────┐
│ Normalização do Texto       │
│ (lowercase / limpeza básica)│
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Regex Determinístico        │
│ (Dados explícitos)          │
│ - CPF, RG, Email            │
│ - Telefone, Endereço        │
│ - Matrículas, Processos     │
└─────────────┬───────────────┘
              │
              ├── Padrão válido detectado?
              │        │
              │        ├─ SIM
              │        │     ▼
              │        │ ┌──────────────────────┐
              │        │ │ Validação Anti-Ruído  │
              │        │ │ (contexto legal, ano, │
              │        │ │ tamanho, whitelist)   │
              │        │ └─────────┬────────────┘
              │        │           │
              │        │           ├─ Válido?
              │        │           │     │
              │        │           │     ├─ SIM → 
              │        │           │     │
              │        │           │     │  Dado Pessoal
              │        │           │     │  (Decisão Final)
              │        │           │     │
              │        │           │     └─ NÃO → Ignorar
              │        │
              │        └─ NÃO
              ▼
┌─────────────────────────────┐
│ Heurística Linguística      │
│ spaCy (NER + Regras)        │
│ - Nome de pessoa            │
│ - Saúde, Religião, Raça     │
└─────────────┬───────────────┘
              │
              ├── Entidade sensível detectada?
              │        │
              │        ├─ SIM → 
              │        │
              │        │  Dado Sensível
              │        │  (Revisão Humana)
              │        │
              │        └─ NÃO
              ▼
┌─────────────────────────────┐
│ Resultado Consolidado       │
│ - Evidências                │
│ - Tipos detectados          │
│ - Origem da decisão         │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Decisão Administrativa      │
│ (Laravel – Regra de Negócio)│
│ - Revisão humana            │
│ - Publicação automática     │
└─────────────────────────────┘
```

## Diagrama Arquitetural (Serviços)
```
┌───────────────────────────────┐
│        Usuário / Sistema      │
│    (e-SIC / Portal / API)     │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│      API Laravel (PHP)        │
│                               │
│ - Validação da requisição     │
│ - Segurança / Logs            │
│ - Regras de negócio           │
│ - Decisão administrativa      │
│ - Evidências para auditoria   │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│    ML Service (FastAPI)       │
│                               │
│  ┌─────────────────────────┐ │
│  │ Regex Determinístico    │ │
│  │ - Regras jurídicas      │ │
│  │ - Auditável             │ │
│  └─────────────────────────┘ │
│                               │
│  ┌─────────────────────────┐ │
│  │ spaCy / NLP Clássico    │ │
│  │ - NER                   │ │
│  │ - EntityRuler           │ │
│  │ - Matcher contextual    │ │
│  └─────────────────────────┘ │
│                               │
│  → Saída estruturada JSON     │
│    (decisão + evidências)     │
└───────────────────────────────┘
```

## Considerações Finais
O VigiaDados DF foi projetado para:

* Proteger dados pessoais e sensíveis;

* Reduzir riscos jurídicos;

* Apoiar servidores públicos;

* Garantir explicabilidade e governança;

* Facilitar adoção institucional.

Trata-se de uma solução simples, robusta, auditável e alinhada ao edital, adequada ao contexto do setor público.