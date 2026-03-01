import streamlit as st
from datetime import datetime
from typing import Dict, List
from firebase_config import get_firestore_db, is_firebase_connected, get_db_for_user, get_all_dbs

def reset_student_analytics(user_id: str) -> bool:
    """
    Reseta todas as questões respondidas de um aluno específico.
    Remove todos os registros de case_analytics para o usuário.
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado.")
            return False
        db = get_db_for_user(user_id)
        docs = db.collection('case_analytics').where('user_id', '==', user_id).get()
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        print(f"ADMIN: Deletados {deleted_count} analytics para usuário {user_id}")
        return True
    except Exception as e:
        st.error(f"Erro ao resetar analytics: {e}")
        return False

def clear_student_chat_interactions(user_id: str) -> bool:
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado.")
            return False
        db = get_db_for_user(user_id)
        docs = db.collection('chat_interactions').where('user_id', '==', user_id).get()
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
    Reseta todas as questões respondidas de TODOS os alunos em TODOS os Firebases.
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado.")
            return {'deleted': 0, 'errors': 0}
        deleted_count = 0
        error_count = 0
        for db in get_all_dbs():
            docs = db.collection('case_analytics').get()
            for doc in docs:
                try:
                    doc.reference.delete()
                    deleted_count += 1
                except Exception as e:
                    error_count += 1
        print(f"ADMIN: Deletados {deleted_count} registros de analytics (total)")
        return {'deleted': deleted_count, 'errors': error_count}
    except Exception as e:
        st.error(f"Erro ao resetar todos os analytics: {e}")
        return {'deleted': 0, 'errors': 1}

def clear_all_chat_interactions() -> Dict[str, int]:
    """
    Limpa TODAS as interações de chat de TODOS os usuários em TODOS os Firebases.
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado.")
            return {'deleted': 0, 'errors': 0}
        deleted_count = 0
        error_count = 0
        for db in get_all_dbs():
            docs = db.collection('chat_interactions').get()
            for doc in docs:
                try:
                    doc.reference.delete()
                    deleted_count += 1
                except Exception as e:
                    error_count += 1
        print(f"ADMIN: Deletadas {deleted_count} interações de chat (total)")
        return {'deleted': deleted_count, 'errors': error_count}
    except Exception as e:
        st.error(f"Erro ao limpar todos os chats: {e}")
        return {'deleted': 0, 'errors': 1}

def reset_all_student_progress() -> Dict[str, int]:
    """
    Remove o campo 'progress' de TODOS os usuários (reseta questão atual, score, streak).
    Usado ao trocar de conjunto de questões.
    """
    try:
        if not is_firebase_connected():
            st.error("Firebase não está conectado.")
            return {'updated': 0, 'errors': 0}
        db = get_firestore_db()  # Usuários ficam sempre no Firebase primário
        docs = db.collection('users').where('user_type', '==', 'aluno').get()
        updated = 0
        errors = 0
        for doc in docs:
            try:
                from google.cloud.firestore_v1 import DELETE_FIELD
                doc.reference.update({'progress': DELETE_FIELD})
                updated += 1
            except Exception:
                # Fallback: set para None caso DELETE_FIELD não funcione
                try:
                    doc.reference.update({'progress': {}})
                    updated += 1
                except Exception as e2:
                    errors += 1
        print(f"ADMIN: Progress resetado para {updated} alunos")
        return {'updated': updated, 'errors': errors}
    except Exception as e:
        st.error(f"Erro ao resetar progress: {e}")
        return {'updated': 0, 'errors': 1}

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

@st.cache_data(ttl=300, show_spinner=False)
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
