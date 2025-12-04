import streamlit as st
import os
import pandas as pd
import plotly.express as px

def load_data(file_name):
    file_path = os.path.join("data", file_name)
    if not os.path.exists(file_path):
        return None
    try:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)
        except:
            df = pd.read_csv(file_path, sep=';', dtype=str)
        
        df.columns = df.columns.str.replace('\ufeff', '').str.strip()
        
        df = df.fillna("")
        df = df.astype(str)
        
        return df
    except Exception:
        return None

@st.cache_data(show_spinner="Carregando dados")
def load_dataframes():
    df_cursos = load_data("FATO_AVCURSOS.csv")
    df_inst = load_data("FATO_AVINSTITUCIONAL.csv")
    df_disc = load_data("FATO_AVDISCIPLINAS.csv")
    df_perguntas = load_data("DIM_PERGUNTAS.csv")
    df_dim_disc = load_data("DIM_DISCIPLINAS.csv")
    df_dim_cursos = load_data("DIM_CURSOS.csv")
    df_tipo_sinaes = load_data("DIM_TIPO_PERGUNTA_SINAES.csv")

    return df_cursos, df_inst, df_disc, df_perguntas, df_dim_disc, df_dim_cursos, df_tipo_sinaes

def render_dashboard():
    st.header("Dashboards Analíticos")

    df_cursos, df_inst, df_disc, df_perguntas, df_dim_disc, df_dim_cursos, df_tipo_sinaes = load_dataframes()

    tabs_names = ["Visão Geral da Avaliação", "Eixos SINAES", "Qualidade de Ensino", "Gestão de cursos", "Clima institucional", "Explorador de Arquivos Brutos"]
    
    tab_overview, tab_sinaes, tab_teaching, tab_courses, tab_climate, tab_explorer = st.tabs(tabs_names)

    context_accumulator = []

    def update_ai_context(tab_name, data_dict, additional_info=""):
        """
        Adiciona informações ao contexto global da IA.
        """
        context = f"### Dashboard: '{tab_name}'\n"
        context += "Dados resumidos desta seção:\n\n"
        
        for name, data in data_dict.items():
            if isinstance(data, pd.DataFrame):
                if len(data) > 20: 
                    context += f"#### Tabela: {name} (Top 20 linhas)\n"
                    context += data.head(20).to_markdown(index=False)
                else:
                    context += f"#### Tabela: {name}\n"
                    context += data.to_markdown(index=False)
            else:
                context += f"- **{name}**: {data}\n"
        
        if additional_info:
            context += "\n" + additional_info
        
        context += "\n---\n"
        context_accumulator.append(context)

    with tab_overview:
        st.subheader("Visão Geral da Avaliação")
        
        if df_cursos is not None and df_inst is not None and df_disc is not None and df_perguntas is not None:
            
            fatos_list = []
            source_map = {
                "Cursos": "Avaliação de Cursos",
                "Institucional": "Avaliação Institucional",
                "Disciplinas": "Avaliação de Disciplinas"
            }
            
            for df, name in [(df_cursos, "Cursos"), (df_inst, "Institucional"), (df_disc, "Disciplinas")]:
                if 'ID_PERGUNTA' in df.columns and 'RESPOSTA' in df.columns:
                    temp_df = df[['ID_PERGUNTA', 'RESPOSTA']].copy()
                    temp_df['TIPO_AVALIACAO'] = source_map[name]
                    fatos_list.append(temp_df)
                else:
                    st.warning(f"Colunas ID_PERGUNTA ou RESPOSTA ausentes em {name}")

            if fatos_list:
                df_fatos = pd.concat(fatos_list, ignore_index=True)
                
                df_merged = pd.merge(df_fatos, df_perguntas[['ID_PERGUNTA', 'PERGUNTA']], on='ID_PERGUNTA', how='inner')
                
                total_rows = len(df_merged)
                
                count_concordo = len(df_merged[df_merged['RESPOSTA'] == 'Concordo'])
                count_discordo = len(df_merged[df_merged['RESPOSTA'] == 'Discordo'])
                count_desconheco = len(df_merged[df_merged['RESPOSTA'] == 'Desconheço'])

                denom_satisfacao = count_concordo + count_discordo
                satisfacao_geral = (count_concordo / denom_satisfacao * 100) if denom_satisfacao > 0 else 0
                
                gap_desconhecimento = (count_desconheco / total_rows * 100) if total_rows > 0 else 0
                
                engajamento_total = total_rows
                
                col1, col2, col3, col4 = st.columns([0.15, 0.15, 0.15, 0.55])
                
                col1.metric("Satisfação Global", f"{satisfacao_geral:.2f}%")
                col2.metric("Gap de Comunicação", f"{gap_desconhecimento:.2f}%")
                col3.metric("Engajamento total", f"{len(df_fatos)}")
                with col4:
                    count_cursos = len(df_cursos) if df_cursos is not None else 0
                    count_inst = len(df_inst) if df_inst is not None else 0
                    count_disc = len(df_disc) if df_disc is not None else 0
                    total_counts = count_cursos + count_inst + count_disc
                    
                    data = [
                        {'Fonte': 'Avaliação de Cursos', 'Contagem': count_cursos},
                        {'Fonte': 'Avaliação Institucional', 'Contagem': count_inst},
                        {'Fonte': 'Avaliação de Disciplinas', 'Contagem': count_disc}
                    ]
                    df_engajamento = pd.DataFrame(data)
                    
                    def format_label(row):
                        pct = (row['Contagem'] / total_counts * 100) if total_counts > 0 else 0
                        cnt_k = row['Contagem'] / 1000
                        return f"{row['Fonte']}: {pct:.1f}% do peso ({cnt_k:.0f}k respostas)"
                    
                    df_engajamento['Label'] = df_engajamento.apply(format_label, axis=1)
                    
                    fig_donut = px.pie(df_engajamento, values='Contagem', names='Label', hole=0.6,
                                     title="Composição do Engajamento")
                    fig_donut.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0), margin=dict(t=30, b=0, l=0, r=0), height=200)
                    st.plotly_chart(fig_donut, width="stretch")


                df_merged['is_concordo'] = (df_merged['RESPOSTA'] == 'Concordo').astype(int)
                df_merged['is_discordo'] = (df_merged['RESPOSTA'] == 'Discordo').astype(int)
                
                df_grouped = df_merged.groupby('TIPO_AVALIACAO')[['is_concordo', 'is_discordo']].sum().reset_index()
                
                df_grouped['total_valid'] = df_grouped['is_concordo'] + df_grouped['is_discordo']
                
                df_grouped['satisfacao'] = df_grouped.apply(
                    lambda x: (x['is_concordo'] / x['total_valid'] * 100) if x['total_valid'] > 0 else 0, axis=1
                )
                df_grouped['discordancia'] = df_grouped.apply(
                    lambda x: (x['is_discordo'] / x['total_valid'] * 100) if x['total_valid'] > 0 else 0, axis=1
                )
                
                col_charts1, col_charts2 = st.columns(2)
                
                with col_charts1:
                    df_sorted_sat = df_grouped.sort_values('satisfacao', ascending=True) 
                    st.markdown("#### Destaques de Excelência")
                    fig_top = px.bar(df_sorted_sat, x='satisfacao', y='TIPO_AVALIACAO', orientation='h',
                                        labels={'satisfacao': 'Satisfação (%)', 'TIPO_AVALIACAO': ''},
                                        color_discrete_sequence=['#28a745'],
                                        text_auto='.1f')
                    st.plotly_chart(fig_top, width="stretch")
            
                with col_charts2:
                    df_sorted_disc = df_grouped.sort_values('discordancia', ascending=True) 
                    st.markdown("#### Pontos de Risco Crítico")
                    fig_bottom = px.bar(df_sorted_disc, x='discordancia', y='TIPO_AVALIACAO', orientation='h',
                                        labels={'discordancia': 'Discordância (%)', 'TIPO_AVALIACAO': ''},
                                        color_discrete_sequence=['#dc3545'],
                                        text_auto='.1f')
                    st.plotly_chart(fig_bottom, width="stretch")
                
                visao_geral_context = f"""
DEFINIÇÕES DOS INDICADORES DA VISÃO GERAL:
1. **Satisfação Média Geral** ({satisfacao_geral:.2f}%): % de respostas "Concordo" sobre total de respostas válidas.
2. **Gap de Comunicação** ({gap_desconhecimento:.2f}%): % de respostas "Desconheço".
3. **Engajamento Total**: {len(df_fatos)} respostas.
"""
                
                update_ai_context("Visão Geral da Avaliação", {
                    "Satisfação Global": f"{satisfacao_geral:.2f}%",
                    "Gap de Comunicação": f"{gap_desconhecimento:.2f}%",
                    "Engajamento Total": f"{len(df_fatos)}",
                    "Destaques": df_sorted_sat[['TIPO_AVALIACAO', 'satisfacao']].head(5),
                    "Riscos": df_sorted_disc[['TIPO_AVALIACAO', 'discordancia']].head(5)
                }, additional_info=visao_geral_context)

            else:
                st.error("Não foi possível carregar as tabelas FATO.")
        else:
            st.error("Arquivos de dados necessários (FATOs ou DIM_PERGUNTAS) não encontrados.")
    
    with tab_sinaes:
        st.subheader("Eixos SINAES")
        
        if df_cursos is not None and df_inst is not None and df_disc is not None and df_perguntas is not None and df_tipo_sinaes is not None:

            cols = ['ID_PERGUNTA', 'RESPOSTA']
            
            dfs_to_concat = []
            for df in [df_cursos, df_inst, df_disc]:
                if all(c in df.columns for c in cols):
                    dfs_to_concat.append(df[cols])
            
            if dfs_to_concat:
                df_master = pd.concat(dfs_to_concat, ignore_index=True)
                
                df_master['ID_PERGUNTA'] = df_master['ID_PERGUNTA'].astype(str)
                df_perguntas['ID_PERGUNTA'] = df_perguntas['ID_PERGUNTA'].astype(str)
                
                df_sinaes = pd.merge(df_master, df_perguntas[['ID_PERGUNTA', 'EIXO_SINAES', 'DIM_SINAES', 'Tipo_Pergunta']], on='ID_PERGUNTA', how='inner')
                
                df_sinaes = df_sinaes[df_sinaes['EIXO_SINAES'] != '']
                df_sinaes = df_sinaes[df_sinaes['DIM_SINAES'] != '']
                
                total_types = df_tipo_sinaes['Tipo_Perg'].nunique()
                evaluated_types = df_sinaes['Tipo_Pergunta'].nunique()
                absent_types = max(0, total_types - evaluated_types)
                
                col_cov, col_axis = st.columns([1, 2])
                
                with col_cov:
                    st.markdown("#### Índice de Cobertura das Dimensões SINAES")
                    df_coverage = pd.DataFrame({
                        'Status': ['Avaliado', 'Ausente'],
                        'Count': [evaluated_types, absent_types]
                    })
                    df_coverage['Percentage'] = (df_coverage['Count'] / total_types * 100).astype(int)
                    df_coverage['Label'] = df_coverage.apply(lambda x: f"{x['Status']} ({x['Percentage']}%)", axis=1)
                    
                    fig_donut = px.pie(df_coverage, values='Count', names='Label', hole=0.6,
                                     color='Status',
                                     color_discrete_map={'Avaliado': '#28a745', 'Ausente': '#adb5bd'})
                    fig_donut.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0), height=300)
                    st.plotly_chart(fig_donut, width="stretch")

                df_sinaes['is_concordo'] = (df_sinaes['RESPOSTA'] == 'Concordo').astype(int)
                df_sinaes['is_discordo'] = (df_sinaes['RESPOSTA'] == 'Discordo').astype(int)
                
                def get_score_df(group_col):
                    df_grouped = df_sinaes.groupby(group_col)[['is_concordo', 'is_discordo']].sum().reset_index()
                    df_grouped['total_valid'] = df_grouped['is_concordo'] + df_grouped['is_discordo']
                    df_grouped['satisfacao'] = df_grouped.apply(
                        lambda x: (x['is_concordo'] / x['total_valid'] * 100) if x['total_valid'] > 0 else 0, axis=1
                    )
                    return df_grouped.sort_values('satisfacao', ascending=True)

                with col_axis:
                    st.markdown("#### Score de Aprovação Líquida por Eixo SINAES")
                    df_axis_score = get_score_df('EIXO_SINAES')
                    
                    fig_axis = px.bar(df_axis_score, x='satisfacao', y='EIXO_SINAES', orientation='h',
                                      text_auto='.1f',
                                      labels={'satisfacao': 'Score de Aprovação (%)', 'EIXO_SINAES': ''},
                                      color='EIXO_SINAES',
                                      color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_axis.update_layout(xaxis_range=[0, 100], showlegend=False, height=300)
                    st.plotly_chart(fig_axis, width="stretch")
                
                st.markdown("#### Score de Aprovação por Dimensão SINAES")
                df_dim_score = get_score_df('DIM_SINAES')
                
                fig_dim = px.bar(df_dim_score, x='satisfacao', y='DIM_SINAES', orientation='h',
                                  text_auto='.1f',
                                  labels={'satisfacao': 'Score de Aprovação (%)', 'DIM_SINAES': ''},
                                  color='satisfacao',
                                  color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
                                  range_color=[50, 100]) 
                fig_dim.update_layout(xaxis_range=[0, 100], height=500)
                st.plotly_chart(fig_dim, width="stretch")
                
                sinaes_context = f"""
DEFINIÇÕES SINAES:
- Cobertura: {evaluated_types}/{total_types} tipos avaliados.
- Score por Eixo: Média de satisfação nos 5 eixos.
"""
                update_ai_context("Eixos SINAES", {
                    "Cobertura": df_coverage,
                    "Score Eixo": df_axis_score,
                    "Score Dimensão": df_dim_score
                }, additional_info=sinaes_context)
                
            else:
                st.warning("Não foi possível concatenar os dados das tabelas FATO.")
        else:
            st.warning("Dados necessários não carregados.")
    
    with tab_teaching:
        st.subheader("Qualidade de Ensino")
        
        if df_disc is not None and df_perguntas is not None:
            def calculate_score(df_subset):
                if df_subset.empty: return 0.0
                concordo = len(df_subset[df_subset['RESPOSTA'] == 'Concordo'])
                discordo = len(df_subset[df_subset['RESPOSTA'] == 'Discordo'])
                total = concordo + discordo
                return (concordo / total * 100) if total > 0 else 0.0

           
            df_aderencia = df_disc[df_disc['ID_PERGUNTA'] == '1733']
            score_aderencia = calculate_score(df_aderencia)

            df_carga = df_disc[df_disc['ID_PERGUNTA'] == '1734']
            score_carga = calculate_score(df_carga)

            didatica_ids = ['1732', '1735', '1736', '1743', '1746', '1750']
            df_didatica = df_disc[df_disc['ID_PERGUNTA'].isin(didatica_ids)]
            score_didatica = calculate_score(df_didatica)

            col1, col2, col3 = st.columns(3)
            col1.metric("Aderência ao Plano de Disciplina", f"{score_aderencia:.1f}%")
            col2.metric("Carga Horária", f"{score_carga:.1f}%")
            col3.metric("Índice de Didática", f"{score_didatica:.1f}%")

            col_c1, col_c2 = st.columns(2)

            df_hist_source = df_disc[df_disc['ID_PERGUNTA'].isin(didatica_ids)].copy()
            disc_col = 'COD_DISCIPLINA' if 'COD_DISCIPLINA' in df_hist_source.columns else 'ID_DISCIPLINA'
            
            df_hist = None
            if disc_col in df_hist_source.columns:
                df_hist_source['is_concordo'] = (df_hist_source['RESPOSTA'] == 'Concordo').astype(int)
                df_hist_source['is_discordo'] = (df_hist_source['RESPOSTA'] == 'Discordo').astype(int)
                
                df_by_disc = df_hist_source.groupby(disc_col)[['is_concordo', 'is_discordo']].sum().reset_index()
                df_by_disc['total'] = df_by_disc['is_concordo'] + df_by_disc['is_discordo']
                df_by_disc['score'] = df_by_disc.apply(lambda x: (x['is_concordo'] / x['total'] * 100) if x['total'] > 0 else 0, axis=1)
                
                bins = [0, 50, 70, 80, 90, 95, 100.1] 
                labels = ['<50% (Crítico)', '50-70% (Ruim)', '70-80% (Regular)', '80-90% (Bom)', '90-95% (Ótimo)', '95-100% (Excelência)']
                df_by_disc['Range'] = pd.cut(df_by_disc['score'], bins=bins, labels=labels, right=False)
                
                df_hist = df_by_disc['Range'].value_counts().reindex(labels).reset_index()
                df_hist.columns = ['Faixa de Satisfação', 'Número de Disciplinas']
                
                with col_c1:
                    st.markdown("#### Distribuição da Qualidade das Disciplinas")
                    fig_hist = px.bar(df_hist, x='Faixa de Satisfação', y='Número de Disciplinas',
                                      text_auto=True,
                                      title="Distribuição por Score de Didática")
                    fig_hist.update_layout(xaxis_title="Faixa de Satisfação", yaxis_title="Número de Disciplinas")
                    st.plotly_chart(fig_hist, width="stretch")
            else:
                with col_c1:
                    st.warning("Coluna de identificação da disciplina não encontrada.")

            aspects_map = {
                'Metodologia': ['1736', '1743'],
                'Conteúdo': ['1735', '1767'],
                'Avaliação': ['1737', '1744', '1748', '1762']
            }
            
            aspect_scores = []
            for aspect, ids in aspects_map.items():
                df_aspect = df_disc[df_disc['ID_PERGUNTA'].isin(ids)]
                score = calculate_score(df_aspect)
                aspect_scores.append({'Aspecto': aspect, 'Score': score})
            
            df_aspects = pd.DataFrame(aspect_scores)
            
            with col_c2:
                st.markdown("#### Comparativo de Score por Aspecto Pedagógico")
                fig_aspects = px.bar(df_aspects, x='Score', y='Aspecto', orientation='h',
                                     text_auto='.1f',
                                     title="Score por Aspecto",
                                     color='Aspecto', 
                                     color_discrete_sequence=px.colors.qualitative.Set2)
                fig_aspects.update_layout(xaxis_range=[0, 100], showlegend=False)
                st.plotly_chart(fig_aspects, width="stretch")

            context_data = {
                "Aderência": f"{score_aderencia:.1f}%",
                "Carga": f"{score_carga:.1f}%",
                "Didática": f"{score_didatica:.1f}%",
                "Aspectos": df_aspects
            }
            if df_hist is not None:
                context_data["Distribuição"] = df_hist
            
            update_ai_context("Qualidade de Ensino", context_data)

        else:
            st.warning("Arquivos necessários (FATO_AVDISCIPLINAS.csv, DIM_PERGUNTAS.csv) não encontrados.")

    with tab_courses:
        st.subheader("Gestão de cursos")
        
        if df_cursos is not None and df_disc is not None:
            def calc_score(df_sub):
                if df_sub.empty: return 0.0
                concordo = len(df_sub[df_sub['RESPOSTA'] == 'Concordo'])
                discordo = len(df_sub[df_sub['RESPOSTA'] == 'Discordo'])
                total = concordo + discordo
                return (concordo / total * 100) if total > 0 else 0.0

            df_inter = df_cursos[df_cursos['ID_PERGUNTA'] == '1942']
            score_inter = calc_score(df_inter)

            df_apoio = df_cursos[df_cursos['ID_PERGUNTA'] == '1957']
            score_apoio = calc_score(df_apoio)
            
            df_vis = df_cursos[df_cursos['ID_PERGUNTA'] == '1820']
            if not df_vis.empty:
                total_vis = len(df_vis)
                desconheco_vis = len(df_vis[df_vis['RESPOSTA'] == 'Desconheço'])
                taxa_visibilidade = (1 - (desconheco_vis / total_vis)) * 100
            else:
                taxa_visibilidade = 0.0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Índice de Interdisciplinaridade", f"{score_inter:.1f}%")
            col2.metric("Satisfação com Atend. e Apoio", f"{score_apoio:.1f}%")
            col3.metric("Taxa de Visibilidade de Apoio", f"{taxa_visibilidade:.1f}%")
            
            if 'COD_CURSO' in df_disc.columns and df_dim_cursos is not None:

                df_disc_clean = df_disc.drop(columns=['SETOR_CURSO'], errors='ignore')
                df_chart_source = pd.merge(df_disc_clean, df_dim_cursos[['COD_CURSO', 'SETOR_CURSO']], on='COD_CURSO', how='inner')
                
                if 'SETOR_CURSO' in df_chart_source.columns:
                    df_chart_source = df_chart_source[df_chart_source['SETOR_CURSO'] != 'PRÓ-REITORIA DE GRADUAÇÃO']
                
                    df_chart_source['is_concordo'] = (df_chart_source['RESPOSTA'] == 'Concordo').astype(int)
                    df_chart_source['is_discordo'] = (df_chart_source['RESPOSTA'] == 'Discordo').astype(int)
                    
                    df_sector = df_chart_source.groupby('SETOR_CURSO')[['is_concordo', 'is_discordo']].sum().reset_index()
                    df_sector['total_valid'] = df_sector['is_concordo'] + df_sector['is_discordo']
                    df_sector['satisfacao'] = df_sector.apply(
                        lambda x: (x['is_concordo'] / x['total_valid'] * 100) if x['total_valid'] > 0 else 0, axis=1
                    )
                    
                    total_concordo_global = df_sector['is_concordo'].sum()
                    total_valid_global = df_sector['total_valid'].sum()
                    global_mean = (total_concordo_global / total_valid_global * 100) if total_valid_global > 0 else 0
                    
                    st.markdown("#### Ranking de Satisfação por Setor (Ensino)")
                    df_sorted_sector = df_sector.sort_values('satisfacao', ascending=True)
                    
                    fig_sector = px.bar(df_sorted_sector, x='satisfacao', y='SETOR_CURSO', orientation='h',
                                        text_auto='.2f',
                                        labels={'satisfacao': 'Score de Aprovação (%)', 'SETOR_CURSO': ''},
                                        color_discrete_sequence=['#28a745'])
                    fig_sector.update_layout(xaxis_range=[40, 100]) 
                    st.plotly_chart(fig_sector, width="stretch")
                    
                    st.markdown("#### Score Médio de Satisfação vs. Volume de Respostas")
                    
                    fig_scatter = px.scatter(df_sector, x='satisfacao', y='total_valid',
                                                color='satisfacao',
                                                color_continuous_scale=['#dc3545', '#ffc107', '#28a745'], 
                                                text='SETOR_CURSO',
                                                labels={'satisfacao': 'Score de Aprovação (%)', 'total_valid': 'Volume de Respostas Válidas'},
                                                title="Intervenção Prioritária")
                    
                    fig_scatter.update_traces(textposition='top center', marker=dict(size=12))
                    fig_scatter.add_vline(x=global_mean, line_width=1, line_dash="dash", line_color="gray", annotation_text=f"Média Geral: {global_mean:.2f}%")
                    st.plotly_chart(fig_scatter, width="stretch")
                    
                    update_ai_context("Gestão de cursos", {
                        "Interdisciplinaridade": f"{score_inter:.1f}%",
                        "Apoio": f"{score_apoio:.1f}%",
                        "Visibilidade": f"{taxa_visibilidade:.1f}%",
                        "Ranking Setores": df_sorted_sector[['SETOR_CURSO', 'satisfacao', 'total_valid']].head(20),
                        "Média Geral": f"{global_mean:.2f}%"
                    })

                else:
                    st.warning("Coluna SETOR_CURSO não encontrada após merge.")
            else:
                st.warning("Dados de Disciplinas ou Cursos (DIM) não carregados ou coluna COD_CURSO ausente.")
                update_ai_context("Gestão de cursos", {
                    "Interdisciplinaridade": f"{score_inter:.1f}%",
                    "Apoio": f"{score_apoio:.1f}%",
                    "Visibilidade": f"{taxa_visibilidade:.1f}%"
                })
        else:
            st.warning("Dados necessários não carregados.")
    
    with tab_climate:
        st.subheader("Clima institucional (dos professores)")
        
        if df_inst is not None:
            def calc_score(df_sub):
                if df_sub.empty: return 0.0
                concordo = len(df_sub[df_sub['RESPOSTA'] == 'Concordo'])
                discordo = len(df_sub[df_sub['RESPOSTA'] == 'Discordo'])
                total = concordo + discordo
                return (concordo / total * 100) if total > 0 else 0.0

            df_transp = df_inst[df_inst['ID_PERGUNTA'] == '2005']
            score_transp = calc_score(df_transp)
            
            df_seg = df_inst[df_inst['ID_PERGUNTA'] == '2013']
            score_seg = calc_score(df_seg)
            
            df_gap = df_inst[df_inst['ID_PERGUNTA'] == '1984']
            score_gap = calc_score(df_gap)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Score de Transparência (RH/Movimentação)", f"{score_transp:.1f}%")
            col2.metric("Índice de Segurança/Infraestrutura", f"{score_seg:.1f}%")
            col3.metric("Gap de Comunicação (Familiaridade com o PDE)", f"{score_gap:.1f}%")
            
            st.markdown("#### Ranking de Satisfação dos Servidores por Unidade")
            if 'SIGLA_LOTACAO' in df_inst.columns:
                df_inst['is_concordo'] = (df_inst['RESPOSTA'] == 'Concordo').astype(int)
                df_inst['is_discordo'] = (df_inst['RESPOSTA'] == 'Discordo').astype(int)
                
                df_unit = df_inst.groupby('SIGLA_LOTACAO')[['is_concordo', 'is_discordo']].sum().reset_index()
                df_unit['total_valid'] = df_unit['is_concordo'] + df_unit['is_discordo']
                df_unit['satisfacao'] = df_unit.apply(
                    lambda x: (x['is_concordo'] / x['total_valid'] * 100) if x['total_valid'] > 0 else 0, axis=1
                )
                
                df_top_unit = df_unit.sort_values('satisfacao', ascending=True).tail(10)
                
                fig_unit = px.bar(df_top_unit, x='satisfacao', y='SIGLA_LOTACAO', orientation='h',
                                    text_auto='.1f',
                                    labels={'satisfacao': 'Score de Aprovação (%)', 'SIGLA_LOTACAO': ''},
                                    color_discrete_sequence=['#28a745'])
                fig_unit.update_layout(xaxis_range=[0, 100])
                st.plotly_chart(fig_unit, width="stretch")
            else:
                st.warning("Coluna SIGLA_LOTACAO não encontrada.")
        
            st.markdown("### Polarização de Opinião em Temas Críticos")
            
            topics = [
                {'Topic': 'Transparência RH', 'ID': '2005'},
                {'Topic': 'Segurança no Trabalho', 'ID': '2013'},
                {'Topic': 'Familiaridade com o PDE/PDI', 'ID': '1984'}
            ]
            
            polarization_data = []
            for item in topics:
                df_topic = df_inst[df_inst['ID_PERGUNTA'] == item['ID']]
                if not df_topic.empty:
                    concordo = len(df_topic[df_topic['RESPOSTA'] == 'Concordo'])
                    discordo = len(df_topic[df_topic['RESPOSTA'] == 'Discordo'])
                    
                    total_valid = concordo + discordo
                    if total_valid > 0:
                        net_score = (concordo - discordo) / total_valid * 100
                    else:
                        net_score = 0
                    
                    polarization_data.append({'Topic': item['Topic'], 'Net Score': net_score})
            
            df_pol = pd.DataFrame(polarization_data)
            
            fig_pol = px.bar(df_pol, x='Net Score', y='Topic', orientation='h',
                                text_auto='.1f',
                                title="Net Score (Concordo - Discordo)",
                                color='Net Score',
                                color_continuous_scale=['#dc3545', '#28a745'], 
                                range_color=[-100, 100])
            fig_pol.update_layout(xaxis_title="Net Score (%)", yaxis_title="")
            st.plotly_chart(fig_pol, width="stretch")

            ctx_data = {
                "Transparência": f"{score_transp:.1f}%",
                "Segurança": f"{score_seg:.1f}%",
                "Gap Comunicação": f"{score_gap:.1f}%",
                "Polarização": df_pol
            }
            if 'df_top_unit' in locals():
                ctx_data["Top Unidades"] = df_top_unit
            
            update_ai_context("Clima institucional", ctx_data)

        else:
            st.warning("Dados Institucionais não carregados.")

    with tab_explorer:
        st.subheader("Explorador de Arquivos Brutos")

        data_dir = "data"
        files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.csv', '.xls'))]
        selected_file = st.selectbox("Selecione um arquivo para visualizar:", files)

        if selected_file:
            df_raw = load_data(selected_file)
            if df_raw is not None:
                try:
                    st.write("Visualização (Primeiras 20 linhas):")
                    st.table(df_raw.head(20).astype(str))
                    
                    update_ai_context("Explorador de Arquivos Brutos", {
                        "Arquivo": selected_file,
                        "Amostra": df_raw.head(20)
                    })
                except Exception as e:
                    st.error(f"Error displaying table: {e}")

    st.session_state['active_tab_context'] = "\n".join(context_accumulator)
