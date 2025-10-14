#!/usr/bin/env python3
"""
Interface de Administração do BioTutor
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from auth_firebase import get_all_users_firebase, delete_user_firebase, create_default_admin
from analytics import get_all_users_analytics, get_global_stats
from firebase_config import is_firebase_connected, get_firestore_db

def show_admin_dashboard():
    """Dashboard de administração"""
    st.title("Painel de Administração - BioTutor")
    st.markdown("---")
    
    # Status do sistema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if is_firebase_connected():
            st.success("Firebase Conectado")
        else:
            st.error("Firebase Desconectado")
    
    with col2:
        try:
            global_stats = get_global_stats()
            st.metric("Total de Usuários", global_stats.get('total_users', 0))
        except:
            st.metric("Total de Usuários", "N/A")
    
    with col3:
        try:
            global_stats = get_global_stats()
            st.metric("Casos Resolvidos", global_stats.get('total_cases', 0))
        except:
            st.metric("Casos Resolvidos", "N/A")
    
    st.markdown("---")
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["Usuários", "Dados", "Estatísticas", "Sistema"])
    
    with tab1:
        show_users_management()
    
    with tab2:
        show_data_management()
    
    with tab3:
        show_statistics()
    
    with tab4:
        show_system_management()

def show_users_management():
    """Gerenciamento de usuários"""
    st.subheader("Gerenciamento de Usuários")
    
    # Botão para criar admin padrão
    if st.button("Criar Administrador Padrão"):
        success, message = create_default_admin()
        if success:
            st.success(message)
        else:
            st.error(message)
        st.rerun()
    
    st.markdown("---")
    
    # Lista de usuários
    try:
        users = get_all_users_firebase()
        
        if not users:
            st.info("Nenhum usuário encontrado")
            return
        
        # Converte para DataFrame para melhor visualização
        users_data = []
        for user in users:
            users_data.append({
                'ID': user.get('id', 'N/A'),
                'Nome': user.get('name', 'N/A'),
                'Email': user.get('email', 'N/A'),
                'Tipo': user.get('user_type', 'N/A'),
                'Criado em': user.get('created_at', 'N/A'),
                'Último Login': user.get('last_login', 'Nunca')
            })
        
        df = pd.DataFrame(users_data)
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            user_type_filter = st.selectbox(
                "Filtrar por tipo:",
                ["Todos"] + list(df['Tipo'].unique())
            )
        
        with col2:
            search_name = st.text_input("Buscar por nome:")
        
        # Aplicar filtros
        filtered_df = df.copy()
        
        if user_type_filter != "Todos":
            filtered_df = filtered_df[filtered_df['Tipo'] == user_type_filter]
        
        if search_name:
            filtered_df = filtered_df[filtered_df['Nome'].str.contains(search_name, case=False, na=False)]
        
        # Mostrar tabela
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Ações em massa
        st.subheader("Ações em Massa")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Excluir Todos os Alunos", type="secondary"):
                if st.session_state.get('confirm_delete_all_students'):
                    # Executa exclusão
                    deleted_count = 0
                    for user in users:
                        if user.get('user_type') == 'aluno':
                            success, _ = delete_user_firebase(user.get('id'))
                            if success:
                                deleted_count += 1
                    st.success(f"{deleted_count} alunos excluídos!")
                    st.rerun()
                else:
                    st.session_state.confirm_delete_all_students = True
                    st.warning("Clique novamente para confirmar a exclusão de todos os alunos")
        
        with col2:
            if st.button("Excluir Todos os Professores", type="secondary"):
                if st.session_state.get('confirm_delete_all_professors'):
                    # Executa exclusão
                    deleted_count = 0
                    for user in users:
                        if user.get('user_type') == 'professor':
                            success, _ = delete_user_firebase(user.get('id'))
                            if success:
                                deleted_count += 1
                    st.success(f"{deleted_count} professores excluídos!")
                    st.rerun()
                else:
                    st.session_state.confirm_delete_all_professors = True
                    st.warning("Clique novamente para confirmar a exclusão de todos os professores")
        
        with col3:
            if st.button("Limpar Confirmações"):
                st.session_state.confirm_delete_all_students = False
                st.session_state.confirm_delete_all_professors = False
                st.info("Confirmações limpas")
        
        # Exclusão individual
        st.subheader("Exclusão Individual")
        
        selected_user_id = st.selectbox(
            "Selecionar usuário para excluir:",
            [""] + [f"{user.get('name')} ({user.get('email')})" for user in users]
        )
        
        if selected_user_id and st.button("Excluir Usuário Selecionado", type="primary"):
            # Encontra o usuário selecionado
            selected_name = selected_user_id.split(" (")[0]
            user_to_delete = None
            
            for user in users:
                if user.get('name') == selected_name:
                    user_to_delete = user
                    break
            
            if user_to_delete:
                if user_to_delete.get('user_type') == 'admin':
                    st.error("Não é possível excluir o administrador!")
                else:
                    success, message = delete_user_firebase(user_to_delete.get('id'))
                    if success:
                        st.success(f"Usuário {user_to_delete.get('name')} excluído!")
                        st.rerun()
                    else:
                        st.error(message)
    
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")

def show_data_management():
    """Gerenciamento de dados"""
    st.subheader("Gerenciamento de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Analytics de Casos")
        
        if st.button("Excluir Todos os Analytics"):
            if st.session_state.get('confirm_delete_analytics'):
                try:
                    if is_firebase_connected():
                        db = get_firestore_db()
                        # Exclui todos os documentos da coleção case_analytics
                        docs = db.collection('case_analytics').stream()
                        deleted_count = 0
                        for doc in docs:
                            doc.reference.delete()
                            deleted_count += 1
                        st.success(f"{deleted_count} registros de analytics excluídos!")
                    else:
                        st.error("Firebase não está conectado")
                except Exception as e:
                    st.error(f"Erro ao excluir analytics: {e}")
            else:
                st.session_state.confirm_delete_analytics = True
                st.warning("Clique novamente para confirmar a exclusão de todos os analytics")
    
    with col2:
        st.subheader("Interações do Chat")
        
        if st.button("Excluir Todas as Interações"):
            if st.session_state.get('confirm_delete_chat'):
                try:
                    if is_firebase_connected():
                        db = get_firestore_db()
                        # Exclui todos os documentos da coleção chat_interactions
                        docs = db.collection('chat_interactions').stream()
                        deleted_count = 0
                        for doc in docs:
                            doc.reference.delete()
                            deleted_count += 1
                        st.success(f"{deleted_count} interações do chat excluídas!")
                    else:
                        st.error("Firebase não está conectado")
                except Exception as e:
                    st.error(f"Erro ao excluir interações: {e}")
            else:
                st.session_state.confirm_delete_chat = True
                st.warning("Clique novamente para confirmar a exclusão de todas as interações")
    
    # Limpar confirmações
    if st.button("Limpar Todas as Confirmações"):
        st.session_state.confirm_delete_analytics = False
        st.session_state.confirm_delete_chat = False
        st.info("Confirmações limpas")
    
    # Estatísticas dos dados
    st.subheader("Estatísticas dos Dados")
    
    try:
        if is_firebase_connected():
            db = get_firestore_db()
            
            # Conta documentos nas coleções
            case_analytics_count = len(list(db.collection('case_analytics').stream()))
            chat_interactions_count = len(list(db.collection('chat_interactions').stream()))
            users_count = len(list(db.collection('users').stream()))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Usuários", users_count)
            
            with col2:
                st.metric("Analytics de Casos", case_analytics_count)
            
            with col3:
                st.metric("Interações do Chat", chat_interactions_count)
        
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")

def show_statistics():
    """Estatísticas detalhadas"""
    st.subheader("Estatísticas Detalhadas")
    
    try:
        global_stats = get_global_stats()
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Usuários", global_stats.get('total_users', 0))
        
        with col2:
            st.metric("Total de Casos", global_stats.get('total_cases', 0))
        
        with col3:
            st.metric("Interações do Chat", global_stats.get('total_chat_interactions', 0))
        
        with col4:
            st.metric("Taxa Média de Acertos", f"{global_stats.get('average_accuracy_rate', 0):.1f}%")
        
        # Gráficos
        st.subheader("Distribuição de Usuários")
        
        users = get_all_users_firebase()
        if users:
            user_types = {}
            for user in users:
                user_type = user.get('user_type', 'N/A')
                user_types[user_type] = user_types.get(user_type, 0) + 1
            
            # Gráfico de pizza
            import plotly.express as px
            
            fig = px.pie(
                values=list(user_types.values()),
                names=list(user_types.keys()),
                title="Distribuição por Tipo de Usuário"
            )
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")

def show_system_management():
    """Gerenciamento do sistema"""
    st.subheader("Gerenciamento do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Status do Sistema")
        
        # Status do Firebase
        if is_firebase_connected():
            st.success("Firebase: Conectado")
        else:
            st.error("Firebase: Desconectado")
        
        # Informações do sistema
        st.info(f"Data/Hora atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Botão para testar conexão
        if st.button("Testar Conexão Firebase"):
            try:
                db = get_firestore_db()
                # Testa uma operação simples
                test_doc = db.collection('test').document('connection')
                test_doc.set({'test': True, 'timestamp': datetime.now()})
                test_doc.delete()
                st.success("Conexão com Firebase funcionando!")
            except Exception as e:
                st.error(f"Erro na conexão: {e}")
    
    with col2:
        st.subheader("Ações do Sistema")
        
        # Botão para limpar cache
        if st.button("Limpar Cache da Sessão"):
            for key in list(st.session_state.keys()):
                if key not in ['user_id', 'user_name', 'user_type']:
                    del st.session_state[key]
            st.success("Cache limpo!")
            st.rerun()
        
        # Botão para reinicializar sistema
        if st.button("Reinicializar Sistema"):
            st.info("Sistema reinicializado!")
            st.rerun()
        
        # Informações de debug
        st.subheader("Informações de Debug")
        
        if st.checkbox("Mostrar informações de debug"):
            st.json({
                "session_state_keys": list(st.session_state.keys()),
                "firebase_connected": is_firebase_connected(),
                "current_time": datetime.now().isoformat()
            })
