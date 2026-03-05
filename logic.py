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

# Modelo Padrão do Groq (Versão 8B para limite muito maior de tokens por minuto)
MODEL_NAME = "llama-3.1-8b-instant"

APP_NAME = "Helix.AI"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".clintutor")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_PATH = os.path.join(DATA_DIR, "progresso_gamificado.json")

# =============================
# Base de Conhecimento: Genética e Biologia Molecular
# =============================
QUESTIONS: List[Dict[str, Any]] = [
    {
      "id": "q_dna_replicacao_multicriterio",
      "pergunta": "A dupla fita do DNA é antiparalela. Defina antiparalelismo e explique, considerando os mecanismos de funcionamento da DNA polimerase, de que forma essa característica impõe limitações à replicação do DNA e quais mecanismos moleculares a célula utiliza para contorná-las.",
      "componentes_conhecimento": [
          "1. Compreensão do antiparalelismo",
          "2. Limitação da direcionalidade da polimerase",
          "3. Mecanismo da fita lagging",
          "4. Papel do primer e da primase",
          "5. Integração entre as limitações"
      ],
      "resposta_esperada": "O antiparalelismo da dupla fita do DNA significa que as duas fitas correm em direções opostas — uma no sentido 5'→3' e a outra no sentido 3'→5'. Isso impõe duas limitações fundamentais à replicação.\nPrimeira limitação: a DNA polimerase só sintetiza no sentido 5'→3'\nComo a enzima só consegue adicionar nucleotídeos na extremidade 3' da fita em crescimento, ela consegue acompanhar a forquilha de replicação continuamente em apenas uma das fitas — a fita leading — que já está orientada no sentido favorável. Na fita complementar, a fita lagging, a orientação é oposta à direção de abertura da forquilha, o que impede a síntese contínua. A célula resolve isso sintetizando a fita lagging em pequenos segmentos no sentido contrário ao avanço da forquilha — os fragmentos de Okazaki — que posteriormente são unidos pela DNA ligase após remoção dos primers.\nSegunda limitação: a DNA polimerase não consegue iniciar a síntese do zero\nA enzima exige uma extremidade 3'-OH livre para começar a trabalhar, ou seja, ela só estende uma fita existente, nunca inicia uma. Para contornar isso, a primase sintetiza pequenos segmentos de RNA chamados primers, que fornecem a extremidade 3'-OH necessária para que a DNA polimerase inicie a síntese em ambas as fitas — e em cada novo fragmento de Okazaki na fita lagging. Após a síntese, os primers são removidos, substituídos por DNA e as lacunas resultantes são seladas pela ligase.\nConsequência integradora\nAs duas limitações estão conectadas: é justamente porque a polimerase não inicia do zero e só trabalha em um sentido que a fita lagging precisa de múltiplos primers e é sintetizada de forma descontínua. O antiparalelismo, portanto, não gera um único problema — gera uma cadeia de necessidades mecanísticas.",
      "erro_critico": "Afirmar que as fitas são sintetizadas na mesma direção (3'->5') ou omitir que a DNA Polimerase só sintetiza no sentido 5'->3'.",
      "pontuacao": 10,
      "dificuldade": "avançado"
    }
]

# Mapping de nivel para filtrar perguntas
LEVEL_MAP = {
    1: ["básico", "intermediário", "avançado"],
    2: ["básico", "intermediário", "avançado"],
    3: ["básico", "intermediário", "avançado"]
}



def evaluate_answer_with_ai(question_data: Dict, user_answer: str) -> Dict[str, Any]:
    prompt = f"""
Você é um avaliador acadêmico preciso para uma plataforma de ensino de Genética e Biologia Molecular.
Sua tarefa é avaliar a resposta do aluno em relação ao gabarito esperado, focando ESTRITAMENTE em 5 critérios.

Pergunta: {question_data.get('pergunta')}
Resposta Esperada / Gabarito: {question_data.get('resposta_esperada')}

Resposta do Aluno: {user_answer}

AVALIE CADA UM DOS 5 CRITÉRIOS ABAIXO com as notas: "Completa", "Parcial" ou "Ausente".
1. Compreensão do antiparalelismo:
   - Completa: Explica 5'→3' e 3'→5' e identifica isso como origem das limitações
   - Parcial: Menciona que as fitas têm direções opostas mas não conecta ao problema
   - Ausente: Não explica o que é antiparalelismo ou usa o termo sem definição

2. Limitação da direcionalidade da polimerase:
   - Completa: Conecta a direcionalidade (5'→3') ao problema específico da fita lagging e à necessidade de síntese descontínua
   - Parcial: Menciona que a polimerase tem uma direção preferencial sem explicar a consequência
   - Ausente: Não menciona a restrição direcional da enzima

3. Mecanismo da fita lagging:
   - Completa: Descreve fragmentos de Okazaki, direção de síntese e necessidade de ligação posterior
   - Parcial: Menciona síntese descontínua mas não explica por quê ocorre
   - Ausente: Não distingue fita leading de lagging

4. Papel do primer e da primase:
   - Completa: Explica que a polimerase não inicia do zero, que a primase sintetiza o primer de RNA e que ele fornece a extremidade 3'-OH necessária
   - Parcial: Cita o primer mas não explica sua função ou origem
   - Ausente: Não menciona a necessidade de primer

5. Integração entre as limitações:
   - Completa: Articula que a necessidade de múltiplos primers na fita lagging é consequência simultânea da direcionalidade da polimerase e do antiparalelismo
   - Parcial: Percebe que há mais de um problema mas não os conecta mecanisticamente
   - Ausente: Trata as limitações como problemas independentes e sem relação ou não cita.

DIRETRIZES FINAIS:
- Se TODOS ou quase todos (4 ou 5) critérios forem "Completa", a "classification" deve ser "CORRETA".
- Se houver mescla de Parcial/Completa ou alguns Ausentes, a "classification" deve ser "PARCIALMENTE CORRETA".
- Se quase tudo for Ausente ou houver erros conceituais graves, a "classification" é "INCORRETA".

Retorne SUA AVALIAÇÃO ESTRITAMENTE NESTE FORMATO JSON VÁLIDO:
{{
  "correct": true ou false,
  "classification": "CORRETA", "PARCIALMENTE CORRETA" ou "INCORRETA",
  "criterios": {{
       "antiparalelismo": "Completa|Parcial|Ausente",
       "direcionalidade": "Completa|Parcial|Ausente",
       "lagging": "Completa|Parcial|Ausente",
       "primer": "Completa|Parcial|Ausente",
       "integracao": "Completa|Parcial|Ausente"
  }},
  "feedback": "Um texto claro indicando o que ele acertou e o que faltou, baseando-se nos 5 critérios."
}}
NÃO RETORNE TEXTO FORA DO JSON.
"""
    # Retry logic for Rate Limits (429) & 503 errors
    import time
    max_retries = 3
    for attempt in range(max_retries):
        # MUDANÇA CRÍTICA: Instanciar um NOVO client a cada tentativa para pegar uma nova chave
        client = get_groq_client()
        if not client:
            return {"correct": False, "feedback": "Erro: Cliente IA não configurado. Verifique as chaves.", "evaluation_type": "error"}
            
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(text)
            except:
                 # Fallback se a IA não retornar JSON limpo
                lower_text = text.lower()
                if "parcial" in lower_text:
                    is_correct = True
                    classification = "PARCIALMENTE CORRETA"
                else:
                    is_correct = "true" in lower_text or "correta" in lower_text
                    classification = "CORRETA" if is_correct else "INCORRETA"
                    
                return {
                    "correct": is_correct,
                    "classification": classification, 
                    "feedback": text
                }
                
        except Exception as e:
            print(f"🔄 Tentativa {attempt+1}/{max_retries} falhou no Avaliador IA: {e}")
            if attempt == max_retries - 1:
                return {"correct": False, "feedback": f"Erro IA após tentar múltiplas chaves: {e}", "evaluation_type": "error"}
            time.sleep(1) # Espera antes de tentar de novo com uma CHAVE DIFERENTE

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
    prompt = f"""
    SITUAÇÃO: Você é um Tutor Inteligente estritamente Socrático de Biologia Molecular da plataforma Helix.AI.
    OBJETIVO: O aluno está tentando responder a seguinte questão: "{question['pergunta']}".
    A resposta correta para essa questão seria: "{question['resposta_esperada']}".

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
            return # Sai da função se o stream completou com sucesso sem crashar
        except Exception as e:
            print(f"🔄 Tentativa {attempt+1}/{max_retries} falhou no Tutor Chat: {e}")
            if attempt == max_retries - 1:
                yield f"Erro na IA após tentar múltiplas chaves: {e}"
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

LEVEL_THRESHOLDS = {1: 0, 2: 120, 3: 300}
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
        if q["id"] == cid: return q
    return QUESTIONS[0]

def finalize_question_response(question: Dict[str, Any], user_answer: str, ai_evaluation: Dict[str, Any]) -> Dict[str, Any]:
    classification = ai_evaluation.get("classification", "INCORRETA").upper()
    max_points = question.get("pontuacao", 1)  # Default to 1 if not set (Level 1)
    
    if "PARCIAL" in classification:
        points = max_points * 0.5
        is_correct = True # Counts as correct/progress for streak purposes? Or maybe distinct?
        outcome = "partial"
    elif "INCORRETA" in classification and "PARCIAL" not in classification: # Strict check
        points = 0
        is_correct = False
        outcome = "incorrect"
    elif "CORRETA" in classification:
        points = max_points
        is_correct = True
        outcome = "correct"
    else:
        # Fallback if AI gave something weird
        points = 0
        is_correct = False
        outcome = "incorrect"
        
    return {
        "points_gained": float(points),
        "is_correct": is_correct,
        "classification": classification,
        "outcome": outcome,
        "feedback": ai_evaluation.get("feedback", ""),
        "user_answer": user_answer
    }

# Compatibilidade para analytics
CASES = QUESTIONS
def correct_exam_name(n): return n, False
def normalize_exam_name(n): return n
def suggest_exam_corrections(n, a): return ""

def generate_category_insights(category_name: str, sample_answers: List[str]) -> str:
    """
    Gera uma análise pedagógica focada em uma categoria de conhecimento, 
    usando as piores respostas dos alunos como base.
    """
    answers_str = "\n\n".join([f"Exemplo {i+1}:\n\"{ans}\"" for i, ans in enumerate(sample_answers)])
    
    prompt = f"""
Você é um Diretor Pedagógico sênior especialista em análise de aprendizagem.
Sua tarefa é analisar as respostas incorretas ou parciais de uma turma para o tópico '{category_name}'.

**Amostra Real das Respostas Incorretas dos Alunos neste Tópico:**
{answers_str if sample_answers else "Nenhuma amostra disponível."}

**O QUE VOCÊ DEVE FAZER:**
1. Escreva um resumo direto e executivo (max 2 parágrafos) analisando o que exatamente os alunos não estão entendendo sobre este tópico com base na amostra recebida. Qual é a falha conceitual principal?
2. Sugira 2 a 3 estratégias curtas e práticas que o professor pode usar em sala de aula para corrigir essa defasagem.
3. Mantenha um tom profissional e encorajador.
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
    Gera um preview curto e direto (1-2 frases) sobre a principal dificuldade
    dos alunos em uma categoria específica.
    """
    answers_str = "\n".join([f"- \"{ans}\"" for ans in sample_answers[:5]]) # Pega até 5 respostas
    
    prompt = f"""
Sua tarefa é ler as respostas incorretas dos alunos sobre o tópico '{category_name}' e identificar a principal falha conceitual.

**Amostras de Respostas Incorretas:**
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
    Analisa uma amostra de respostas da turma e gera um feedback curto
    sobre como a turma foi em cada um dos 5 critérios estabelecidos.
    """
    answers_str = "\n".join([f"- Resposta de Aluno: \"{ans}\"" for ans in answers_list[:15]])
    
    prompt = f"""
Sua tarefa é analisar uma amostra de respostas recentes da turma para a questão sobre "Antiparalelismo e Limitações da DNA Polimerase".

**Amostra de Respostas Recentes:**
{answers_str}

**O QUE VOCÊ DEVE FAZER:**
Analise o desempenho da turma (mesmo que haja apenas UMA única resposta na amostra) em relação aos 5 critérios de avaliação abaixo.
Para cada critério, escreva UMA FRASE CURTA resumindo o nível de compreensão (Exemplo: "O aluno entende que os sentidos são opostos" ou "Faltou citar a primase").

Critérios:
1. Compreensão do antiparalelismo
2. Limitação da direcionalidade da polimerase
3. Mecanismo da fita lagging
4. Papel do primer e da primase
5. Integração entre as limitações

Devolva ESTRITAMENTE um JSON no formato abaixo, sem nenhum texto extra fora do JSON.
{{
    "Compreensão do antiparalelismo": "frase de análise",
    "Limitação da direcionalidade da polimerase": "frase de análise",
    "Mecanismo da fita lagging": "frase de análise",
    "Papel do primer e da primase": "frase de análise",
    "Integração entre as limitações": "frase de análise"
}}
"""

    import time
    import json
    max_retries = 2
    default_resp = {
        "Compreensão do antiparalelismo": "Não foi possível analisar adequadamente.",
        "Limitação da direcionalidade da polimerase": "Não avaliado.",
        "Mecanismo da fita lagging": "Não avaliado.",
        "Papel do primer e da primase": "Não avaliado.",
        "Integração entre as limitações": "Não avaliado."
    }

    if not answers_list:
        return {k: "Sem dados suficientes na turma." for k in default_resp.keys()}

    for attempt in range(max_retries):
        client = get_groq_client()
        if not client:
            return default_resp
            
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        except Exception as e:
            if attempt == max_retries - 1:
                return default_resp
            time.sleep(1)
