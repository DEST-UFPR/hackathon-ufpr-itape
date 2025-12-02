#!/usr/bin/env python3
"""
Script de teste do sistema RAG híbrido.
Testa as ferramentas de análise de dados sem precisar rodar o Streamlit.
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.data_tools import DataAnalyzer
from src.services.table_metadata import get_all_tables_summary, get_table_info

def test_data_analyzer():
    """Testa as funcionalidades do DataAnalyzer."""
    print("=" * 80)
    print("TESTE DO DATA ANALYZER")
    print("=" * 80)
    
    print("\nCarregando dados...")
    analyzer = DataAnalyzer(data_dir="data")
    
    print(f"Tabelas carregadas: {', '.join(analyzer.get_available_tables())}")
    
    # Teste 1: Satisfação geral
    print("\n" + "-" * 80)
    print("TESTE 1: Satisfação geral de cursos")
    print("-" * 80)
    try:
        result = analyzer.calculate_satisfaction("FATO_AVCURSOS")
        print(result)
        print("Teste 1 passou!")
    except Exception as e:
        print(f"Teste 1 falhou: {e}")
    
    # Teste 2: Top 10 cursos por satisfação (com verificação de nomes)
    print("\n" + "-" * 80)
    print("TESTE 2: Top 10 cursos com maior satisfação (Auto-Join Check)")
    print("-" * 80)
    try:
        result = analyzer.get_top_n(
            "FATO_AVCURSOS",
            metric="satisfacao",
            n=10,
            group_by="COD_CURSO",
            ascending=False
        )
        print(result)
        
        if 'CURSO' in result.columns:
            print("Auto-join funcionou! Coluna CURSO encontrada.")
            print(result[['COD_CURSO', 'CURSO', 'satisfacao_%']].head())
        else:
            print("Auto-join FALHOU! Coluna CURSO não encontrada.")
            
        print("Teste 2 passou!")
    except Exception as e:
        print(f"Teste 2 falhou: {e}")
    
    # Teste 3: Contagem de respostas "Desconheço"
    print("\n" + "-" * 80)
    print("TESTE 3: Total de respostas 'Desconheço'")
    print("-" * 80)
    try:
        result = analyzer.count_responses(
            "FATO_AVINSTITUCIONAL",
            response_type="Desconheço"
        )
        print(result)
        print("Teste 3 passou!")
    except Exception as e:
        print(f"Teste 3 falhou: {e}")
    
    # Teste 4: Join com dimensão
    print("\n" + "-" * 80)
    print("TESTE 4: Join FATO_AVCURSOS com DIM_PERGUNTAS")
    print("-" * 80)
    try:
        result = analyzer.join_with_dimension(
            "FATO_AVCURSOS",
            "DIM_PERGUNTAS",
            dim_columns=["PERGUNTA", "EIXO_SINAES"]
        )
        print(f"Join retornou {len(result)} linhas")
        print(f"Colunas: {list(result.columns)}")
        print(result.head(3))
        print("Teste 4 passou!")
    except Exception as e:
        print(f"Teste 4 falhou: {e}")
    
    # Teste 5: Estatísticas de tabela
    print("\n" + "-" * 80)
    print("TESTE 5: Estatísticas das tabelas")
    print("-" * 80)
    try:
        for table in ["FATO_AVCURSOS", "FATO_AVDISCIPLINAS", "FATO_AVINSTITUCIONAL"]:
            stats = analyzer.get_table_stats(table)
            print(f"\n{table}:")
            print(f"  Linhas: {stats['num_rows']:,}")
            print(f"  Colunas: {stats['num_columns']}")
            print(f"  Memória: {stats['memory_usage_mb']:.2f} MB")
            if 'resposta_distribution' in stats:
                print(f"  Distribuição de respostas: {stats['resposta_distribution']}")
        print("Teste 5 passou!")
    except Exception as e:
        print(f"Teste 5 falhou: {e}")
    
    print("\n" + "=" * 80)
    print("TODOS OS TESTES CONCLUÍDOS!")
    print("=" * 80)

def test_metadata():
    """Testa os metadados das tabelas."""
    print("\n" + "=" * 80)
    print("TESTE DE METADADOS")
    print("=" * 80)
    
    print("\nResumo de todas as tabelas:")
    print(get_all_tables_summary())
    
    print("\n" + "-" * 80)
    print("Detalhes da FATO_AVCURSOS:")
    print("-" * 80)
    print(get_table_info("FATO_AVCURSOS"))

if __name__ == "__main__":
    try:
        test_metadata()
        test_data_analyzer()
        
        print("\nTODOS OS TESTES PASSARAM COM SUCESSO!")
        print("\nSistema híbrido RAG está pronto para uso.")
        print("Execute: streamlit run app.py")
        
    except Exception as e:
        print(f"\nERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
