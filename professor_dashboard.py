import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
from analytics import (
    get_all_users_analytics, get_user_detailed_stats, get_global_stats,
    get_user_chat_interactions, format_duration
)
from auth_firebase import get_all_users, get_user_by_id
from logic import get_case

def show_advanced_professor_dashboard():
    """Dashboard avançado para professores com analytics detalhados"""
    st.title("📊 Dashboard Avançado - Analytics dos Alunos")
    st.markdown("---")
    
    # Carrega dados
    all_users = get_all_users()
    all_analytics = get_all_users_analytics()
    global_stats = get_global_stats()
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por período
        period = st.selectbox(
            "📅 Período",
            ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo o período"],
            key="analytics_period"
        )
    
    with col2:
        # Filtro por tipo de usuário
        user_type_filter = st.selectbox(
            "👥 Tipo de Usuário",
            ["Todos", "Alunos", "Professores"],
            key="user_type_filter"
        )
    
    with col3:
        # Filtro por atividade
        activity_filter = st.selectbox(
            "⚡ Atividade",
            ["Todos", "Ativos hoje", "Ativos esta semana", "Inativos"],
            key="activity_filter"
        )
    
    st.markdown("---")
    
    # Estatísticas globais
    show_global_statistics(global_stats)
    
    st.markdown("---")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Visão Geral", 
        "👥 Por Aluno", 
        "💬 Interações Chat", 
        "📊 Relatórios"
    ])
    
    with tab1:
        show_overview_tab(all_users, all_analytics, period)
    
    with tab2:
        show_student_details_tab(all_users, all_analytics, period)
    
    with tab3:
        show_chat_interactions_tab(all_users, all_analytics, period)
    
    with tab4:
        show_reports_tab(all_users, all_analytics, period)

def show_global_statistics(global_stats: Dict[str, Any]):
    """Mostra estatísticas globais do sistema"""
    st.subheader("🌍 Estatísticas Globais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "👥 Total de Usuários",
            global_stats.get('total_users', 0)
        )
    
    with col2:
        st.metric(
            "📚 Total de Casos",
            global_stats.get('total_cases', 0)
        )
    
    with col3:
        st.metric(
            "💬 Interações Chat",
            global_stats.get('total_chat_interactions', 0)
        )
    
    with col4:
        st.metric(
            "🎯 Taxa Média de Acertos",
            f"{global_stats.get('average_accuracy_rate', 0):.1f}%"
        )
    
    with col5:
        st.metric(
            "⚡ Usuários Ativos Hoje",
            global_stats.get('active_users_today', 0)
        )

def show_overview_tab(all_users: List[Dict], all_analytics: Dict, period: str):
    """Tab de visão geral com gráficos"""
    st.subheader("📈 Visão Geral")
    
    # Prepara dados para gráficos
    users_data = []
    for user in all_users:
        if user.get('user_type') == 'aluno':  # Foca em alunos
            user_stats = get_user_detailed_stats(user['id'])
            users_data.append({
                'Nome': user['name'],
                'Email': user['email'],
                'Casos Resolvidos': user_stats['case_stats']['total_cases'],
                'Taxa de Acertos': user_stats['case_stats']['accuracy_rate'],
                'Tempo Médio': user_stats['case_stats']['average_time'],
                'Interações Chat': user_stats['total_chat_interactions'],
                'Última Atividade': user_stats['last_activity']
            })
    
    if not users_data:
        st.info("Nenhum dado de aluno encontrado.")
        return
    
    df = pd.DataFrame(users_data)
    
    # Gráfico de taxa de acertos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Taxa de Acertos por Aluno")
        fig_accuracy = px.bar(
            df, 
            x='Nome', 
            y='Taxa de Acertos',
            title="Taxa de Acertos (%)",
            color='Taxa de Acertos',
            color_continuous_scale='RdYlGn'
        )
        fig_accuracy.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_accuracy, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ Tempo Médio por Caso")
        fig_time = px.bar(
            df, 
            x='Nome', 
            y='Tempo Médio',
            title="Tempo Médio (segundos)",
            color='Tempo Médio',
            color_continuous_scale='Blues'
        )
        fig_time.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_time, use_container_width=True)
    
    # Gráfico de atividade
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Casos Resolvidos")
        fig_cases = px.pie(
            df, 
            values='Casos Resolvidos', 
            names='Nome',
            title="Distribuição de Casos Resolvidos"
        )
        st.plotly_chart(fig_cases, use_container_width=True)
    
    with col2:
        st.subheader("💬 Interações com Chat")
        fig_chat = px.scatter(
            df,
            x='Casos Resolvidos',
            y='Interações Chat',
            size='Taxa de Acertos',
            hover_name='Nome',
            title="Casos vs Interações Chat (tamanho = taxa de acertos)"
        )
        st.plotly_chart(fig_chat, use_container_width=True)
    
    # Tabela resumo
    st.subheader("📋 Resumo dos Alunos")
    
    # Formata dados para exibição
    display_df = df.copy()
    display_df['Tempo Médio'] = display_df['Tempo Médio'].apply(lambda x: format_duration(x))
    display_df['Taxa de Acertos'] = display_df['Taxa de Acertos'].apply(lambda x: f"{x:.1f}%")
    display_df['Última Atividade'] = display_df['Última Atividade'].apply(
        lambda x: x.strftime('%d/%m/%Y %H:%M') if isinstance(x, datetime) else 'N/A'
    )
    
    # Remove coluna Email para economizar espaço
    display_df = display_df.drop('Email', axis=1)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

def show_student_details_tab(all_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com detalhes por aluno"""
    st.subheader("👥 Detalhes por Aluno")
    
    # Filtra apenas alunos
    students = [user for user in all_users if user.get('user_type') == 'aluno']
    
    if not students:
        st.info("Nenhum aluno encontrado.")
        return
    
    # Seletor de aluno
    student_names = [f"{student['name']} ({student['email']})" for student in students]
    selected_student_idx = st.selectbox(
        "Selecione um aluno:",
        range(len(student_names)),
        format_func=lambda x: student_names[x]
    )
    
    selected_student = students[selected_student_idx]
    student_stats = get_user_detailed_stats(selected_student['id'])
    
    st.markdown(f"### 👤 {selected_student['name']}")
    
    # Métricas do aluno
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📚 Casos Resolvidos",
            student_stats['case_stats']['total_cases']
        )
    
    with col2:
        st.metric(
            "🎯 Taxa de Acertos",
            f"{student_stats['case_stats']['accuracy_rate']:.1f}%"
        )
    
    with col3:
        st.metric(
            "⏱️ Tempo Médio",
            student_stats['case_stats']['average_time_formatted']
        )
    
    with col4:
        st.metric(
            "💬 Interações Chat",
            student_stats['total_chat_interactions']
        )
    
    # Gráficos específicos do aluno
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de casos por dia
        if student_stats['cases_by_day']:
            st.subheader("📅 Atividade por Dia (Últimos 7 dias)")
            days = list(student_stats['cases_by_day'].keys())
            cases = list(student_stats['cases_by_day'].values())
            
            fig_daily = px.bar(
                x=days,
                y=cases,
                title="Casos Resolvidos por Dia",
                labels={'x': 'Data', 'y': 'Casos'}
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("Nenhuma atividade recente.")
    
    with col2:
        # Gráfico de progresso
        st.subheader("📈 Progresso do Aluno")
        
        # Simula dados de progresso (casos resolvidos ao longo do tempo)
        case_analytics = all_analytics.get(selected_student['id'], {}).get('case_analytics', [])
        if case_analytics:
            # Ordena por data
            case_analytics.sort(key=lambda x: x.get('timestamp', datetime.min))
            
            # Calcula acertos acumulados
            cumulative_correct = 0
            cumulative_total = 0
            progress_data = []
            
            for case_data in case_analytics:
                cumulative_total += 1
                if case_data.get('case_result', {}).get('breakdown', {}).get('diagnóstico', 0) >= 10:
                    cumulative_correct += 1
                
                accuracy = (cumulative_correct / cumulative_total * 100) if cumulative_total > 0 else 0
                progress_data.append({
                    'Caso': cumulative_total,
                    'Taxa de Acertos': accuracy
                })
            
            if progress_data:
                df_progress = pd.DataFrame(progress_data)
                fig_progress = px.line(
                    df_progress,
                    x='Caso',
                    y='Taxa de Acertos',
                    title="Evolução da Taxa de Acertos",
                    markers=True
                )
                st.plotly_chart(fig_progress, use_container_width=True)
        else:
            st.info("Nenhum caso resolvido ainda.")
    
    # Histórico de casos
    st.subheader("📋 Histórico de Casos")
    
    case_analytics = all_analytics.get(selected_student['id'], {}).get('case_analytics', [])
    if case_analytics:
        # Prepara dados para tabela
        case_history = []
        for case_data in case_analytics:
            case_id = case_data.get('case_id')
            case_info = get_case(case_id)
            
            case_result = case_data.get('case_result', {})
            breakdown = case_result.get('breakdown', {})
            is_correct = breakdown.get('diagnóstico', 0) >= 10
            
            case_history.append({
                'Caso': case_info.get('titulo', 'N/A'),
                'Nível': case_info.get('nivel', 'N/A'),
                'Tempo': format_duration(case_data.get('duration_seconds', 0)),
                'Acertou': '✅' if is_correct else '❌',
                'Pontos': case_result.get('points_gained', 0),
                'Data': case_data.get('timestamp', datetime.now()).strftime('%d/%m/%Y %H:%M')
            })
        
        # Ordena por data (mais recente primeiro)
        case_history.sort(key=lambda x: x['Data'], reverse=True)
        
        df_history = pd.DataFrame(case_history)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum caso resolvido ainda.")

def show_chat_interactions_tab(all_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com interações do chat"""
    st.subheader("💬 Interações com o Chatbot")
    
    # Filtra apenas alunos
    students = [user for user in all_users if user.get('user_type') == 'aluno']
    
    if not students:
        st.info("Nenhum aluno encontrado.")
        return
    
    # Seletor de aluno
    student_names = [f"{student['name']} ({student['email']})" for student in students]
    selected_student_idx = st.selectbox(
        "Selecione um aluno:",
        range(len(student_names)),
        format_func=lambda x: student_names[x],
        key="chat_student_selector"
    )
    
    selected_student = students[selected_student_idx]
    
    # Busca interações do chat
    chat_interactions = get_user_chat_interactions(selected_student['id'])
    
    if not chat_interactions:
        st.info("Nenhuma interação com o chatbot encontrada.")
        return
    
    # Estatísticas do chat
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💬 Total de Interações",
            len(chat_interactions)
        )
    
    with col2:
        avg_response_time = sum(i.get('response_time_seconds', 0) for i in chat_interactions) / len(chat_interactions)
        st.metric(
            "⏱️ Tempo Médio de Resposta",
            format_duration(avg_response_time)
        )
    
    with col3:
        # Conta interações por caso
        cases_with_chat = len(set(i.get('case_id') for i in chat_interactions))
        st.metric(
            "📚 Casos com Chat",
            cases_with_chat
        )
    
    # Lista de interações
    st.subheader("📝 Histórico de Conversas")
    
    for interaction in chat_interactions[:20]:  # Mostra apenas as últimas 20
        case_id = interaction.get('case_id')
        case_info = get_case(case_id)
        
        with st.expander(f"💬 {case_info.get('titulo', 'Caso')} - {interaction.get('timestamp', datetime.now()).strftime('%d/%m/%Y %H:%M')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👤 Aluno:**")
                st.write(interaction.get('user_message', 'N/A'))
            
            with col2:
                st.markdown("**🤖 IA Tutora:**")
                st.write(interaction.get('bot_response', 'N/A'))
            
            if interaction.get('response_time_seconds'):
                st.caption(f"⏱️ Tempo de resposta: {format_duration(interaction['response_time_seconds'])}")

def show_reports_tab(all_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com relatórios"""
    st.subheader("📊 Relatórios")
    
    # Botão para gerar relatório
    if st.button("📄 Gerar Relatório Completo", type="primary"):
        generate_complete_report(all_users, all_analytics)
    
    st.markdown("---")
    
    # Relatório de performance
    st.subheader("📈 Relatório de Performance")
    
    # Prepara dados para relatório
    performance_data = []
    for user in all_users:
        if user.get('user_type') == 'aluno':
            user_stats = get_user_detailed_stats(user['id'])
            performance_data.append({
                'Aluno': user['name'],
                'Email': user['email'],
                'Casos Resolvidos': user_stats['case_stats']['total_cases'],
                'Taxa de Acertos': f"{user_stats['case_stats']['accuracy_rate']:.1f}%",
                'Tempo Médio': user_stats['case_stats']['average_time_formatted'],
                'Interações Chat': user_stats['total_chat_interactions'],
                'Última Atividade': user_stats['last_activity'].strftime('%d/%m/%Y') if isinstance(user_stats['last_activity'], datetime) else 'N/A'
            })
    
    if performance_data:
        df_performance = pd.DataFrame(performance_data)
        
        # Ordena por taxa de acertos
        df_performance = df_performance.sort_values('Taxa de Acertos', ascending=False)
        
        st.dataframe(df_performance, use_container_width=True, hide_index=True)
        
        # Botão para download
        csv = df_performance.to_csv(index=False)
        st.download_button(
            label="📥 Baixar Relatório CSV",
            data=csv,
            file_name=f"relatorio_performance_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum dado de performance encontrado.")

def generate_complete_report(all_users: List[Dict], all_analytics: Dict):
    """Gera relatório completo"""
    st.success("📄 Relatório gerado com sucesso!")
    
    # Aqui você pode implementar a geração de um relatório mais detalhado
    # Por exemplo, PDF, Excel, etc.
    
    with st.expander("📋 Relatório Completo", expanded=True):
        st.markdown("### 📊 Resumo Executivo")
        
        global_stats = get_global_stats()
        
        st.markdown(f"""
        - **Total de Usuários**: {global_stats.get('total_users', 0)}
        - **Total de Casos Resolvidos**: {global_stats.get('total_cases', 0)}
        - **Total de Interações Chat**: {global_stats.get('total_chat_interactions', 0)}
        - **Taxa Média de Acertos**: {global_stats.get('average_accuracy_rate', 0):.1f}%
        - **Usuários Ativos Hoje**: {global_stats.get('active_users_today', 0)}
        """)
        
        st.markdown("### 👥 Performance por Aluno")
        
        for user in all_users:
            if user.get('user_type') == 'aluno':
                user_stats = get_user_detailed_stats(user['id'])
                st.markdown(f"""
                **{user['name']}**
                - Casos resolvidos: {user_stats['case_stats']['total_cases']}
                - Taxa de acertos: {user_stats['case_stats']['accuracy_rate']:.1f}%
                - Tempo médio: {user_stats['case_stats']['average_time_formatted']}
                - Interações chat: {user_stats['total_chat_interactions']}
                """)
