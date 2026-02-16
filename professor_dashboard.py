import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
from analytics import (
    get_all_users_analytics, get_global_stats,
    get_global_knowledge_component_stats, get_average_user_level,
    get_hardest_categories, get_student_complete_profile,
    get_student_weakness_analysis, format_duration
)
from auth_firebase import get_all_users, get_user_by_id
from logic import get_case
from admin_utils import (
    reset_student_analytics, clear_student_chat_interactions,
    reset_all_students_analytics, clear_all_chat_interactions,
    log_admin_action, get_database_stats
)

def show_advanced_professor_dashboard():
    """Dashboard redesenhado para professores com foco em insights acionáveis"""
    st.title("📊 Dashboard do Professor")
    st.markdown("---")
    
    try:
        # Carrega dados
        all_users = get_all_users()
        all_analytics = get_all_users_analytics()
        
        # Filtra apenas alunos
        student_users = [user for user in all_users if user.get('user_type') == 'aluno']
        
        if not student_users:
            st.warning("Nenhum aluno encontrado.")
            return
            
        if not all_analytics:
            st.info("Nenhum dado de analytics encontrado ainda. Os alunos precisam responder questões primeiro.")
            # Ainda permite acesso ao admin mesmo sem dados
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return
    
    # Sistema de tabs redesenhado: 3 tabs (adicionada aba Admin)
    tab1, tab2, tab3 = st.tabs([
        "📊 Visão Geral", 
        "👤 Análise Individual",
        "⚙️ Admin"
    ])
    
    with tab1:
        if all_analytics:
            show_general_overview_tab(student_users, all_analytics)
        else:
            st.info("Aguardando dados de analytics...")
    
    with tab2:
        if all_analytics:
            show_individual_analysis_tab(student_users, all_analytics)
        else:
            st.info("Aguardando dados de analytics...")
    
    with tab3:
        show_admin_tab(student_users)

def show_general_overview_tab(student_users: List[Dict], all_analytics: Dict):
    """Tab de visão geral com estatísticas gerais de todos os alunos"""
    st.subheader("📈 Visão Geral da Turma")
    
    # Carrega estatísticas globais
    global_stats = get_global_stats()
    component_stats = get_global_knowledge_component_stats()
    level_stats = get_average_user_level()
    hardest_categories = get_hardest_categories(top_n=5)
    
    # ===== KPIs PRINCIPAIS =====
    st.markdown("### 📌 Métricas Principais")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "👥 Total de Alunos",
            len(student_users),
            help="Número total de alunos cadastrados"
        )
    
    with col2:
        st.metric(
            "🎯 Média Geral",
            f"{global_stats.get('average_accuracy_rate', 0):.1f}%",
            help="Taxa média de acertos de todos os alunos"
        )
    
    
    with col3:
        # Categoria com maior dificuldade - Custom display para evitar truncamento
        if hardest_categories:
            hardest_cat = hardest_categories[0]['componente']
            hardest_acc = hardest_categories[0]['taxa_acerto']
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%); 
                            padding: 1rem; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3);'>
                    <div style='color: #94a3b8; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;'>
                        ⚠️ Categoria Mais Difícil
                    </div>
                    <div style='color: #ef4444; font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; 
                                word-wrap: break-word; line-height: 1.2;'>
                        {hardest_cat}
                    </div>
                    <div style='color: #ef4444; font-size: 0.875rem;'>
                        Taxa: {hardest_acc:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("⚠️ Categoria Mais Difícil", "N/A", help="Componente com menor taxa de acerto geral")
    
    
    with col4:
        # Nível médio - Custom display para consistência visual
        nivel_map = {1: "Básico", 2: "Intermediário", 3: "Avançado"}
        nivel_medio = nivel_map.get(level_stats.get('nivel_medio', 1), "Básico")
        
        # Cores por nível
        nivel_colors = {
            "Básico": "#3b82f6",
            "Intermediário": "#eab308", 
            "Avançado": "#22c55e"
        }
        color = nivel_colors.get(nivel_medio, "#3b82f6")
        
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%); 
                        padding: 1rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);'>
                <div style='color: #94a3b8; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;'>
                    📊 Nível Médio
                </div>
                <div style='color: {color}; font-size: 1.875rem; font-weight: 600;'>
                    {nivel_medio}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.metric(
            "📚 Questões Respondidas",
            global_stats.get('total_cases', 0),
            help="Total de questões respondidas por todos os alunos"
        )
    
    st.markdown("---")
    
    # ===== VISUALIZAÇÕES =====
    
    # Linha 1: Desempenho por Componente e Distribuição por Nível
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📚 Desempenho por Componente de Conhecimento")
        if component_stats:
            df_comp = pd.DataFrame(component_stats)
            
            # Trunca nomes muito longos para melhor visualização
            df_comp['componente_display'] = df_comp['componente'].apply(
                lambda x: x if len(x) <= 30 else x[:27] + '...'
            )
            
            fig_comp = px.bar(
                df_comp,
                x='taxa_acerto',
                y='componente_display',
                orientation='h',
                title="Taxa de Acerto por Componente (%)",
                text_auto='.1f',
                color='taxa_acerto',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                hover_data={'componente': True, 'componente_display': False}  # Mostra nome completo no hover
            )
            fig_comp.update_layout(
                xaxis_title="Taxa de Acerto (%)",
                yaxis_title=None,
                showlegend=False,
                height=400,
                margin=dict(l=200, r=20, t=40, b=40),  # Mais espaço à esquerda para labels
                yaxis=dict(tickfont=dict(size=11))  # Fonte menor para caber melhor
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tooltip explicativo
            st.caption("💡 Componentes no topo têm menor taxa de acerto (mais difíceis)")
        else:
            st.info("Dados insuficientes para análise por componente")
    
    with col2:
        st.markdown("### 📊 Distribuição de Alunos por Nível")
        if level_stats.get('total_alunos', 0) > 0:
            dist = level_stats['distribuicao']
            
            df_level = pd.DataFrame({
                'Nível': ['Básico', 'Intermediário', 'Avançado'],
                'Quantidade': [dist['basico'], dist['intermediario'], dist['avancado']]
            })
            
            fig_level = px.pie(
                df_level,
                values='Quantidade',
                names='Nível',
                title="Distribuição de Alunos",
                color='Nível',
                color_discrete_map={
                    'Básico': '#3b82f6',
                    'Intermediário': '#eab308',
                    'Avançado': '#22c55e'
                }
            )
            fig_level.update_traces(textposition='inside', textinfo='percent+label')
            fig_level.update_layout(height=400)
            st.plotly_chart(fig_level, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    st.markdown("---")
    
    # Linha 2: Top 5 Categorias Mais Difíceis
    st.markdown("### ⚠️ Top 5 Categorias Mais Difíceis")
    if hardest_categories:
        df_hardest = pd.DataFrame(hardest_categories)
        
        # Trunca nomes muito longos
        df_hardest['componente_display'] = df_hardest['componente'].apply(
            lambda x: x if len(x) <= 30 else x[:27] + '...'
        )
        
        fig_hardest = px.bar(
            df_hardest,
            x='taxa_acerto',
            y='componente_display',
            orientation='h',
            title="Componentes que Precisam de Mais Atenção",
            text_auto='.1f',
            color='taxa_acerto',
            color_continuous_scale='Reds_r',
            range_color=[0, 100],
            hover_data={'componente': True, 'componente_display': False}
        )
        fig_hardest.update_layout(
            xaxis_title="Taxa de Acerto (%)",
            yaxis_title=None,
            showlegend=False,
            height=300,
            margin=dict(l=200, r=20, t=40, b=40),
            yaxis=dict(tickfont=dict(size=11))
        )
        st.plotly_chart(fig_hardest, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("📋 Detalhes das Categorias Difíceis"):
            df_display = df_hardest[['componente', 'taxa_acerto', 'total_questoes', 'acertos', 'tempo_medio_formatado']].copy()
            df_display.columns = ['Componente', 'Taxa de Acerto (%)', 'Total de Questões', 'Acertos', 'Tempo Médio']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Dados insuficientes")
    
    st.markdown("---")
    
    # Linha 3: Ranking de Alunos
    st.markdown("### 🏆 Ranking de Alunos")
    
    # Prepara dados para ranking
    ranking_data = []
    for user in student_users:
        uid = user['id']
        u_data = all_analytics.get(uid, {})
        case_analytics = u_data.get('case_analytics', [])
        
        if not case_analytics:
            continue
        
        total_cases = len(case_analytics)
        correct_cases = sum(1 for c in case_analytics 
                           if c.get("case_result", {}).get("is_correct", False))
        acc_rate = (correct_cases / total_cases * 100) if total_cases > 0 else 0.0
        
        ranking_data.append({
            'Nome': user['name'],
            'Email': user['email'],
            'Questões': total_cases,
            'Acertos': correct_cases,
            'Taxa de Acerto': acc_rate
        })
    
    if ranking_data:
        df_ranking = pd.DataFrame(ranking_data)
        df_ranking = df_ranking.sort_values('Taxa de Acerto', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌟 Top 10 Melhores Desempenhos")
            top_10 = df_ranking.head(10).copy()
            top_10['Taxa de Acerto'] = top_10['Taxa de Acerto'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(top_10, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### 🎯 Alunos que Precisam de Atenção")
            # Alunos com taxa de acerto < 50% ou menos de 3 questões respondidas
            need_attention = df_ranking[
                (df_ranking['Taxa de Acerto'] < 50) | (df_ranking['Questões'] < 3)
            ].head(10).copy()
            
            if not need_attention.empty:
                need_attention['Taxa de Acerto'] = need_attention['Taxa de Acerto'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(need_attention, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Todos os alunos estão com bom desempenho!")
    else:
        st.info("Nenhum aluno respondeu questões ainda")

def show_individual_analysis_tab(student_users: List[Dict], all_analytics: Dict):
    """Tab de análise individual com perfil detalhado de cada aluno"""
    st.subheader("👤 Análise Individual de Alunos")
    
    # ===== SELEÇÃO DE ALUNO =====
    st.markdown("### 🔍 Selecione um Aluno")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔎 Buscar por nome ou email", "")
    
    with col2:
        filter_performance = st.selectbox(
            "📊 Filtrar por desempenho",
            ["Todos", "Acima da média", "Abaixo da média", "Sem atividade"]
        )
    
    with col3:
        filter_level = st.selectbox(
            "📈 Filtrar por nível",
            ["Todos", "Básico", "Intermediário", "Avançado"]
        )
    
    # Aplica filtros
    filtered_students = student_users.copy()
    
    # Filtro de busca
    if search_term:
        filtered_students = [
            s for s in filtered_students 
            if search_term.lower() in s['name'].lower() or search_term.lower() in s['email'].lower()
        ]
    
    # Prepara lista para seleção
    if not filtered_students:
        st.warning("Nenhum aluno encontrado com os filtros aplicados.")
        return
    
    student_names = [f"{student['name']} ({student['email']})" for student in filtered_students]
    selected_student_idx = st.selectbox(
        "👤 Aluno:",
        range(len(student_names)),
        format_func=lambda x: student_names[x]
    )
    
    selected_student = filtered_students[selected_student_idx]
    student_id = selected_student['id']
    
    st.markdown("---")
    
    # ===== PERFIL DO ALUNO =====
    
    # Carrega perfil completo
    try:
        profile = get_student_complete_profile(student_id)
    except Exception as e:
        st.error(f"Erro ao carregar perfil do aluno: {e}")
        return
    
    basic_stats = profile['estatisticas_basicas']
    advanced_stats = profile['estatisticas_avancadas']
    weakness = profile['analise_fraquezas']
    comparison = profile['comparacao_turma']
    evolution = profile['evolucao_temporal']
    
    # Cabeçalho do perfil
    st.markdown(f"## 👤 {selected_student['name']}")
    st.caption(f"📧 {selected_student['email']}")
    
    # ===== SEÇÃO: DESEMPENHO GERAL =====
    st.markdown("### 📊 Desempenho Geral")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📚 Questões Respondidas",
            basic_stats['case_stats']['total_cases']
        )
    
    with col2:
        acc = basic_stats['case_stats']['accuracy_rate']
        st.metric(
            "🎯 Taxa de Acertos",
            f"{acc:.1f}%"
        )
    
    with col3:
        st.metric(
            "⏱️ Tempo Médio",
            basic_stats['case_stats']['average_time_formatted']
        )
    
    with col4:
        st.metric(
            "💬 Interações Chat",
            basic_stats['total_chat_interactions']
        )
    
    with col5:
        # Comparação com turma
        perf_icon = "🔼" if comparison['performance'] == 'acima' else "🔽" if comparison['performance'] == 'abaixo' else "➡️"
        st.metric(
            "📊 vs Turma",
            f"{perf_icon} {comparison['performance'].title()}",
            delta=f"{comparison['diferenca']:.1f}%",
            delta_color="normal" if comparison['performance'] == 'acima' else "inverse"
        )
    
    st.markdown("---")
    
    # ===== SEÇÃO: ANÁLISE DE DIFICULDADES =====
    st.markdown("### ⚠️ Análise de Dificuldades")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Componente Mais Difícil")
        worst_comp = weakness.get('componente_mais_dificil')
        if worst_comp:
            st.error(f"**{worst_comp['nome']}**")
            st.write(f"- Taxa de acerto: **{worst_comp['acuracia']:.1f}%**")
            st.write(f"- Questões: {worst_comp['acertos']}/{worst_comp['total']}")
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.markdown("#### 📈 Nível Mais Difícil")
        worst_diff = weakness.get('nivel_mais_dificil')
        if worst_diff:
            st.error(f"**{worst_diff['nivel'].title()}**")
            st.write(f"- Taxa de acerto: **{worst_diff['acuracia']:.1f}%**")
            st.write(f"- Questões: {worst_diff['acertos']}/{worst_diff['total']}")
        else:
            st.info("Dados insuficientes")
    
    # Componentes problemáticos
    problematic = weakness.get('componentes_problematicos', [])
    if problematic:
        st.markdown("#### 🚨 Componentes Problemáticos (Taxa < 50%)")
        for comp in problematic[:5]:  # Top 5
            st.warning(f"**{comp['nome']}**: {comp['acuracia']:.1f}% ({comp['acertos']}/{comp['total']})")
    
    # Padrões de erro
    patterns = weakness.get('padroes_erro', [])
    if patterns:
        st.markdown("#### 🔍 Padrões Identificados")
        for pattern in patterns:
            st.info(f"**{pattern['padrao']}**: {pattern['descricao']}")
    
    st.markdown("---")
    
    # ===== SEÇÃO: DESEMPENHO POR CATEGORIA =====
    st.markdown("### 📚 Desempenho por Categoria")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Por Componente de Conhecimento")
        if advanced_stats['componentes']:
            df_comp = pd.DataFrame(advanced_stats['componentes'])
            
            # Trunca nomes longos
            df_comp['nome_display'] = df_comp['nome'].apply(
                lambda x: x if len(x) <= 25 else x[:22] + '...'
            )
            
            fig_comp = px.bar(
                df_comp,
                x='acuracia',
                y='nome_display',
                orientation='h',
                text_auto='.1f',
                color='acuracia',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                hover_data={'nome': True, 'nome_display': False}
            )
            fig_comp.update_layout(
                xaxis_title="Acurácia (%)",
                yaxis_title=None,
                showlegend=False,
                height=400,
                margin=dict(l=180, r=20, t=20, b=40),
                yaxis=dict(tickfont=dict(size=10))
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.markdown("#### Por Nível de Dificuldade")
        if advanced_stats['dificuldade']:
            df_diff = pd.DataFrame(advanced_stats['dificuldade'])
            
            fig_diff = px.bar(
                df_diff,
                x='nivel',
                y='acuracia',
                text_auto='.1f',
                color='nivel',
                color_discrete_map={
                    'básico': '#22c55e',
                    'intermediário': '#eab308',
                    'avançado': '#ef4444'
                }
            )
            fig_diff.update_layout(
                xaxis_title="Nível",
                yaxis_title="Acurácia (%)",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig_diff, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    # Tabela detalhada
    with st.expander("📋 Tabela Detalhada por Componente"):
        if advanced_stats['componentes']:
            df_comp_table = pd.DataFrame(advanced_stats['componentes'])
            df_comp_table.columns = ['Componente', 'Acurácia (%)', 'Total', 'Acertos']
            df_comp_table = df_comp_table.sort_values('Acurácia (%)')
            st.dataframe(df_comp_table, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ===== SEÇÃO: HISTÓRICO DE RESPOSTAS =====
    st.markdown("### 📋 Histórico de Respostas")
    
    case_analytics = all_analytics.get(student_id, {}).get('case_analytics', [])
    
    if case_analytics:
        # Filtros para histórico
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_status = st.selectbox(
                "Status",
                ["Todos", "Corretas", "Incorretas"],
                key="hist_status"
            )
        
        with col2:
            # Pega componentes únicos
            all_components = set()
            for entry in case_analytics:
                cid = entry.get('case_id')
                q_info = get_case(cid)
                comps = q_info.get('componentes_conhecimento', [])
                all_components.update(comps)
            
            filter_component = st.selectbox(
                "Componente",
                ["Todos"] + sorted(list(all_components)),
                key="hist_comp"
            )
        
        with col3:
            filter_difficulty = st.selectbox(
                "Dificuldade",
                ["Todos", "básico", "intermediário", "avançado"],
                key="hist_diff"
            )
        
        # Prepara histórico
        history = []
        for entry in case_analytics:
            cid = entry.get('case_id')
            q_info = get_case(cid)
            result = entry.get('case_result', {})
            
            is_correct = result.get('is_correct', False)
            timestamp = entry.get('timestamp')
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Aplica filtros
            if filter_status == "Corretas" and not is_correct:
                continue
            if filter_status == "Incorretas" and is_correct:
                continue
            
            comps = q_info.get('componentes_conhecimento', [])
            if filter_component != "Todos" and filter_component not in comps:
                continue
            
            diff = q_info.get('dificuldade', 'básico')
            if filter_difficulty != "Todos" and diff != filter_difficulty:
                continue
            
            history.append({
                'Data': timestamp.strftime('%d/%m/%Y %H:%M'),
                'Questão': q_info.get('pergunta', 'N/A')[:50] + '...',
                'Componente': ', '.join(comps),
                'Dificuldade': diff.title(),
                'Status': '✅ Correto' if is_correct else '❌ Incorreto',
                'Tempo': format_duration(entry.get('duration_seconds', 0)),
                'Pontos': result.get('points_gained', 0)
            })
        
        if history:
            df_history = pd.DataFrame(history)
            st.dataframe(df_history, use_container_width=True, hide_index=True)
            
            # Botão de download
            csv = df_history.to_csv(index=False)
            st.download_button(
                label="📥 Baixar Histórico (CSV)",
                data=csv,
                file_name=f"historico_{selected_student['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhuma resposta encontrada com os filtros aplicados")
    else:
        st.info("Nenhuma questão respondida ainda")
    
    st.markdown("---")
    
    # ===== SEÇÃO: EVOLUÇÃO TEMPORAL =====
    st.markdown("### 📈 Evolução Temporal")
    
    weekly_perf = evolution.get('desempenho_semanal', {})
    trend = evolution.get('tendencia', 'estável')
    
    if weekly_perf:
        # Prepara dados para gráfico
        weeks = sorted(weekly_perf.keys())
        accuracies = []
        
        for week in weeks:
            data = weekly_perf[week]
            acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            accuracies.append(acc)
        
        df_evolution = pd.DataFrame({
            'Semana': weeks,
            'Taxa de Acerto (%)': accuracies
        })
        
        fig_evolution = px.line(
            df_evolution,
            x='Semana',
            y='Taxa de Acerto (%)',
            title=f"Evolução nas Últimas 4 Semanas (Tendência: {trend.title()})",
            markers=True
        )
        fig_evolution.update_layout(height=400)
        st.plotly_chart(fig_evolution, use_container_width=True)
        
        # Indicador de tendência
        if trend == 'melhorando':
            st.success("📈 **Tendência Positiva**: O aluno está melhorando!")
        elif trend == 'piorando':
            st.error("📉 **Atenção**: O desempenho está caindo")
        else:
            st.info("➡️ **Tendência Estável**: Desempenho consistente")
    else:
        st.info("Dados insuficientes para análise temporal (mínimo 1 semana de atividade)")

def show_admin_tab(student_users: List[Dict]):
    """Tab de administração para gerenciar banco de dados"""
    st.subheader("⚙️ Painel de Administração")
    
    st.warning("⚠️ **ATENÇÃO**: Esta área contém operações que podem deletar dados permanentemente!")
    
    st.markdown("---")
    
    # ===== ESTATÍSTICAS DO BANCO =====
    st.markdown("### 📊 Estatísticas do Banco de Dados")
    
    db_stats = get_database_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📚 Total de Questões Respondidas",
            db_stats['total_analytics'],
            help="Total de registros de case_analytics no banco"
        )
    
    with col2:
        st.metric(
            "💬 Total de Interações Chat",
            db_stats['total_chat_interactions'],
            help="Total de registros de chat_interactions no banco"
        )
    
    with col3:
        st.metric(
            "👥 Total de Usuários",
            db_stats['total_users'],
            help="Total de usuários cadastrados"
        )
    
    st.markdown("---")
    
    # ===== AÇÕES INDIVIDUAIS =====
    st.markdown("### 👤 Gerenciar Aluno Individual")
    
    if not student_users:
        st.info("Nenhum aluno cadastrado.")
    else:
        # Seletor de aluno
        student_names = [f"{student['name']} ({student['email']})" for student in student_users]
        selected_student_idx = st.selectbox(
            "Selecione um aluno:",
            range(len(student_names)),
            format_func=lambda x: student_names[x],
            key="admin_student_selector"
        )
        
        selected_student = student_users[selected_student_idx]
        student_id = selected_student['id']
        
        st.markdown(f"**Aluno selecionado:** {selected_student['name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🗑️ Resetar Questões")
            st.caption("Remove todas as questões respondidas por este aluno")
            
            if st.button("Resetar Questões do Aluno", key="reset_student_analytics", type="secondary"):
                # Confirmação
                if 'confirm_reset_student' not in st.session_state:
                    st.session_state.confirm_reset_student = True
                    st.warning("⚠️ Clique novamente para confirmar")
                else:
                    with st.spinner("Resetando questões..."):
                        success = reset_student_analytics(student_id)
                        if success:
                            log_admin_action(
                                "reset_student_analytics",
                                f"Resetadas questões do aluno {selected_student['name']} (ID: {student_id})",
                                student_id
                            )
                            st.success(f"✅ Questões de {selected_student['name']} resetadas com sucesso!")
                            del st.session_state.confirm_reset_student
                            st.rerun()
                        else:
                            st.error("❌ Erro ao resetar questões")
                            del st.session_state.confirm_reset_student
        
        with col2:
            st.markdown("#### 💬 Limpar Chat")
            st.caption("Remove todas as mensagens de chat deste aluno")
            
            if st.button("Limpar Chat do Aluno", key="clear_student_chat", type="secondary"):
                # Confirmação
                if 'confirm_clear_student_chat' not in st.session_state:
                    st.session_state.confirm_clear_student_chat = True
                    st.warning("⚠️ Clique novamente para confirmar")
                else:
                    with st.spinner("Limpando chat..."):
                        success = clear_student_chat_interactions(student_id)
                        if success:
                            log_admin_action(
                                "clear_student_chat",
                                f"Limpado chat do aluno {selected_student['name']} (ID: {student_id})",
                                student_id
                            )
                            st.success(f"✅ Chat de {selected_student['name']} limpo com sucesso!")
                            del st.session_state.confirm_clear_student_chat
                            st.rerun()
                        else:
                            st.error("❌ Erro ao limpar chat")
                            del st.session_state.confirm_clear_student_chat
    
    st.markdown("---")
    
    # ===== AÇÕES GLOBAIS =====
    st.markdown("### 🌍 Gerenciar Todos os Alunos")
    st.error("⚠️ **PERIGO**: Estas ações afetam TODOS os alunos e são IRREVERSÍVEIS!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🗑️ Resetar Todas as Questões")
        st.caption("Remove TODAS as questões respondidas de TODOS os alunos")
        
        # Checkbox de confirmação
        confirm_all_analytics = st.checkbox(
            "Eu entendo que esta ação é irreversível",
            key="confirm_checkbox_all_analytics"
        )
        
        if st.button(
            "RESETAR TODAS AS QUESTÕES",
            key="reset_all_analytics",
            type="primary",
            disabled=not confirm_all_analytics
        ):
            # Dupla confirmação
            if 'confirm_reset_all' not in st.session_state:
                st.session_state.confirm_reset_all = True
                st.error("🚨 ÚLTIMA CHANCE: Clique novamente para CONFIRMAR a deleção de TODOS os dados!")
            else:
                with st.spinner("Resetando TODAS as questões..."):
                    result = reset_all_students_analytics()
                    if result['deleted'] > 0:
                        log_admin_action(
                            "reset_all_analytics",
                            f"Resetadas TODAS as questões: {result['deleted']} registros deletados, {result['errors']} erros"
                        )
                        st.success(f"✅ {result['deleted']} questões resetadas com sucesso!")
                        if result['errors'] > 0:
                            st.warning(f"⚠️ {result['errors']} erros durante a operação")
                        del st.session_state.confirm_reset_all
                        st.rerun()
                    else:
                        st.error("❌ Erro ao resetar questões")
                        del st.session_state.confirm_reset_all
    
    with col2:
        st.markdown("#### 💬 Limpar Todos os Chats")
        st.caption("Remove TODAS as mensagens de chat de TODOS os usuários")
        
        # Checkbox de confirmação
        confirm_all_chat = st.checkbox(
            "Eu entendo que esta ação é irreversível",
            key="confirm_checkbox_all_chat"
        )
        
        if st.button(
            "LIMPAR TODOS OS CHATS",
            key="clear_all_chat",
            type="primary",
            disabled=not confirm_all_chat
        ):
            # Dupla confirmação
            if 'confirm_clear_all_chat' not in st.session_state:
                st.session_state.confirm_clear_all_chat = True
                st.error("🚨 ÚLTIMA CHANCE: Clique novamente para CONFIRMAR a deleção de TODAS as mensagens!")
            else:
                with st.spinner("Limpando TODOS os chats..."):
                    result = clear_all_chat_interactions()
                    if result['deleted'] > 0:
                        log_admin_action(
                            "clear_all_chat",
                            f"Limpados TODOS os chats: {result['deleted']} registros deletados, {result['errors']} erros"
                        )
                        st.success(f"✅ {result['deleted']} mensagens deletadas com sucesso!")
                        if result['errors'] > 0:
                            st.warning(f"⚠️ {result['errors']} erros durante a operação")
                        del st.session_state.confirm_clear_all_chat
                        st.rerun()
                    else:
                        st.error("❌ Erro ao limpar chats")
                        del st.session_state.confirm_clear_all_chat
    
    st.markdown("---")
    
    # ===== INFORMAÇÕES =====
    st.markdown("### ℹ️ Informações")
    
    with st.expander("📋 Sobre as Operações de Admin"):
        st.markdown("""
        **Resetar Questões:**
        - Remove todos os registros de `case_analytics` do aluno
        - O aluno poderá responder as questões novamente
        - Não afeta o cadastro do aluno
        
        **Limpar Chat:**
        - Remove todos os registros de `chat_interactions` do aluno
        - Libera espaço no banco de dados
        - Não afeta as questões respondidas
        
        **Logs de Admin:**
        - Todas as ações são registradas em `admin_logs`
        - Inclui timestamp, ação realizada e usuário admin
        - Útil para auditoria
        
        **Segurança:**
        - Operações individuais requerem confirmação dupla
        - Operações globais requerem checkbox + confirmação dupla
        - Não há como desfazer estas operações
        """)

