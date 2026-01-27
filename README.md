poderia montar em markdown
# VigiaDados DF

Projeto desenvolvido para o 1º Hackathon em Controle Social – Desafio Participa DF,na categoria Acesso à Informação.
O VigiaDados DF tem como objetivo apoiar a Administração Pública na proteção de dados pessoais e dados sensíveis, identificando automaticamente pedidos de acesso à informação que apresentem risco de exposição, evitando sua divulgação indevida, em conformidade com a Lei Geral de Proteção de Dados Pessoais (LGPD – Lei nº 13.709/2018).

## Problema

Órgãos públicos recebem diariamente um grande volume de pedidos de acesso à informação.\
A análise manual desses pedidos pode resultar em:

* Exposição indevida de dados pessoais ou sensíveis;

* Classificação equivocada de pedidos como públicos;

* Risco jurídico e administrativo;

* Sobrecarga operacional dos servidores responsáveis pela triagem.

## Objetivo da Solução
Atuar como um filtro preventivo automatizado, auxiliando servidores públicos na triagem inicial de pedidos de acesso à informação, sem substituir a decisão humana.
O VigiaDados DF busca:

* Identificar automaticamente dados pessoais explícitos;

* Detectar dados sensíveis, conforme definido pela LGPD;

* Sinalizar pedidos que exigem revisão humana;

* Priorizar alta sensibilidade (recall), reduzindo falsos negativos;

* Garantir explicabilidade, auditabilidade e governança.

## Visão Geral da Solução
A solução adota uma arquitetura determinística e linguística, com separação clara de responsabilidades:

* Regras explícitas (Regex) → detecção direta e auditável

* Heurística linguística (spaCy / NER) → interpretação contextual

* Camada de orquestração (Laravel) → integração e regras de negócio

Essa abordagem é recomendada para o edital, pois evita decisões opacas e garante total controle institucional.
Abordagem Técnica (Recomendada pelo Edital)
A solução utiliza uma arquitetura sem treinamento de modelos, combinando:

### Camada 1 — Regras Determinísticas (Regex)
Utiliza expressões regulares para identificar padrões explícitos de dados pessoais, como:

* CPF;

* E-mail;

* Telefone;

* Placas de veículos;

* Matrículas e identificadores administrativos;

* Endereços (Rua, Avenida, Quadra, Lote).

Características dessa camada:

* Decisão conservadora;

* Alta sensibilidade (recall);

* Totalmente explicável e auditável;

* Baseada em regras jurídicas claras.

### Camada 2 — Heurística Linguística com spaCy
Utiliza Processamento de Linguagem Natural clássico (NLP), sem modelos generativos, para identificar:
🔹 Dados pessoais

* Nomes de pessoas (NER – PER);

* Menções indiretas a identificação pessoal.

🔹 Dados sensíveis (LGPD – Art. 5º, II)

* Saúde (ex: “sou portador de…”);

* Religião;

* Raça / etnia;

* Orientação sexual (quando explicitamente mencionada).

São utilizados:

* spaCy NER (modelo pré-treinado);

* EntityRuler para padrões linguísticos controlados;

* Matcher para contexto sensível;

* Regex complementar integrada ao pipeline.

Não há treinamento automático de modelos. O pipeline é determinístico, reproduzível e auditável.

## Uso de Inteligência Artificial
A Inteligência Artificial é utilizada de forma:

* Não generativa;

* Sem aprendizado automático em produção;

* Totalmente explicável;

* Com controle humano garantido.

Não são utilizados:

* LLMs;

* Modelos generativos;

* Classificadores estatísticos opacos.

A solução está alinhada às boas práticas de IA Responsável no setor público.
Dados Utilizados

* Amostras anonimizadas e/ou sintéticas, conforme o edital;

* Nenhum dado pessoal real foi utilizado;

* A solução é compatível com bases reais sob governança institucional.

## Arquitetura da Aplicação
Arquitetura distribuída com separação clara de responsabilidades:
🔹 Python / FastAPI
Responsável por:

* Análise textual;

* Detecção de dados pessoais e sensíveis;

* Execução do pipeline linguístico (Regex + spaCy).

🔹 PHP / Laravel
Responsável por:

* Orquestração da API;

* Validação de requisições;

* Regras de negócio;

* Definição da ação sugerida (revisão ou publicação).

Essa abordagem segue o princípio de Separação de Responsabilidades (SoC).

### Tecnologias Utilizadas

* Python 3.10

* FastAPI

* spaCy (pt_core_news_lg)

* Docker

* Docker Compose

* PHP 8.2

* Laravel 10

### Execução com Docker (Recomendado)
Pré-requisitos

* Docker

* Docker Compose

Subir a aplicação

```
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
  "tipos_detectados": ["cpf", "nome_pessoa"],
  "tem_dado_sensivel": false,
  "origem_decisao": "regex",
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

## Considerações Finais
O VigiaDados DF foi projetado para:

* Proteger dados pessoais e sensíveis;

* Reduzir riscos jurídicos;

* Apoiar servidores públicos;

* Garantir explicabilidade e governança;

* Facilitar adoção institucional.

Trata-se de uma solução simples, robusta, auditável e alinhada ao edital, adequada ao contexto do setor público.