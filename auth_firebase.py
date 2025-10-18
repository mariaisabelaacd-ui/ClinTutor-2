import hashlib
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from firebase_config import get_firestore_db, is_firebase_connected
import json
import os

# Configurações do banco de dados local (fallback)
USERS_DB_PATH = os.path.join(os.path.expanduser("~"), ".clintutor", "users.json")

def init_users_db():
    """Inicializa o banco de dados local se não existir (fallback)"""
    os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
    if not os.path.exists(USERS_DB_PATH):
        with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_users_local() -> List[Dict]:
    """Carrega usuários do banco local (fallback)"""
    init_users_db()
    try:
        with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_users_local(users: List[Dict]):
    """Salva usuários no banco local (fallback)"""
    try:
        with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erro ao salvar usuários localmente: {e}")

def hash_password(password: str) -> str:
    """Cria hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Valida formato do email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_email_domain(email: str) -> Tuple[bool, str]:
    """
    Valida se o email pertence aos domínios permitidos da Santa Casa
    Retorna: (is_valid, user_type)
    """
    if not email or '@' not in email:
        return False, ""
    
    domain = email.split('@')[1].lower()
    
    # Domínios permitidos
    allowed_domains = {
        'professor': 'fcmsantacasasp.edu.br',
        'aluno': 'aluno.fcmsantacasasp.edu.br'
    }
    
    if domain == allowed_domains['professor']:
        return True, 'professor'
    elif domain == allowed_domains['aluno']:
        return True, 'aluno'
    else:
        return False, ""

def email_exists_firebase(email: str) -> bool:
    """Verifica se email já está cadastrado no Firebase"""
    if not is_firebase_connected():
        return False
    
    try:
        db = get_firestore_db()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email.lower().strip()).limit(1)
        docs = query.get()
        return len(docs) > 0
    except Exception as e:
        st.error(f"Erro ao verificar email no Firebase: {e}")
        return False

def email_exists_local(email: str) -> bool:
    """Verifica se email já está cadastrado no banco local"""
    users = load_users_local()
    return any(user["email"].lower() == email.lower() for user in users)

def email_exists(email: str) -> bool:
    """Verifica se email já está cadastrado (Firebase ou local)"""
    if is_firebase_connected():
        return email_exists_firebase(email)
    else:
        return email_exists_local(email)

def register_user_firebase(name: str, email: str, password: str, user_type: str, ra: str = None) -> Tuple[bool, str]:
    """Registra usuário no Firebase"""
    try:
        db = get_firestore_db()
        users_ref = db.collection('users')
        
        # Validação do tipo de usuário
        if user_type not in ["aluno", "professor", "admin"]:
            return False, "Tipo de usuário inválido"
        
        # Cria novo usuário
        user_data = {
            'name': name.strip(),
            'email': email.lower().strip(),
            'password': hash_password(password),
            'user_type': user_type,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        # Adiciona RA se for aluno
        if user_type == "aluno" and ra:
            user_data['ra'] = ra.strip()
        
        # Adiciona ao Firestore e captura o ID do documento
        doc_ref = users_ref.add(user_data)
        doc_id = doc_ref[1].id  # O ID do documento criado
        
        return True, f"Usuário cadastrado com sucesso no Firebase! ID: {doc_id}"
        
    except Exception as e:
        return False, f"Erro ao cadastrar no Firebase: {e}"

def register_user_local(name: str, email: str, password: str, user_type: str, ra: str = None) -> Tuple[bool, str]:
    """Registra usuário no banco local"""
    new_user = {
        "id": len(load_users_local()) + 1,
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hash_password(password),
        "user_type": user_type,
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    # Adiciona RA se for aluno
    if user_type == "aluno" and ra:
        new_user['ra'] = ra.strip()
    
    users = load_users_local()
    users.append(new_user)
    save_users_local(users)
    
    return True, "Usuário cadastrado com sucesso localmente!"

def register_user(name: str, email: str, password: str, user_type: str, ra: str = None, verification_code: str = None) -> Tuple[bool, str]:
    """Registra um novo usuário (Firebase ou local) com verificação de email"""
    # Validações
    if not name.strip():
        return False, "Nome é obrigatório"
    
    if not email.strip():
        return False, "Email é obrigatório"
    
    if not validate_email(email):
        return False, "Formato de email inválido"
    
    # Validação de domínio
    is_valid_domain, detected_user_type = validate_email_domain(email)
    if not is_valid_domain:
        return False, "❌ Email não permitido! Use apenas emails da Santa Casa:\n• Professores: @fcmsantacasasp.edu.br\n• Alunos: @aluno.fcmsantacasasp.edu.br"
    
    # Verifica se o tipo de usuário corresponde ao domínio
    if user_type != detected_user_type:
        return False, f"❌ Tipo de usuário incorreto! Email {email} deve ser registrado como {detected_user_type}"
    
    # Verificação de código (se fornecido)
    if verification_code:
        from email_auth_system import get_email_auth_system
        email_auth = get_email_auth_system()
        success, message = email_auth.verify_code(email, verification_code)
        if not success:
            return False, f"❌ Código de verificação inválido: {message}"
    
    if email_exists(email):
        return False, "Email já está cadastrado"
    
    if not password.strip():
        return False, "Senha é obrigatória"
    
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    
    if user_type not in ["professor", "aluno"]:
        return False, "Tipo de usuário inválido"
    
    # Validação específica para alunos
    if user_type == "aluno" and (not ra or not ra.strip()):
        return False, "RA é obrigatório para alunos"
    
    # Tenta Firebase primeiro, depois local
    if is_firebase_connected():
        return register_user_firebase(name, email, password, user_type, ra)
    else:
        return register_user_local(name, email, password, user_type, ra)

def authenticate_user_firebase(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Autentica usuário no Firebase"""
    try:
        db = get_firestore_db()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email.lower().strip()).limit(1)
        docs = query.get()
        
        if not docs:
            return False, "Email ou senha incorretos", None
        
        user_doc = docs[0]
        user_data = user_doc.to_dict()
        
        if user_data['password'] != hash_password(password):
            return False, "Email ou senha incorretos", None
        
        # Atualiza último login
        user_doc.reference.update({'last_login': datetime.now()})
        
        # Adiciona ID do documento
        user_data['id'] = user_doc.id
        
        return True, "Login realizado com sucesso!", user_data
        
    except Exception as e:
        return False, f"Erro ao autenticar no Firebase: {e}", None

def authenticate_user_local(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Autentica usuário no banco local"""
    users = load_users_local()
    hashed_password = hash_password(password)
    
    for user in users:
        if user["email"].lower() == email.lower() and user["password"] == hashed_password:
            # Atualiza último login
            user["last_login"] = datetime.now().isoformat()
            save_users_local(users)
            return True, "Login realizado com sucesso!", user
    
    return False, "Email ou senha incorretos", None

def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Autentica um usuário (Firebase ou local)"""
    if not email.strip() or not password.strip():
        return False, "Email e senha são obrigatórios", None
    
    if is_firebase_connected():
        return authenticate_user_firebase(email, password)
    else:
        return authenticate_user_local(email, password)

def get_user_by_id_firebase(user_id: str) -> Optional[Dict]:
    """Busca usuário por ID no Firebase"""
    try:
        db = get_firestore_db()
        user_doc = db.collection('users').document(user_id).get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['id'] = user_doc.id
            return user_data
        return None
    except Exception:
        return None

def get_user_by_id_local(user_id: int) -> Optional[Dict]:
    """Busca usuário por ID no banco local"""
    users = load_users_local()
    for user in users:
        if user["id"] == user_id:
            return user
    return None

def get_user_by_id(user_id) -> Optional[Dict]:
    """Busca usuário por ID (Firebase ou local)"""
    if is_firebase_connected():
        return get_user_by_id_firebase(str(user_id))
    else:
        return get_user_by_id_local(int(user_id))

def get_all_users_firebase() -> List[Dict]:
    """Retorna todos os usuários do Firebase"""
    try:
        db = get_firestore_db()
        users_ref = db.collection('users')
        docs = users_ref.get()
        
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            users.append(user_data)
        
        return users
    except Exception as e:
        st.error(f"Erro ao buscar usuários no Firebase: {e}")
        return []

def get_all_users_local() -> List[Dict]:
    """Retorna todos os usuários do banco local"""
    return load_users_local()

def get_all_users() -> List[Dict]:
    """Retorna lista de todos os usuários (Firebase ou local)"""
    if is_firebase_connected():
        return get_all_users_firebase()
    else:
        return get_all_users_local()

def delete_user_firebase(user_id: str) -> Tuple[bool, str]:
    """Remove usuário do Firebase"""
    try:
        db = get_firestore_db()
        db.collection('users').document(user_id).delete()
        return True, "Usuário removido do Firebase!"
    except Exception as e:
        return False, f"Erro ao remover usuário do Firebase: {e}"

def delete_user_local(user_id: int) -> Tuple[bool, str]:
    """Remove usuário do banco local"""
    users = load_users_local()
    users = [user for user in users if user["id"] != user_id]
    save_users_local(users)
    return True, "Usuário removido com sucesso!"

def delete_user(user_id) -> Tuple[bool, str]:
    """Remove usuário (Firebase ou local)"""
    if is_firebase_connected():
        return delete_user_firebase(str(user_id))
    else:
        return delete_user_local(int(user_id))

def update_user_profile_firebase(user_id: str, name: str = None, email: str = None) -> Tuple[bool, str]:
    """Atualiza perfil do usuário no Firebase"""
    try:
        db = get_firestore_db()
        user_ref = db.collection('users').document(user_id)
        
        update_data = {}
        if name:
            update_data['name'] = name.strip()
        if email:
            update_data['email'] = email.lower().strip()
        
        if update_data:
            user_ref.update(update_data)
        
        return True, "Perfil atualizado com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar perfil no Firebase: {e}"

def update_user_profile_local(user_id: int, name: str = None, email: str = None) -> Tuple[bool, str]:
    """Atualiza perfil do usuário no banco local"""
    users = load_users_local()
    user_index = None
    
    for i, user in enumerate(users):
        if user["id"] == user_id:
            user_index = i
            break
    
    if user_index is None:
        return False, "Usuário não encontrado"
    
    if name:
        users[user_index]["name"] = name.strip()
    if email:
        users[user_index]["email"] = email.lower().strip()
    
    save_users_local(users)
    return True, "Perfil atualizado com sucesso!"

def update_user_profile(user_id, name: str = None, email: str = None) -> Tuple[bool, str]:
    """Atualiza perfil do usuário (Firebase ou local)"""
    if is_firebase_connected():
        return update_user_profile_firebase(str(user_id), name, email)
    else:
        return update_user_profile_local(int(user_id), name, email)

def change_password_firebase(user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Altera senha do usuário no Firebase"""
    try:
        db = get_firestore_db()
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists:
            return False, "Usuário não encontrado"
        
        user_data = user_doc.to_dict()
        
        if user_data['password'] != hash_password(current_password):
            return False, "Senha atual incorreta"
        
        if len(new_password) < 6:
            return False, "Nova senha deve ter pelo menos 6 caracteres"
        
        user_doc.reference.update({'password': hash_password(new_password)})
        return True, "Senha alterada com sucesso!"
        
    except Exception as e:
        return False, f"Erro ao alterar senha no Firebase: {e}"

def change_password_local(user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Altera senha do usuário no banco local"""
    users = load_users_local()
    user_index = None
    
    for i, user in enumerate(users):
        if user["id"] == user_id:
            user_index = i
            break
    
    if user_index is None:
        return False, "Usuário não encontrado"
    
    if users[user_index]["password"] != hash_password(current_password):
        return False, "Senha atual incorreta"
    
    if len(new_password) < 6:
        return False, "Nova senha deve ter pelo menos 6 caracteres"
    
    users[user_index]["password"] = hash_password(new_password)
    save_users_local(users)
    
    return True, "Senha alterada com sucesso!"

def change_password(user_id, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Altera senha do usuário (Firebase ou local)"""
    if is_firebase_connected():
        return change_password_firebase(str(user_id), current_password, new_password)
    else:
        return change_password_local(int(user_id), current_password, new_password)

# Funções de sessão do Streamlit (mantidas iguais)
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

def migrate_local_to_firebase():
    """Migra dados locais para Firebase"""
    if not is_firebase_connected():
        return False, "Firebase não está conectado"
    
    try:
        local_users = load_users_local()
        if not local_users:
            return True, "Nenhum usuário local para migrar"
        
        db = get_firestore_db()
        users_ref = db.collection('users')
        
        migrated_count = 0
        for user in local_users:
            # Remove campos específicos do formato local
            user_data = {
                'name': user['name'],
                'email': user['email'],
                'password': user['password'],
                'user_type': user['user_type'],
                'created_at': datetime.fromisoformat(user['created_at']),
                'last_login': datetime.fromisoformat(user['last_login']) if user.get('last_login') else None
            }
            
            users_ref.add(user_data)
            migrated_count += 1
        
        return True, f"Migração concluída! {migrated_count} usuários migrados para o Firebase."
        
    except Exception as e:
        return False, f"Erro na migração: {e}"

def create_default_admin():
    """Cria o administrador padrão se não existir"""
    try:
        # Verifica se já existe um admin
        if is_firebase_connected():
            db = get_firestore_db()
            admin_query = db.collection('users').where('user_type', '==', 'admin').limit(1).get()
            if admin_query:
                return True, "Administrador já existe"
        else:
            # Verifica localmente também
            users = load_users_local()
            if any(user.get('user_type') == 'admin' for user in users):
                return True, "Administrador já existe"
        
        # Cria o admin padrão
        admin_data = {
            'name': 'Administrador',
            'email': 'admin@biotutor.com',
            'password': hash_password('admin123'),
            'user_type': 'admin',
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        if is_firebase_connected():
            db = get_firestore_db()
            users_ref = db.collection('users')
            doc_ref = users_ref.add(admin_data)
            return True, f"Administrador criado! Login: admin@biotutor.com | Senha: admin123"
        else:
            # Salva localmente se Firebase não estiver conectado
            users = load_users_local()
            admin_data['id'] = len(users) + 1
            users.append(admin_data)
            save_users_local(users)
            return True, f"Administrador criado localmente! Login: admin@biotutor.com | Senha: admin123"
            
    except Exception as e:
        return False, f"Erro ao criar administrador: {e}"
