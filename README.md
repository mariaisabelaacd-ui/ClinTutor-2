# BioTutor - Sistema de Tutor de Clínica Geral

Sistema educacional para casos clínicos com integração Firebase e analytics avançados.

## 🚀 Funcionalidades

- **Sistema de Login/Cadastro** com roles (Aluno/Professor/Admin)
- **Casos Clínicos Interativos** com timer automático
- **Analytics Detalhados** de performance dos alunos
- **Dashboard do Professor** com estatísticas avançadas
- **Chat com IA** para suporte aos alunos
- **Armazenamento Firebase** com fallback local
- **Campo RA obrigatório** para alunos

## 📋 Pré-requisitos

- Python 3.8+
- Conta Firebase
- Streamlit

## ⚙️ Configuração

### 1. Clone o repositório
```bash
git clone https://github.com/mariaisabelaacd-ui/ClinTutor-2.git
cd ClinTutor-2
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o Firebase

1. **Crie um projeto no Firebase Console**
2. **Ative o Firestore Database**
3. **Configure as regras do Firestore** (use o arquivo `firestore.rules`)
4. **Baixe as credenciais do Service Account**
5. **Renomeie o arquivo para `firebase-credentials.json`**

### 4. Execute o aplicativo
```bash
streamlit run app.py
```

## 🔐 Configuração do Firebase

### Regras do Firestore
Use as regras do arquivo `firestore.rules`:

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

### Credenciais
- **Arquivo:** `firebase-credentials.json` (não versionado)
- **Exemplo:** `firebase-credentials-example.json`

## 👥 Tipos de Usuário

### Aluno
- Acessa casos clínicos
- Visualiza suas estatísticas
- Interage com o chat IA
- Campo RA obrigatório no cadastro

### Professor
- Dashboard com analytics de todos os alunos
- Visualiza tempo de resposta e taxa de acertos
- Gerencia interações de chat
- Acesso a estatísticas globais

### Administrador
- Login: `admin@biotutor.com`
- Senha: `admin123`
- Painel de administração completo
- Gerenciamento de usuários e dados

## 📊 Estrutura do Banco

### Coleções Firebase
- `users` - Dados dos usuários
- `case_analytics` - Analytics dos casos
- `chat_interactions` - Interações com IA

### Campos do Usuário
- `name` - Nome completo
- `email` - Email (único)
- `password` - Senha (hash)
- `user_type` - Tipo (aluno/professor/admin)
- `ra` - RA (apenas para alunos)
- `created_at` - Data de criação
- `last_login` - Último login

## 🛠️ Desenvolvimento

### Estrutura do Projeto
```
BioTutor/
├── app.py                 # Aplicação principal
├── auth_firebase.py       # Autenticação e usuários
├── firebase_config.py     # Configuração Firebase
├── analytics.py           # Sistema de analytics
├── admin_dashboard.py     # Dashboard administrativo
├── logic.py              # Lógica dos casos clínicos
├── firestore.rules       # Regras do Firestore
└── requirements.txt      # Dependências
```

## 🔒 Segurança

- **Senhas:** Hash SHA-256
- **Credenciais:** Não versionadas
- **Validação:** Email e campos obrigatórios
- **Sessões:** Gerenciadas pelo Streamlit

## 📝 Licença

Este projeto é privado e educacional.

## 🤝 Contribuição

Para contribuir, entre em contato com a equipe de desenvolvimento.
