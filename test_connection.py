#!/usr/bin/env python3
"""
Script para testar conexão com Firebase
"""

import os
import sys
import json

def test_firebase_connection():
    """Testa diferentes métodos de conexão com Firebase"""
    
    print("Testando conexao com Firebase...")
    print("=" * 50)
    
    # 1. Verificar se existe arquivo de credenciais local
    print("\n1. Verificando arquivo local...")
    cred_path = 'firebase-credentials.json'
    if os.path.exists(cred_path):
        print(f"OK - Arquivo encontrado: {cred_path}")
        try:
            with open(cred_path, 'r') as f:
                cred_data = json.load(f)
            print(f"OK - Arquivo JSON valido")
            print(f"   - Project ID: {cred_data.get('project_id', 'N/A')}")
            print(f"   - Client Email: {cred_data.get('client_email', 'N/A')}")
        except Exception as e:
            print(f"ERRO - Erro ao ler arquivo: {e}")
    else:
        print(f"ERRO - Arquivo nao encontrado: {cred_path}")
    
    # 2. Verificar variáveis de ambiente
    print("\n2. Verificando variaveis de ambiente...")
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
    
    env_found = 0
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"OK - {var}: {'*' * 20}...")
            env_found += 1
        else:
            print(f"ERRO - {var}: Nao definida")
    
    print(f"\nVariaveis encontradas: {env_found}/{len(env_vars)}")
    
    # 3. Testar importação do Firebase
    print("\n3. Testando importacao do Firebase...")
    try:
        from firebase_admin import credentials, firestore, initialize_app, get_app
        print("OK - Firebase Admin SDK importado com sucesso")
    except ImportError as e:
        print(f"ERRO - Erro ao importar Firebase: {e}")
        return False
    
    # 4. Testar inicialização
    print("\n4. Testando inicializacao do Firebase...")
    try:
        # Verificar se já existe app
        try:
            existing_app = get_app()
            print("OK - App Firebase ja existe")
        except ValueError:
            print("INFO - Nenhum app Firebase existente")
            
            # Tentar inicializar com arquivo local
            if os.path.exists(cred_path):
                print("Tentando inicializar com arquivo local...")
                cred = credentials.Certificate(cred_path)
                app = initialize_app(cred)
                db = firestore.client()
                print("OK - Firebase inicializado com arquivo local!")
                
                # Testar operação
                test_doc = db.collection('test').document('connection')
                test_doc.set({'test': True})
                test_doc.delete()
                print("OK - Teste de operacao no Firestore bem-sucedido!")
                
            else:
                print("ERRO - Nenhum metodo de autenticacao disponivel")
                return False
                
    except Exception as e:
        print(f"ERRO - Erro na inicializacao: {e}")
        return False
    
    print("\nTeste concluido com sucesso!")
    return True

if __name__ == "__main__":
    test_firebase_connection()
