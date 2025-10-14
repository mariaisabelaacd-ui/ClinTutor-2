# 🚀 Guia de Deploy - BioTutor

## 📋 Opções de Deploy

### 1. 🎯 **Streamlit Cloud (RECOMENDADO)**

#### **Vantagens:**
- ✅ **Gratuito** para projetos públicos
- ✅ **Integração automática** com GitHub
- ✅ **Deploy automático** a cada push
- ✅ **Fácil configuração** de variáveis de ambiente
- ✅ **URL pública** para compartilhar

#### **Passo a Passo:**

1. **Acesse o Streamlit Cloud**
   - Vá para: https://share.streamlit.io/
   - Faça login com sua conta GitHub

2. **Conecte o Repositório**
   - Clique em "New app"
   - Repository: `mariaisabelaacd-ui/ClinTutor-2`
   - Branch: `main`
   - Main file path: `app.py`

3. **Configure as Variáveis de Ambiente**
   No painel do Streamlit Cloud, adicione:
   ```
   FIREBASE_PROJECT_ID=seu-projeto-id
   FIREBASE_PRIVATE_KEY_ID=sua-private-key-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nsua-chave-privada\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=seu-service-account@seu-projeto.iam.gserviceaccount.com
   FIREBASE_CLIENT_ID=seu-client-id
   FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
   FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
   FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
   FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/seu-service-account%40seu-projeto.iam.gserviceaccount.com
   ```

4. **Deploy!**
   - Clique em "Deploy!"
   - Aguarde alguns minutos
   - Sua URL será: `https://seu-app-name.streamlit.app`

---

### 2. 🌐 **Heroku (Alternativa)**

#### **Vantagens:**
- ✅ **Gratuito** (com limitações)
- ✅ **Suporte completo** ao Firebase
- ✅ **Escalável**

#### **Configuração:**
1. Crie um `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Configure as variáveis de ambiente no Heroku

---

### 3. ☁️ **Google Cloud Run (Profissional)**

#### **Vantagens:**
- ✅ **Integração nativa** com Firebase
- ✅ **Escalável** e confiável
- ✅ **Pago por uso**

---

## 🔧 **Configuração do Firebase para Deploy**

### 1. **Obter Credenciais do Firebase**

1. Acesse: https://console.firebase.google.com
2. Selecione seu projeto
3. Vá em "Configurações do Projeto" > "Contas de Serviço"
4. Clique em "Gerar nova chave privada"
5. Baixe o arquivo JSON

### 2. **Configurar Firestore**

1. No Firebase Console, vá em "Firestore Database"
2. Clique em "Criar banco de dados"
3. Escolha "Modo de produção"
4. Selecione uma localização (ex: us-central1)

### 3. **Configurar Regras de Segurança**

Use o arquivo `firestore.rules` que já está no projeto.

---

## 🎯 **Para Iniciação Científica**

### **Recomendação: Streamlit Cloud**

1. **Deploy rápido** - 5 minutos
2. **URL pública** - Fácil de compartilhar
3. **Sem custos** - Gratuito
4. **Firebase funcionando** - Dados salvos na nuvem
5. **Analytics completo** - Professor pode ver estatísticas

### **URL Final:**
```
https://biotutor-clintutor-2.streamlit.app
```

### **Compartilhamento:**
- Envie o link para os participantes
- Todos podem acessar sem instalar nada
- Dados ficam salvos no Firebase
- Professor pode acompanhar progresso em tempo real

---

## 🔒 **Segurança**

- ✅ Credenciais não ficam no código
- ✅ Variáveis de ambiente protegidas
- ✅ Firebase com regras de segurança
- ✅ Apenas usuários autenticados podem acessar

---

## 📱 **Teste Local vs Deploy**

### **Local:**
- `streamlit run app.py`
- Usa `firebase-credentials.json`
- URL: `http://localhost:8501`

### **Deploy:**
- Usa variáveis de ambiente
- URL pública
- Mesma funcionalidade

---

## 🚨 **Troubleshooting**

### **Erro de Conexão Firebase:**
- Verifique se as variáveis de ambiente estão corretas
- Confirme se o Firestore está habilitado
- Teste as credenciais localmente primeiro

### **Erro de Deploy:**
- Verifique se todos os arquivos estão no GitHub
- Confirme se o `requirements.txt` está atualizado
- Veja os logs no Streamlit Cloud

---

## 📞 **Suporte**

Se tiver problemas:
1. Verifique os logs no Streamlit Cloud
2. Teste localmente primeiro
3. Confirme as configurações do Firebase
