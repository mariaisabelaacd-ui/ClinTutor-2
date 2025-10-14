#!/usr/bin/env python3
"""
Script para debug das credenciais do Streamlit Cloud
"""

import os
import sys

def debug_streamlit_secrets():
    """Debug das credenciais do Streamlit"""
    
    print("=== DEBUG STREAMLIT SECRETS ===")
    print()
    
    # 1. Verificar se estamos no Streamlit Cloud
    print("1. Verificando ambiente Streamlit Cloud...")
    if os.getenv('STREAMLIT_SERVER_PORT'):
        print(f"   ✅ STREAMLIT_SERVER_PORT: {os.getenv('STREAMLIT_SERVER_PORT')}")
    else:
        print("   ❌ STREAMLIT_SERVER_PORT não definido")
    
    if os.getenv('STREAMLIT_SERVER_ADDRESS'):
        print(f"   ✅ STREAMLIT_SERVER_ADDRESS: {os.getenv('STREAMLIT_SERVER_ADDRESS')}")
    else:
        print("   ❌ STREAMLIT_SERVER_ADDRESS não definido")
    
    print()
    
    # 2. Verificar se o módulo streamlit está disponível
    print("2. Verificando módulo streamlit...")
    try:
        import streamlit as st
        print("   ✅ Streamlit importado com sucesso")
        print(f"   📦 Versão: {st.__version__}")
    except ImportError as e:
        print(f"   ❌ Erro ao importar streamlit: {e}")
        return
    
    print()
    
    # 3. Verificar secrets do Streamlit
    print("3. Verificando secrets do Streamlit...")
    try:
        # Tenta acessar os secrets
        if hasattr(st, 'secrets'):
            print("   ✅ st.secrets disponível")
            
            # Lista todos os secrets disponíveis
            if hasattr(st.secrets, '_secrets'):
                print(f"   📋 Secrets disponíveis: {list(st.secrets._secrets.keys())}")
            else:
                print("   📋 Secrets disponíveis: (não conseguiu listar)")
            
            # Verifica especificamente firebase_credentials
            if 'firebase_credentials' in st.secrets:
                print("   ✅ firebase_credentials encontrado!")
                cred = st.secrets['firebase_credentials']
                print(f"   📋 Chaves: {list(cred.keys())}")
                print(f"   🆔 Project ID: {cred.get('project_id', 'N/A')}")
                print(f"   📧 Client Email: {cred.get('client_email', 'N/A')}")
            else:
                print("   ❌ firebase_credentials NÃO encontrado")
                
            # Verifica google_api
            if 'google_api' in st.secrets:
                print("   ✅ google_api encontrado!")
                api_key = st.secrets['google_api']
                if 'api_key' in api_key:
                    print(f"   🔑 API Key: {api_key['api_key'][:10]}...")
                else:
                    print("   ❌ api_key não encontrado em google_api")
            else:
                print("   ❌ google_api NÃO encontrado")
                
        else:
            print("   ❌ st.secrets não disponível")
            
    except Exception as e:
        print(f"   ❌ Erro ao acessar secrets: {e}")
    
    print()
    
    # 4. Verificar variáveis de ambiente
    print("4. Verificando variáveis de ambiente...")
    env_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY_ID', 
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_CLIENT_ID',
        'FIREBASE_AUTH_URI',
        'FIREBASE_TOKEN_URI',
        'FIREBASE_AUTH_PROVIDER_X509_CERT_URL',
        'FIREBASE_CLIENT_X509_CERT_URL'
    ]
    
    found_env_vars = 0
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:20]}...")
            found_env_vars += 1
        else:
            print(f"   ❌ {var}: não definida")
    
    print(f"   📊 Variáveis encontradas: {found_env_vars}/{len(env_vars)}")
    
    print()
    
    # 5. Verificar arquivo local
    print("5. Verificando arquivo local...")
    cred_path = 'firebase-credentials.json'
    if os.path.exists(cred_path):
        print(f"   ✅ Arquivo local encontrado: {cred_path}")
        try:
            import json
            with open(cred_path, 'r') as f:
                cred_data = json.load(f)
            print(f"   🆔 Project ID: {cred_data.get('project_id', 'N/A')}")
            print(f"   📧 Client Email: {cred_data.get('client_email', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")
    else:
        print(f"   ❌ Arquivo local não encontrado: {cred_path}")
    
    print()
    print("=== FIM DO DEBUG ===")

if __name__ == "__main__":
    debug_streamlit_secrets()
