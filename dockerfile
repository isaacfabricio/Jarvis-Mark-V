# Usando Python 3.12 Slim para máxima eficiência e segurança
FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Instula dependências de sistema essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia apenas o código-fonte e o frontend (SEM copiar o .env por segurança)
COPY cerebro_api.py .
COPY frontend/ frontend/

# Cria o diretório do cofre de memórias criptografadas
RUN mkdir -p vault_jarvis

# Expõe a porta do Cérebro
EXPOSE 8000

# Executa o Cérebro Central
CMD ["python", "cerebro_api.py"]