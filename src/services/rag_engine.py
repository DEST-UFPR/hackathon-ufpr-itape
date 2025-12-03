"""
RAG Engine híbrido com capacidades analíticas.
Combina busca semântica (embeddings) com análise estruturada de dados (Pandas).
"""

import os
import shutil
import streamlit as st
from llama_index.core import VectorStoreIndex, Settings, Document, StorageContext, load_index_from_storage, SimpleDirectoryReader
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
import pandas as pd
import gc

from src.services.data_tools import DataAnalyzer
from src.services.table_metadata import get_table_info, get_all_tables_summary, COMMON_METRICS


@st.cache_resource(show_spinner=False)
def get_data_analyzer():
    """
    Inicializa e retorna o analisador de dados.
    Carrega todos os DataFrames em memória para análise rápida.
    """
    return DataAnalyzer(data_dir="data")


@st.cache_resource(show_spinner=False)
def get_vector_index():
    """
    Carrega ou cria o índice vetorial para busca semântica.
    Usado apenas para perguntas conceituais/descritivas.
    """
    from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, SimpleDirectoryReader
    import pandas as pd
    
    STORAGE_DIR = "./storage"
    DATA_DIR = "data"

    if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
        return None

    if os.path.exists(STORAGE_DIR):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
            index = load_index_from_storage(storage_context)
            gc.collect() 
            return index
        except Exception as e:
            # Silently clear storage and re-index
            if os.path.exists(STORAGE_DIR):
                try:
                    for item in os.listdir(STORAGE_DIR):
                        item_path = os.path.join(STORAGE_DIR, item)
                        if os.path.isfile(item_path) or os.path.islink(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                except Exception:
                    pass  # Silently continue
        
    index = VectorStoreIndex([])
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls', '.csv', '.pdf', '.md'))]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(files):
        file_path = os.path.join(DATA_DIR, file)
        status_text.text(f"Processing {file}...")
        try:
            documents = []
            if file.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, sep=None, engine='python', dtype=str) 
                except:
                    df = pd.read_csv(file_path, sep=';', dtype=str)
            
                df.columns = df.columns.str.replace('\ufeff', '').str.strip()
                df = df.fillna("")
                
                text = df.to_csv(index=False)
                documents = [Document(text=text, metadata={"filename": file})]
                
                del df
                gc.collect()
            else:
                documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
                for d in documents:
                    d.metadata["filename"] = file

            nodes = Settings.node_parser.get_nodes_from_documents(documents)
            
            index.insert_nodes(nodes)
            
            del documents
            del nodes
            gc.collect()
            
        except Exception as e:
            st.error(f"Error reading {file}: {e}")
        
        progress_bar.progress((i + 1) / len(files))
    
    status_text.text("Persisting index...")
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    
    status_text.empty()
    progress_bar.empty()
    gc.collect()
    
    return index


def create_analysis_tools(analyzer: DataAnalyzer):
    """
    Cria ferramentas de análise que o agente pode chamar.
    
    Args:
        analyzer: Instância do DataAnalyzer
        
    Returns:
        Lista de FunctionTool
    """
    
    def calculate_satisfaction_tool(
        table_name: str, 
        group_by: str = None,
        filter_column: str = None,
        filter_value: str = None
    ) -> str:
        """
        Calcula satisfação (% de 'Concordo' sobre respostas válidas).
        
        Use esta ferramenta para perguntas sobre:
        - Média/percentual de satisfação
        - Aprovação por grupo (curso, setor, unidade, etc.)
        - Comparações de satisfação
        
        Args:
            table_name: Nome da tabela (FATO_AVCURSOS, FATO_AVDISCIPLINAS, FATO_AVINSTITUCIONAL)
            group_by: Coluna para agrupar (ex: COD_CURSO, SIGLA_LOTACAO, ID_PERGUNTA)
            filter_column: Coluna para filtrar (opcional)
            filter_value: Valor do filtro (opcional)
            
        Returns:
            String formatada com resultados
        """
        try:
            filters = {filter_column: filter_value} if filter_column and filter_value else None
            result = analyzer.calculate_satisfaction(table_name, group_by=group_by, filters=filters)
            
            if len(result) > 20:
                return f"Resultados (top 20 de {len(result)}):\n{result.head(20).to_string(index=False)}"
            else:
                return f"Resultados:\n{result.to_string(index=False)}"
        except Exception as e:
            return f"Erro ao calcular satisfação: {str(e)}"
    
    def count_responses_tool(
        table_name: str,
        group_by: str = None,
        response_type: str = None,
        filter_column: str = None,
        filter_value: str = None
    ) -> str:
        """
        Conta respostas com filtros opcionais.
        
        Use esta ferramenta para perguntas sobre:
        - Quantas respostas (total ou por tipo)
        - Contagem de 'Concordo', 'Discordo', 'Desconheço'
        - Volume de respostas por grupo
        
        Args:
            table_name: Nome da tabela
            group_by: Coluna para agrupar (opcional)
            response_type: Tipo de resposta: 'Concordo', 'Discordo' ou 'Desconheço' (opcional)
            filter_column: Coluna para filtrar (opcional)
            filter_value: Valor do filtro (opcional)
            
        Returns:
            String formatada com contagens
        """
        try:
            filters = {filter_column: filter_value} if filter_column and filter_value else None
            result = analyzer.count_responses(
                table_name, 
                group_by=group_by, 
                filters=filters,
                response_type=response_type
            )
            
            if len(result) > 20:
                return f"Resultados (top 20 de {len(result)}):\n{result.head(20).to_string(index=False)}"
            else:
                return f"Resultados:\n{result.to_string(index=False)}"
        except Exception as e:
            return f"Erro ao contar respostas: {str(e)}"
    
    def get_top_bottom_tool(
        table_name: str,
        metric: str,
        n: int,
        group_by: str,
        get_bottom: bool = False
    ) -> str:
        """
        Retorna top/bottom N por métrica.
        
        Use esta ferramenta para perguntas sobre:
        - Melhores/piores cursos, setores, unidades
        - Rankings
        - Extremos (maior/menor satisfação, etc.)
        
        Args:
            table_name: Nome da tabela
            metric: Métrica: 'satisfacao', 'contagem', 'gap_desconhecimento'
            n: Número de resultados (ex: 10 para top 10)
            group_by: Coluna para agrupar
            get_bottom: True para bottom N (piores), False para top N (melhores)
            
        Returns:
            String formatada com ranking
        """
        try:
            result = analyzer.get_top_n(
                table_name,
                metric=metric,
                n=n,
                group_by=group_by,
                ascending=get_bottom
            )
            
            ranking_type = "Bottom" if get_bottom else "Top"
            return f"{ranking_type} {n} por {metric}:\n{result.to_string(index=False)}"
        except Exception as e:
            return f"Erro ao obter ranking: {str(e)}"
    
    def get_table_schema_tool(table_name: str = None) -> str:
        """
        Retorna informações sobre o schema das tabelas.
        
        Use esta ferramenta quando:
        - Usuário pergunta sobre estrutura dos dados
        - Você precisa saber quais colunas existem
        - Você precisa entender relacionamentos entre tabelas
        
        Args:
            table_name: Nome da tabela (opcional, None retorna resumo de todas)
            
        Returns:
            String com informações do schema
        """
        try:
            if table_name:
                return get_table_info(table_name)
            else:
                return get_all_tables_summary()
        except Exception as e:
            return f"Erro ao obter schema: {str(e)}"
    
    def join_and_analyze_tool(
        fact_table: str,
        dim_table: str,
        analysis_type: str,
        group_by: str = None
    ) -> str:
        """
        Faz join e análise entre tabelas fato e dimensão.
        
        Use esta ferramenta para perguntas que precisam relacionar dados:
        - Satisfação por nome de curso (precisa join FATO_AVCURSOS + DIM_CURSOS)
        - Respostas por texto da pergunta (precisa join com DIM_PERGUNTAS)
        - Análises por eixo SINAES, dimensão, etc.
        
        Args:
            fact_table: Tabela fato (FATO_*)
            dim_table: Tabela dimensão (DIM_*)
            analysis_type: Tipo de análise: 'satisfacao' ou 'contagem'
            group_by: Coluna para agrupar (da tabela dimensão, ex: NOME_CURSO, PERGUNTA)
            
        Returns:
            String formatada com resultados
        """
        try:
            df_joined = analyzer.join_with_dimension(fact_table, dim_table)
            
            if analysis_type == 'satisfacao':
                df_joined['is_concordo'] = (df_joined['RESPOSTA'] == 'Concordo').astype(int)
                df_joined['is_discordo'] = (df_joined['RESPOSTA'] == 'Discordo').astype(int)
                
                if group_by:
                    result = df_joined.groupby(group_by).agg({
                        'is_concordo': 'sum',
                        'is_discordo': 'sum'
                    }).reset_index()
                    
                    result['total_valid'] = result['is_concordo'] + result['is_discordo']
                    result['satisfacao_%'] = result.apply(
                        lambda x: round((x['is_concordo'] / x['total_valid'] * 100), 2) if x['total_valid'] > 0 else 0,
                        axis=1
                    )
                    result = result.sort_values('satisfacao_%', ascending=False)
                else:
                    total_c = df_joined['is_concordo'].sum()
                    total_d = df_joined['is_discordo'].sum()
                    total_v = total_c + total_d
                    sat = round((total_c / total_v * 100), 2) if total_v > 0 else 0
                    result = pd.DataFrame([{'satisfacao_%': sat, 'total_validas': total_v}])
                    
            elif analysis_type == 'contagem':
                if group_by:
                    result = df_joined.groupby(group_by).size().reset_index(name='contagem')
                    result = result.sort_values('contagem', ascending=False)
                else:
                    result = pd.DataFrame([{'contagem_total': len(df_joined)}])
            else:
                return f"Tipo de análise '{analysis_type}' não suportado. Use: satisfacao ou contagem"
            
            if len(result) > 20:
                return f"Resultados (top 20 de {len(result)}):\n{result.head(20).to_string(index=False)}"
            else:
                return f"Resultados:\n{result.to_string(index=False)}"
                
        except Exception as e:
            return f"Erro ao fazer join e análise: {str(e)}"
    
    tools = [
        FunctionTool.from_defaults(fn=calculate_satisfaction_tool),
        FunctionTool.from_defaults(fn=count_responses_tool),
        FunctionTool.from_defaults(fn=get_top_bottom_tool),
        FunctionTool.from_defaults(fn=get_table_schema_tool),
        FunctionTool.from_defaults(fn=join_and_analyze_tool),
    ]
    
    return tools


def get_chat_engine(api_key: str = None):
    """
    Inicializa e retorna o chat engine híbrido usando Gemini.
    Combina análise estruturada (data tools) com busca semântica (vector index).
    """
    if not api_key:
        from src.utils.key_manager import get_decrypted_key
        api_key = get_decrypted_key()
        
    if not api_key:
        st.error("GOOGLE_API_KEY not found in environment variables. Please set it in .env file.")
        return None

    try:
        Settings.llm = GoogleGenAI(api_key=api_key, model_name="models/gemini-2.5-flash-live")
        Settings.embed_model = GoogleGenAIEmbedding(api_key=api_key, model_name="models/text-embedding-004")

        analyzer = get_data_analyzer()
        vector_index = get_vector_index()
        
        analysis_tools = create_analysis_tools(analyzer)
        
        all_tools = analysis_tools.copy()
        
        if vector_index:
            query_engine = vector_index.as_query_engine(
                similarity_top_k=3,
                llm=Settings.llm,
                embed_model=Settings.embed_model
            )
            
            def semantic_search_tool(question: str) -> str:
                """
                Busca semântica em documentos PDF e metadados.
                
                Use esta ferramenta APENAS para perguntas CONCEITUAIS/DESCRITIVAS:
                - "O que é SINAES?"
                - "Explique a metodologia da avaliação"
                - "Quais são os eixos avaliativos?"
                - "O que significa dimensão X?"
                
                NÃO use para cálculos, contagens ou análises quantitativas.
                
                Args:
                    question: Pergunta conceitual
                    
                Returns:
                    Resposta baseada nos documentos
                """
                try:
                    response = query_engine.query(question)
                    return str(response)
                except Exception as e:
                    return f"Erro na busca semântica: {str(e)}"
            
            all_tools.append(FunctionTool.from_defaults(fn=semantic_search_tool))
        
        system_prompt = f"""Você é um assistente de análise de dados da UFPR especializado em avaliação institucional.

FERRAMENTAS DISPONÍVEIS:

1. **Ferramentas de Análise de Dados** (para perguntas QUANTITATIVAS):
   - calculate_satisfaction_tool: Calcular satisfação (% Concordo)
   - count_responses_tool: Contar respostas
   - get_top_bottom_tool: Rankings (top/bottom N)
   - join_and_analyze_tool: Relacionar tabelas e analisar
   - get_table_schema_tool: Ver estrutura das tabelas

2. **Busca Semântica** (para perguntas CONCEITUAIS):
   - semantic_search_tool: Buscar informações em PDFs e documentos

REGRAS IMPORTANTES:

1. **PRIORIZE O CONTEXTO DA TELA**:
   - O usuário receberá um contexto detalhado sobre qual dashboard está visualizando
   - Este contexto inclui DEFINIÇÕES, CÁLCULOS e DADOS VISÍVEIS na tela
   - Para perguntas sobre indicadores/métricas visíveis, USE O CONTEXTO FORNECIDO
   - Exemplo: Se o usuário pergunta "o que significa índice de didática" e o contexto contém a definição, use essa informação diretamente
   - Exemplo: Se o usuário pergunta "o que levou ao score X", consulte os dados no contexto que mostram os valores

2. **Escolha a ferramenta certa**:
   - Perguntas sobre DEFINIÇÕES/SIGNIFICADOS de indicadores → Use o contexto fornecido primeiro
   - Perguntas com números/cálculos novos → Use data tools
   - Perguntas "o que é", "explique" (conceitos gerais) → Use semantic search
   
3. **SEMPRE cite a fonte**: Mencione se usou o contexto da tela, tabela ou documento

4. **Formato de resposta**:
   - Seja direto e objetivo
   - Use números formatados (ex: 85.5%, não 0.855)
   - Liste top N em formato legível
   - Quando usar contexto da tela, mencione: "Com base nos dados visíveis na tela..."
   
5. **Se não souber**: Pergunte ao usuário para esclarecer

6. **Responda SEMPRE em português brasileiro**

MÉTRICAS COMUNS:
{str(COMMON_METRICS)}

TABELAS DISPONÍVEIS:
{get_all_tables_summary()}

Comece analisando a pergunta do usuário, verificando o contexto fornecido, e escolhendo a(s) ferramenta(s) apropriada(s).
"""
        agent = ReActAgent(
            tools=all_tools,
            llm=Settings.llm,
            verbose=True,
            max_iterations=10,
            system_prompt=system_prompt
        )
        
        return agent
        
    except Exception as e:
        st.error(f"Error initializing hybrid RAG engine: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None
