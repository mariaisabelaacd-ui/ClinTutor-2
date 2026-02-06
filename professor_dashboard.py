import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import datetime as dt
from typing import Dict, List, Any
from analytics import (
    get_all_users_analytics, get_user_detailed_stats, get_global_stats,
    get_user_chat_interactions, format_duration, get_case_resolution_times,
    get_resolution_time_stats
)
from auth_firebase import get_all_users, get_user_by_id
from logic import get_case

def show_advanced_professor_dashboard():
    """Dashboard avançado para professores com analytics detalhados"""
    st.title("📊 Dashboard Avançado - Analytics dos Alunos")
    st.markdown("---")
    
    try:
        # Carrega dados com tratamento de erro
        all_users = get_all_users()
        all_analytics = get_all_users_analytics()
        global_stats = get_global_stats()
        
        # Filtra apenas alunos para exibição
        student_users = [user for user in all_users if user.get('user_type') == 'aluno']
        
        if not student_users:
            st.warning("Nenhum aluno encontrado.")
            return
            
        if not all_analytics:
            st.warning("Nenhum dado de analytics encontrado.")
            return
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return
    
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Visão Geral", 
        "👥 Por Aluno", 
        "⏱️ Tempos de Resolução",
        "💬 Interações Chat", 
        "📊 Relatórios"
    ])
    
    with tab1:
        show_overview_tab(student_users, all_analytics, period)
    
    with tab2:
        show_student_details_tab(student_users, all_analytics, period)
    
    with tab3:
        show_resolution_times_tab(student_users, all_analytics, period)
    
    with tab4:
        show_chat_interactions_tab(student_users, all_analytics, period)
    
    with tab5:
        show_reports_tab(student_users, all_analytics, period)

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

def filter_data_by_period(data_list: List[Dict], period: str) -> List[Dict]:
    """Filtra lista de dados baseada no período selecionado"""
    if not data_list: return []
    
    now = datetime.now()
    days_map = {
        "Últimos 7 dias": 7,
        "Últimos 30 dias": 30,
        "Últimos 90 dias": 90
    }
    
    if period == "Todo o período":
        return data_list
        
    days = days_map.get(period, 7)
    cutoff = now - timedelta(days=days)
    
    filtered = []
    for item in data_list:
        ts = item.get('timestamp')
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except: continue
        
        # Garante timezone correction
        if isinstance(ts, datetime): 
             if ts.tzinfo is not None: ts = ts.replace(tzinfo=None)
             if now.tzinfo is not None: now = now.replace(tzinfo=None)
             
             if ts >= cutoff:
                 filtered.append(item)
                 
    return filtered

def show_overview_tab(student_users: List[Dict], all_analytics: Dict, period: str):
    """Tab de visão geral com gráficos (Dados Filtrados)"""
    st.subheader(f"📈 Visão Geral ({period})")
    
    # Prepara dados para gráficos
    users_data = []
    for user in student_users:
        uid = user['id']
        u_data = all_analytics.get(uid, {})
        
        # Filtra dados brutos
        raw_cases = u_data.get('case_analytics', [])
        raw_chat = u_data.get('chat_interactions', [])
        
        filtered_cases = filter_data_by_period(raw_cases, period)
        filtered_chat = filter_data_by_period(raw_chat, period)
        
        # Recalcula estatísticas com dados filtrados
        total_cases = len(filtered_cases)
        correct_cases = sum(1 for c in filtered_cases 
                           if c.get("case_result", {}).get("breakdown", {}).get("diagnóstico", 0) >= 10)
        acc_rate = (correct_cases / total_cases * 100) if total_cases > 0 else 0.0
        
        durations = [c.get('duration_seconds', 0) for c in filtered_cases if c.get('duration_seconds', 0) > 0]
        avg_time = sum(durations) / len(durations) if durations else 0
        
        # Pega última atividade do período
        last_act = "N/A"
        all_acts = filtered_cases + filtered_chat
        if all_acts:
            # Ordena seguro
            all_acts.sort(key=lambda x: datetime.fromisoformat(x['timestamp']) if isinstance(x.get('timestamp'), str) else datetime.min, reverse=True)
            last_ts = all_acts[0].get('timestamp')
            if isinstance(last_ts, str): last_ts = datetime.fromisoformat(last_ts)
            last_act = last_ts

        users_data.append({
                'Nome': user['name'],
                'Email': user['email'],
                'Casos Resolvidos': total_cases,
                'Taxa de Acertos': acc_rate,
                'Tempo Médio': avg_time,
                'Interações Chat': len(filtered_chat),
                'Última Atividade': last_act
            })
    
    if not users_data:
        st.info("Nenhum dado de aluno encontrado.")
        return
    
    df = pd.DataFrame(users_data)
    
    # KPIs do Período
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_active_period = sum(1 for u in users_data if u['Casos Resolvidos'] > 0 or u['Interações Chat'] > 0)
    total_cases_period = sum(u['Casos Resolvidos'] for u in users_data)
    avg_score_period = df[df['Casos Resolvidos'] > 0]['Taxa de Acertos'].mean() if not df.empty else 0
    total_chat_period = sum(u['Interações Chat'] for u in users_data)
    
    with kpi1: st.metric("Alunos Ativos", total_active_period, help="Alunos com alguma atividade neste período")
    with kpi2: st.metric("Casos Resolvidos", total_cases_period)
    with kpi3: st.metric("Média Geral de Acertos", f"{avg_score_period:.1f}%")
    with kpi4: st.metric("Interações Totais", total_chat_period)
    
    st.markdown("---")

    # Gráfico de Dispersão: Tempo x Desempenho (Mais visual que barra simples)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Desempenho vs Tempo")
        if not df[df['Casos Resolvidos'] > 0].empty:
            fig_scatter = px.scatter(
                df[df['Casos Resolvidos'] > 0],
                x='Tempo Médio',
                y='Taxa de Acertos',
                size='Casos Resolvidos',
                color='Taxa de Acertos',
                hover_name='Nome',
                color_continuous_scale='RdYlGn',
                title="Relação: Tempo Gasto x Taxa de Acerto (Tamanho = Volume de Casos)",
                labels={'Tempo Médio': 'Tempo Médio (s)', 'Taxa de Acertos': 'Acerto (%)'}
            )
            # Adiciona linhas médias
            fig_scatter.add_hline(y=avg_score_period, line_dash="dash", line_color="gray", annotation_text="Média Acertos")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Sem dados de atividade para cruzar.")

    with col2:
        st.subheader("📊 Distribuição de Atividade")
        # Gráfico de Barras melhorado (Top Alunos por volume)
        fig_vol = px.bar(
            df.sort_values('Casos Resolvidos', ascending=True).tail(10), # Top 10
            x='Casos Resolvidos',
            y='Nome',
            orientation='h',
            title="Top Alunos Mais Ativos (Casos)",
            color='Casos Resolvidos',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_vol, use_container_width=True)
    
    # Tabela resumo melhorada
    st.subheader("📋 Detalhamento dos Alunos")
    
    # Ajuste de Fuso Horário (-3h) e formatação
    display_df = df.copy()
    
    def format_brt(x):
        if hasattr(x, 'replace') and isinstance(x, datetime):
            # Tira 3 horas simples
            return (x - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')
        return 'N/A'

    display_df['Tempo Médio'] = display_df['Tempo Médio'].apply(lambda x: format_duration(x))
    display_df['Última Atividade'] = display_df['Última Atividade'].apply(format_brt)
    
    # Remove coluna Email para economizar espaço
    display_df = display_df.drop('Email', axis=1)
    
    # Configuração visual das colunas
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Taxa de Acertos": st.column_config.ProgressColumn(
                "Taxa de Acertos",
                help="Percentual de diagnósticos corretos",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Casos Resolvidos": st.column_config.NumberColumn(
                "Casos",
                help="Total de casos finalizados"
            ),
            "Interações Chat": st.column_config.NumberColumn(
                "Chat",
                format="%d 💬"
            )
        }
    )

def show_student_details_tab(student_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com detalhes por aluno"""
    st.subheader("👥 Detalhes por Aluno")
    
    # Usa apenas alunos (já filtrados)
    students = student_users
    
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
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
    
    with col5:
        st.metric(
            "📊 Score Total",
            student_stats['case_stats'].get('total_score', 0)
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
            # Função auxiliar segura para obter timestamp
            def get_safe_timestamp(x):
                ts = x.get('timestamp', datetime.min)
                if isinstance(ts, str):
                    try:
                        return datetime.fromisoformat(ts)
                    except:
                        return datetime.min
                return ts if isinstance(ts, datetime) else datetime.min

            # Ordena por data
            case_analytics.sort(key=get_safe_timestamp)
            
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
                'Data': (datetime.fromisoformat(case_data.get('timestamp', datetime.now().isoformat())) if isinstance(case_data.get('timestamp'), str) else case_data.get('timestamp', datetime.now())).strftime('%d/%m/%Y %H:%M')
            })
        
        # Ordena por data (mais recente primeiro)
        case_history.sort(key=lambda x: x['Data'], reverse=True)
        
        df_history = pd.DataFrame(case_history)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum caso resolvido ainda.")

def show_resolution_times_tab(student_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com tempos de resolução de casos"""
    st.subheader("⏱️ Tempos de Resolução de Casos")
    
    if not student_users:
        st.info("Nenhum aluno encontrado.")
        return
    
    # Seletor de aluno
    student_names = [f"{user['name']} ({user['email']})" for user in student_users]
    selected_student_idx = st.selectbox(
        "👤 Selecione um aluno:",
        range(len(student_names)),
        format_func=lambda x: student_names[x]
    )
    
    if selected_student_idx is not None:
        selected_student = student_users[selected_student_idx]
        student_id = selected_student['id']
        
        # Obtém dados de tempo de resolução
        resolution_times = get_case_resolution_times(student_id)
        time_stats = get_resolution_time_stats(student_id)
        
        if not resolution_times:
            st.info(f"Nenhum caso resolvido por {selected_student['name']} ainda.")
            return
        
        # Estatísticas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total de Casos", time_stats['total_cases'])
        
        with col2:
            st.metric("⏱️ Tempo Médio", time_stats['average_time_formatted'])
        
        with col3:
            st.metric("⚡ Mais Rápido", time_stats['fastest_time_formatted'])
        
        with col4:
            st.metric("🐌 Mais Lento", time_stats['slowest_time_formatted'])
        
        st.markdown("---")
        
        # Gráfico de distribuição de tempos
        st.subheader("📈 Distribuição de Tempos")
        
        # Prepara dados para o gráfico
        times_data = []
        for case_data in resolution_times:
            case_info = get_case(case_data['case_id'])
            times_data.append({
                'Caso': case_info.get('titulo', f"Caso {case_data['case_id']}"),
                'Tempo (segundos)': case_data['duration_seconds'],
                'Tempo Formatado': case_data['duration_formatted'],
                'Resultado': '✅ Correto' if case_data['is_correct'] else '❌ Incorreto',
                'Data': case_data['timestamp'].strftime('%d/%m/%Y %H:%M')
            })
        
        if times_data:
            df_times = pd.DataFrame(times_data)
            
            # Gráfico de barras
            fig = px.bar(
                df_times, 
                x='Caso', 
                y='Tempo (segundos)',
                color='Resultado',
                title="Tempo de Resolução por Caso",
                color_discrete_map={'✅ Correto': '#00ff00', '❌ Incorreto': '#ff0000'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("📋 Detalhes dos Casos")
            st.dataframe(
                df_times[['Caso', 'Tempo Formatado', 'Resultado', 'Data']],
                use_container_width=True,
                hide_index=True
            )
        
        # Comparação entre casos corretos e incorretos
        if time_stats['correct_cases_time'] and time_stats['incorrect_cases_time']:
            st.subheader("🔍 Análise Comparativa")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "✅ Tempo Médio (Corretos)", 
                    format_duration(time_stats['correct_avg_time'])
                )
            
            with col2:
                st.metric(
                    "❌ Tempo Médio (Incorretos)", 
                    format_duration(time_stats['incorrect_avg_time'])
                )

def show_chat_interactions_tab(student_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com interações do chat"""
    st.subheader("💬 Interações com o Chatbot")
    
    # Usa apenas alunos (já filtrados)
    students = student_users
    
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
        
        timestamp = interaction.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        timestamp_str = timestamp.strftime('%d/%m/%Y %H:%M')
        with st.expander(f"💬 {case_info.get('titulo', 'Caso')} - {timestamp_str}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👤 Aluno:**")
                st.write(interaction.get('user_message', 'N/A'))
            
            with col2:
                st.markdown("**🤖 IA Tutora:**")
                st.write(interaction.get('bot_response', 'N/A'))
            
            if interaction.get('response_time_seconds'):
                st.caption(f"⏱️ Tempo de resposta: {format_duration(interaction['response_time_seconds'])}")

def show_reports_tab(student_users: List[Dict], all_analytics: Dict, period: str):
    """Tab com relatórios"""
    st.subheader("📊 Relatórios")
    
    # Botão para gerar relatório
    if st.button("📄 Gerar Relatório Completo", type="primary"):
        generate_complete_report(student_users, all_analytics)
    
    st.markdown("---")
    
    # Relatório de performance
    st.subheader("📈 Relatório de Performance")
    
    # Prepara dados para relatório
    performance_data = []
    for user in student_users:
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

def generate_complete_report(student_users: List[Dict], all_analytics: Dict):
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
        
        for user in student_users:
            user_stats = get_user_detailed_stats(user['id'])
            st.markdown(f"""
                **{user['name']}**
                - Casos resolvidos: {user_stats['case_stats']['total_cases']}
                - Taxa de acertos: {user_stats['case_stats']['accuracy_rate']:.1f}%
                - Tempo médio: {user_stats['case_stats']['average_time_formatted']}
                - Interações chat: {user_stats['total_chat_interactions']}
                """)
