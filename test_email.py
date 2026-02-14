"""
Script de teste para verificar envio de email
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from email_service import send_verification_email_smtp, get_smtp_credentials, get_firebase_api_key

def test_smtp():
    """Testa envio via SMTP"""
    print("=" * 60)
    print("🧪 TESTE DE ENVIO DE EMAIL VIA SMTP")
    print("=" * 60)
    
    # Verifica credenciais
    email, password = get_smtp_credentials()
    
    if not email or not password:
        print("❌ Credenciais SMTP não encontradas!")
        return False
    
    print(f"\n✅ Credenciais encontradas:")
    print(f"   Email: {email}")
    print(f"   Senha: {'*' * len(password)}")
    
    # Testa envio
    test_email = input("\nDigite o email de destino para teste: ")
    test_link = "https://exemplo.com/verify?token=123456"
    test_name = "Usuário Teste"
    
    print(f"\n🔄 Enviando email de teste para {test_email}...")
    
    try:
        success, message = send_verification_email_smtp(test_email, test_link, test_name)
        
        if success:
            print(f"\n✅ {message}")
            return True
        else:
            print(f"\n❌ {message}")
            return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_firebase_api():
    """Testa Firebase REST API"""
    print("\n" + "=" * 60)
    print("🧪 TESTE DE FIREBASE REST API")
    print("=" * 60)
    
    api_key = get_firebase_api_key()
    
    if not api_key:
        print("❌ API Key do Firebase não encontrada!")
        return False
    
    print(f"\n✅ API Key encontrada: {api_key[:20]}...")
    
    # Testa criação de usuário
    test_email = input("\nDigite o email para teste (será criado no Firebase): ")
    test_password = "teste123456"
    test_name = "Usuário Teste"
    
    print(f"\n⚠️  ATENÇÃO: Isso irá criar um usuário de teste no Firebase!")
    confirm = input("Deseja continuar? (sim/não): ")
    
    if confirm.lower() not in ['sim', 's', 'yes', 'y']:
        print("❌ Teste cancelado")
        return False
    
    from email_service import send_verification_email_firebase_rest
    
    print(f"\n🔄 Criando usuário e enviando email via Firebase REST API...")
    
    try:
        success, message, user_id = send_verification_email_firebase_rest(test_email, test_password, test_name)
        
        if success:
            print(f"\n✅ {message}")
            print(f"   User ID: {user_id}")
            return True
        else:
            print(f"\n❌ {message}")
            return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔧 DIAGNÓSTICO DE ENVIO DE EMAIL\n")
    print("Escolha o teste:")
    print("1. Testar SMTP Gmail")
    print("2. Testar Firebase REST API")
    print("3. Ambos")
    
    choice = input("\nEscolha (1-3): ")
    
    if choice == "1":
        test_smtp()
    elif choice == "2":
        test_firebase_api()
    elif choice == "3":
        smtp_ok = test_smtp()
        firebase_ok = test_firebase_api()
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"SMTP Gmail: {'✅ OK' if smtp_ok else '❌ FALHOU'}")
        print(f"Firebase REST API: {'✅ OK' if firebase_ok else '❌ FALHOU'}")
    else:
        print("❌ Opção inválida")
