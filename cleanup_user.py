"""
Script para limpar TODOS os dados de usuários (Firestore + Authentication)
Use este script para fazer uma limpeza completa
"""

import firebase_admin
from firebase_admin import credentials, auth, firestore
import os

def init_firebase():
    """Inicializa Firebase"""
    try:
        app = firebase_admin.get_app()
        return firestore.client()
    except ValueError:
        secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
        
        if os.path.exists(secrets_path):
            import toml
            secrets = toml.load(secrets_path)
            cred_dict = dict(secrets['firebase_credentials'])
            
            if 'private_key' in cred_dict:
                cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        else:
            print("❌ Arquivo secrets.toml não encontrado")
            return None

def clean_firestore_by_email(email: str):
    """Remove usuário do Firestore pelo email"""
    try:
        db = init_firebase()
        
        if not db:
            print("❌ Não foi possível conectar ao Firestore")
            return
        
        # Busca usuário no Firestore
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email.lower().strip()).limit(10)
        docs = query.get()
        
        if len(docs) == 0:
            print(f"\n❌ Nenhum usuário com email {email} encontrado no Firestore")
            return
        
        print(f"\n✅ Encontrado(s) {len(docs)} documento(s) no Firestore:")
        
        for doc in docs:
            data = doc.to_dict()
            print(f"\n   - ID: {doc.id}")
            print(f"   - Nome: {data.get('name', 'N/A')}")
            print(f"   - Email: {data.get('email', 'N/A')}")
            print(f"   - Tipo: {data.get('user_type', 'N/A')}")
        
        confirm = input("\n⚠️  Deseja REALMENTE excluir estes documentos? (sim/não): ")
        
        if confirm.lower() in ['sim', 's', 'yes', 'y']:
            for doc in docs:
                doc.reference.delete()
                print(f"✅ Documento {doc.id} removido do Firestore")
            
            print(f"\n✅ Limpeza concluída! Agora você pode criar uma nova conta com {email}")
        else:
            print("\n❌ Exclusão cancelada")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")

def list_firestore_users():
    """Lista todos os usuários do Firestore"""
    try:
        db = init_firebase()
        
        if not db:
            print("❌ Não foi possível conectar ao Firestore")
            return
        
        print("\n📋 Listando todos os usuários do Firestore:\n")
        
        users_ref = db.collection('users')
        docs = users_ref.get()
        
        count = 0
        for doc in docs:
            count += 1
            data = doc.to_dict()
            print(f"{count}. {data.get('email', 'N/A')}")
            print(f"   ID: {doc.id}")
            print(f"   Nome: {data.get('name', 'N/A')}")
            print(f"   Tipo: {data.get('user_type', 'N/A')}")
            print(f"   Verificado: {'✅' if data.get('email_verified') else '❌'}")
            print()
        
        if count == 0:
            print("Nenhum usuário encontrado no Firestore")
        else:
            print(f"\nTotal: {count} usuários")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")

def clean_all():
    """Limpa TODOS os usuários (Authentication + Firestore)"""
    try:
        db = init_firebase()
        
        print("\n⚠️  ATENÇÃO: Esta operação irá remover TODOS os usuários!")
        confirm = input("Deseja continuar? (sim/não): ")
        
        if confirm.lower() not in ['sim', 's', 'yes', 'y']:
            print("\n❌ Operação cancelada")
            return
        
        # Limpa Authentication
        print("\n🔄 Limpando Firebase Authentication...")
        page = auth.list_users()
        auth_count = 0
        for user in page.users:
            auth.delete_user(user.uid)
            auth_count += 1
            print(f"   ✅ Removido: {user.email}")
        
        # Limpa Firestore
        print("\n🔄 Limpando Firestore...")
        users_ref = db.collection('users')
        docs = users_ref.get()
        firestore_count = 0
        for doc in docs:
            doc.reference.delete()
            firestore_count += 1
            data = doc.to_dict()
            print(f"   ✅ Removido: {data.get('email', 'N/A')}")
        
        print(f"\n✅ Limpeza concluída!")
        print(f"   - Authentication: {auth_count} usuários removidos")
        print(f"   - Firestore: {firestore_count} documentos removidos")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 LIMPEZA COMPLETA DO FIREBASE")
    print("=" * 60)
    
    print("\nOpções:")
    print("1. Limpar usuário específico (Firestore) por email")
    print("2. Listar usuários do Firestore")
    print("3. Listar usuários do Authentication")
    print("4. LIMPAR TUDO (Authentication + Firestore)")
    print("5. Sair")
    
    choice = input("\nEscolha uma opção (1-5): ")
    
    if choice == "1":
        email = input("\nDigite o email do usuário para excluir: ")
        clean_firestore_by_email(email)
    elif choice == "2":
        list_firestore_users()
    elif choice == "3":
        init_firebase()
        print("\n📋 Listando usuários do Authentication:\n")
        page = auth.list_users()
        count = 0
        for user in page.users:
            count += 1
            print(f"{count}. {user.email} (UID: {user.uid})")
        if count == 0:
            print("Nenhum usuário encontrado")
    elif choice == "4":
        clean_all()
    elif choice == "5":
        print("\n👋 Até logo!")
    else:
        print("\n❌ Opção inválida")
