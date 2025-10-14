#!/usr/bin/env python3
"""
Script simples para testar secrets do Streamlit
"""

import streamlit as st

def test_secrets():
    """Testa se os secrets estão funcionando"""
    
    st.title("🔍 Teste de Secrets do Streamlit")
    
    st.write("### Verificando secrets disponíveis...")
    
    try:
        # Lista todos os secrets
        if hasattr(st, 'secrets'):
            st.success("✅ st.secrets está disponível")
            
            # Verifica firebase_credentials
            if 'firebase_credentials' in st.secrets:
                st.success("✅ firebase_credentials encontrado!")
                cred = st.secrets['firebase_credentials']
                st.write("**Chaves disponíveis:**", list(cred.keys()))
                st.write("**Project ID:**", cred.get('project_id', 'N/A'))
                st.write("**Client Email:**", cred.get('client_email', 'N/A'))
            else:
                st.error("❌ firebase_credentials NÃO encontrado")
                
            # Verifica google_api
            if 'google_api' in st.secrets:
                st.success("✅ google_api encontrado!")
                api_key = st.secrets['google_api']
                if 'api_key' in api_key:
                    st.write("**API Key:**", api_key['api_key'][:10] + "...")
                else:
                    st.error("❌ api_key não encontrado em google_api")
            else:
                st.error("❌ google_api NÃO encontrado")
                
        else:
            st.error("❌ st.secrets não disponível")
            
    except Exception as e:
        st.error(f"❌ Erro ao acessar secrets: {e}")
    
    st.write("### Teste de conexão Firebase...")
    
    try:
        from firebase_config import is_firebase_connected
        if is_firebase_connected():
            st.success("✅ Firebase conectado!")
        else:
            st.error("❌ Firebase não conectado")
    except Exception as e:
        st.error(f"❌ Erro ao testar Firebase: {e}")

if __name__ == "__main__":
    test_secrets()
