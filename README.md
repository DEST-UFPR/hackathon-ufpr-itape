# Dashboard & Chat RAG - Dados UFPR

Este projeto é uma aplicação Streamlit que combina um Dashboard de visualização de dados (Excel/CSV) com um Chatbot inteligente (RAG) capaz de responder perguntas sobre os documentos.

## Funcionalidades

- **Dashboard**: Visualização de planilhas Excel e CSV localizadas na pasta `data/`.
- **Chat RAG**: Assistente de IA (Gemini) que lê e responde perguntas baseadas nos documentos (PDFs, Excel, CSV) da pasta `data/`.
- **Indexação Otimizada**: Processamento de arquivos com barra de progresso e estimativa de tempo (ETA).
- **Persistência**: O índice é salvo em disco (`storage/`) para carregamento instantâneo nas próximas execuções.

## Como Executar

## Rodando com Docker (Recomendado)

Esta aplicação está containerizada para facilitar a execução.

### Pré-requisitos
- Docker e Docker Compose instalados.
- Git LFS instalado (para baixar os arquivos de índice).

### Passo a Passo

1.  **Clone o repositório e baixe os arquivos grandes**:
    ```bash
    git clone https://github.com/luis-ota/hackathon-ufpr-dados-2025.git
    cd hackathon-ufpr-dados-2025
    git lfs install
    git lfs pull
    ```

2.  **Configuração**:
    -   Crie um arquivo `.env` na raiz do projeto com sua chave de API:
        ```env
        GOOGLE_API_KEY=sua_chave_aqui
        ```

3.  **Executar**:
    ```bash
    docker compose up --build
    ```

4.  **Acessar**:
    -   Acesse `http://localhost:8501` no seu navegador.

### Observação sobre Persistência
A pasta `storage/` é mapeada como um volume, então o índice gerado pela IA será persistido mesmo se você destruir o container. Se você adicionar novos arquivos na pasta `data/`, pode ser necessário reiniciar o container ou rodar o script de reindexação.
