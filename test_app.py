#!/usr/bin/env python3
"""
Script para testar a aplicação principal
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_firebase import get_all_users, is_firebase_connected
from firebase_config import test_firebase_connection

def test_app_functions():
    """Testa as funções da aplicação"""
    print("Testando funcoes da aplicacao...")
    print("=" * 50)
    
    # Teste 1: Conexão Firebase
    print("1. Testando conexao Firebase...")
    success, message = test_firebase_connection()
    print(f"   Resultado: {message}")
    
    if not success:
        print("ERRO: Firebase nao conectado")
        return False
    
    print("SUCESSO: Firebase conectado!")
    print()
    
    # Teste 2: Verificar status de conexão
    print("2. Verificando status de conexao...")
    connected = is_firebase_connected()
    print(f"   Firebase conectado: {connected}")
    print()
    
    # Teste 3: Listar usuários
    print("3. Listando usuarios...")
    try:
        users = get_all_users()
        print(f"   Encontrados {len(users)} usuarios:")
        
        for i, user in enumerate(users, 1):
            print(f"   {i}. {user.get('name', 'N/A')} ({user.get('email', 'N/A')}) - {user.get('user_type', 'N/A')}")
        
        print()
        
    except Exception as e:
        print(f"   ERRO ao listar usuarios: {e}")
        return False
    
    print("=" * 50)
    print("SUCESSO: Todas as funcoes estao funcionando!")
    return True

if __name__ == "__main__":
    test_app_functions()
