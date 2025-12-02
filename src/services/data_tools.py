"""
Ferramentas de análise de dados para o sistema RAG.
Este módulo fornece funções seguras para o LLM executar queries e análises
nos DataFrames das tabelas de avaliação UFPR.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Union
import re
from src.services.table_metadata import TABLES_SCHEMA, COMMON_METRICS, VALID_VALUES


class DataAnalyzer:
    """
    Classe para análise segura de dados.
    Carrega os DataFrames em memória e fornece métodos para queries.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Inicializa o analisador carregando todos os DataFrames.
        
        Args:
            data_dir: Diretório contendo os arquivos CSV
        """
        self.data_dir = data_dir
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self._load_all_dataframes()
    
    def _load_all_dataframes(self):
        """Carrega todos os CSVs mencionados no schema."""
        import os
        
        for table_name in TABLES_SCHEMA.keys():
            file_path = os.path.join(self.data_dir, f"{table_name}.csv")
            if os.path.exists(file_path):
                try:
                    try:
                        df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)
                    except:
                        df = pd.read_csv(file_path, sep=';', dtype=str)
                    
                    df.columns = df.columns.str.replace('\ufeff', '').str.strip()
                    
                    df = df.fillna("")
                    
                    self.dataframes[table_name] = df
                    
                except Exception as e:
                    print(f"Warning: Failed to load {table_name}: {e}")
    def _auto_join_dimensions(self, df: pd.DataFrame, source_table: str) -> pd.DataFrame:
        """
        Automaticamente faz join com tabelas de dimensão para trazer nomes legíveis.
        Verifica se o DataFrame tem colunas que são FKs e traz a display_column da dimensão.
        """
        if source_table not in TABLES_SCHEMA:
            return df
            
        schema = TABLES_SCHEMA[source_table]
        if 'relationships' not in schema:
            return df
            
        result = df.copy()
        
        for dim_table, (fk, pk) in schema['relationships'].items():
            if fk in result.columns:
                if dim_table in TABLES_SCHEMA and 'display_column' in TABLES_SCHEMA[dim_table]:
                    display_col = TABLES_SCHEMA[dim_table]['display_column']
                    
                    if dim_table in self.dataframes:
                        dim_df = self.dataframes[dim_table]
                        
                        dim_subset = dim_df[[pk, display_col]].drop_duplicates()
                        
                        result = pd.merge(
                            result, 
                            dim_subset, 
                            left_on=fk, 
                            right_on=pk, 
                            how='left'
                        )
        
        return result

    def get_available_tables(self) -> List[str]:
        """Retorna lista de tabelas carregadas."""
        return list(self.dataframes.keys())
    
    def calculate_satisfaction(
        self, 
        table_name: str, 
        group_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Calcula satisfação (% Concordo sobre válidos).
        
        Args:
            table_name: Nome da tabela (FATO_*)
            group_by: Coluna para agrupar (ex: 'COD_CURSO', 'SIGLA_LOTACAO')
            filters: Dicionário de filtros {coluna: valor}
            
        Returns:
            DataFrame com colunas: [group_by], satisfacao, total_respostas
            
        Example:
            >>> analyzer.calculate_satisfaction('FATO_AVCURSOS', group_by='COD_CURSO')
            >>> analyzer.calculate_satisfaction('FATO_AVINSTITUCIONAL', filters={'ID_PERGUNTA': '2005'})
        """
        if table_name not in self.dataframes:
            raise ValueError(f"Tabela {table_name} não encontrada. Disponíveis: {self.get_available_tables()}")
        
        df = self.dataframes[table_name].copy()
        
        if filters:
            for col, value in filters.items():
                if col not in df.columns:
                    raise ValueError(f"Coluna {col} não existe em {table_name}")
                df = df[df[col] == str(value)]
        
        if 'RESPOSTA' not in df.columns:
            raise ValueError(f"Tabela {table_name} não tem coluna RESPOSTA")
        
        df['is_concordo'] = (df['RESPOSTA'] == 'Concordo').astype(int)
        df['is_discordo'] = (df['RESPOSTA'] == 'Discordo').astype(int)
        
        if group_by:
            if group_by not in df.columns:
                raise ValueError(f"Coluna {group_by} não existe em {table_name}")
            
            grouped = df.groupby(group_by).agg({
                'is_concordo': 'sum',
                'is_discordo': 'sum'
            }).reset_index()
            
            grouped['total_valid'] = grouped['is_concordo'] + grouped['is_discordo']
            grouped['satisfacao'] = grouped.apply(
                lambda x: round((x['is_concordo'] / x['total_valid'] * 100), 2) if x['total_valid'] > 0 else 0, 
                axis=1
            )
            
            result = grouped[[group_by, 'satisfacao', 'total_valid']].copy()
            result.columns = [group_by, 'satisfacao_%', 'total_respostas_validas']
            
            result = self._auto_join_dimensions(result, table_name)
            
            return result.sort_values('satisfacao_%', ascending=False)
        else:
            total_concordo = df['is_concordo'].sum()
            total_discordo = df['is_discordo'].sum()
            total_valid = total_concordo + total_discordo
            
            satisfacao = round((total_concordo / total_valid * 100), 2) if total_valid > 0 else 0
            
            return pd.DataFrame([{
                'satisfacao_%': satisfacao,
                'total_concordo': int(total_concordo),
                'total_discordo': int(total_discordo),
                'total_respostas_validas': int(total_valid)
            }])
    
    def count_responses(
        self,
        table_name: str,
        group_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        response_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Conta respostas com filtros opcionais.
        
        Args:
            table_name: Nome da tabela
            group_by: Coluna para agrupar
            filters: Filtros a aplicar
            response_type: Tipo de resposta específico ('Concordo', 'Discordo', 'Desconheço')
            
        Returns:
            DataFrame com contagens
            
        Example:
            >>> analyzer.count_responses('FATO_AVINSTITUCIONAL', response_type='Desconheço')
            >>> analyzer.count_responses('FATO_AVCURSOS', group_by='COD_CURSO', response_type='Concordo')
        """
        if table_name not in self.dataframes:
            raise ValueError(f"Tabela {table_name} não encontrada")
        
        df = self.dataframes[table_name].copy()
        
        if filters:
            for col, value in filters.items():
                if col not in df.columns:
                    raise ValueError(f"Coluna {col} não existe em {table_name}")
                df = df[df[col] == str(value)]
        
        if response_type:
            if response_type not in VALID_VALUES['RESPOSTA']:
                raise ValueError(f"response_type deve ser um de: {VALID_VALUES['RESPOSTA']}")
            df = df[df['RESPOSTA'] == response_type]
        
        if group_by:
            if group_by not in df.columns:
                raise ValueError(f"Coluna {group_by} não existe em {table_name}")
            
            result = df.groupby(group_by).size().reset_index(name='contagem')
            
            result = self._auto_join_dimensions(result, table_name)
            
            return result.sort_values('contagem', ascending=False)
        else:
            return pd.DataFrame([{'contagem_total': len(df)}])
    
    def join_with_dimension(
        self,
        fact_table: str,
        dim_table: str,
        dim_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Faz join de uma tabela fato com uma dimensão.
        
        Args:
            fact_table: Nome da tabela fato (FATO_*)
            dim_table: Nome da tabela dimensão (DIM_*)
            dim_columns: Colunas da dimensão para incluir (None = todas)
            
        Returns:
            DataFrame mesclado
            
        Example:
            >>> analyzer.join_with_dimension('FATO_AVCURSOS', 'DIM_PERGUNTAS', ['PERGUNTA', 'EIXO_SINAES'])
        """
        if fact_table not in self.dataframes:
            raise ValueError(f"Tabela {fact_table} não encontrada")
        if dim_table not in self.dataframes:
            raise ValueError(f"Tabela {dim_table} não encontrada")
        
        if dim_table not in TABLES_SCHEMA[fact_table].get('relationships', {}):
            raise ValueError(f"Não há relacionamento definido entre {fact_table} e {dim_table}")
        
        fk, pk = TABLES_SCHEMA[fact_table]['relationships'][dim_table]
        
        df_fact = self.dataframes[fact_table].copy()
        df_dim = self.dataframes[dim_table].copy()
        
        if dim_columns:
            cols_to_include = list(set([pk] + dim_columns))
            df_dim = df_dim[cols_to_include]
        
        result = pd.merge(df_fact, df_dim, left_on=fk, right_on=pk, how='inner')
        
        return result
    
    def get_top_n(
        self,
        table_name: str,
        metric: str = 'satisfacao',
        n: int = 10,
        group_by: Optional[str] = None,
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Retorna top N registros por métrica.
        
        Args:
            table_name: Nome da tabela
            metric: Métrica ('satisfacao', 'contagem', 'gap_desconhecimento')
            n: Número de resultados
            group_by: Coluna para agrupar
            ascending: True para bottom N, False para top N
            filters: Filtros a aplicar
            
        Returns:
            DataFrame com top/bottom N
            
        Example:
            >>> analyzer.get_top_n('FATO_AVCURSOS', metric='satisfacao', n=5, group_by='COD_CURSO')
            >>> analyzer.get_top_n('FATO_AVINSTITUCIONAL', metric='contagem', n=10, group_by='SIGLA_LOTACAO')
        """
        if metric == 'satisfacao':
            df = self.calculate_satisfaction(table_name, group_by=group_by, filters=filters)
            sort_col = 'satisfacao_%'
        elif metric == 'contagem':
            df = self.count_responses(table_name, group_by=group_by, filters=filters)
            sort_col = 'contagem'
        elif metric == 'gap_desconhecimento':
            df_all = self.count_responses(table_name, group_by=group_by, filters=filters)
            df_desc = self.count_responses(
                table_name, 
                group_by=group_by, 
                filters=filters, 
                response_type='Desconheço'
            )
            
            df = pd.merge(
                df_all, 
                df_desc, 
                on=group_by if group_by else None,
                how='left',
                suffixes=('_total', '_desconheco')
            )
            df['gap_desconhecimento_%'] = round(
                (df['contagem_desconheco'] / df['contagem_total'] * 100), 2
            )
            sort_col = 'gap_desconhecimento_%'
        else:
            raise ValueError(f"Métrica '{metric}' não suportada. Use: satisfacao, contagem, gap_desconhecimento")
        
        if metric == 'gap_desconhecimento':
             df = self._auto_join_dimensions(df, table_name)
             
        return df.sort_values(sort_col, ascending=ascending).head(n)
    
    def custom_query(
        self,
        table_name: str,
        query_text: str
    ) -> pd.DataFrame:
        """
        Executa uma query personalizada segura usando pd.query().
        
        Args:
            table_name: Nome da tabela
            query_text: String de query (ex: "RESPOSTA == 'Concordo' and ANO == '2024'")
            
        Returns:
            DataFrame filtrado
            
        Example:
            >>> analyzer.custom_query('FATO_AVCURSOS', "RESPOSTA == 'Concordo' and SEMESTRE == '1'")
        """
        if table_name not in self.dataframes:
            raise ValueError(f"Tabela {table_name} não encontrada")
        
        dangerous_patterns = [
            r'\bimport\b', r'\bexec\b', r'\beval\b', r'\b__\b',
            r'\bopen\b', r'\bfile\b', r'\bos\b', r'\bsys\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query_text, re.IGNORECASE):
                raise ValueError(f"Query contém operação não permitida: {pattern}")
        
        try:
            df = self.dataframes[table_name].copy()
            result = df.query(query_text)
            return result
        except Exception as e:
            raise ValueError(f"Erro ao executar query: {str(e)}")
    
    def get_table_preview(self, table_name: str, n: int = 5) -> pd.DataFrame:
        """
        Retorna preview de uma tabela.
        
        Args:
            table_name: Nome da tabela
            n: Número de linhas
            
        Returns:
            DataFrame com primeiras n linhas
        """
        if table_name not in self.dataframes:
            raise ValueError(f"Tabela {table_name} não encontrada")
        
        return self.dataframes[table_name].head(n)
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Retorna estatísticas de uma tabela.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Dicionário com estatísticas
        """
        if table_name not in self.dataframes:
            raise ValueError(f"Tabela {table_name} não encontrada")
        
        df = self.dataframes[table_name]
        
        stats = {
            'num_rows': len(df),
            'num_columns': len(df.columns),
            'columns': list(df.columns),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
        
        if 'RESPOSTA' in df.columns:
            stats['resposta_distribution'] = df['RESPOSTA'].value_counts().to_dict()
        
        return stats
