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
    get_student_weakness_analysis, format_duration, get_user_chat_interactions
)
from auth_firebase import get_all_users, get_user_by_id
from logic import get_case

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
            return
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return
    
    # Sistema de tabs redesenhado: 3 tabs principais
    tab1, tab2, tab3 = st.tabs([
        "📊 Visão Geral", 
        "👤 Análise Individual",
        "⚙️ Admin"
    ])
    
    with tab1:
        show_general_overview_tab(student_users, all_analytics)
    
    with tab2:
        show_individual_analysis_tab(student_users, all_analytics)

    with tab3:
        show_admin_tab()

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
        # Categoria com maior dificuldade
        hardest_cat = hardest_categories[0]['componente'] if hardest_categories else "N/A"
        hardest_acc = f"{hardest_categories[0]['taxa_acerto']:.1f}%" if hardest_categories else "N/A"
        st.metric(
            "⚠️ Categoria Mais Difícil",
            hardest_cat,
            delta=f"{hardest_acc}",
            delta_color="inverse",
            help="Componente com menor taxa de acerto geral"
        )
    
    with col4:
        # Nível médio
        nivel_map = {1: "Básico", 2: "Intermediário", 3: "Avançado"}
        nivel_medio = nivel_map.get(level_stats.get('nivel_medio', 1), "Básico")
        st.metric(
            "📊 Nível Médio",
            nivel_medio,
            help="Nível médio dos alunos baseado em pontuação"
        )
    
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
            
            fig_comp = px.bar(
                df_comp,
                x='taxa_acerto',
                y='componente',
                orientation='h',
                title="Taxa de Acerto por Componente (%)",
                text_auto='.1f',
                color='taxa_acerto',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            fig_comp.update_layout(
                xaxis_title="Taxa de Acerto (%)",
                yaxis_title=None,
                showlegend=False,
                height=400
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
        
        fig_hardest = px.bar(
            df_hardest,
            x='taxa_acerto',
            y='componente',
            orientation='h',
            title="Componentes que Precisam de Mais Atenção",
            text_auto='.1f',
            color='taxa_acerto',
            color_continuous_scale='Reds_r',
            range_color=[0, 100]
        )
        fig_hardest.update_layout(
            xaxis_title="Taxa de Acerto (%)",
            yaxis_title=None,
            showlegend=False,
            height=300
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
            
            fig_comp = px.bar(
                df_comp,
                x='acuracia',
                y='nome',
                orientation='h',
                text_auto='.1f',
                color='acuracia',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100]
            )
            fig_comp.update_layout(
                xaxis_title="Acurácia (%)",
                yaxis_title=None,
                showlegend=False,
                height=400
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
        
    st.markdown("---")
    
    # ===== SEÇÃO: HISTÓRICO DO TUTOR IA =====
    st.markdown("### 💬 Histórico do Tutor IA")
    chat_history = get_user_chat_interactions(student_id)
    
    if chat_history:
        st.write(f"Encontradas {len(chat_history)} interações com a IA.")
        
        # Filtro opcional por questão para facilitar a vida do professor
        all_cases_in_chat = set()
        for chat in chat_history:
            if chat.get('case_id'):
                all_cases_in_chat.add(chat['case_id'])
                
        selected_case_filter = st.selectbox(
            "Filtrar por Questão:",
            ["Todas as Questões"] + sorted(list(all_cases_in_chat)),
            key="chat_filter"
        )
        
        # Exibe os chats
        for chat in chat_history:
            if selected_case_filter != "Todas as Questões" and chat.get('case_id') != selected_case_filter:
                continue
                
            timestamp = chat.get('timestamp', '')
            if isinstance(timestamp, str) and 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp)
                timestamp_str = dt.strftime('%d/%m/%Y %H:%M')
            else:
                timestamp_str = str(timestamp)
                
            q_info = get_case(chat.get('case_id', ''))
            q_title = q_info.get('pergunta', 'Questão Desconhecida')[:60] + '...'
            
            with st.expander(f"🕒 {timestamp_str} | Questão: {q_title}"):
                st.markdown("**👤 Aluno perguntou:**")
                st.info(chat.get('user_message', 'MENSAGEM VAZIA'))
                
                st.markdown("**🤖 IA respondeu:**")
                st.success(chat.get('bot_response', 'MENSAGEM VAZIA'))
    else:
        st.info("Este aluno ainda não utilizou o Tutor IA.")

def show_admin_tab():
    """Tab de administração para gerenciar configurações da conta"""
    st.subheader("⚙️ Configurações Administrativas")
    
    # Ação: Mudar a própria senha
    st.markdown("### 🔑 Alterar Sua Senha")
    st.write("Aqui você pode alterar sua própria senha de acesso.")
    
    with st.expander("Abrir painel de alteração de senha", expanded=False):
        current_prof = st.session_state.get('user_id')
        if current_prof:
            with st.form("change_prof_password_form_new"):
                current_pw = st.text_input("Senha Atual", type="password")
                new_pw = st.text_input("Nova Senha", type="password", help="No mínimo 6 caracteres")
                confirm_pw = st.text_input("Confirmar Nova Senha", type="password")
                
                submit_pw = st.form_submit_button("Alterar Senha")
                
                if submit_pw:
                    if not current_pw or not new_pw or not confirm_pw:
                        st.error("Todos os campos de senha são obrigatórios.")
                    elif new_pw != confirm_pw:
                        st.error("A nova senha e a confirmação não coincidem.")
                    elif len(new_pw) < 6:
                        st.error("A nova senha deve ter pelo menos 6 caracteres.")
                    else:
                        from auth_firebase import change_password
                        ok, msg = change_password(current_prof, current_pw, new_pw)
                        if ok:
                            st.success(f"Senha alterada com sucesso! {msg}")
                        else:
                            st.error(f"Falha ao alterar senha: {msg}")
        else:
            st.warning("Usuário não identificado na sessão.")
