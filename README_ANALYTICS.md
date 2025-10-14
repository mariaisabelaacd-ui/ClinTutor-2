# 📊 Sistema de Analytics - ClinTutor

## Funcionalidades Implementadas

### 🎯 **Rastreamento de Tempo de Resposta**
- **Timer automático** para cada caso clínico
- **Medição precisa** do tempo de resolução
- **Armazenamento** no Firebase com timestamp
- **Formatação inteligente** (segundos, minutos, horas)

### 📈 **Taxa de Acertos por Aluno**
- **Cálculo automático** baseado nos resultados dos casos
- **Métricas detalhadas**: total de casos, acertos, taxa percentual
- **Tempo médio** de resolução por aluno
- **Progresso visual** com barras de progresso

### 💬 **Interações com Chatbot**
- **Rastreamento completo** de todas as conversas
- **Tempo de resposta** da IA para cada pergunta
- **Histórico detalhado** por caso e por aluno
- **Análise de padrões** de uso do chatbot

### 🔥 **Armazenamento no Firebase**
- **Coleções organizadas**:
  - `case_analytics`: Dados de tempo e resultados dos casos
  - `chat_interactions`: Interações com o chatbot
- **Fallback local** quando Firebase não está disponível
- **Sincronização automática** entre dispositivos

## 📊 Dashboard para Professores

### 🌍 **Visão Geral**
- **Estatísticas globais** do sistema
- **Métricas em tempo real** de todos os alunos
- **Gráficos interativos** com Plotly
- **Filtros avançados** por período e tipo de usuário

### 👥 **Análise por Aluno**
- **Perfil individual** com métricas detalhadas
- **Gráficos de progresso** ao longo do tempo
- **Histórico completo** de casos resolvidos
- **Análise de performance** por nível de dificuldade

### 💬 **Interações do Chat**
- **Histórico completo** de conversas
- **Análise de padrões** de uso
- **Tempo de resposta** da IA
- **Casos com mais interações**

### 📊 **Relatórios**
- **Relatório de performance** completo
- **Exportação em CSV** para análise externa
- **Métricas comparativas** entre alunos
- **Identificação de dificuldades** comuns

## 👨‍🎓 Estatísticas para Alunos

### 📈 **Sidebar Personalizada**
- **Taxa de acertos** atual
- **Tempo médio** de resolução
- **Número de interações** com o chatbot
- **Progresso visual** com barra de progresso

### 🎯 **Métricas Motivacionais**
- **Casos acertados** vs total
- **Evolução** da performance
- **Comparação** com média da turma
- **Conquistas** e badges

## 🛠️ Arquitetura Técnica

### 📁 **Estrutura de Arquivos**
```
ClinTutor 2/
├── analytics.py              # Sistema de analytics
├── professor_dashboard.py    # Dashboard avançado
├── app.py                   # Integração principal
├── test_analytics.py        # Testes do sistema
└── README_ANALYTICS.md      # Esta documentação
```

### 🔧 **Componentes Principais**

#### **analytics.py**
- `start_case_timer()`: Inicia cronômetro do caso
- `end_case_timer()`: Finaliza e salva dados
- `log_chat_interaction()`: Registra interações do chat
- `calculate_accuracy_rate()`: Calcula taxa de acertos
- `get_user_detailed_stats()`: Estatísticas completas

#### **professor_dashboard.py**
- `show_advanced_professor_dashboard()`: Dashboard principal
- `show_overview_tab()`: Visão geral com gráficos
- `show_student_details_tab()`: Detalhes por aluno
- `show_chat_interactions_tab()`: Análise do chat
- `show_reports_tab()`: Relatórios e exportação

### 🗄️ **Estrutura de Dados no Firebase**

#### **Coleção: case_analytics**
```json
{
  "user_id": "string",
  "case_id": "string", 
  "start_time": "timestamp",
  "end_time": "timestamp",
  "duration_seconds": "number",
  "duration_formatted": "string",
  "case_result": {
    "points_gained": "number",
    "breakdown": {
      "diagnóstico": "number",
      "exames": "number", 
      "plano": "number"
    }
  },
  "timestamp": "timestamp"
}
```

#### **Coleção: chat_interactions**
```json
{
  "user_id": "string",
  "case_id": "string",
  "user_message": "string",
  "bot_response": "string", 
  "response_time_seconds": "number",
  "timestamp": "timestamp"
}
```

## 🚀 Como Usar

### 👨‍🏫 **Para Professores**
1. **Faça login** como professor
2. **Navegue** para "Analytics Avançado"
3. **Explore** as diferentes abas:
   - **Visão Geral**: Gráficos e métricas globais
   - **Por Aluno**: Análise individual detalhada
   - **Interações Chat**: Histórico de conversas
   - **Relatórios**: Exportação de dados

### 👨‍🎓 **Para Alunos**
1. **Faça login** como aluno
2. **Veja suas estatísticas** na sidebar
3. **Acompanhe seu progresso** em tempo real
4. **Use o chatbot** - todas as interações são rastreadas

## 📊 Métricas Disponíveis

### 🎯 **Por Aluno**
- Total de casos resolvidos
- Taxa de acertos (%)
- Tempo médio de resolução
- Número de interações com chat
- Última atividade
- Progresso por dia (últimos 7 dias)

### 🌍 **Globais**
- Total de usuários ativos
- Total de casos resolvidos
- Total de interações com chat
- Taxa média de acertos
- Usuários ativos hoje

### 💬 **Chat Analytics**
- Tempo médio de resposta da IA
- Casos com mais interações
- Padrões de uso por aluno
- Histórico completo de conversas

## 🔧 Comandos de Teste

```bash
# Testar sistema de analytics
python test_analytics.py

# Ver resumo dos analytics
python test_analytics.py summary

# Executar aplicação
streamlit run app.py
```

## 🎉 Benefícios

### 👨‍🏫 **Para Professores**
- **Visão completa** do progresso dos alunos
- **Identificação** de dificuldades comuns
- **Métricas objetivas** para avaliação
- **Relatórios** para gestão acadêmica

### 👨‍🎓 **Para Alunos**
- **Feedback imediato** sobre performance
- **Motivação** através de métricas visuais
- **Acompanhamento** do progresso pessoal
- **Identificação** de áreas de melhoria

### 🏫 **Para a Instituição**
- **Dados quantitativos** sobre o uso da plataforma
- **Análise de eficácia** do método de ensino
- **Relatórios** para órgãos reguladores
- **Insights** para melhorias pedagógicas

## 🔮 Próximos Passos

- [ ] **Notificações** automáticas para professores
- [ ] **Comparação** entre turmas
- [ ] **Predição** de dificuldades
- [ ] **Gamificação** avançada
- [ ] **Integração** com LMS externos
- [ ] **API** para integração com outros sistemas
