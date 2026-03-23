import os
import json
from datetime import datetime
from typing import Dict, List, Any, Generator
from groq import Groq
import streamlit as st  
import numpy as np

print("DEBUG: LOADED LOGIC.PY v4 (GROQ SDK - LLAMA 3)")

# =============================
# CONFIGURAÇÃO DA IA (GROQ LOAD BALANCER)
# =============================
GROQ_API_KEYS = []

try:
    import toml
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    try:
        with open(secrets_path, "r") as f:
            secrets_data = toml.load(f)
            
        if 'groq_api' in secrets_data and 'api_keys' in secrets_data['groq_api']:
            GROQ_API_KEYS = secrets_data['groq_api']['api_keys']
        elif 'groq_api' in secrets_data and 'api_key' in secrets_data['groq_api']:
            GROQ_API_KEYS = [secrets_data['groq_api']['api_key']]
    except Exception as e:
        print(f"Erro ao carregar TOML direto: {e}")
except ImportError:
    pass

if not GROQ_API_KEYS:
    # Fallback to st.secrets
    try:
        if "api_keys" in st.secrets["groq_api"]:
            GROQ_API_KEYS = list(st.secrets["groq_api"]["api_keys"])
        elif "api_key" in st.secrets["groq_api"]:
            GROQ_API_KEYS = [st.secrets["groq_api"]["api_key"]]
    except Exception as e:
        print(f"Erro no Fallback st.secrets: {e}")

import random
def get_groq_client():
    if not GROQ_API_KEYS:
        return None
    # Escolhe uma chave aleatoria para dividir a carga e evitar Rate Limit (429)
    key = random.choice(GROQ_API_KEYS)
    safe_key = key[:10] + "..." + key[-5:]
    print(f"🤖 [IA LOGGER] Requisição enviada. Usando chave Groq: {safe_key}", flush=True)
    return Groq(api_key=key)

# Modelo Padrão do Groq (8B para chat rápido e tutoria)
MODEL_NAME = "llama-3.1-8b-instant"
# Modelo mais capaz para avaliações precisas de critérios (diferencia Parcial vs Ausente)
EVAL_MODEL_NAME = "llama-3.3-70b-versatile"

APP_NAME = "Helix.AI"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".clintutor")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_PATH = os.path.join(DATA_DIR, "progresso_gamificado.json")

# =============================
# Base de Conhecimento: Genética e Biologia Molecular
# =============================
QUESTIONS: List[Dict[str, Any]] = [
    {
      "id": "q1_dna_interacoes",
      "pergunta": "A dupla hélice do DNA é mantida por diferentes tipos de interações químicas. Explique quais são essas forças, onde cada uma atua na estrutura e o que acontece com a molécula quando elas são rompidas.",
      "componentes_conhecimento": ["Interações Químicas", "Estabilidade do DNA", "Conformação do DNA"],
      "referencia": {
          "Básico": "A dupla hélice é mantida por ligações de hidrogênio entre as bases nitrogenadas complementares (A=T com duas ligações; G≡C com três) e por ligações covalentes no backbone (esqueleto / cadeia principal) de açúcar e fosfato. Quando rompidas, as fitas se separam. Na célula, isso é feito por helicases.",
          "Médio": "Além das ligações de hidrogênio, forças de empilhamento (base stacking) entre bases adjacentes — interações hidrofóbicas e de van der Waals — contribuem igualmente para a estabilidade. A repulsão dos grupos fosfato negativos é uma força desestabilizadora neutralizada por histonas e cátions.",
          "Avançado": "A estabilidade não é uniforme ao longo da sequência — regiões A-T são menos estáveis e constituem pontos preferenciais de abertura, como origens de replicação. O DNA pode adotar conformações A, B ou Z dependendo de hidratação, superenrolamento (supercoiling) e contexto proteico. As forças de empilhamento são anisotrópicas e sequência-dependentes. Proteínas HMG e topoisomerases modulam ativamente o estado conformacional in vivo."
      },
      "pontuacao_maxima": 3
    },
    {
      "id": "q2_dna_polimerase_limitacoes",
      "pergunta": "A DNA polimerase é a principal enzima da replicação, mas sozinha ela não consegue copiar o DNA. Explique quais são as suas limitações estruturais e funcionais e como a célula resolve cada uma delas para garantir que a replicação ocorra com fidelidade.",
      "componentes_conhecimento": ["DNA Polimerase", "Mecanismos de Replicação", "Fidelidade da Replicação"],
      "referencia": {
          "Básico": "A DNA polimerase precisa de fita molde, iniciador (primer) com extremidade 3'-OH e não consegue iniciar síntese do zero. A primase fornece o iniciador (primer) de RNA. A polimerase só sintetiza 5'→3' e corrige erros pelo proofreading (revisão / atividade corretora).",
          "Médio": "A incapacidade de iniciar é contornada pela primase (RNA polimerase que não exige iniciador). A energia vem da hidrólise do pirofosfato do dNTP incorporado. O proofreading (revisão) usa o sítio exonuclease 3'→5' da própria polimerase. A processividade é garantida pelo grampo deslizante (sliding clamp). Os iniciadores (primers) são removidos pela DNA pol I (procariotos) após a síntese.",
          "Avançado": "A direcionalidade 5'→3' é vantagem evolutiva: permite proofreading (revisão) sem destruir a fonte de energia. Em eucariotos, Pol α inicia com iniciador (primer) acoplado, depois é substituída por Pol ε (fita líder / leading strand) e Pol δ (fita atrasada / lagging strand) após recrutamento do PCNA (grampo deslizante eucariótico). Pol δ também atua no NER (reparo por excisão de nucleotídeo) e MMR (reparo de mau-pareamento), integrando replicação e reparo."
      },
      "pontuacao_maxima": 3
    },
    {
      "id": "q3_replicacao_fita_atrasada",
      "pergunta": "As duas fitas do DNA são copiadas de formas diferentes durante a replicação. Explique por que isso acontece e descreva, passo a passo, como a fita que apresenta maior dificuldade para ser copiada é sintetizada e processada até gerar uma fita contínua e completa.",
      "componentes_conhecimento": ["Antiparalelismo", "Fragmentos de Okazaki", "Mecanismo da Fita Atrasada"],
      "referencia": {
          "Básico": "O antiparalelismo faz com que apenas uma fita — fita líder (leading strand) — possa ser copiada continuamente. A outra — fita atrasada (lagging strand) — é copiada em fragmentos de Okazaki, cada um iniciado por um iniciador (primer), depois unidos pela ligase.",
          "Médio": "A síntese da fita atrasada (lagging strand) é cíclica: primase sintetiza o iniciador (primer), a pol III extende a fita até o fragmento anterior. A DNA pol I remove o iniciador e preenche (síntese por substituição / nick translation). A ligase sela com NAD+/ATP. Em eucariotos os fragmentos são menores (~100-200 nt) por causa dos nucleossomos.",
          "Avançado": "O modelo do trombone (trombone model) mantém ambas as polimerases acopladas no replissomo. Em eucariotos, Pol δ realiza deslocamento de fita (strand displacement)."
      },
      "pontuacao_maxima": 3
    },
    {
      "id": "q4_problemas_mecanicos_topoisomerases",
      "pergunta": "A abertura da dupla fita durante a replicação cria problemas mecânicos que precisam ser resolvidos para que a forquilha avance. Identifique esses problemas e explique como as enzimas envolvidas os resolvem — e o que acontece quando uma delas é inibida por um fármaco.",
      "componentes_conhecimento": ["Topoisomerases", "Superenrolamento", "Inibidores Enzimáticos"],
      "referencia": {
          "Básico": "A helicase abre a fita; as proteínas SSB (SSBPs / proteínas de ligação à fita simples) estabilizam a fita simples; topoisomerases resolvem o superenrolamento (supercoiling). A ciprofloxacina inibe a DNA girase (DNA gyrase) bacteriana, bloqueando a replicação.",
          "Médio": "A DNA girase (gyrase) introduz superenrolamentos negativos cortando transitoriamente as duas fitas. A ciprofloxacina estabiliza o complexo covalente girase-DNA, gerando quebras letais. O etoposídeo age analogamente sobre a topoisomerase II eucariótica — útil em quimioterapia mas genotóxico.",
          "Avançado": "A seletividade da ciprofloxacina deve-se às diferenças estruturais entre GyrA/B e Top2α/β. A camptotecina inibe a topoisomerase I eucariótica. O complexo CMG eucariótico acopla velocidade da helicase à síntese para evitar excesso de fita simples exposta que ativaria a via de resposta ao dano ao DNA (DDR)."
      },
      "pontuacao_maxima": 3
    },
    {
      "id": "q5_lesoes_e_reparo",
      "pergunta": "Escolha dois tipos de lesão quimicamente distintos, explique como cada um é formado, qual é a consequência para a informação genética se não for reparado e como a célula os identifica e corrige.",
      "componentes_conhecimento": ["Lesões no DNA", "Mecanismos de Reparo (BER/NER)", "Mutagênese"],
      "referencia": {
          "Básico": "Despurinação perde a base, gerando sítio AP (sítio abásico / sítio apurídico) — polimerase insere nucleotídeo incorreto. Dímeros de pirimidina por UV bloqueiam a polimerase. Ambos são corrigidos por excisão de base (BER / REB) ou excisão de nucleotídeo (NER / REN).",
          "Médio": "Reparo por excisão de base (BER / REB) para lesões pontuais: glicosilase remove a base → AP endonuclease → polimerase → ligase. Reparo por excisão de nucleotídeo (NER / REN) para dímeros: remove oligonucleotídeo ~25-30 nt contendo a lesão. Fotorreativação (photoreactivation) em bactérias usa energia luminosa para reverter o dímero diretamente. Deaminação (desaminação) de metil-citosina gera timina — difícil de reconhecer como lesão.",
          "Avançado": "O NER acoplado à transcrição (TC-NER) é ativado pelo bloqueio da RNA pol II e é prioritário. Defeitos no NER causam xeroderma pigmentosum, síndrome de Cockayne e tricotiodistrofia. O reparo de mau-pareamento (MMR) depende de metilação (procariotos) ou quebras de fita simples transitórias (nicks) em eucariotos para identificar a fita com erro. Perda do MMR causa instabilidade de microssatélites — síndrome de Lynch."
      },
      "pontuacao_maxima": 3
    },
    {
      "id": "q6_consequencias_falha_reparo",
      "pergunta": "Uma célula em divisão apresenta simultaneamente uma lesão na fita molde e um erro de incorporação de nucleotídeo cometido pela polimerase. Compare os mecanismos disponíveis para corrigir cada um desses problemas, explique por que o momento em que a correção ocorre é crítico e o que acontece se ambos não forem resolvidos antes da próxima divisão.",
      "componentes_conhecimento": ["Revisão e MMR", "Síntese Translesão", "Checkpoints do Ciclo Celular"],
      "referencia": {
          "Básico": "O proofreading (revisão / atividade corretora) corrige erros durante a síntese; o MMR (reparo de mau-pareamento) atua depois. Lesões bloqueiam a polimerase e precisam ser reparadas ou contornadas. Erros não corrigidos geram mutações transmitidas às filhas.",
          "Médio": "O MMR (reparo de mau-pareamento) depende de marcadores de identidade da fita — metilação em procariotos; quebras de fita simples transitórias (nicks) em eucariotos — e tem janela temporal estreita. Lesões durante a replicação podem ser contornadas por síntese translesão (TLS / síntese sobre lesão) com polimerases de baixa fidelidade, ou reparadas por recombinação homóloga (HR / RH) usando a cromátide irmã. Acúmulo de danos ativa p53 → senescência ou apoptose.",
          "Avançado": "A via de resposta ao dano ao DNA impõe pontos de checagem (checkpoints) para garantir tempo de reparo. A recombinação homóloga (HR / RH) é restrita às fases S/G2 (cromátide irmã disponível); a junção de extremidades não homólogas (NHEJ / JENH) opera em todo o ciclo mas é mutagênica. O colapso da forquilha replicativa (replication fork collapse) ativa a HR de emergência. Perda de função (loss of function) de p53 permite tolerância a danos e progressão tumoral — conexão direta entre falha nos sistemas de reparo e oncogênese."
      },
      "pontuacao_maxima": 3
    }
]

# Mapping de nivel para filtrar perguntas
LEVEL_MAP = {
    1: ["básico", "intermediário", "avançado"],
    2: ["básico", "intermediário", "avançado"],
    3: ["básico", "intermediário", "avançado"]
}



def evaluate_answer_with_ai(question_data: Dict, user_answer: str) -> Dict[str, Any]:
    # Extrai as referências disponíveis
    referencias = question_data.get('referencia', {})
    ref_basico = referencias.get('Básico', '')
    ref_medio = referencias.get('Médio', '')
    ref_avancado = referencias.get('Avançado', '')

    prompt = f"""
Você é um avaliador acadêmico preciso para uma plataforma de ensino de Genética e Biologia Molecular.
Sua tarefa é avaliar a resposta do aluno e classificá-la em um de quatro níveis: "Básico", "Médio", "Avançado" ou "Incorreto".

Pergunta: {question_data.get('pergunta')}

---
**GABARITOS DE REFERÊNCIA:**

NÍVEL BÁSICO: {ref_basico}
NÍVEL MÉDIO (Inclui o Básico e adiciona): {ref_medio}
NÍVEL AVANÇADO (Inclui o Médio e adiciona profundidade): {ref_avancado}
---

**RESPOSTA DO ALUNO:**
{user_answer}

**INSTRUÇÕES DE AVALIAÇÃO:**
1. **Incorreto**: A resposta está errada, é irrelevante ou não aborda nenhum dos pontos do gabarito básico.
2. **Básico**: O aluno demonstra compreensão fundamental descrita no gabarito básico.
3. **Médio**: O aluno aborda os pontos do gabarito básico e inclui conhecimentos do nível médio (ex: forças de empilhamento, processividade, energia, etc).
4. **Avançado**: O aluno demonstra domínio profundo, citando detalhes técnicos, nomes de proteínas específicas ou contextos conformacionais/moleculares descritos no nível avançado.

**DIRETRIZES:**
- Classifique no nível mais alto que o aluno preencheu satisfatoriamente.
- O feedback deve ser construtivo, indicando o que ele alcançou e o que faltou para o próximo nível.
- Se o aluno ficar entre dois níveis, seja criterioso. Para o "Médio", ele precisa ter ido significativamente além do "Básico".

Retorne SUA AVALIAÇÃO ESTRITAMENTE NESTE FORMATO JSON VÁLIDO:
{{
  "level": "Básico" | "Médio" | "Avançado" | "Incorreto",
  "points": 1, 2, 3 ou 0,
  "classification": "BÁSICO", "MÉDIO", "AVANÇADO" ou "INCORRETO",
  "feedback": "Texto claro explicando a classificação."
}}
NÃO RETORNE TEXTO FORA DO JSON.
"""
    # Retry logic for Rate Limits (429) & 503 errors
    import time
    max_retries = 3
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            return {"level": "Incorreto", "points": 0, "classification": "INCORRETO", "feedback": "Erro: Cliente IA não configurado."}
            
        try:
            response = client.chat.completions.create(
                model=EVAL_MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(text)
            except:
                 # Fallback manual em caso de erro no JSON
                lower_text = text.lower()
                if "avançado" in lower_text or "avancado" in lower_text:
                    return {"level": "Avançado", "points": 3, "classification": "AVANÇADO", "feedback": text}
                elif "médio" in lower_text or "medio" in lower_text:
                    return {"level": "Médio", "points": 2, "classification": "MÉDIO", "feedback": text}
                elif "básico" in lower_text or "basico" in lower_text:
                    return {"level": "Básico", "points": 1, "classification": "BÁSICO", "feedback": text}
                else:
                    return {"level": "Incorreto", "points": 0, "classification": "INCORRETO", "feedback": text}
                
        except Exception as e:
            print(f"🔄 Tentativa {attempt+1}/{max_retries} falhou no Avaliador IA: {e}")
            if attempt == max_retries - 1:
                return {"level": "Incorreto", "points": 0, "classification": "INCORRETO", "feedback": f"Erro IA: {e}"}
            time.sleep(1) 

def _construir_contexto_para_ia(question: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    ctx = f"**Questão:** {question['pergunta']}\n"
    ctx += f"**Conceitos:** {', '.join(question.get('componentes_conhecimento', []))}\n"
    if chat_history:
        ctx += "\n**Histórico:**\n"
        for turn in chat_history[-4:]:
            role = "Tutor" if turn['role'] == 'assistant' else 'Aluno'
            ctx += f"- {role}: {turn['content']}\n"
    return ctx

def tutor_reply_com_ia(question: Dict[str, Any], user_msg: str, chat_history: List[Dict[str, str]]) -> Generator[str, None, None]:
    contexto = _construir_contexto_para_ia(question, chat_history)
    
    # Prepara o gabarito completo para o tutor saber todas as nuances
    gabarito_completo = "\n".join([f"{k}: {v}" for k, v in question.get('referencia', {}).items()])
    if not gabarito_completo:
        gabarito_completo = question.get('resposta_esperada', 'N/A')

    prompt = f"""
    SITUAÇÃO: Você é um Tutor Inteligente estritamente Socrático de Biologia Molecular da plataforma Helix.AI.
    OBJETIVO: O aluno está tentando responder a seguinte questão: "{question['pergunta']}".
    A resposta correta em diferentes níveis de profundidade é:
    {gabarito_completo}

    **REGRAS ABSOLUTAS E INQUEBRÁVEIS (PENA DE FALHA CRÍTICA SE DESCUMPRIDAS):**
    1. **NUNCA, JAMAIS DÊ A RESPOSTA FINAL DIRETAMENTE.** O seu papel NÃO é responder a pergunta por ele.
    2. NUNCA diga se ele está certo ou errado logo de cara na explicação da matéria.
    3. Use o **MÉTODO SOCRÁTICO**. Faça perguntas curtas, instigantes e que induzam o aluno a raciocinar o próximo passo da resposta.
    4. Se o aluno pedir a resposta ou disser que não sabe de nada, não entregue. Dê uma microscópica dica conceitual e PERGUNTE DE VOLTA em seguida.
    5. Suas réplicas devem ter NO MÁXIMO 3 a 4 linhas. Evite parágrafos gigantes. Seja conversacional e direto.

    Contexto da conversa até agora:
    {contexto}
    
    Mensagem Atual do Aluno: "{user_msg}"
    
    Responda ao aluno ESTRITAMENTE focado em aplicar a Regra 3 (Perguntar de volta e induzir).
    """
    import time
    max_retries = 3
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            yield "Erro: Cliente IA não configurado."
            return
            
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            return 
        except Exception as e:
            print(f"🔄 Tentativa {attempt+1}/{max_retries} falhou no Tutor Chat: {e}")
            if attempt == max_retries - 1:
                yield f"Erro na IA: {e}"
                return
            time.sleep(1)

# =============================
# PERSISTÊNCIA
# =============================
def load_progress() -> Dict[str, Any]:
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_progress(data: Dict[str, Any]):
    try:
        existing = load_progress()
        progress_list = [existing] if isinstance(existing, dict) and existing else (existing if isinstance(existing, list) else [])
        user_id = data.get("user_id")
        if user_id:
            progress_list = [p for p in progress_list if p.get("user_id") != user_id]
            progress_list.append(data)
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(progress_list, f, ensure_ascii=False, indent=2)
    except: pass

LEVEL_THRESHOLDS = {1: 0, 2: 20, 3: 50} # Ajustado para escala de 3 pontos
MAX_LEVEL = 3

def level_from_score(score: int) -> int:
    lvl = 1
    for L in sorted(LEVEL_THRESHOLDS.keys()):
        if score >= LEVEL_THRESHOLDS[L]: lvl = L
    return min(lvl, MAX_LEVEL)

def progress_to_next_level(score: int) -> float:
    lvl = level_from_score(score)
    if lvl == MAX_LEVEL: return 1.0
    cur, nxt = LEVEL_THRESHOLDS[lvl], LEVEL_THRESHOLDS[lvl+1]
    return (score - cur) / (nxt - cur) if nxt > cur else 1.0

def pick_new_case(level: int, used_cases: List[str] = None) -> Dict[str, Any]:
    used_cases = used_cases or []
    available = [q for q in QUESTIONS if q["id"] not in used_cases]
    
    if not available: 
        used_cases.clear()
        available = QUESTIONS
    if not available: return QUESTIONS[0]
    
    return available[0].copy()

def get_case(cid: str) -> Dict[str, Any]:
    for q in QUESTIONS:
        if q["id"] == cid:
            res = q.copy()
            if "resposta_esperada" not in res and "referencia" in res:
                # Usa o nível avançado como resposta de referência principal para compatibilidade
                res["resposta_esperada"] = res["referencia"].get("Avançado", "")
            return res
    return QUESTIONS[0]

def finalize_question_response(question: Dict[str, Any], user_answer: str, ai_evaluation: Dict[str, Any]) -> Dict[str, Any]:
    classification = ai_evaluation.get("classification", "INCORRETO").upper()
    points = float(ai_evaluation.get("points", 0))
    feedback = ai_evaluation.get("feedback", "")
    level = ai_evaluation.get("level", "Incorreto")

    is_correct = points > 0
    outcome = "correct" if points >= 1 else "incorrect" # Simplificado para o novo sistema
    if points == 2: outcome = "partial" # Médio como parcial se quiser manter a lógica original
    
    return {
        "points_gained": points,
        "is_correct": is_correct,
        "classification": classification,
        "level": level,
        "outcome": outcome,
        "feedback": feedback,
        "user_answer": user_answer,
        "criterios": {"Nível": level} 
    }

# Compatibilidade para analytics
CASES = QUESTIONS
def correct_exam_name(n): return n, False
def normalize_exam_name(n): return n
def suggest_exam_corrections(n, a): return ""

def generate_category_insights(category_name: str, sample_answers: List[str]) -> str:
    """
    Gera uma análise pedagógica focada em uma categoria de conhecimento, 
    usando todas as respostas dos alunos como base.
    """
    answers_str = "\n\n".join([f"Exemplo {i+1}:\n\"{ans}\"" for i, ans in enumerate(sample_answers)])
    
    prompt = f"""
Você é um Diretor Pedagógico sênior especialista em análise de aprendizagem.
Sua tarefa é analisar uma amostra geral das respostas recentes de uma turma para o tópico '{category_name}'.

**Amostra de Respostas dos Alunos neste Tópico (Mistura de certas, parciais e incorretas):**
{answers_str if sample_answers else "Nenhuma amostra disponível."}

**O QUE VOCÊ DEVE FAZER:**
1. Escreva um resumo direto e executivo (max 2 parágrafos) analisando o desempenho geral dos alunos neste tópico com base na amostra recebida. Há clareza ou confusão dominante? Qual é a falha conceitual principal presente nos que erraram?
2. Sugira 2 a 3 estratégias curtas e práticas que o professor pode usar em sala de aula para reforçar e corrigir as defasagens.
3. Mantenha um tom profissional, equilibrado e encorajador.
4. Escreva uma resposta curta e direta. Cuidado para não gerar um texto gigante.

Não inclua saudações, vá direto para a análise.
"""

    import time
    max_retries = 3
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            return "Erro: O assistente de leitura de IA não está configurado. Verifique as chaves."
            
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"🔄 Tentativa {attempt+1}/{max_retries} falhou no Insight de PDF IA (Categoria): {e}")
            if attempt == max_retries - 1:
                return f"Não foi possível gerar a análise profunda devido a um erro de comunicação com a IA: {e}"
            time.sleep(1)

def generate_difficulty_preview(category_name: str, sample_answers: List[str]) -> str:
    """
    Gera um preview curto e direto (1-2 frases) sobre o status geral
    dos alunos em uma categoria específica.
    """
    answers_str = "\n".join([f"- \"{ans}\"" for ans in sample_answers[:5]]) # Pega até 5 respostas
    
    prompt = f"""
Sua tarefa é ler essa amostra de respostas dos alunos sobre o tópico '{category_name}' e identificar a principal falha conceitual entre os que estão patinando, ou atestar o domínio geral.

**Amostras de Respostas (Mistas):**
{answers_str if sample_answers else "Nenhuma amostra disponível."}

**O QUE VOCÊ DEVE FAZER:**
Escreva UMA frase curta e direta resumindo o que os alunos não estão entendendo. 
Exemplo de formato: "Os alunos estão confundindo X com Y, esquecendo a etapa Z."
NÃO dê sugestões pedagógicas, NÃO use saudações. Vá direto ao ponto.
"""

    import time
    max_retries = 2
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            return "Assistente de IA não configurado."
            
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                return "Erro ao gerar preview com a IA."
            time.sleep(1)

def generate_ai_usage_preview(chat_samples: List[str]) -> str:
    """
    Gera um preview curto (1-2 frases) analisando como os alunos
    estão utilizando a IA (ex: buscando respostas diretas, pedindo revisão, etc).
    """
    chat_str = "\n".join([f"- Aluno: \"{ans}\"" for ans in chat_samples[:10]])
    
    prompt = f"""
Analise o histórico de perguntas recentes que os alunos fizeram para a inteligência artificial (Tutor).

**Mensagens recentes dos alunos:**
{chat_str if chat_samples else "Nenhuma interação registrada."}

**O QUE VOCÊ DEVE FAZER:**
Escreva UMA frase curta e direta resumindo o padrão principal de uso da IA pelos alunos.
Exemplo de formato: "A maioria dos alunos está usando o tutor para confirmar respostas antes de enviar." ou "Os alunos estão frequentemente pedindo dicas conceituais sem solicitar a resposta completa."
NÃO use saudações. Vá direto ao ponto.
"""

    import time
    max_retries = 2
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            return "Assistente de IA não configurado."
            
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                return "Erro ao gerar preview com a IA."
            time.sleep(1)

def generate_class_criteria_analysis(answers_list: List[str]) -> Dict[str, str]:
    """
    Analisa uma amostra de respostas da turma e gera uma análise DETALHADA
    por tópico, com pontos positivos, pontos de atenção e sugestões.
    """
    answers_str = "\n\n".join([f"Resposta do Aluno {i+1}:\n\"{ans}\"" for i, ans in enumerate(answers_list[:20])])
    
    prompt = f"""
Você é um Diretor Pedagógico sênior especialista em Biologia Molecular, com experiência em análise de aprendizagem.

Sua tarefa é analisar DETALHADAMENTE as respostas dos alunos abaixo sobre "Antiparalelismo e Limitações da DNA Polimerase".

**Respostas dos Alunos:**
{answers_str}

**INSTRUÇÕES DETALHADAS:**

Para CADA um dos 5 tópicos abaixo, escreva uma análise RICA e DETALHADA contendo:
- **Ponto positivo:** O que a maioria dos alunos acertou ou compreendeu
- **Ponto de atenção:** Onde está a dificuldade principal, com exemplos concretos do que os alunos escreveram
- **Lacunas:** Quais conceitos foram omitidos ou tratados de forma superficial
- Se poucos ou nenhum aluno abordou aquele tópico, diga isso CLARAMENTE

REGRAS ABSOLUTAS:
- NÃO invente que os alunos mencionaram algo se eles não mencionaram.
- Se um tópico não foi abordado por nenhum aluno, diga: "Nenhum aluno abordou este tópico de forma explícita."
- Seja honesto e preciso. Cada análise deve ter 3-5 frases.

Os 5 tópicos:
1. Compreensão do antiparalelismo (definição de 5'→3' e 3'→5')
2. Limitação da direcionalidade da polimerase (só sintetiza 5'→3')
3. Mecanismo da fita lagging (fragmentos de Okazaki, síntese descontínua)
4. Papel do primer e da primase (necessidade de extremidade 3'-OH)
5. Integração entre as limitações (conexão entre os problemas)

Devolva ESTRITAMENTE um JSON com as 5 chaves abaixo. Cada valor deve ter 3-5 frases ricas de análise.
{{
    "1. Compreensão do antiparalelismo": "análise detalhada aqui",
    "2. Limitação da direcionalidade da polimerase": "análise detalhada aqui",
    "3. Mecanismo da fita lagging": "análise detalhada aqui",
    "4. Papel do primer e da primase": "análise detalhada aqui",
    "5. Integração entre as limitações": "análise detalhada aqui"
}}
NÃO RETORNE TEXTO FORA DO JSON.
"""

    import time
    import json
    max_retries = 3
    default_resp = {
        "1. Compreensão do antiparalelismo": "Não foi possível analisar adequadamente.",
        "2. Limitação da direcionalidade da polimerase": "Não avaliado.",
        "3. Mecanismo da fita lagging": "Não avaliado.",
        "4. Papel do primer e da primase": "Não avaliado.",
        "5. Integração entre as limitações": "Não avaliado."
    }

    if not answers_list:
        return {k: "Sem dados suficientes na turma." for k in default_resp.keys()}

    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            return default_resp
            
        try:
            response = client.chat.completions.create(
                model=EVAL_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            print(f"🔄 Tentativa {attempt+1}/{max_retries} falhou no Class Criteria Analysis: {e}")
            if attempt == max_retries - 1:
                return default_resp
            time.sleep(1)
