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
      "id": "q_meselson_stahl",
      "pergunta": "O experimento de Meselson e Stahl demonstrou que a replicação do DNA é semiconservativa. Explique o que significa esse mecanismo e por que ele é biologicamente relevante para a manutenção da informação genética.",
      "componentes_conhecimento": ["Mecanismo semiconservativo de replicação"],
      "resposta_esperada": "Na replicação semiconservativa, a dupla-fita de DNA parental é separada, e cada fita serve como molde para a síntese de uma nova fita complementar. O resultado são duas moléculas-filhas, cada uma contendo uma fita original (parental) e uma fita recém-sintetizada. Esse mecanismo garante que a informação genética seja fielmente copiada e transmitida às células-filhas, pois a fita parental serve como gabarito altamente preciso para a montagem da nova fita.",
      "erro_critico": "Confundir com replicação conservativa (molde permanece intacto) ou dispersiva. Afirmar que ambas as fitas são completamente novas. Não mencionar que cada fita parental serve como molde.",
      "pontuacao": 1,
      "dificuldade": "básico"
    },
    {
      "id": "q_dna_polimerase_requisitos",
      "pergunta": "A DNA polimerase requer condições especiais para sintetizar DNA. Quais são os componentes obrigatórios para sua ação e quais são suas principais limitações funcionais?",
      "componentes_conhecimento": ["As características e limitações funcionais da DNA polimerase"],
      "resposta_esperada": "A DNA polimerase possui os seguintes requisitos: Molde (template) — uma fita de DNA simples para servir de base; Primer — um oligonucleotídeo (geralmente de RNA) com extremidade 3'-OH livre, pois a DNA polimerase não consegue iniciar síntese do zero; Desoxirribonucleotídeos trifosfato (dNTPs) — os substratos energéticos. Limitações: só sintetiza no sentido 5'→3'; não consegue iniciar uma nova fita sem primer.",
      "erro_critico": "Afirmar que a DNA polimerase pode iniciar a síntese sem um primer. Dizer que a energia vem de outra fonte. Omitir a importância do molde.",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q_direcionalidade_5_3",
      "pergunta": "A síntese de DNA ocorre exclusivamente no sentido 5'→3'. Explique por que isso ocorre e quais são as consequências dessa direcionalidade para a síntese da fita lagging.",
      "componentes_conhecimento": ["A direcionalidade da síntese de DNA (5'→3')", "As características e limitações funcionais da DNA polimerase"],
      "resposta_esperada": "A direcionalidade 5'→3' está diretamente associada à adição de nucleotídeos ao 3'-OH livre da fita crescente — a DNA polimerase só catalisa essa reação nesse sentido. Durante a síntese 5'→3', o substrato da reação é o dNTP que entra na posição 5'. Como as duas fitas são antiparalelas, apenas a fita leading pode ser sintetizada continuamente; a fita lagging deve ser sintetizada em fragmentos (fragmentos de Okazaki), cada um com seu próprio primer, no sentido oposto ao da abertura da forquilha. Se a polimerase sintetizasse no sentido 3'→5', não haveria liberação do pirofosfato na direção correta e a reação seria energeticamente desfavorável.",
      "erro_critico": "Não relacionar a direcionalidade ao 3'-OH livre. Confundir os sentidos das fitas. Não discutir o que acontece com a fita lagging.",
      "pontuacao": 3,
      "dificuldade": "avançado"
    }
]

# Mapping de nivel para filtrar perguntas
LEVEL_MAP = {
    1: ["básico"],
    2: ["básico", "intermediário"],
    3: ["básico", "intermediário", "avançado"]
}



def evaluate_answer_with_ai(question_data: Dict, user_answer: str) -> Dict[str, Any]:
    prompt = f"""
Você é um avaliador acadêmico preciso para uma plataforma de ensino de Genética e Biologia Molecular.
Sua tarefa é avaliar a resposta do aluno em relação ao gabarito esperado.

Pergunta: {question_data.get('pergunta')}
Conceitos-chave: {', '.join(question_data.get('componentes_conhecimento', []))}
Resposta Esperada / Gabarito: {question_data.get('resposta_esperada')}
Erro Crítico a penalizar com nota zero (se houver aplicável): {question_data.get('erro_critico', 'Nenhum')}

Resposta do Aluno: {user_answer}

DIRETRIZES DE AVALIAÇÃO:
1. CORRETA: O aluno acertou **perfeitamente** o cerne da questão e **NÃO OMITIU** nenhum detalhe relevante do gabarito esperado. A resposta deve ser completa, precisa e cobrir todos os pontos principais.
2. PARCIALMENTE CORRETA: O aluno acertou parte da resposta ou demonstrou conhecimento válido, mas **COMETEU PEQUENOS ERROS, FOI IMPRECISO OU DEIXOU A RESPOSTA INCOMPLETA**. Se faltar qualquer informação importante que está no gabarito, você DEVE classificar como PARCIALMENTE CORRETA.
3. INCORRETA: O aluno errou completamente, demonstrou desconhecimento ou cometeu o "Erro Crítico" supracitado.

Avalie a resposta do aluno e retorne SUA AVALIAÇÃO ESTRITAMENTE NESTE FORMATO JSON VÁLIDO:
{{
  "correct": true ou false,
  "classification": "CORRETA" ou "PARCIALMENTE CORRETA" ou "INCORRETA",
  "feedback": "Um texto claro indicando o que ele acertou e o que faltou ou errou."
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

