# Dashboard & Chat RAG - Dados UFPR

Este projeto é uma aplicação Streamlit que combina um Dashboard de visualização de dados (Excel/CSV) com um Chatbot inteligente (RAG) capaz de responder perguntas sobre os documentos.

## Funcionalidades

- **Dashboard**: Visualização de planilhas Excel e CSV localizadas na pasta `data/`.
- **Chat RAG**: Assistente de IA (Gemini) que lê e responde perguntas baseadas nos documentos (PDFs, Excel, CSV) da pasta `data/`.
- **Indexação Otimizada**: Processamento de arquivos com barra de progresso e estimativa de tempo (ETA).
- **Persistência**: O índice é salvo em disco (`storage/`) para carregamento instantâneo nas próximas execuções.

## Como Executar

1.  **Pré-requisitos**:
    -   Ter o `uv` instalado (gerenciador de pacotes Python).
    -   Ter uma API Key do Google Gemini.

2.  **Configuração**:
    -   Crie um arquivo `.env` na raiz do projeto:
        ```env
        GOOGLE_API_KEY=sua_chave_aqui
        ```
    -   Coloque seus arquivos de dados (Excel, CSV, PDF) na pasta `data/`.

3.  **Rodar**:
    ```bash
    uv run streamlit run app.py
    ```

4.  **Acesso**:
    -   Abra o navegador no endereço indicado (geralmente `http://localhost:8501`).
