# 🚀 Deploy no Streamlit Cloud - BioTutor

## 📋 Pré-requisitos
1. Repositório no GitHub (✅ já feito)
2. Conta no Streamlit Cloud
3. Firebase configurado

## 🔧 Configuração do Streamlit Cloud

### 1. Acesse o Streamlit Cloud
- Vá para: https://share.streamlit.io/
- Faça login com sua conta GitHub

### 2. Conecte o Repositório
- Clique em "New app"
- Selecione: `mariaisabelaacd-ui/ClinTutor-2`
- Branch: `main`
- Main file path: `app.py`

### 3. Configure as Variáveis de Ambiente
No Streamlit Cloud, adicione estas variáveis:

```
FIREBASE_PROJECT_ID=seu-projeto-id
FIREBASE_PRIVATE_KEY_ID=sua-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nsua-chave-privada\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=seu-service-account@seu-projeto.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=seu-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/seu-service-account%40seu-projeto.iam.gserviceaccount.com
```

### 4. Atualize o firebase_config.py
```python
import os
import json
from firebase_admin import credentials, initialize_app, firestore

def get_firebase_credentials():
    """Obtém credenciais do Firebase a partir de variáveis de ambiente"""
    try:
        # Para Streamlit Cloud - usar variáveis de ambiente
        if os.getenv('FIREBASE_PROJECT_ID'):
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
            return credentials.Certificate(cred_dict)
        
        # Fallback para arquivo local
        if os.path.exists('firebase-credentials.json'):
            return credentials.Certificate('firebase-credentials.json')
        
        return None
    except Exception as e:
        print(f"Erro ao obter credenciais: {e}")
        return None
```

## 🔒 Segurança
- ✅ Credenciais não ficam no código
- ✅ Variáveis de ambiente seguras
- ✅ Firebase protegido

## 📱 URL Final
Após o deploy: `https://seu-app-name.streamlit.app`

## 🎯 Para Iniciação Científica
- Compartilhe o link com os participantes
- Todos podem testar sem instalar nada
- Dados salvos no Firebase
- Analytics funcionando
