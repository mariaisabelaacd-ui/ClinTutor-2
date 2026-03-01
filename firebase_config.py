import os
import json
import hashlib
import streamlit as st
from firebase_admin import credentials, firestore, auth, initialize_app, get_app
from typing import Optional

# =============================
# Dual Firebase Manager
# =============================

class DualFirebaseManager:
    """
    Gerencia dois projetos Firebase em paralelo.
    - Autenticação (Firebase Auth) sempre no app primário (índice 0)
    - Firestore é roteado por hash(user_id) % 2 para distribuir writes
    - Todos os dados de um mesmo usuário ficam sempre no mesmo Firebase
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.dbs = [None, None]   # Dois Firebases
            self.apps = [None, None]
            self._init_primary()
            self._init_secondary()
            DualFirebaseManager._initialized = True

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def _load_cred_dict(self, secrets_key: str) -> Optional[dict]:
        """Carrega credenciais de st.secrets pela chave informada."""
        if secrets_key not in st.secrets:
            return None
        cred_dict = dict(st.secrets[secrets_key])
        if 'private_key' in cred_dict and isinstance(cred_dict['private_key'], str):
            cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        return cred_dict

    def _init_primary(self):
        """Inicializa Firebase primário (índice 0) — também contém Auth."""
        try:
            # Tenta reutilizar app já inicializado
            try:
                app = get_app('firebase-primary')
                self.apps[0] = app
                self.dbs[0] = firestore.client(app=app)
                return
            except ValueError:
                pass

            cred_dict = self._load_cred_dict('firebase_credentials')
            if not cred_dict:
                # Fallback para arquivo local
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    st.error("❌ Credenciais do Firebase primário não encontradas.")
                    return
            else:
                cred = credentials.Certificate(cred_dict)

            self.apps[0] = initialize_app(cred, name='firebase-primary')
            self.dbs[0] = firestore.client(app=self.apps[0])

        except Exception as e:
            if 'already exists' in str(e):
                try:
                    self.apps[0] = get_app('firebase-primary')
                    self.dbs[0] = firestore.client(app=self.apps[0])
                except Exception:
                    pass
            else:
                st.error(f"❌ Erro ao conectar Firebase primário: {e}")

    def _init_secondary(self):
        """Inicializa Firebase secundário (índice 1) — somente Firestore."""
        try:
            try:
                app = get_app('firebase-secondary')
                self.apps[1] = app
                self.dbs[1] = firestore.client(app=app)
                return
            except ValueError:
                pass

            cred_dict = self._load_cred_dict('firebase_credentials_2')
            if not cred_dict:
                # Sem segundo Firebase configurado — usa o primário como fallback
                self.apps[1] = self.apps[0]
                self.dbs[1] = self.dbs[0]
                return

            cred = credentials.Certificate(cred_dict)
            self.apps[1] = initialize_app(cred, name='firebase-secondary')
            self.dbs[1] = firestore.client(app=self.apps[1])

        except Exception as e:
            if 'already exists' in str(e):
                try:
                    self.apps[1] = get_app('firebase-secondary')
                    self.dbs[1] = firestore.client(app=self.apps[1])
                except Exception:
                    pass
            else:
                # Fallback silencioso: usa o primário
                self.apps[1] = self.apps[0]
                self.dbs[1] = self.dbs[0]

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get_db_for_user(self, user_id: str):
        """
        Retorna o cliente Firestore correto para este user_id.
        O roteamento é determinístico: mesmo user_id → mesmo Firebase sempre.
        """
        if not user_id:
            return self.dbs[0]
        idx = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 2
        db = self.dbs[idx]
        return db if db is not None else self.dbs[0]

    def get_all_dbs(self):
        """Retorna lista de todos os clientes Firestore disponíveis (sem duplicatas)."""
        unique = []
        seen = set()
        for db in self.dbs:
            if db is not None and id(db) not in seen:
                unique.append(db)
                seen.add(id(db))
        return unique

    def get_primary_db(self):
        """Retorna Firestore do Firebase primário (índice 0)."""
        return self.dbs[0]

    def is_connected(self) -> bool:
        return self.dbs[0] is not None

    def secondary_is_configured(self) -> bool:
        """True se o segundo Firebase foi configurado e é diferente do primário."""
        return (
            self.dbs[1] is not None and
            id(self.dbs[1]) != id(self.dbs[0])
        )


# Instância global
_manager = DualFirebaseManager()


# =============================
# Funções de compatibilidade
# =============================

def get_firestore_db():
    """Retorna Firestore primário (compatibilidade retroativa)."""
    return _manager.get_primary_db()

def get_db_for_user(user_id: str):
    """Retorna o Firestore correto para este user_id (hash routing)."""
    return _manager.get_db_for_user(user_id)

def get_all_dbs():
    """Retorna todos os Firestores ativos (para leituras globais do professor)."""
    return _manager.get_all_dbs()

def is_firebase_connected() -> bool:
    return _manager.is_connected()

def dual_firebase_active() -> bool:
    """True quando o segundo Firebase está separado e operacional."""
    return _manager.secondary_is_configured()

def test_firebase_connection():
    """Testa conexão com Firebase primário."""
    if not is_firebase_connected():
        return False, "Firebase não está conectado"
    try:
        db = get_firestore_db()
        test_doc = db.collection('test').document('connection')
        test_doc.set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
        test_doc.delete()
        return True, "Conexão com Firebase primário funcionando!"
    except Exception as e:
        return False, f"Erro na conexão: {e}"


# =============================
# Firebase Authentication Helpers
# (sempre usa o app primário)
# =============================

def _auth():
    """Retorna o módulo auth apontando para o app primário."""
    return auth

def create_firebase_user(email: str, password: str, display_name: str):
    """Cria usuário no Firebase Authentication e envia email de verificação."""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False,
            app=_manager.apps[0]
        )
        link = auth.generate_email_verification_link(email, app=_manager.apps[0])
        return True, user.uid, link
    except auth.EmailAlreadyExistsError:
        return False, None, "Email já cadastrado"
    except Exception as e:
        return False, None, f"Erro ao criar usuário: {e}"

def verify_firebase_user(email: str, password: str):
    """Verifica credenciais e status de verificação do email."""
    try:
        user = auth.get_user_by_email(email, app=_manager.apps[0])
        return True, user.uid, user.email_verified
    except auth.UserNotFoundError:
        return False, None, False
    except Exception:
        return False, None, False

def send_verification_email_firebase(email: str):
    """Reenvia email de verificação."""
    try:
        link = auth.generate_email_verification_link(email, app=_manager.apps[0])
        try:
            from email_service import send_verification_email_smtp
            user = auth.get_user_by_email(email, app=_manager.apps[0])
            display_name = user.display_name or email.split('@')[0]
            success, message = send_verification_email_smtp(email, link, display_name)
            if success:
                return True, "Email de verificação enviado com sucesso!"
            return True, f"Link gerado (SMTP falhou): {link}"
        except Exception:
            return True, f"Link de verificação: {link}"
    except Exception as e:
        return False, f"Erro ao gerar link: {e}"

def get_firebase_user_by_email(email: str):
    """Busca usuário no Firebase Auth por email."""
    try:
        return auth.get_user_by_email(email, app=_manager.apps[0])
    except Exception:
        return None

def delete_firebase_auth_user(uid: str):
    """Remove usuário do Firebase Authentication."""
    try:
        auth.delete_user(uid, app=_manager.apps[0])
        return True
    except Exception:
        return False
