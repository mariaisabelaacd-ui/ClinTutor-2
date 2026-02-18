import streamlit as st
# Force redeploy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
from analytics import (
    get_all_users_analytics, get_global_stats,
    get_global_knowledge_component_stats, get_average_user_level,
    get_hardest_categories, get_student_complete_profile,
    get_student_weakness_analysis, format_duration,
    get_user_chat_interactions
)
from auth_firebase import get_all_users, get_user_by_id
from logic import get_case
from admin_utils import (
    reset_student_analytics, clear_student_chat_interactions,
    reset_all_students_analytics, clear_all_chat_interactions,
    log_admin_action, get_database_stats
)
from ui_helpers import icon, metric_card

def show_advanced_professor_dashboard():
    """Dashboard redesenhado para professores com foco em insights acionáveis"""
    # Garante carregamento dos ícones
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined" rel="stylesheet">', unsafe_allow_html=True)
    
    st.markdown(f"# {icon('dashboard', '#10b981', 32)} Dashboard do Professor", unsafe_allow_html=True)
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
    st.markdown(f"### {icon('push_pin', '#10b981', 24)} Métricas Principais", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(metric_card(
            "Total de Alunos",
            str(len(student_users)),
            icon_name="people",
            icon_color="#3b82f6"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(metric_card(
            "Média Geral",
            f"{global_stats.get('average_accuracy_rate', 0):.1f}%",
            icon_name="track_changes", # Fixed: target -> track_changes
            icon_color="#10b981"
        ), unsafe_allow_html=True)
    
    
    with col3:
        # Categoria com maior dificuldade - Custom display para evitar truncamento
        if hardest_categories:
            hardest_cat = hardest_categories[0]['componente']
            hardest_acc = hardest_categories[0]['taxa_acerto']
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%); 
                            padding: 1rem; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3);'>
                    <div style='color: #94a3b8; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;'>
                        {icon('warning', '#ef4444', 18)} Categoria Mais Difícil
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
        st.markdown(metric_card(
            "Questões Respondidas",
            str(global_stats.get('total_cases', 0)),
            icon_name="quiz",
            icon_color="#8b5cf6"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== VISUALIZAÇÕES =====
    
    # Linha 1: Desempenho por Componente e Distribuição por Nível
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {icon('menu_book', '#8b5cf6', 24)} Desempenho por Componente de Conhecimento", unsafe_allow_html=True)
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
            st.caption(f"{icon('lightbulb', '#eab308', 16)} Componentes no topo têm menor taxa de acerto (mais difíceis)", unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes para análise por componente")
    
    with col2:
        st.markdown(f"### {icon('bar_chart', '#3b82f6', 24)} Distribuição de Alunos por Nível", unsafe_allow_html=True)
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
    st.markdown(f"### {icon('warning', '#ef4444', 24)} Top 5 Categorias Mais Difíceis", unsafe_allow_html=True)
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
    st.markdown(f"### {icon('emoji_events', '#f59e0b', 24)} Ranking de Alunos", unsafe_allow_html=True)
    
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
            st.markdown(f"#### {icon('star', '#eab308', 20)} Top 10 Melhores Desempenhos", unsafe_allow_html=True)
            top_10 = df_ranking.head(10).copy()
            top_10['Taxa de Acerto'] = top_10['Taxa de Acerto'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(top_10, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown(f"#### {icon('priority_high', '#ef4444', 20)} Alunos que Precisam de Atenção", unsafe_allow_html=True)
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
    st.markdown(f"## {icon('person', '#3b82f6', 28)} Análise Individual de Alunos", unsafe_allow_html=True)
    
    # ===== SELEÇÃO DE ALUNO =====
    st.markdown(f"### {icon('search', '#10b981', 24)} Selecione um Aluno", unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Buscar por nome ou email", "")
    
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
        f"{icon('person', '#64748b', 18)} Aluno:",
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
    st.markdown(f"## {icon('account_circle', '#3b82f6', 32)} {selected_student['name']}", unsafe_allow_html=True)
    st.caption(f"{icon('email', '#64748b', 16)} {selected_student['email']}", unsafe_allow_html=True)
    
    # ===== SEÇÃO: DESEMPENHO GERAL =====
    st.markdown(f"### {icon('analytics', '#10b981', 24)} Desempenho Geral", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(metric_card(
            "Questões Respondidas",
            str(basic_stats['case_stats']['total_cases']),
            icon_name="quiz",
            icon_color="#8b5cf6"
        ), unsafe_allow_html=True)
    
    with col2:
        acc = basic_stats['case_stats']['accuracy_rate']
        st.markdown(metric_card(
            "Taxa de Acertos",
            f"{acc:.1f}%",
            icon_name="target",
            icon_color="#10b981"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(metric_card(
            "Tempo Médio",
            basic_stats['case_stats']['average_time_formatted'],
            icon_name="schedule",
            icon_color="#3b82f6"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(metric_card(
            "Interações Chat",
            str(basic_stats['total_chat_interactions']),
            icon_name="chat",
            icon_color="#ec4899"
        ), unsafe_allow_html=True)
    
    with col5:
        # Comparação com turma
        perf_icons = {
            'acima': icon('trending_up', '#10b981', 20),
            'abaixo': icon('trending_down', '#ef4444', 20),
            'na_media': icon('trending_flat', '#64748b', 20)
        }
        perf_icon = perf_icons.get(comparison['performance'], perf_icons['na_media'])
        
        st.markdown(metric_card(
            "vs Turma",
            f"{perf_icon} {comparison['performance'].title()}",
            icon_name="compare_arrows",
            icon_color="#6366f1",
            subtitle=f"{comparison['diferenca']:.1f}%"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== SEÇÃO: ANÁLISE DE DIFICULDADES =====
    st.markdown(f"### {icon('warning', '#ef4444', 24)} Análise de Dificuldades", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {icon('error', '#ef4444', 20)} Componente Mais Difícil", unsafe_allow_html=True)
        worst_comp = weakness.get('componente_mais_dificil')
        if worst_comp:
            st.error(f"**{worst_comp['nome']}**")
            st.write(f"- Taxa de acerto: **{worst_comp['acuracia']:.1f}%**")
            st.write(f"- Questões: {worst_comp['acertos']}/{worst_comp['total']}")
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.markdown(f"#### {icon('trending_up', '#3b82f6', 20)} Nível Mais Difícil", unsafe_allow_html=True)
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
        st.markdown(f"#### {icon('error_outline', '#ef4444', 20)} Componentes Problemáticos (Taxa < 50%)", unsafe_allow_html=True)
        for comp in problematic[:5]:  # Top 5
            st.warning(f"**{comp['nome']}**: {comp['acuracia']:.1f}% ({comp['acertos']}/{comp['total']})")
    
    # Padrões de erro
    patterns = weakness.get('padroes_erro', [])
    if patterns:
        st.markdown(f"#### {icon('search', '#6366f1', 20)} Padrões Identificados", unsafe_allow_html=True)
        for pattern in patterns:
            st.info(f"**{pattern['padrao']}**: {pattern['descricao']}")
    
    st.markdown("---")
    
    # ===== SEÇÃO: DESEMPENHO POR CATEGORIA =====
    st.markdown(f"### {icon('menu_book', '#8b5cf6', 24)} Desempenho por Categoria", unsafe_allow_html=True)
    
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
    with st.expander(f"{icon('table_chart', '#64748b', 18)} Tabela Detalhada por Componente"):
        if advanced_stats['componentes']:
            df_comp_table = pd.DataFrame(advanced_stats['componentes'])
            df_comp_table.columns = ['Componente', 'Acurácia (%)', 'Total', 'Acertos']
            df_comp_table = df_comp_table.sort_values('Acurácia (%)')
            st.dataframe(df_comp_table, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ===== SEÇÃO: HISTÓRICO DE RESPOSTAS =====
    st.markdown(f"### {icon('history', '#10b981', 24)} Histórico de Respostas", unsafe_allow_html=True)
    
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
        
        
        # Prepara histórico com detalhes completos
        filtered_entries = []
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
            
            filtered_entries.append({
                'entry': entry,
                'q_info': q_info,
                'result': result,
                'timestamp': timestamp,
                'is_correct': is_correct,
                'comps': comps,
                'diff': diff
            })
        
        
        if filtered_entries:
            # Ordena por data (mais recente primeiro)
            filtered_entries.sort(key=lambda x: x['timestamp'], reverse=True)
            
            st.markdown(f"**{len(filtered_entries)} questões encontradas**")
            st.markdown("")
            
            # Agrupa por data
            grouped_entries = {}
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            for item in filtered_entries:
                item_date = item['timestamp'].date()
                if item_date == today:
                    key = "📅 Hoje"
                elif item_date == yesterday:
                    key = "📅 Ontem"
                else:
                    key = f"📅 {item_date.strftime('%d/%m/%Y')}"
                
                if key not in grouped_entries:
                    grouped_entries[key] = []
                grouped_entries[key].append(item)
            
            # Exibe Timeline
            for date_label, items in grouped_entries.items():
                st.markdown(f"### {date_label}")
                
                for item in items:
                    entry = item['entry']
                    q_info = item['q_info']
                    result = item['result']
                    timestamp = item['timestamp']
                    is_correct = item['is_correct']
                    comps = item['comps']
                    diff = item['diff']
                    
                    # Layout de Timeline
                    col_time, col_content = st.columns([0.15, 0.85])
                    
                    with col_time:
                        st.markdown(f"""
                            <div style="text-align: right; padding-top: 10px; color: #64748b; font-size: 0.85rem;">
                                {timestamp.strftime('%H:%M')}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_content:
                        # Título do expander mais limpo
                        status_icon = "🟢" if is_correct else "🔴"
                        question_preview = q_info.get('pergunta', 'N/A')[:60] + "..."
                        
                        # Usando container para simular timeline visual
                        with st.container():
                            st.markdown(f"""
                                <div style="border-left: 2px solid #e2e8f0; margin-left: -10px; padding-left: 20px; padding-bottom: 20px;">
                                    <div style="font-weight: 500; margin-bottom: 5px; color: #334155;">
                                        {status_icon} {question_preview}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Detalhes (expansível)
                            with st.expander("Ver detalhes", expanded=False):
                                # Busca interações do chat para esta questão
                                # Tenta buscar por case_id primeiro
                                chat_interactions = get_user_chat_interactions(student_id, entry.get('case_id'))
                                
                                # Fallback simples se não achar (opcional, pode ser complexo implementar aqui agora)
                                
                                # Exibe card detalhado
                                from ui_helpers import answer_detail_card
                                
                                detail_html = answer_detail_card(
                                    question_text=q_info.get('pergunta', 'N/A'),
                                    student_answer=result.get('user_answer', None), # Passa None para ativar fallback
                                    expected_answer=q_info.get('resposta_esperada', None),
                                    feedback=result.get('feedback', None),
                                    classification=result.get('classification', 'INCORRETA'),
                                    components=comps,
                                    difficulty=diff,
                                    time_spent=format_duration(entry.get('duration_seconds', 0)),
                                    points=result.get('points_gained', 0)
                                )
                                
                                st.markdown(detail_html, unsafe_allow_html=True)
                                
                                # Mostra interações do chat se houver
                                if chat_interactions:
                                    st.markdown(f"#### {icon('chat', '#ec4899', 20)} Interações do Chat ({len(chat_interactions)})", unsafe_allow_html=True)
                                    
                                    for chat_idx, interaction in enumerate(chat_interactions):
                                        chat_time = interaction.get('timestamp', '')
                                        if isinstance(chat_time, str):
                                            try:
                                                chat_time = datetime.fromisoformat(chat_time).strftime('%H:%M:%S')
                                            except:
                                                chat_time = 'N/A'
                                        
                                        user_msg = interaction.get('user_message', '')
                                        bot_msg = interaction.get('bot_response', '')
                                        
                                        st.markdown(f"""
                                            <div style='background: rgba(236, 72, 153, 0.05); padding: 0.75rem; 
                                                        border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #ec4899;'>
                                                <div style='color: #64748b; font-size: 0.75rem; margin-bottom: 0.25rem;'>
                                                    {icon('schedule', '#64748b', 14)} {chat_time}
                                                </div>
                                                <div style='color: #1e293b; font-size: 0.875rem; margin-bottom: 0.5rem;'>
                                                    <strong>{icon('person', '#3b82f6', 16)} Aluno:</strong> {user_msg}
                                                </div>
                                                <div style='color: #475569; font-size: 0.875rem;'>
                                                    <strong>{icon('smart_toy', '#ec4899', 16)} Tutor:</strong> {bot_msg}
                                                </div>
                                            </div>
                                        """, unsafe_allow_html=True)

            
            # Botão de download (tabela resumida)
            st.markdown("---")
            history_summary = []
            for item in filtered_entries:
                history_summary.append({
                    'Data': item['timestamp'].strftime('%d/%m/%Y %H:%M'),
                    'Questão': item['q_info'].get('pergunta', 'N/A')[:50] + '...',
                    'Componente': ', '.join(item['comps']),
                    'Dificuldade': item['diff'].title(),
                    'Status': '✅ Correto' if item['is_correct'] else '❌ Incorreto',
                    'Tempo': format_duration(item['entry'].get('duration_seconds', 0)),
                    'Pontos': item['result'].get('points_gained', 0)
                })
            
            df_history = pd.DataFrame(history_summary)
            csv = df_history.to_csv(index=False)
            st.download_button(
                label=f"{icon('download', '#10b981', 18)} Baixar Histórico (CSV)",
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
    st.markdown(f"## {icon('admin_panel_settings', '#eab308', 28)} Painel de Administração", unsafe_allow_html=True)
    
    st.warning("⚠️ **ATENÇÃO**: Esta área contém operações que podem deletar dados permanentemente!")
    
    st.markdown("---")
    
    # ===== ESTATÍSTICAS DO BANCO =====
    st.markdown(f"### {icon('storage', '#3b82f6', 24)} Estatísticas do Banco de Dados", unsafe_allow_html=True)
    
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
    st.markdown(f"### {icon('person', '#3b82f6', 24)} Gerenciar Aluno Individual", unsafe_allow_html=True)
    
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
            st.markdown(f"#### {icon('delete', '#ef4444', 20)} Resetar Questões", unsafe_allow_html=True)
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
            st.markdown(f"#### {icon('chat_bubble', '#ec4899', 20)} Limpar Chat", unsafe_allow_html=True)
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
    st.markdown(f"### {icon('public', '#f59e0b', 24)} Gerenciar Todos os Alunos", unsafe_allow_html=True)
    st.error("⚠️ **PERIGO**: Estas ações afetam TODOS os alunos e são IRREVERSÍVEIS!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {icon('delete_forever', '#ef4444', 20)} Resetar Todas as Questões", unsafe_allow_html=True)
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
        st.markdown(f"#### {icon('forum', '#ec4899', 20)} Limpar Todos os Chats", unsafe_allow_html=True)
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

