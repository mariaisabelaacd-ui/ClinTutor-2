import json
import os
import hashlib
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configurações do banco de dados de usuários
USERS_DB_PATH = os.path.join(os.path.expanduser("~"), ".clintutor", "users.json")

def init_users_db():
    """Inicializa o banco de dados de usuários se não existir"""
    os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
    if not os.path.exists(USERS_DB_PATH):
        with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_users() -> List[Dict]:
    """Carrega a lista de usuários do banco de dados"""
    init_users_db()
    try:
        with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_users(users: List[Dict]):
    """Salva a lista de usuários no banco de dados"""
    try:
        with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")

def hash_password(password: str) -> str:
    """Cria hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Valida formato do email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def email_exists(email: str) -> bool:
    """Verifica se email já está cadastrado"""
    users = load_users()
    return any(user["email"].lower() == email.lower() for user in users)

def register_user(name: str, email: str, password: str, user_type: str) -> Tuple[bool, str]:
    """
    Registra um novo usuário
    Retorna (sucesso, mensagem)
    """
    # Validações
    if not name.strip():
        return False, "Nome é obrigatório"
    
    if not email.strip():
        return False, "Email é obrigatório"
    
    if not validate_email(email):
        return False, "Formato de email inválido"
    
    if email_exists(email):
        return False, "Email já está cadastrado"
    
    if not password.strip():
        return False, "Senha é obrigatória"
    
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    
    if user_type not in ["professor", "aluno"]:
        return False, "Tipo de usuário inválido"
    
    # Cria novo usuário
    new_user = {
        "id": len(load_users()) + 1,
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hash_password(password),
        "user_type": user_type,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    # Salva no banco
    users = load_users()
    users.append(new_user)
    save_users(users)
    
    return True, "Usuário cadastrado com sucesso!"

def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Autentica um usuário
    Retorna (sucesso, mensagem, dados_do_usuário)
    """
    if not email.strip() or not password.strip():
        return False, "Email e senha são obrigatórios", None
    
    users = load_users()
    hashed_password = hash_password(password)
    
    for user in users:
        if user["email"].lower() == email.lower() and user["password"] == hashed_password:
            # Atualiza último login
            user["last_login"] = datetime.now().isoformat()
            save_users(users)
            return True, "Login realizado com sucesso!", user
    
    return False, "Email ou senha incorretos", None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Busca usuário por ID"""
    users = load_users()
    for user in users:
        if user["id"] == user_id:
            return user
    return None

def update_user_profile(user_id: int, name: str = None, email: str = None) -> Tuple[bool, str]:
    """
    Atualiza perfil do usuário
    Retorna (sucesso, mensagem)
    """
    users = load_users()
    user_index = None
    
    for i, user in enumerate(users):
        if user["id"] == user_id:
            user_index = i
            break
    
    if user_index is None:
        return False, "Usuário não encontrado"
    
    # Validações
    if email and email != users[user_index]["email"]:
        if not validate_email(email):
            return False, "Formato de email inválido"
        if email_exists(email):
            return False, "Email já está cadastrado"
        users[user_index]["email"] = email.lower().strip()
    
    if name:
        if not name.strip():
            return False, "Nome é obrigatório"
        users[user_index]["name"] = name.strip()
    
    save_users(users)
    return True, "Perfil atualizado com sucesso!"

def change_password(user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Altera senha do usuário
    Retorna (sucesso, mensagem)
    """
    users = load_users()
    user_index = None
    
    for i, user in enumerate(users):
        if user["id"] == user_id:
            user_index = i
            break
    
    if user_index is None:
        return False, "Usuário não encontrado"
    
    # Verifica senha atual
    if user["password"] != hash_password(current_password):
        return False, "Senha atual incorreta"
    
    # Valida nova senha
    if not new_password.strip():
        return False, "Nova senha é obrigatória"
    
    if len(new_password) < 6:
        return False, "Nova senha deve ter pelo menos 6 caracteres"
    
    # Atualiza senha
    users[user_index]["password"] = hash_password(new_password)
    save_users(users)
    
    return True, "Senha alterada com sucesso!"

def get_all_users() -> List[Dict]:
    """Retorna lista de todos os usuários (apenas para professores)"""
    return load_users()

def delete_user(user_id: int) -> Tuple[bool, str]:
    """
    Remove usuário (apenas para administradores)
    Retorna (sucesso, mensagem)
    """
    users = load_users()
    users = [user for user in users if user["id"] != user_id]
    save_users(users)
    return True, "Usuário removido com sucesso!"

# Funções de sessão do Streamlit
def init_session():
    """Inicializa variáveis de sessão"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_type" not in st.session_state:
        st.session_state.user_type = None
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False

def login_user(user_data: Dict):
    """Define dados do usuário na sessão"""
    st.session_state.user_id = user_data["id"]
    st.session_state.user_name = user_data["name"]
    st.session_state.user_email = user_data["email"]
    st.session_state.user_type = user_data["user_type"]
    st.session_state.is_logged_in = True

def logout_user():
    """Remove dados do usuário da sessão"""
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.user_type = None
    st.session_state.is_logged_in = False

def is_logged_in() -> bool:
    """Verifica se usuário está logado"""
    return st.session_state.get("is_logged_in", False)

def get_current_user() -> Optional[Dict]:
    """Retorna dados do usuário atual"""
    if not is_logged_in():
        return None
    
    return {
        "id": st.session_state.user_id,
        "name": st.session_state.user_name,
        "email": st.session_state.user_email,
        "user_type": st.session_state.user_type
    }

def require_login():
    """Decorador para verificar se usuário está logado"""
    if not is_logged_in():
        st.error("Você precisa fazer login para acessar esta página.")
        st.stop()

def require_professor():
    """Verifica se usuário é professor"""
    require_login()
    if st.session_state.user_type != "professor":
        st.error("Acesso restrito a professores.")
        st.stop()
