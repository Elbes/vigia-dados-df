FROM python:3.10-slim

# Evita arquivos .pyc e buffer de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências
COPY requirements.txt .

RUN pip install -r requirements.txt \
    && python -m spacy download pt_core_news_lg

# Código
COPY . .

# Porta da API
EXPOSE 8000

# Inicializa API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
