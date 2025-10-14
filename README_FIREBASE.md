# 🔥 Integração com Firebase - ClinTutor

## Visão Geral

O ClinTutor agora suporta armazenamento de usuários tanto localmente quanto no Firebase Firestore, oferecendo maior flexibilidade e escalabilidade.

## 🚀 Configuração do Firebase

### 1. Criar Projeto no Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Clique em "Adicionar projeto"
3. Digite o nome do projeto (ex: "clintutor-app")
4. Siga as instruções para criar o projeto

### 2. Habilitar Firestore Database

1. No console do Firebase, vá para "Firestore Database"
2. Clique em "Criar banco de dados"
3. Escolha "Iniciar no modo de teste" (para desenvolvimento)
4. Selecione uma localização (recomendado: us-central1)

### 3. Gerar Chave de Serviço

1. Vá para "Configurações do projeto" (ícone de engrenagem)
2. Clique na aba "Contas de serviço"
3. Clique em "Gerar nova chave privada"
4. Baixe o arquivo JSON

### 4. Configurar Credenciais

#### Opção A: Arquivo Local (Recomendado para desenvolvimento)
1. Renomeie o arquivo baixado para `firebase-credentials.json`
2. Coloque na pasta do projeto (mesmo diretório do `app.py`)

#### Opção B: Streamlit Secrets (Recomendado para produção)
1. Crie/edite o arquivo `.streamlit/secrets.toml`
2. Adicione as credenciais:

```toml
[firebase_credentials]
type = "service_account"
project_id = "seu-projeto-firebase"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxxxx@seu-projeto-firebase.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs/firebase-adminsdk-xxxxx%40seu-projeto-firebase.iam.gserviceaccount.com"
```

## 🔄 Funcionamento do Sistema

### Modo Híbrido
- **Com Firebase**: Dados salvos na nuvem (Firestore)
- **Sem Firebase**: Dados salvos localmente (JSON)
- **Migração**: Professores podem migrar dados locais para Firebase

### Estrutura de Dados no Firestore

```
users/
├── {user_id}/
│   ├── name: string
│   ├── email: string
│   ├── password: string (hash)
│   ├── user_type: "aluno" | "professor"
│   ├── created_at: timestamp
│   └── last_login: timestamp
```

## 🛠️ Funcionalidades

### ✅ Implementadas
- [x] Autenticação híbrida (Firebase + Local)
- [x] Migração automática de dados
- [x] Interface de status de conexão
- [x] Dashboard de migração para professores
- [x] Fallback para modo local
- [x] Validação de credenciais

### 🔧 Comandos Úteis

```bash
# Instalar dependências
pip install firebase-admin

# Executar aplicação
streamlit run app.py

# Testar conexão Firebase
python -c "from firebase_config import test_firebase_connection; print(test_firebase_connection())"
```

## 📊 Vantagens do Firebase

### 🚀 Performance
- Consultas rápidas e indexadas
- Escalabilidade automática
- Cache inteligente

### 🔒 Segurança
- Autenticação robusta
- Regras de segurança configuráveis
- Backup automático

### 🌐 Acessibilidade
- Dados acessíveis de qualquer lugar
- Sincronização em tempo real
- API REST e SDKs

## 🚨 Troubleshooting

### Erro: "Firebase não está conectado"
- Verifique se o arquivo `firebase-credentials.json` existe
- Confirme se as credenciais estão corretas
- Teste a conexão com internet

### Erro: "Permission denied"
- Verifique as regras do Firestore
- Confirme se a conta de serviço tem permissões

### Erro: "Project not found"
- Verifique o `project_id` nas credenciais
- Confirme se o projeto existe no Firebase Console

## 📝 Regras do Firestore (Recomendadas)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Usuários podem ler/escrever seus próprios dados
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Professores podem ler todos os usuários
    match /users/{userId} {
      allow read: if request.auth != null && 
        get(/databases/$(database)/documents/users/$(request.auth.uid)).data.user_type == 'professor';
    }
  }
}
```

## 🔄 Migração de Dados

### Para Professores
1. Faça login como professor
2. Vá para "Dashboard Professor"
3. Clique em "🔄 Migração de Dados"
4. Clique em "🚀 Migrar Dados Locais"

### Dados Migrados
- ✅ Nome, email, senha
- ✅ Tipo de usuário
- ✅ Data de criação
- ✅ Último login

## 🎯 Próximos Passos

- [ ] Backup automático
- [ ] Sincronização em tempo real
- [ ] Relatórios de uso
- [ ] Notificações push
- [ ] Analytics de usuários
