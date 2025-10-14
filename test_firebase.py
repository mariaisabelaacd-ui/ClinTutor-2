#!/usr/bin/env python3
"""
Script para testar a conexão e operações do Firebase
"""

import sys
import os
from datetime import datetime

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firebase_config import get_firestore_db, is_firebase_connected, test_firebase_connection
from auth_firebase import register_user_firebase, authenticate_user_firebase, get_all_users_firebase

def test_firebase_operations():
    """Testa operações básicas do Firebase"""
    print("Testando Firebase...")
    print("=" * 50)
    
    # Teste 1: Conexão
    print("1. Testando conexão...")
    success, message = test_firebase_connection()
    print(f"   Resultado: {message}")
    
    if not success:
        print("ERRO: Firebase nao esta conectado. Verifique as credenciais.")
        return False
    
    print("SUCESSO: Firebase conectado com sucesso!")
    print()
    
    # Teste 2: Listar usuários existentes
    print("2. Listando usuários existentes...")
    try:
        users = get_all_users_firebase()
        print(f"   Encontrados {len(users)} usuários:")
        for user in users:
            print(f"   - {user.get('name', 'N/A')} ({user.get('email', 'N/A')}) - {user.get('user_type', 'N/A')}")
        print()
    except Exception as e:
        print(f"   ERRO ao listar usuarios: {e}")
        print()
    
    # Teste 3: Registrar usuário de teste
    print("3. Testando registro de usuário...")
    test_email = f"teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}@exemplo.com"
    test_name = "Usuario Teste"
    test_password = "123456"
    test_type = "aluno"
    
    try:
        success, message = register_user_firebase(test_name, test_email, test_password, test_type)
        print(f"   Resultado: {message}")
        
        if success:
            print("SUCESSO: Usuario de teste registrado com sucesso!")
            
            # Teste 4: Autenticar usuário
            print()
            print("4. Testando autenticação...")
            auth_success, auth_message, user_data = authenticate_user_firebase(test_email, test_password)
            print(f"   Resultado: {auth_message}")
            
            if auth_success:
                print("SUCESSO: Autenticação funcionando!")
                print(f"   Dados do usuário: {user_data}")
            else:
                print("ERRO: Falha na autenticação")
        else:
            print("ERRO: Falha no registro")
            
    except Exception as e:
        print(f"   ERRO no teste: {e}")
    
    print()
    print("=" * 50)
    print("Teste concluido!")
    
    return True

def list_all_users():
    """Lista todos os usuários do Firebase"""
    print("Listando todos os usuarios do Firebase...")
    print("=" * 50)
    
    try:
        users = get_all_users_firebase()
        if not users:
            print("Nenhum usuario encontrado.")
            return
        
        for i, user in enumerate(users, 1):
            print(f"{i}. {user.get('name', 'N/A')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   Tipo: {user.get('user_type', 'N/A')}")
            print(f"   ID: {user.get('id', 'N/A')}")
            print(f"   Criado em: {user.get('created_at', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"ERRO ao listar usuarios: {e}")

if __name__ == "__main__":
    print("ClinTutor - Teste do Firebase")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_all_users()
    else:
        test_firebase_operations()
