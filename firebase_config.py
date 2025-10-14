import os
import json
import streamlit as st
from firebase_admin import credentials, firestore, initialize_app, get_app
from typing import Optional

class FirebaseConfig:
    """Classe para gerenciar configuração do Firebase"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.db = None
            self.app = None
            self._initialize_firebase()
            FirebaseConfig._initialized = True
    
    def _initialize_firebase(self):
        """Inicializa conexão com Firebase"""
        try:
            # Verifica se já existe um app Firebase inicializado
            try:
                self.app = get_app()
                self.db = firestore.client()
                st.info("🔄 Firebase já estava inicializado")
                return  # Já está inicializado
            except ValueError:
                pass  # App não existe, continua com a inicialização
            
            # Debug: Verifica qual método de credenciais está sendo usado
            st.info("🔍 Verificando credenciais do Firebase...")
            
            # Tenta carregar credenciais do Streamlit secrets (Streamlit Cloud)
            if 'firebase_credentials' in st.secrets:
                st.info("✅ Usando credenciais do Streamlit Secrets")
                cred_dict = dict(st.secrets['firebase_credentials'])  # Cria uma cópia
                
                # Corrige a chave privada se necessário
                if 'private_key' in cred_dict and isinstance(cred_dict['private_key'], str):
                    # Garante que as quebras de linha estão corretas
                    cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
                
                cred = credentials.Certificate(cred_dict)
            # Tenta carregar credenciais de variáveis de ambiente (Streamlit Cloud)
            elif os.getenv('FIREBASE_PROJECT_ID'):
                st.info("✅ Usando credenciais de variáveis de ambiente")
                cred_dict = {
                    "type": "service_account",
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
                    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
                    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
                    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
                }
                cred = credentials.Certificate(cred_dict)
            else:
                # Fallback para arquivo local
                st.info("⚠️ Usando arquivo local (modo offline)")
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    st.error("""
                    🔥 **Configuração do Firebase necessária!**
                    
                    Para usar o Firebase, você precisa:
                    
                    1. **Criar um projeto no Firebase Console** (https://console.firebase.google.com)
                    2. **Habilitar Firestore Database**
                    3. **Gerar uma chave de serviço** (Service Account Key)
                    4. **Configurar as credenciais** de uma das formas:
                    
                    **Opção A - Arquivo local:**
                    - Salve o arquivo JSON da chave como `firebase-credentials.json` na pasta do projeto
                    
                    **Opção B - Streamlit Secrets (Streamlit Cloud):**
                    - Adicione as credenciais em `.streamlit/secrets.toml`:
                    ```toml
                    [firebase_credentials]
                    type = "service_account"
                    project_id = "seu-projeto-id"
                    private_key_id = "sua-private-key-id"
                    private_key = "sua-private-key"
                    client_email = "seu-client-email"
                    client_id = "seu-client-id"
                    auth_uri = "https://accounts.google.com/o/oauth2/auth"
                    token_uri = "https://oauth2.googleapis.com/token"
                    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
                    client_x509_cert_url = "sua-cert-url"
                    ```
                    
                    **Opção C - Variáveis de Ambiente (Streamlit Cloud):**
                    - Configure as variáveis no painel do Streamlit Cloud
                    """)
                    return
            
            # Inicializa o app Firebase
            self.app = initialize_app(cred)
            self.db = firestore.client()
            
            st.success("✅ Firebase conectado com sucesso!")
            
        except Exception as e:
            if "already exists" not in str(e):
                st.error(f"❌ Erro ao conectar com Firebase: {e}")
                st.info("💡 Verifique se as credenciais estão configuradas corretamente.")
            else:
                # Firebase já foi inicializado, apenas conecta
                try:
                    self.app = get_app()
                    self.db = firestore.client()
                except Exception as e2:
                    st.error(f"❌ Erro ao conectar com Firebase: {e2}")
    
    def get_database(self):
        """Retorna instância do Firestore"""
        return self.db
    
    def is_connected(self) -> bool:
        """Verifica se está conectado ao Firebase"""
        return self.db is not None

# Instância global do Firebase
firebase_config = FirebaseConfig()

def get_firestore_db():
    """Retorna instância do Firestore ou None se não conectado"""
    return firebase_config.get_database()

def is_firebase_connected() -> bool:
    """Verifica se Firebase está conectado"""
    return firebase_config.is_connected()

def test_firebase_connection():
    """Testa conexão com Firebase"""
    if not is_firebase_connected():
        return False, "Firebase não está conectado"
    
    try:
        db = get_firestore_db()
        # Tenta fazer uma operação simples
        test_doc = db.collection('test').document('connection')
        test_doc.set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
        test_doc.delete()
        return True, "Conexão com Firebase funcionando!"
    except Exception as e:
        return False, f"Erro na conexão: {e}"
