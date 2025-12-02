"""
Metadados das tabelas do sistema de avaliação UFPR.
Este módulo define o schema e relacionamentos entre tabelas para ajudar o LLM
a entender a estrutura dos dados e fazer queries corretas.
"""

TABLES_SCHEMA = {
    "FATO_AVCURSOS": {
        "description": "Respostas da avaliação de cursos (dados factuais de cada resposta)",
        "columns": {
            "ID_QUESTIONARIO": "Identificador único do questionário respondido",
            "ID_PERGUNTA": "Código da pergunta (FK para DIM_PERGUNTAS)",
            "RESPOSTA": "Resposta: 'Concordo', 'Discordo' ou 'Desconheço'",
            "COD_CURSO": "Código do curso avaliado (FK para DIM_CURSOS)",
            "ANO": "Ano da avaliação",
            "SEMESTRE": "Semestre da avaliação (1 ou 2)"
        },
        "relationships": {
            "DIM_PERGUNTAS": ("ID_PERGUNTA", "ID_PERGUNTA"),
            "DIM_CURSOS": ("COD_CURSO", "COD_CURSO")
        },
        "primary_key": "ID_QUESTIONARIO",
        "row_count_approx": 2000000
    },
    
    "FATO_AVDISCIPLINAS": {
        "description": "Respostas da avaliação de disciplinas (maior volume de dados)",
        "columns": {
            "ID_QUESTIONARIO": "Identificador único do questionário respondido",
            "ID_PERGUNTA": "Código da pergunta (FK para DIM_PERGUNTAS)",
            "RESPOSTA": "Resposta: 'Concordo', 'Discordo' ou 'Desconheço'",
            "COD_DISCIPLINA": "Código da disciplina avaliada (FK para DIM_DISCIPLINAS)",
            "COD_CURSO": "Código do curso (FK para DIM_CURSOS)",
            "ANO": "Ano da avaliação",
            "SEMESTRE": "Semestre da avaliação (1 ou 2)"
        },
        "relationships": {
            "DIM_PERGUNTAS": ("ID_PERGUNTA", "ID_PERGUNTA"),
            "DIM_DISCIPLINAS": ("COD_DISCIPLINA", "COD_DISCIPLINA"),
            "DIM_CURSOS": ("COD_CURSO", "COD_CURSO")
        },
        "primary_key": "ID_QUESTIONARIO",
        "row_count_approx": 20000000
    },
    
    "FATO_AVINSTITUCIONAL": {
        "description": "Respostas da avaliação institucional (servidores/professores)",
        "columns": {
            "ID_QUESTIONARIO": "Identificador único do questionário respondido",
            "ID_PERGUNTA": "Código da pergunta (FK para DIM_PERGUNTAS)",
            "RESPOSTA": "Resposta: 'Concordo', 'Discordo' ou 'Desconheço'",
            "SIGLA_LOTACAO": "Sigla da unidade de lotação do respondente",
            "ANO": "Ano da avaliação",
            "SEMESTRE": "Semestre da avaliação (1 ou 2)"
        },
        "relationships": {
            "DIM_PERGUNTAS": ("ID_PERGUNTA", "ID_PERGUNTA")
        },
        "primary_key": "ID_QUESTIONARIO",
        "row_count_approx": 2400000
    },
    
    "DIM_PERGUNTAS": {
        "description": "Dimensão de perguntas - contém o texto e classificação de cada pergunta",
        "columns": {
            "ID_PERGUNTA": "Identificador único da pergunta (PK)",
            "PERGUNTA": "Texto completo da pergunta",
            "EIXO_SINAES": "Classificação no eixo SINAES (1-5)",
            "DIM_SINAES": "Dimensão SINAES detalhada",
            "Tipo_Pergunta": "Tipo/categoria da pergunta"
        },
        "primary_key": "ID_PERGUNTA",
        "display_column": "PERGUNTA",
        "row_count_approx": 200
    },
    
    "DIM_CURSOS": {
        "description": "Dimensão de cursos - informações dos cursos da UFPR",
        "columns": {
            "COD_CURSO": "Código único do curso (PK)",
            "CURSO": "Nome completo do curso",
            "SETOR_CURSO": "Setor/Centro ao qual o curso pertence",
            "GRAU": "Grau: Bacharelado, Licenciatura, Tecnólogo"
        },
        "primary_key": "COD_CURSO",
        "display_column": "CURSO",
        "row_count_approx": 300
    },
    
    "DIM_DISCIPLINAS": {
        "description": "Dimensão de disciplinas - catálogo de disciplinas",
        "columns": {
            "COD_DISCIPLINA": "Código único da disciplina (PK)",
            "NOME_DISCIPLINA": "Nome completo da disciplina",
            "COD_CURSO": "Código do curso (FK para DIM_CURSOS)",
            "CARGA_HORARIA": "Carga horária da disciplina"
        },
        "relationships": {
            "DIM_CURSOS": ("COD_CURSO", "COD_CURSO")
        },
        "primary_key": "COD_DISCIPLINA",
        "display_column": "NOME_DISCIPLINA",
        "row_count_approx": 5000
    },
    
    "DIM_TIPO_PERGUNTA_SINAES": {
        "description": "Dimensão de tipos de perguntas SINAES - taxonomia completa",
        "columns": {
            "Tipo_Perg": "Tipo da pergunta (identificador único)",
            "Descricao": "Descrição do tipo de pergunta"
        },
        "primary_key": "Tipo_Perg",
        "display_column": "Descricao",
        "row_count_approx": 50
    },
    
    "DIM_UNIDADES": {
        "description": "Dimensão de unidades - setores e centros da UFPR",
        "columns": {
            "SIGLA_LOTACAO": "Sigla da unidade (PK)",
            "UNIDADE GESTORA": "Nome completo da unidade",
            "LOTACAO": "Lotação detalhada"
        },
        "primary_key": "SIGLA_LOTACAO",
        "display_column": "UNIDADE GESTORA",
        "row_count_approx": 100
    }
}

VALID_VALUES = {
    "RESPOSTA": ["Concordo", "Discordo", "Desconheço"],
    "SEMESTRE": ["1", "2"],
    "GRAU": ["Bacharelado", "Licenciatura", "Tecnólogo"]
}

COMMON_METRICS = {
    "satisfacao": {
        "description": "Percentual de 'Concordo' sobre total de respostas válidas (Concordo + Discordo)",
        "formula": "(count(Concordo) / (count(Concordo) + count(Discordo))) * 100"
    },
    "discordancia": {
        "description": "Percentual de 'Discordo' sobre total de respostas válidas",
        "formula": "(count(Discordo) / (count(Concordo) + count(Discordo))) * 100"
    },
    "gap_desconhecimento": {
        "description": "Percentual de 'Desconheço' sobre total de respostas",
        "formula": "(count(Desconheço) / count(*)) * 100"
    },
    "net_score": {
        "description": "Diferença entre Concordo e Discordo normalizada",
        "formula": "((count(Concordo) - count(Discordo)) / (count(Concordo) + count(Discordo))) * 100"
    }
}

def get_table_info(table_name: str) -> str:
    """
    Retorna informações formatadas sobre uma tabela.
    
    Args:
        table_name: Nome da tabela
        
    Returns:
        String formatada com schema da tabela
    """
    if table_name not in TABLES_SCHEMA:
        available = ", ".join(TABLES_SCHEMA.keys())
        return f"Tabela '{table_name}' não encontrada. Tabelas disponíveis: {available}"
    
    schema = TABLES_SCHEMA[table_name]
    info = f"**{table_name}**\n"
    info += f"Descrição: {schema['description']}\n"
    info += f"Aproximadamente {schema['row_count_approx']:,} linhas\n\n"
    info += "**Colunas:**\n"
    
    for col, desc in schema['columns'].items():
        info += f"  - {col}: {desc}\n"
    
    if 'relationships' in schema:
        info += "\n**Relacionamentos:**\n"
        for related_table, (fk, pk) in schema['relationships'].items():
            info += f"  - {related_table} via {fk} → {pk}\n"
    
    return info

def get_all_tables_summary() -> str:
    """Retorna resumo de todas as tabelas disponíveis."""
    summary = "**Tabelas Disponíveis no Sistema de Avaliação UFPR:**\n\n"
    
    summary += "**Tabelas Fato (Respostas):**\n"
    for table in ["FATO_AVCURSOS", "FATO_AVDISCIPLINAS", "FATO_AVINSTITUCIONAL"]:
        schema = TABLES_SCHEMA[table]
        summary += f"  - {table}: {schema['description']} (~{schema['row_count_approx']:,} linhas)\n"
    
    summary += "\n**Tabelas Dimensão (Metadados):**\n"
    for table in ["DIM_PERGUNTAS", "DIM_CURSOS", "DIM_DISCIPLINAS", "DIM_UNIDADES", "DIM_TIPO_PERGUNTA_SINAES"]:
        schema = TABLES_SCHEMA[table]
        summary += f"  - {table}: {schema['description']} (~{schema['row_count_approx']:,} linhas)\n"
    
    summary += "\n**Métricas Comuns:**\n"
    for metric, info in COMMON_METRICS.items():
        summary += f"  - {metric}: {info['description']}\n"
    
    return summary
