import streamlit as st
from datetime import datetime
from typing import Dict, List
from firebase_config import get_firestore_db, is_firebase_connected

def reset_student_analytics(user_id: str) -> bool:
    """
    Reseta todas as questões respondidas de um aluno específico.
    Remove todos os registros de case_analytics para o usuário.
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado. Não é possível resetar dados.")
            return False
        
        db = get_firestore_db()
        
        # Busca todos os analytics do usuário
        analytics_ref = db.collection('case_analytics')
        query = analytics_ref.where('user_id', '==', user_id)
        docs = query.get()
        
        # Deleta cada documento
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        print(f"ADMIN: Deletados {deleted_count} registros de analytics para usuário {user_id}")
        return True
        
    except Exception as e:
        st.error(f"Erro ao resetar analytics: {e}")
        return False

def clear_student_chat_interactions(user_id: str) -> bool:
    """
    Limpa todas as interações de chat de um aluno específico.
    Remove todos os registros de chat_interactions para o usuário.
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado. Não é possível limpar chat.")
            return False
        
        db = get_firestore_db()
        
        # Busca todas as interações do usuário
        chat_ref = db.collection('chat_interactions')
        query = chat_ref.where('user_id', '==', user_id)
        docs = query.get()
        
        # Deleta cada documento
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        
        print(f"ADMIN: Deletadas {deleted_count} interações de chat para usuário {user_id}")
        return True
        
    except Exception as e:
        st.error(f"Erro ao limpar chat: {e}")
        return False

def reset_all_students_analytics() -> Dict[str, int]:
    """
    Reseta todas as questões respondidas de TODOS os alunos.
    ATENÇÃO: Esta é uma operação destrutiva!
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado. Não é possível resetar dados.")
            return {'deleted': 0, 'errors': 0}
        
        db = get_firestore_db()
        
        # Busca TODOS os analytics
        analytics_ref = db.collection('case_analytics')
        docs = analytics_ref.get()
        
        # Deleta cada documento
        deleted_count = 0
        error_count = 0
        
        for doc in docs:
            try:
                doc.reference.delete()
                deleted_count += 1
            except Exception as e:
                error_count += 1
                print(f"Erro ao deletar documento {doc.id}: {e}")
        
        print(f"ADMIN: Deletados {deleted_count} registros de analytics (total)")
        return {'deleted': deleted_count, 'errors': error_count}
        
    except Exception as e:
        st.error(f"Erro ao resetar todos os analytics: {e}")
        return {'deleted': 0, 'errors': 1}

def clear_all_chat_interactions() -> Dict[str, int]:
    """
    Limpa TODAS as interações de chat de TODOS os usuários.
    ATENÇÃO: Esta é uma operação destrutiva!
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado. Não é possível limpar chat.")
            return {'deleted': 0, 'errors': 0}
        
        db = get_firestore_db()
        
        # Busca TODAS as interações
        chat_ref = db.collection('chat_interactions')
        docs = chat_ref.get()
        
        # Deleta cada documento
        deleted_count = 0
        error_count = 0
        
        for doc in docs:
            try:
                doc.reference.delete()
                deleted_count += 1
            except Exception as e:
                error_count += 1
                print(f"Erro ao deletar documento {doc.id}: {e}")
        
        print(f"ADMIN: Deletadas {deleted_count} interações de chat (total)")
        return {'deleted': deleted_count, 'errors': error_count}
        
    except Exception as e:
        st.error(f"Erro ao limpar todos os chats: {e}")
        return {'deleted': 0, 'errors': 1}

def log_admin_action(action: str, details: str, user_id: str = None):
    """
    Registra uma ação administrativa para auditoria.
    """
    try:
        if not is_firebase_connected():
            return
        
        db = get_firestore_db()
        
        log_entry = {
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'admin_user': st.session_state.get('user_id', 'unknown')
        }
        
        if user_id:
            log_entry['target_user_id'] = user_id
        
        db.collection('admin_logs').add(log_entry)
        
    except Exception as e:
        print(f"Erro ao registrar log de admin: {e}")

def get_database_stats() -> Dict[str, int]:
    """
    Retorna estatísticas sobre o tamanho do banco de dados.
    """
    try:
        if not is_firebase_connected():
            return {
                'total_analytics': 0,
                'total_chat_interactions': 0,
                'total_users': 0
            }
        
        db = get_firestore_db()
        
        # Conta analytics
        analytics_count = len(db.collection('case_analytics').get())
        
        # Conta chat interactions
        chat_count = len(db.collection('chat_interactions').get())
        
        # Conta usuários
        users_count = len(db.collection('users').get())
        
        return {
            'total_analytics': analytics_count,
            'total_chat_interactions': chat_count,
            'total_users': users_count
        }
        
    except Exception as e:
        st.error(f"Erro ao obter estatísticas: {e}")
        return {
            'total_analytics': 0,
            'total_chat_interactions': 0,
            'total_users': 0
        }
