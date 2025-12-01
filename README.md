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
    -   Edite o arquvio `docker-compose.yml` e insira sua chave de API do Google
        Voce pode gerala acessando: https://aistudio.google.com/api-keys

3.  **Executar**:
    ```bash
    docker compose up --build
    ```

4.  **Acessar**:
    -   Acesse `http://localhost:8501` no seu navegador.

### Observação sobre Persistência
A pasta `storage/` é mapeada como um volume, então o índice gerado pela IA será persistido mesmo se você destruir o container. Se você adicionar novos arquivos na pasta `data/`, pode ser necessário reiniciar o container ou rodar o script de reindexação.

## Modelagem e Tratamento dos Dados

Os dados brutos foram remodelados para o padrão _Star Schema_, otimizando a performance e a clareza analítica. O conjunto de dados original foi transformado nas seguintes tabelas:
#### Tabelas Fato:
```
FATO_AVCURSOS
FATO_AVDISCIPLINAS
FATO_AVINSTITUCIONAL
```

#### Tabelas Dimensão:
```
DIM_CURSOS
DIM_DISCIPLINAS
DIM_PERGUNTAS
DIM_TIPO_PERGUNTA_SINAES
DIM_UNIDADES
```

A relação entre as tabelas é feita principalmente entre as colunas ```ID_PERGUNTA``` e ```ID_QUESTIONARIO```.

## Dashboards Analíticos
Foram desenvolvidos cinco dashboards interativos para facilitar a visualização e aprofundamento das análises.

1. Página Inicial:
    - **Foco Analítico:** Panorama imediato da satisfação e engajamento.

    - **Indicadores-Chave:** Satisfação Média Geral, Engajamento Total (Contagem de Respostas), Gap de Comunicação (% de "Desconheço"), Destaques e Pontos de Risco.

2. SINAES:
    - **Foco Analítico:** Conformidade e score institucional nos 5 Eixos Avaliativos

    - **Indicadores-Chave:** Cobertura das Dimensões do SINAES, Score de Aprovação por Eixo e por Dimensão.

3. Qualidade de Ensino:
    - **Foco Analítico:** Avaliação do processo de ensino-aprendizagem

    - **Indicadores-Chave:** Aderência ao Plano de Disciplina, Carga Horária, Índice de Didática, Histograma de Faixa de Satisfação e Comparativo de Score Pedagógico.


4. Gestão de Cursos:
    - **Foco Analítico:** Análise da estrutura curricular, apoio e resultados por unidade

    - **Indicadores-Chave:** Interdisciplinaridade, Satisfação com Atendimento e Apoio, Taxa de Visibilidade de Apoio, Ranking de Satisfação por Setor e Gráfico de Dispersão (Score x Volume de Respostas).


5. Clima Institucional:
    - **Foco Analítico:** Percepção dos servidores sobre gestão e infraestrutura.

    - **Indicadores-Chave:** Score de Transparência (RH/Movimentação), Índice de Segurança/Infraestrutura, Gap de Comunicação (Familiaridade com PDE), Ranking de Satisfação dos Servidores e Polarização de Opiniões (Net Score).
