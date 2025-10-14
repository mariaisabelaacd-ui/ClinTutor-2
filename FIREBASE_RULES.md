# BioTutor - Regras do Firebase

## 📋 Regras do Firestore

Para configurar corretamente o Firebase Firestore, use as seguintes regras no arquivo `firestore.rules`:

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {

    // Permite leitura/escrita apenas se a origem for o app (não pública)
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

## 🔧 Como Configurar

1. **Acesse o Firebase Console:**
   - Vá para [console.firebase.google.com](https://console.firebase.google.com)
   - Selecione seu projeto BioTutor

2. **Configure as Regras:**
   - No menu lateral, clique em "Firestore Database"
   - Clique na aba "Regras"
   - Cole o código acima
   - Clique em "Publicar"

3. **Verifique a Configuração:**
   - As regras permitem leitura e escrita para todos os documentos
   - Isso é adequado para um aplicativo educacional interno
   - Para produção, considere implementar autenticação mais restritiva

## ⚠️ Importante

- Estas regras permitem acesso total ao banco de dados
- Adequadas para desenvolvimento e uso interno
- Para aplicações públicas, implemente regras mais restritivas baseadas em autenticação

## 📁 Estrutura do Banco

O BioTutor usa as seguintes coleções:
- `users` - Dados dos usuários (alunos, professores, admin)
- `case_analytics` - Analytics dos casos clínicos
- `chat_interactions` - Interações com o chatbot
