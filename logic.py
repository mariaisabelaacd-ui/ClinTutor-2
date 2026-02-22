import os
import json
from datetime import datetime
from typing import Dict, List, Any, Generator
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Generator
from groq import Groq
import streamlit as st  
import numpy as np

print("DEBUG: LOADED LOGIC.PY v4 (GROQ SDK - LLAMA 3)")

# =============================
# CONFIGURAÇÃO DA IA (GROQ)
# =============================
GROQ_API_KEY = None
CLIENT = None

try:
    import toml
    
    # Bypass st.secrets to avoid caching issues
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    print(f"DEBUG: Loading secrets from {secrets_path}")
    
    try:
        with open(secrets_path, "r") as f:
            secrets_data = toml.load(f)
            
        if 'groq_api' in secrets_data and 'api_key' in secrets_data['groq_api']:
            GROQ_API_KEY = secrets_data['groq_api']['api_key']
            print(f"DEBUG: Loaded Key Direct: {GROQ_API_KEY[:5]}...{GROQ_API_KEY[-5:]}")
            CLIENT = Groq(api_key=GROQ_API_KEY)
        else:
            print("AVISO: Chave api_key do groq não encontrada no TOML.")
    except Exception as e:
        print(f"Erro ao carregar TOML direto: {e}")
except ImportError:
    print("AVISO: Biblioteca toml não instalada.")

if not CLIENT:
    # Fallback to st.secrets just in case
    try:
        GROQ_API_KEY = st.secrets["groq_api"]["api_key"]
        CLIENT = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Erro no Fallback st.secrets: {e}")
        CLIENT = None

# Modelo Padrão do Groq
MODEL_NAME = "llama-3.3-70b-versatile"

APP_NAME = "Helix.AI"
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
    if not CLIENT:
        return {"correct": False, "feedback": "Erro: Cliente IA não configurado.", "evaluation_type": "error"}

    prompt = f"""
    ATENÇÃO: Você é um professor rigoroso. Sua principal tarefa é avaliar se a RESPOSTA DO ALUNO responde DE FATO à PERGUNTA ATUAL.
    Se o aluno escrever um fato biológico correto, mas que NÃO responda ao que foi especificamente perguntado, você DEVE marcar como INCORRETA.
    
    CONTEXTO DA QUESTÃO:
    Pergunta Atual: "{question_data['pergunta']}"
    Resposta Esperada: "{question_data['resposta_esperada']}"
    Erro Crítico: "{question_data.get('erro_critico', 'N/A')}"
    
    RESPOSTA DO ALUNO: "{user_answer}"
    
    Avalie a resposta. 
    Responda APENAS com um JSON válido (sem markdown), neste formato estrito:
    {{
        "correct": true/false,
        "classification": "CORRETA" | "PARCIALMENTE CORRETA" | "INCORRETA",
        "feedback": "Explicação curta."
    }}
    """
    
    # Retry logic for 503 errors
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = CLIENT.chat.completions.create(
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
            print(f"Tentativa {attempt+1} falhou: {e}")
            if attempt == max_retries - 1:
                return {"correct": False, "feedback": f"Erro IA (pós retentativas): {e}", "evaluation_type": "error"}
            time.sleep(1) # Espera antes de tentar de novo

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
    if not CLIENT:
        yield "Erro: Cliente IA não configurado."
        return

    contexto = _construir_contexto_para_ia(question, chat_history)
    prompt = f"""
    Você é um Tutor Inteligente de Biologia Molecular da plataforma Helix.AI.
    Objetivo: Guiar o aluno a responder a questão: "{question['pergunta']}".
    NUNCA dê a resposta final: "{question['resposta_esperada']}".
    Contexto: {contexto}
    Aluno: "{user_msg}"
    """
    try:
        stream = CLIENT.chat.completions.create(
            model=MODEL_NAME, 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
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
    classification = ai_evaluation.get("classification", "INCORRETA").upper()
    max_points = question.get("pontuacao", 1)  # Default to 1 if not set (Level 1)
    
    if "PARCIAL" in classification:
        points = max_points * 0.5
        is_correct = True # Counts as correct/progress for streak purposes? Or maybe distinct?
        outcome = "partial"
    elif "CORRETA" in classification and "INCORRETA" not in classification: # Strict check
        points = max_points
        is_correct = True
        outcome = "correct"
    else:
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
