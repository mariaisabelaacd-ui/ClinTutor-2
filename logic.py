import os
import json
from datetime import datetime
from typing import Dict, List, Any, Generator
import google.generativeai as genai
import streamlit as st  
import numpy as np

print("DEBUG: LOADED LOGIC.PY v2 (MOLECULAR BIOLOGY)")

# =============================
# CONFIGURAÇÃO DA IA (GEMINI)
# =============================
try:
    if 'google_api' in st.secrets and 'api_key' in st.secrets['google_api']:
        GOOGLE_API_KEY = st.secrets['google_api']['api_key']
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", None)
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
        else:
            # Em vez de falhar silenciosamente, printa no console
            print("AVISO: Chave de API não encontrada.")
            GOOGLE_API_KEY = None
except Exception as e:
    print(f"Erro na configuração da IA: {e}")
    GOOGLE_API_KEY = None

GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

APP_NAME = "BioTutor"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".clintutor")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_PATH = os.path.join(DATA_DIR, "progresso_gamificado.json")

# =============================
# Base de Conhecimento: Genética e Biologia Molecular
# =============================
QUESTIONS: List[Dict[str, Any]] = [
    {
      "id": "q1_nucleotideo",
      "pergunta": "Qual a estrutura do nucleotídeo?",
      "componentes_conhecimento": ["Química dos nucleotídeos"],
      "resposta_esperada": "O nucleotídeo é composto por uma base nitrogenada, uma pentose e um ou mais grupos fosfato.",
      "erro_critico": "Nucleotídeo é uma base do DNA",
      "pontuacao": 1,
      "dificuldade": "básico"
    },
    {
      "id": "q2_ribose_vs_desoxi",
      "pergunta": "Compare ribose e desoxirribose destacando a diferença no carbono 2’ e por que isso distingue RNA de DNA.",
      "componentes_conhecimento": ["Química dos nucleotídeos"],
      "resposta_esperada": "Ribose possui OH no carbono 2’, enquanto a desoxirribose tem H; essa ausência do 2’-OH caracteriza o DNA e ajuda a distingui-lo do RNA.",
      "pontuacao": 1,
      "dificuldade": "básico"
    },
    {
      "id": "q3_nucleosideo_vs_nucleotideo",
      "pergunta": "Defina nucleosídeo e nucleotídeo e explique por que apenas um deles forma polímeros.",
      "componentes_conhecimento": ["Química dos nucleotídeos"],
      "resposta_esperada": "Nucleosídeo é formado por base e pentose; nucleotídeo inclui fosfato, que viabiliza ligações fosfodiéster e a formação do polímero.",
      "pontuacao": 1,
      "dificuldade": "básico"
    },
    {
      "id": "q4_atp_damp_ump",
      "pergunta": "Explique o que significam ATP, dAMP e UMP (açúcar, base e número de fosfatos).",
      "componentes_conhecimento": ["Nomenclatura de nucleotídeos"],
      "resposta_esperada": "ATP é adenosina trifosfato, dAMP é desoxiadenosina monofosfato, UMP é uridina monofosfato.",
      "pontuacao": 1,
      "dificuldade": "básico"
    },
    {
      "id": "q5_purinas_pirimidinas",
      "pergunta": "Resuma as diferenças estruturais entre bases púricas e pirimídicas e relacione com o pareamento na dupla hélice.",
      "componentes_conhecimento": ["Estrutura das bases nitrogenadas e pareamento"],
      "resposta_esperada": "Purinas (A,G) têm dois anéis; pirimidinas (C,T) um anel; pareamento purina-pirimidina ajuda a manter diâmetro constante da hélice.",
      "erro_critico": "A e G são pirimidinas; T e C são purinas",
      "pontuacao": 1,
      "dificuldade": "básico"
    },
    {
      "id": "q6_dna_definicao",
      "pergunta": "O que é DNA? Responda incluindo do que ele é feito e que tipo de informação ele armazena.",
      "componentes_conhecimento": ["Estrutura química do DNA", "Organização da dupla hélice"],
      "resposta_esperada": "DNA é um polímero de desoxirribonucleotídeos; a ordem das bases (A, T, C, G) codifica informação hereditária e instruções para produzir RNAs e proteínas.",
      "erro_critico": "DNA é uma proteína ou é feito de aminoácidos",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q7_5_3_line",
      "pergunta": "O que representam as denominações 5' e 3' de uma cadeia polinucleotídica?",
      "componentes_conhecimento": ["Organização da dupla hélice"],
      "resposta_esperada": "Uma extremidade termina em 5’-fosfato e a outra em 3’-hidroxila; sequências são sintetizadas com referência a 5’→3’.",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q8_ligacao_fosfodiester",
      "pergunta": "O que é a ligação fosfodiéster e qual é a consequência dela para a estrutura da fita de DNA?",
      "componentes_conhecimento": ["Interações do DNA"],
      "resposta_esperada": "Ligação covalente 3’–5’ entre nucleotídeos, formando o esqueleto açúcar-fosfato contínuo e conferindo estabilidade e polaridade à fita.",
      "erro_critico": "Ligação fraca ou ligação de hidrogênio entre bases",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q9_complementaridade",
      "pergunta": "Explique o que é complementaridade de bases e dê um exemplo.",
      "componentes_conhecimento": ["Interações do DNA"],
      "resposta_esperada": "Cada base pareia preferencialmente com sua complementar (A com T; G com C) ou uma purina sempre com uma pirimidina.",
      "erro_critico": "A pareia com C ou G pareia com T",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q10_antiparalelismo",
      "pergunta": "O que significa dizer que as fitas do DNA são antiparalelas?",
      "componentes_conhecimento": ["Organização da dupla hélice"],
      "resposta_esperada": "A extremidade 3' de uma fita está pareada à extremidade 5' da fita complementar; enquanto uma fita vai 5'→3', a outra está no sentido contrário.",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q11_interacoes_fitas",
      "pergunta": "Quais interações mantêm as duas fitas unidas na dupla hélice? Diferencie o que une na mesma fita vs entre fitas.",
      "componentes_conhecimento": ["Interações do DNA"],
      "resposta_esperada": "Na mesma fita: fosfodiéster (covalente). Entre fitas: ligações de hidrogênio e empilhamento de bases que estabilizam a hélice.",
      "erro_critico": "As fitas são unidas por ligações peptídicas",
      "pontuacao": 2,
      "dificuldade": "intermediário"
    },
    {
      "id": "q12_dna_armazenamento",
      "pergunta": "Explique por que o DNA é adequado para armazenar informação por longos períodos.",
      "componentes_conhecimento": ["Estrutura química do DNA", "Organização da dupla hélice"],
      "resposta_esperada": "O backbone covalente é estável, a informação está na sequência, a dupla hélice protege as bases e a complementaridade permite cópia fiel e reparo.",
      "erro_critico": "Porque o DNA tem desoxirribose, sendo menos reativo",
      "pontuacao": 3,
      "dificuldade": "avançado"
    },
    {
      "id": "q13_complementaridade_func",
      "pergunta": "Por que a complementaridade de bases permite que o DNA funcione como molde na replicação e transcrição?",
      "componentes_conhecimento": ["Organização da dupla hélice", "Estrutura química do DNA"],
      "resposta_esperada": "Uma fita contém a informação para gerar a outra por regras de pareamento; enzimas usam a fita molde para adicionar nucleotídeos complementares.",
      "pontuacao": 3,
      "dificuldade": "avançado"
    },
    {
      "id": "q14_hidrogenio_vs_empilhamento",
      "pergunta": "Compare o papel das ligações de hidrogênio com o empilhamento de bases na estabilidade do DNA.",
      "componentes_conhecimento": ["Organização da dupla hélice"],
      "resposta_esperada": "Ligações de hidrogênio definem o pareamento e contribuem para coesão; o empilhamento hidrofóbico/van der Waals contribui fortemente para estabilidade global.",
      "erro_critico": "Apenas as ligações de hidrogênio são importantes",
      "pontuacao": 3,
      "dificuldade": "avançado"
    },
    {
      "id": "q15_desnaturacao",
      "pergunta": "O que acontece com a dupla hélice durante a desnaturação?",
      "componentes_conhecimento": ["Organização da dupla hélice", "Interações do DNA"],
      "resposta_esperada": "Rompem-se interações entre fitas (ligações de hidrogênio e empilhamento), mas o backbone fosfodiéster geralmente permanece intacto.",
      "erro_critico": "Desnaturação rompe ligação fosfodiéster",
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
    if not GOOGLE_API_KEY:
        return {"correct": False, "feedback": "Erro: Chave API ausente.", "evaluation_type": "error"}

    prompt = f"""
    CONTEXTO:
    Pergunta: "{question_data['pergunta']}"
    Resposta Esperada: "{question_data['resposta_esperada']}"
    Erro Crítico: "{question_data.get('erro_critico', 'N/A')}"
    
    ALUNO: "{user_answer}"
    
    Avalie se está correto. Retorne JSON:
    {{
        "correct": true/false,
        "classification": "CORRETA" | "PARCIALMENTE CORRETA" | "INCORRETA",
        "feedback": "Explicação curta."
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-pro", generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except:
             # Fallback
            txt = response.text.lower()
            acc = "true" in txt or "correta" in txt
            return {"correct": acc, "classification": "CORRETA" if acc else "INCORRETA", "feedback": response.text}
    except Exception as e:
        return {"correct": False, "feedback": f"Erro IA: {e}", "evaluation_type": "error"}

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
    if not GOOGLE_API_KEY:
        yield "Erro: Chave API ausente."
        return

    contexto = _construir_contexto_para_ia(question, chat_history)
    prompt = f"""
    Você é um Tutor de Biologia Molecular.
    Objetivo: Guiar o aluno a responder a questão: "{question['pergunta']}".
    NUNCA dê a resposta final: "{question['resposta_esperada']}".
    Contexto: {contexto}
    Aluno: "{user_msg}"
    """
    try:
        model = genai.GenerativeModel("gemini-pro", generation_config={"temperature": 0.7})
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            yield chunk.text
    except Exception as e:
        yield f"Erro na IA: {e}"

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
    allowed_diffs = LEVEL_MAP.get(level, ["básico"])
    
    pool = [q for q in QUESTIONS if q["dificuldade"] in allowed_diffs]
    available = [q for q in pool if q["id"] not in used_cases]
    
    if not available: available = pool # Reset se acabar
    if not available: return QUESTIONS[0]
    
    return np.random.choice(available).copy()

def get_case(cid: str) -> Dict[str, Any]:
    for q in QUESTIONS:
        if q["id"] == cid: return q
    return QUESTIONS[0]

def finalize_question_response(question: Dict[str, Any], user_answer: str, ai_evaluation: Dict[str, Any]) -> Dict[str, Any]:
    is_correct = ai_evaluation.get("correct", False)
    points = 10 if is_correct else 2
    return {
        "points_gained": int(points),
        "is_correct": is_correct,
        "classification": ai_evaluation.get("classification", "INCORRETA"),
        "feedback": ai_evaluation.get("feedback", ""),
        "user_answer": user_answer
    }

# Compatibilidade para analytics
CASES = QUESTIONS
def correct_exam_name(n): return n, False
def normalize_exam_name(n): return n
def suggest_exam_corrections(n, a): return ""
