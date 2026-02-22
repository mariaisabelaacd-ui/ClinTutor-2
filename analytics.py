import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from firebase_config import get_firestore_db, is_firebase_connected
import json
import os

# Configurações do banco de dados local (fallback)
ANALYTICS_DB_PATH = os.path.join(os.path.expanduser("~"), ".clintutor", "analytics.json")

def init_analytics_db():
    """Inicializa o banco de dados de analytics local se não existir (fallback)"""
    os.makedirs(os.path.dirname(ANALYTICS_DB_PATH), exist_ok=True)
    if not os.path.exists(ANALYTICS_DB_PATH):
        with open(ANALYTICS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_analytics_local() -> List[Dict]:
    """Carrega analytics do banco local (fallback)"""
    init_analytics_db()
    try:
        with open(ANALYTICS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_analytics_local(analytics: List[Dict]):
    """Salva analytics no banco local (fallback)"""
    try:
        with open(ANALYTICS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(analytics, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar analytics localmente: {e}")

# =============================
# Rastreamento de Tempo de Resposta
# =============================

def start_case_timer(user_id: str, case_id: str) -> str:
    """Inicia o timer para um caso clínico"""
    timer_id = f"{user_id}_{case_id}_{datetime.now().timestamp()}"
    
    # Armazena o timer na sessão do Streamlit
    if "case_timers" not in st.session_state:
        st.session_state.case_timers = {}
    
    st.session_state.case_timers[timer_id] = {
        "user_id": user_id,
        "case_id": case_id,
        "start_time": datetime.now().isoformat(),
        "status": "active"
    }
    
    return timer_id

def end_case_timer(timer_id: str, case_result: Dict) -> Optional[Dict]:
    """Finaliza o timer e salva os dados de tempo de resposta"""
    if "case_timers" not in st.session_state:
        return None
    
    if timer_id not in st.session_state.case_timers:
        return None
    
    timer_data = st.session_state.case_timers[timer_id]
    end_time = datetime.now()
    
    # Converte start_time de string para datetime
    start_time = datetime.fromisoformat(timer_data["start_time"])
    
    # Garante que ambos os timestamps tenham o mesmo timezone
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=None)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=None)
    
    duration = (end_time - start_time).total_seconds()
    
    # Dados do caso
    case_analytics = {
        "user_id": timer_data["user_id"],
        "case_id": timer_data["case_id"],
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "duration_formatted": format_duration(duration),
        "case_result": case_result,
        "timestamp": datetime.now().isoformat()
    }
    
    # Salva no Firebase ou local
    save_case_analytics(case_analytics)
    
    # Remove o timer da sessão
    del st.session_state.case_timers[timer_id]
    
    return case_analytics

def format_duration(seconds: float) -> str:
    """Formata duração em segundos para formato legível"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

# =============================
# Rastreamento de Interações com Chatbot
# =============================

def log_chat_interaction(user_id: str, case_id: str, user_message: str, bot_response: str, response_time: float = None):
    """Registra uma interação com o chatbot"""
    interaction = {
        "user_id": user_id,
        "case_id": case_id,
        "user_message": user_message,
        "bot_response": bot_response,
        "response_time_seconds": response_time,
        "timestamp": datetime.now().isoformat()
    }
    
    save_chat_interaction(interaction)

# =============================
# Cálculo de Taxa de Acertos
# =============================

def calculate_accuracy_rate(user_id: str) -> Dict[str, Any]:
    """Calcula a taxa de acertos de um usuário"""
    case_analytics = get_user_case_analytics(user_id)
    
    if not case_analytics:
        return {
            "total_cases": 0,
            "correct_cases": 0,
            "accuracy_rate": 0.0,
            "average_time": 0.0,
            "total_time": 0.0,
            "average_time_formatted": "0.0s",
            "total_time_formatted": "0.0s"
        }
    
    total_cases = len(case_analytics)
    correct_cases = sum(1 for case_data in case_analytics 
                       if case_data.get("case_result", {}).get("is_correct", False))
    
    accuracy_rate = (correct_cases / total_cases * 100) if total_cases > 0 else 0.0
    
    # Calcula tempo total usando duration_seconds diretamente
    total_time = 0
    valid_durations = 0
    
    for case_data in case_analytics:
        duration = case_data.get("duration_seconds", 0)
        
        # Se duration é numérico, usa diretamente
        if isinstance(duration, (int, float)) and duration > 0:
            total_time += duration
            valid_durations += 1
    
    # Calcula média baseada em durações válidas
    average_time = total_time / valid_durations if valid_durations > 0 else 0.0
    
    return {
        "total_cases": total_cases,
        "correct_cases": correct_cases,
        "accuracy_rate": accuracy_rate,
        "average_time": average_time,
        "total_time": total_time,
        "average_time_formatted": format_duration(average_time),
        "total_time_formatted": format_duration(total_time)
    }

# =============================
# Armazenamento no Firebase
# =============================

def save_case_analytics(case_analytics: Dict):
    """Salva analytics de caso no Firebase ou local"""
    if is_firebase_connected():
        save_case_analytics_firebase(case_analytics)
    else:
        # Se Firebase não está conectado, tenta usar local
        st.warning("⚠️ Firebase não está conectado. Salvando localmente.")
        save_case_analytics_local(case_analytics)

def save_case_analytics_firebase(case_analytics: Dict):
    """Salva analytics de caso no Firebase"""
    try:
        db = get_firestore_db()
        analytics_ref = db.collection('case_analytics')
        doc_ref = analytics_ref.add(case_analytics)
        print(f"SUCESSO: Analytics salvo no Firebase: {doc_ref[1].id}")
        return True
    except Exception as e:
        print(f"ERRO: Erro ao salvar analytics no Firebase: {e}")
        st.error(f"Erro ao salvar analytics no Firebase: {e}")
        return False

def save_case_analytics_local(case_analytics: Dict):
    """Salva analytics de caso localmente"""
    analytics = load_analytics_local()
    analytics.append(case_analytics)
    save_analytics_local(analytics)

def save_chat_interaction(interaction: Dict):
    """Salva interação do chat no Firebase ou local"""
    if is_firebase_connected():
        save_chat_interaction_firebase(interaction)
    else:
        # Se Firebase não está conectado, tenta usar local
        st.warning("⚠️ Firebase não está conectado. Salvando localmente.")
        save_chat_interaction_local(interaction)

def save_chat_interaction_firebase(interaction: Dict):
    """Salva interação do chat no Firebase"""
    try:
        db = get_firestore_db()
        chat_ref = db.collection('chat_interactions')
        doc_ref = chat_ref.add(interaction)
        print(f"SUCESSO: Interação do chat salva no Firebase: {doc_ref[1].id}")
        return True
    except Exception as e:
        print(f"ERRO: Erro ao salvar interação do chat no Firebase: {e}")
        st.error(f"Erro ao salvar interação do chat no Firebase: {e}")
        return False

def save_chat_interaction_local(interaction: Dict):
    """Salva interação do chat localmente"""
    # Para simplificar, vamos salvar no mesmo arquivo de analytics
    analytics = load_analytics_local()
    interaction["type"] = "chat_interaction"
    analytics.append(interaction)
    save_analytics_local(analytics)

# =============================
# Recuperação de Dados
# =============================

@st.cache_data(ttl=300, show_spinner=False)
def get_user_case_analytics(user_id: str) -> List[Dict]:
    """Recupera analytics de casos de um usuário"""
    if is_firebase_connected():
        return get_user_case_analytics_firebase(user_id)
    else:
        # Se Firebase não está conectado, usa local
        return get_user_case_analytics_local(user_id)

@st.cache_data(ttl=300, show_spinner=False)
def get_user_case_analytics_firebase(user_id: str) -> List[Dict]:
    """Recupera analytics de casos do Firebase"""
    try:
        db = get_firestore_db()
        analytics_ref = db.collection('case_analytics')
        
        # Busca sem order_by para evitar necessidade de índice composto
        query = analytics_ref.where('user_id', '==', user_id)
        docs = query.get()
        
        analytics = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            analytics.append(data)
        
        # Ordena no código por timestamp (mais recente primeiro)
        try:
            analytics.sort(key=get_timestamp_sort_key, reverse=True)
        except Exception as e:
            st.warning(f"⚠️ Erro ao ordenar analytics: {e}")
            pass
        
        print(f"DEBUG: Encontrados {len(analytics)} analytics para usuário {user_id}")
        return analytics
    except Exception as e:
        print(f"ERRO: Erro ao buscar analytics no Firebase: {e}")
        st.error(f"Erro ao buscar analytics no Firebase: {e}")
        return []

@st.cache_data(ttl=300, show_spinner=False)
def get_user_case_analytics_local(user_id: str) -> List[Dict]:
    """Recupera analytics de casos localmente"""
    analytics = load_analytics_local()
    return [data for data in analytics if data.get("user_id") == user_id and data.get("type") != "chat_interaction"]

@st.cache_data(ttl=300, show_spinner=False)
def get_user_chat_interactions(user_id: str, case_id: str = None) -> List[Dict]:
    """Recupera interações do chat de um usuário"""
    if is_firebase_connected():
        return get_user_chat_interactions_firebase(user_id, case_id)
    else:
        # Se Firebase não está conectado, usa local
        return get_user_chat_interactions_local(user_id, case_id)

@st.cache_data(ttl=300, show_spinner=False)
def get_user_chat_interactions_firebase(user_id: str, case_id: str = None) -> List[Dict]:
    """Recupera interações do chat do Firebase"""
    try:
        db = get_firestore_db()
        chat_ref = db.collection('chat_interactions')
        query = chat_ref.where('user_id', '==', user_id)
        
        if case_id:
            query = query.where('case_id', '==', case_id)
        
        # Remove order_by para evitar necessidade de índice composto
        docs = query.get()
        
        interactions = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            interactions.append(data)
        
        # Ordena no código por timestamp (mais recente primeiro)
        try:
            interactions.sort(key=get_timestamp_sort_key, reverse=True)
        except Exception as e:
            st.warning(f"⚠️ Erro ao ordenar interações: {e}")
            pass
        
        return interactions
    except Exception as e:
        st.error(f"Erro ao buscar interações do chat no Firebase: {e}")
        return []

@st.cache_data(ttl=300, show_spinner=False)
def get_user_chat_interactions_local(user_id: str, case_id: str = None) -> List[Dict]:
    """Recupera interações do chat localmente"""
    analytics = load_analytics_local()
    interactions = [data for data in analytics if data.get("user_id") == user_id and data.get("type") == "chat_interaction"]
    
    if case_id:
        interactions = [data for data in interactions if data.get("case_id") == case_id]
    
    return interactions

@st.cache_data(ttl=300, show_spinner=False)
def get_all_users_analytics() -> Dict[str, Dict]:
    """Recupera analytics de todos os usuários (apenas alunos)"""
    if is_firebase_connected():
        return get_all_users_analytics_firebase()
    else:
        # Se Firebase não está conectado, usa local
        st.warning("⚠️ Firebase não está conectado. Dados podem não estar sincronizados.")
        return get_all_users_analytics_local()

@st.cache_data(ttl=300, show_spinner=False)
def get_all_users_analytics_firebase() -> Dict[str, Dict]:
    """Recupera analytics de todos os usuários do Firebase (apenas alunos)"""
    try:
        db = get_firestore_db()
        
        # Obtém apenas IDs de alunos
        student_ids = get_students_only()
        if not student_ids:
            return {}
        
        # Busca todos os analytics de casos
        case_analytics_ref = db.collection('case_analytics')
        case_docs = case_analytics_ref.get()
        
        # Busca todas as interações do chat
        chat_ref = db.collection('chat_interactions')
        chat_docs = chat_ref.get()
        
        # Organiza por usuário (apenas alunos)
        users_analytics = {}
        
        for doc in case_docs:
            data = doc.to_dict()
            user_id = data.get('user_id')
            if user_id in student_ids:  # Filtra apenas alunos
                if user_id not in users_analytics:
                    users_analytics[user_id] = {
                        'case_analytics': [],
                        'chat_interactions': []
                    }
                users_analytics[user_id]['case_analytics'].append(data)
        
        for doc in chat_docs:
            data = doc.to_dict()
            user_id = data.get('user_id')
            if user_id in student_ids:  # Filtra apenas alunos
                if user_id not in users_analytics:
                    users_analytics[user_id] = {
                        'case_analytics': [],
                        'chat_interactions': []
                    }
                users_analytics[user_id]['chat_interactions'].append(data)
        
        return users_analytics
        
    except Exception as e:
        st.error(f"Erro ao buscar analytics no Firebase: {e}")
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def get_all_users_analytics_local() -> Dict[str, Dict]:
    """Recupera analytics de todos os usuários localmente (apenas alunos)"""
    analytics = load_analytics_local()
    users_analytics = {}
    
    # Obtém apenas IDs de alunos
    student_ids = get_students_only()
    if not student_ids:
        return {}
    
    for data in analytics:
        user_id = data.get('user_id')
        if user_id in student_ids:  # Filtra apenas alunos
            if user_id not in users_analytics:
                users_analytics[user_id] = {
                    'case_analytics': [],
                    'chat_interactions': []
                }
            
            if data.get('type') == 'chat_interaction':
                users_analytics[user_id]['chat_interactions'].append(data)
            else:
                users_analytics[user_id]['case_analytics'].append(data)
    
    return users_analytics

# =============================
# Funções Auxiliares
# =============================

def get_students_only() -> List[str]:
    """Retorna lista de IDs de usuários que são alunos"""
    try:
        from auth_firebase import get_all_users
        all_users = get_all_users()
        return [user['id'] for user in all_users if user.get('user_type') == 'aluno']
    except Exception:
        return []

def get_timestamp_sort_key(x):
    """Função auxiliar para ordenação de timestamps - versão ultra robusta"""
    try:
        timestamp = x.get('timestamp', datetime.min.isoformat())
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp)
                # Garante que seja timezone-naive para comparação
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except (ValueError, TypeError, AttributeError):
                return datetime.min
        elif hasattr(timestamp, 'timestamp'):
            # Se for um objeto datetime, garante que seja timezone-naive
            try:
                if timestamp.tzinfo is not None:
                    return timestamp.replace(tzinfo=None)
                return timestamp
            except (AttributeError, TypeError):
                return datetime.min
        else:
            return datetime.min
    except Exception:
        return datetime.min

def get_case_resolution_times(user_id: str) -> List[Dict[str, Any]]:
    """Retorna lista de casos com tempos de resolução para um usuário"""
    case_analytics = get_user_case_analytics(user_id)
    resolution_times = []
    
    for case_data in case_analytics:
        case_id = case_data.get('case_id')
        duration_seconds = case_data.get('duration_seconds', 0)
        duration_formatted = case_data.get('duration_formatted', 'N/A')
        case_result = case_data.get('case_result', 'unknown')
        timestamp = case_data.get('timestamp', datetime.now().isoformat())
        
        # Converte timestamp para datetime se necessário
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        resolution_times.append({
            'case_id': case_id,
            'duration_seconds': duration_seconds,
            'duration_formatted': duration_formatted,
            'case_result': case_result,
            'timestamp': timestamp,
            'is_correct': case_result == 'correct'
        })
    
    # Ordena por timestamp (mais recente primeiro) com tratamento robusto de erro
    try:
        def safe_timestamp_sort(x):
            try:
                timestamp = x.get('timestamp')
                if timestamp is None:
                    return datetime.min
                
                dt_val = datetime.min
                if isinstance(timestamp, str):
                    try:
                        dt_val = datetime.fromisoformat(timestamp)
                    except (ValueError, TypeError):
                        pass
                elif isinstance(timestamp, datetime):
                    dt_val = timestamp
                
                # Garante que seja sempre timezone-naive para comparação segura
                if dt_val.tzinfo is not None:
                    dt_val = dt_val.replace(tzinfo=None)
                
                return dt_val
            except Exception:
                return datetime.min
        
        resolution_times.sort(key=safe_timestamp_sort, reverse=True)
    except Exception as e:
        # Se ainda assim der erro, mantém a lista sem ordenar
        st.warning(f"⚠️ Erro ao ordenar tempos de resolução: {e}")
        pass
    
    return resolution_times

def get_resolution_time_stats(user_id: str) -> Dict[str, Any]:
    """Retorna estatísticas de tempo de resolução para um usuário"""
    resolution_times = get_case_resolution_times(user_id)
    
    if not resolution_times:
        return {
            'total_cases': 0,
            'average_time_seconds': 0,
            'average_time_formatted': '0s',
            'fastest_time_seconds': 0,
            'fastest_time_formatted': '0s',
            'slowest_time_seconds': 0,
            'slowest_time_formatted': '0s',
            'correct_cases_time': [],
            'incorrect_cases_time': []
        }
    
    # Separa casos corretos e incorretos
    correct_times = [r['duration_seconds'] for r in resolution_times if r['is_correct']]
    incorrect_times = [r['duration_seconds'] for r in resolution_times if not r['is_correct']]
    
    # Calcula estatísticas gerais
    all_times = [r['duration_seconds'] for r in resolution_times]
    avg_time = sum(all_times) / len(all_times) if all_times else 0
    fastest_time = min(all_times) if all_times else 0
    slowest_time = max(all_times) if all_times else 0
    
    return {
        'total_cases': len(resolution_times),
        'average_time_seconds': avg_time,
        'average_time_formatted': format_duration(avg_time),
        'fastest_time_seconds': fastest_time,
        'fastest_time_formatted': format_duration(fastest_time),
        'slowest_time_seconds': slowest_time,
        'slowest_time_formatted': format_duration(slowest_time),
        'correct_cases_time': correct_times,
        'incorrect_cases_time': incorrect_times,
        'correct_avg_time': sum(correct_times) / len(correct_times) if correct_times else 0,
        'incorrect_avg_time': sum(incorrect_times) / len(incorrect_times) if incorrect_times else 0
    }

# =============================
# Funções de Estatísticas
# =============================

def get_user_detailed_stats(user_id: str) -> Dict[str, Any]:
    """Retorna estatísticas detalhadas de um usuário"""
    case_analytics = get_user_case_analytics(user_id)
    chat_interactions = get_user_chat_interactions(user_id)
    
    # Estatísticas de casos
    case_stats = calculate_accuracy_rate(user_id)
    
    # Estatísticas de chat
    total_chat_interactions = len(chat_interactions)
    avg_response_time = 0
    if chat_interactions:
        response_times = [i.get('response_time_seconds', 0) for i in chat_interactions if i.get('response_time_seconds')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Casos por dia (últimos 7 dias)
    now = datetime.now()
    recent_cases = []
    for c in case_analytics:
        timestamp = c.get('timestamp', now)
        
        # Converte string para datetime se necessário
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Garante que ambos tenham o mesmo timezone (timezone-naive)
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
        if hasattr(now, 'tzinfo') and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        # Verifica se é dos últimos 7 dias
        try:
            if (now - timestamp).days <= 7:
                recent_cases.append(c)
        except (TypeError, ValueError):
            # Se houver erro na operação, pula este caso
            continue
            
    cases_by_day = {}
    for case_data in recent_cases:
        timestamp = case_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Garante timezone-naive
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
            
        day = timestamp.strftime('%Y-%m-%d')
        cases_by_day[day] = cases_by_day.get(day, 0) + 1
    
    return {
        'user_id': user_id,
        'case_stats': case_stats,
        'total_chat_interactions': total_chat_interactions,
        'avg_chat_response_time': avg_response_time,
        'avg_chat_response_time_formatted': format_duration(avg_response_time),
        'recent_cases_count': len(recent_cases),
        'cases_by_day': cases_by_day,
        'last_activity': max([get_timestamp_sort_key(c) for c in case_analytics + chat_interactions], default=datetime.min)
    }

def _is_today(timestamp) -> bool:
    """Verifica se um timestamp é de hoje"""
    try:
        now = datetime.now()
        
        # Converte string para datetime se necessário
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Garante que ambos sejam timezone-naive
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
        if hasattr(now, 'tzinfo') and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        # Verifica se é do mesmo dia
        return (now - timestamp).days == 0
    except (TypeError, ValueError, AttributeError):
        return False

def get_global_stats() -> Dict[str, Any]:
    """Retorna estatísticas globais do sistema"""
    all_analytics = get_all_users_analytics()
    
    total_users = len(all_analytics)
    total_cases = sum(len(data['case_analytics']) for data in all_analytics.values())
    total_chat_interactions = sum(len(data['chat_interactions']) for data in all_analytics.values())
    
    # Média de acertos
    accuracy_rates = []
    for user_id in all_analytics:
        user_stats = get_user_detailed_stats(user_id)
        if user_stats['case_stats']['total_cases'] > 0:
            accuracy_rates.append(user_stats['case_stats']['accuracy_rate'])
    
    avg_accuracy = sum(accuracy_rates) / len(accuracy_rates) if accuracy_rates else 0
    
    return {
        'total_users': total_users,
        'total_cases': total_cases,
        'total_chat_interactions': total_chat_interactions,
        'average_accuracy_rate': avg_accuracy,
        'active_users_today': len([user_id for user_id, data in all_analytics.items() 
                                  if any(_is_today(case.get('timestamp', datetime.min.isoformat())) 
                                        for case in data['case_analytics'] + data['chat_interactions'])])
    }
def get_student_advanced_stats(user_id: str) -> Dict[str, Any]:
    """
    Gera estatísticas avançadas para o aluno:
    - Desempenho por Componente de Conhecimento
    - Desempenho por Dificuldade
    - Tempo médio por Dificuldade
    """
    case_analytics = get_user_case_analytics(user_id)
    
    # Importa aqui para evitar circularidade no topo, se houver
    from logic import QUESTIONS
    
    # Mapeamentos
    q_map = {q['id']: q for q in QUESTIONS}
    
    stats = {
        "componentes": {},
        "dificuldade": {},
        "tempo_por_dificuldade": {}
    }
    
    for entry in case_analytics:
        cid = entry.get('case_id')
        result = entry.get('case_result', {})
        duration = entry.get('duration_seconds', 0)
        
        # Garante fallback se mudar estrutura
        if not isinstance(result, dict): continue
        
        q_data = q_map.get(cid)
        if not q_data: continue
        
        is_correct = result.get('is_correct', False)
        
        # 1. Componentes
        comps = q_data.get('componentes_conhecimento', ['Geral'])
        for comp in comps:
            if comp not in stats['componentes']:
                stats['componentes'][comp] = {'total': 0, 'correct': 0}
            stats['componentes'][comp]['total'] += 1
            if is_correct: stats['componentes'][comp]['correct'] += 1
            
        # 2. Dificuldade
        diff = q_data.get('dificuldade', 'Não Classificado')
        if diff not in stats['dificuldade']:
            stats['dificuldade'][diff] = {'total': 0, 'correct': 0}
            stats['tempo_por_dificuldade'][diff] = []
            
        stats['dificuldade'][diff]['total'] += 1
        if is_correct: stats['dificuldade'][diff]['correct'] += 1
        stats['tempo_por_dificuldade'][diff].append(duration)
        
    # Processa médias
    final_stats = {
        "componentes": [],
        "dificuldade": []
    }
    
    for comp, data in stats['componentes'].items():
        acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        final_stats['componentes'].append({
            "nome": comp,
            "acuracia": acc,
            "total": data['total'],
            "acertos": data['correct']
        })
        
    for diff, data in stats['dificuldade'].items():
        acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        times = stats['tempo_por_dificuldade'].get(diff, [])
        avg_time = sum(times) / len(times) if times else 0
        
        final_stats['dificuldade'].append({
            "nivel": diff,
            "acuracia": acc,
            "tempo_medio": avg_time,
            "total": data['total']
        })
        
    return final_stats

# =============================
# Novas Funções para Dashboard Redesenhado
# =============================

def get_global_knowledge_component_stats() -> List[Dict[str, Any]]:
    """
    Calcula estatísticas agregadas por componente de conhecimento para todos os alunos.
    Retorna lista de componentes com total de questões, acertos, taxa de acerto e tempo médio.
    """
    from logic import QUESTIONS
    
    all_analytics = get_all_users_analytics()
    q_map = {q['id']: q for q in QUESTIONS}
    
    # Estrutura para agregar dados por componente
    component_stats = {}
    
    for user_id, user_data in all_analytics.items():
        case_analytics = user_data.get('case_analytics', [])
        
        for entry in case_analytics:
            cid = entry.get('case_id')
            result = entry.get('case_result', {})
            duration = entry.get('duration_seconds', 0)
            
            q_data = q_map.get(cid)
            if not q_data:
                continue
            
            is_correct = result.get('is_correct', False)
            components = q_data.get('componentes_conhecimento', ['Geral'])
            
            for comp in components:
                if comp not in component_stats:
                    component_stats[comp] = {
                        'total': 0,
                        'correct': 0,
                        'times': []
                    }
                
                component_stats[comp]['total'] += 1
                if is_correct:
                    component_stats[comp]['correct'] += 1
                if duration > 0:
                    component_stats[comp]['times'].append(duration)
    
    # Processa resultados finais
    results = []
    for comp, data in component_stats.items():
        accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
        
        results.append({
            'componente': comp,
            'total_questoes': data['total'],
            'acertos': data['correct'],
            'taxa_acerto': accuracy,
            'tempo_medio': avg_time,
            'tempo_medio_formatado': format_duration(avg_time)
        })
    
    # Ordena por taxa de acerto (menor para maior = mais difícil primeiro)
    results.sort(key=lambda x: x['taxa_acerto'])
    
    return results

def get_average_user_level() -> Dict[str, Any]:
    """
    Calcula o nível médio de todos os alunos baseado em pontuação.
    Retorna distribuição de alunos por nível (básico, intermediário, avançado).
    """
    from logic import level_from_score
    
    all_analytics = get_all_users_analytics()
    
    level_distribution = {
        1: 0,  # básico
        2: 0,  # intermediário
        3: 0   # avançado
    }
    
    total_score = 0
    total_students = 0
    
    for user_id, user_data in all_analytics.items():
        case_analytics = user_data.get('case_analytics', [])
        
        # Calcula pontuação total do aluno
        user_score = 0
        for entry in case_analytics:
            result = entry.get('case_result', {})
            points = result.get('points_gained', 0)
            user_score += points
        
        # Determina nível do aluno
        user_level = level_from_score(int(user_score))
        level_distribution[user_level] += 1
        
        total_score += user_score
        total_students += 1
    
    avg_score = total_score / total_students if total_students > 0 else 0
    avg_level = level_from_score(int(avg_score))
    
    return {
        'nivel_medio': avg_level,
        'pontuacao_media': avg_score,
        'distribuicao': {
            'basico': level_distribution[1],
            'intermediario': level_distribution[2],
            'avancado': level_distribution[3]
        },
        'total_alunos': total_students
    }

def get_hardest_categories(top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Identifica as categorias/componentes com menor taxa de acerto.
    Retorna top N categorias mais difíceis com estatísticas.
    """
    component_stats = get_global_knowledge_component_stats()
    
    # Já está ordenado por taxa de acerto (menor primeiro)
    hardest = component_stats[:top_n]
    
    return hardest

def get_student_weakness_analysis(user_id: str) -> Dict[str, Any]:
    """
    Análise detalhada das fraquezas de um aluno específico.
    Retorna:
    - Componente com maior dificuldade
    - Nível de questão com menor acerto
    - Tags/componentes problemáticos
    - Padrões de erro
    """
    from logic import QUESTIONS
    
    case_analytics = get_user_case_analytics(user_id)
    q_map = {q['id']: q for q in QUESTIONS}
    
    if not case_analytics:
        return {
            'componente_mais_dificil': None,
            'nivel_mais_dificil': None,
            'componentes_problematicos': [],
            'padroes_erro': []
        }
    
    # Análise por componente
    component_performance = {}
    difficulty_performance = {
        'básico': {'total': 0, 'correct': 0},
        'intermediário': {'total': 0, 'correct': 0},
        'avançado': {'total': 0, 'correct': 0}
    }
    
    for entry in case_analytics:
        cid = entry.get('case_id')
        result = entry.get('case_result', {})
        
        q_data = q_map.get(cid)
        if not q_data:
            continue
        
        is_correct = result.get('is_correct', False)
        components = q_data.get('componentes_conhecimento', ['Geral'])
        difficulty = q_data.get('dificuldade', 'básico')
        
        # Análise por componente
        for comp in components:
            if comp not in component_performance:
                component_performance[comp] = {'total': 0, 'correct': 0}
            component_performance[comp]['total'] += 1
            if is_correct:
                component_performance[comp]['correct'] += 1
        
        # Análise por dificuldade
        if difficulty in difficulty_performance:
            difficulty_performance[difficulty]['total'] += 1
            if is_correct:
                difficulty_performance[difficulty]['correct'] += 1
    
    # Identifica componente mais difícil
    worst_component = None
    worst_accuracy = 100
    
    for comp, data in component_performance.items():
        if data['total'] >= 2:  # Mínimo de 2 questões para considerar
            accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            if accuracy < worst_accuracy:
                worst_accuracy = accuracy
                worst_component = {
                    'nome': comp,
                    'acuracia': accuracy,
                    'total': data['total'],
                    'acertos': data['correct']
                }
    
    # Identifica nível mais difícil
    worst_difficulty = None
    worst_diff_accuracy = 100
    
    for diff, data in difficulty_performance.items():
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total'] * 100)
            if accuracy < worst_diff_accuracy:
                worst_diff_accuracy = accuracy
                worst_difficulty = {
                    'nivel': diff,
                    'acuracia': accuracy,
                    'total': data['total'],
                    'acertos': data['correct']
                }
    
    # Identifica componentes problemáticos (acurácia < 50%)
    problematic_components = []
    for comp, data in component_performance.items():
        if data['total'] >= 2:
            accuracy = (data['correct'] / data['total'] * 100)
            if accuracy < 50:
                problematic_components.append({
                    'nome': comp,
                    'acuracia': accuracy,
                    'total': data['total'],
                    'acertos': data['correct']
                })
    
    # Ordena por acurácia (pior primeiro)
    problematic_components.sort(key=lambda x: x['acuracia'])
    
    # Identifica padrões de erro
    error_patterns = []
    
    # Padrão 1: Sempre erra questões avançadas
    if difficulty_performance['avançado']['total'] >= 2:
        adv_accuracy = (difficulty_performance['avançado']['correct'] / 
                       difficulty_performance['avançado']['total'] * 100)
        if adv_accuracy < 30:
            error_patterns.append({
                'padrao': 'Dificuldade com questões avançadas',
                'descricao': f'Taxa de acerto em questões avançadas: {adv_accuracy:.1f}%'
            })
    
    # Padrão 2: Componente específico sempre problemático
    if worst_component and worst_component['acuracia'] < 30:
        error_patterns.append({
            'padrao': f'Dificuldade consistente em {worst_component["nome"]}',
            'descricao': f'Taxa de acerto: {worst_component["acuracia"]:.1f}%'
        })
    
    return {
        'componente_mais_dificil': worst_component,
        'nivel_mais_dificil': worst_difficulty,
        'componentes_problematicos': problematic_components,
        'padroes_erro': error_patterns
    }

def get_student_complete_profile(user_id: str) -> Dict[str, Any]:
    """
    Perfil completo do aluno incluindo:
    - Todas as estatísticas existentes
    - Análise de fraquezas
    - Histórico temporal de evolução
    - Comparação com a média da turma
    """
    # Estatísticas básicas
    detailed_stats = get_user_detailed_stats(user_id)
    advanced_stats = get_student_advanced_stats(user_id)
    weakness_analysis = get_student_weakness_analysis(user_id)
    
    # Estatísticas globais para comparação
    global_stats = get_global_stats()
    
    # Calcula comparação com média da turma
    user_accuracy = detailed_stats['case_stats']['accuracy_rate']
    class_avg_accuracy = global_stats['average_accuracy_rate']
    
    performance_vs_class = 'acima' if user_accuracy > class_avg_accuracy else 'abaixo' if user_accuracy < class_avg_accuracy else 'igual'
    difference = abs(user_accuracy - class_avg_accuracy)
    
    # Evolução temporal (últimos 30 dias)
    case_analytics = get_user_case_analytics(user_id)
    
    # Agrupa por semana
    weekly_performance = {}
    now = datetime.now()
    
    for entry in case_analytics:
        timestamp = entry.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Garante timezone-naive
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
        if hasattr(now, 'tzinfo') and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        # Verifica se é dos últimos 30 dias
        try:
            days_ago = (now - timestamp).days
            if days_ago <= 30:
                week = f'Semana {days_ago // 7 + 1}'
                if week not in weekly_performance:
                    weekly_performance[week] = {'total': 0, 'correct': 0}
                
                weekly_performance[week]['total'] += 1
                result = entry.get('case_result', {})
                if result.get('is_correct', False):
                    weekly_performance[week]['correct'] += 1
        except (TypeError, ValueError):
            continue
    
    # Calcula tendência (melhorando/piorando/estável)
    trend = 'estável'
    if len(weekly_performance) >= 2:
        weeks = sorted(weekly_performance.keys())
        first_week_acc = (weekly_performance[weeks[0]]['correct'] / 
                         weekly_performance[weeks[0]]['total'] * 100) if weekly_performance[weeks[0]]['total'] > 0 else 0
        last_week_acc = (weekly_performance[weeks[-1]]['correct'] / 
                        weekly_performance[weeks[-1]]['total'] * 100) if weekly_performance[weeks[-1]]['total'] > 0 else 0
        
        if last_week_acc > first_week_acc + 10:
            trend = 'melhorando'
        elif last_week_acc < first_week_acc - 10:
            trend = 'piorando'
    
    return {
        'estatisticas_basicas': detailed_stats,
        'estatisticas_avancadas': advanced_stats,
        'analise_fraquezas': weakness_analysis,
        'comparacao_turma': {
            'acuracia_aluno': user_accuracy,
            'acuracia_turma': class_avg_accuracy,
            'performance': performance_vs_class,
            'diferenca': difference
        },
        'evolucao_temporal': {
            'desempenho_semanal': weekly_performance,
            'tendencia': trend
        }
    }

