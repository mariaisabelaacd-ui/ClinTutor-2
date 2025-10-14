# Sistema de Autenticação - ClinTutor

## Funcionalidades Implementadas

### 🔐 Sistema de Login e Cadastro
- **Login**: Email e senha obrigatórios
- **Cadastro**: Nome, email, senha e tipo de usuário (professor/aluno)
- **Validação**: Email único, senha mínima de 6 caracteres
- **Segurança**: Senhas criptografadas com SHA-256

### 👥 Tipos de Usuário

#### 🎓 Alunos
- Acessam casos clínicos
- Progresso individual salvo
- Sistema de pontuação e níveis
- Chat com IA tutora

#### 👨‍🏫 Professores
- Dashboard com estatísticas
- Gerenciamento de usuários
- Visualização de todos os cadastros
- Remoção de usuários

### 💾 Armazenamento de Dados
- **Usuários**: `~/.clintutor/users.json`
- **Progresso**: `~/.clintutor/progresso_gamificado.json`
- **Formato**: JSON com estrutura organizada

### 🔒 Segurança
- Senhas hasheadas (SHA-256)
- Validação de email único
- Sessões gerenciadas pelo Streamlit
- Controle de acesso por tipo de usuário

## Como Usar

### 1. Primeiro Acesso
1. Execute a aplicação: `streamlit run app.py`
2. Clique na aba "📝 Cadastro"
3. Preencha os dados:
   - Nome completo
   - Email válido
   - Senha (mínimo 6 caracteres)
   - Tipo: Aluno ou Professor
4. Clique em "Cadastrar"

### 2. Login
1. Na aba "🔐 Login"
2. Digite email e senha
3. Clique em "Entrar"

### 3. Navegação
- **Alunos**: Acesso direto aos casos clínicos
- **Professores**: Menu de navegação com opções:
  - Casos Clínicos
  - Dashboard Professor

### 4. Dashboard do Professor
- Estatísticas de usuários
- Lista completa de cadastros
- Opção de remover usuários
- Informações de último login

## Estrutura dos Arquivos

```
ClinTutor 2/
├── app.py              # Aplicação principal com autenticação
├── auth.py             # Sistema de autenticação
├── logic.py            # Lógica dos casos clínicos
├── progress.json       # Progresso dos usuários
└── README_AUTH.md      # Esta documentação
```

## Funcionalidades Técnicas

### Validações Implementadas
- ✅ Email único no sistema
- ✅ Formato de email válido
- ✅ Senha mínima de 6 caracteres
- ✅ Confirmação de senha
- ✅ Campos obrigatórios

### Gerenciamento de Sessão
- ✅ Login automático após cadastro
- ✅ Logout com limpeza de sessão
- ✅ Persistência de dados por usuário
- ✅ Controle de acesso por tipo

### Interface do Usuário
- ✅ Página de login/cadastro responsiva
- ✅ Informações do usuário na sidebar
- ✅ Navegação específica para professores
- ✅ Dashboard administrativo

## Próximos Passos Sugeridos
- [ ] Recuperação de senha por email
- [ ] Edição de perfil do usuário
- [ ] Relatórios de progresso dos alunos
- [ ] Sistema de notificações
- [ ] Backup automático dos dados
