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
      "pergunta": "O que acontece com a dupla hélice durante a desnaturação? O que se rompe e o que permanece intacto?",
      "componentes_conhecimento": ["Organização da dupla hélice: complementaridade e antiparalelismo", "Interações que estabilizam e permitem dinâmica do DNA"],
      "resposta_esperada": "Rompem-se principalmente as interações entre fitas (ligações de hidrogênio e empilhamento de bases); o backbone fosfodiéster permanece intacto (a fita de DNA continua íntegra). A desnaturação NÃO rompe a ligação fosfodiéster.",
      "erro_critico": "Afirmar que a desnaturação rompe a ligação fosfodiéster",
      "pontuacao": 3,
      "dificuldade": "avançado"
    },
    {
      "id": "q16_circular_vs_linear",
      "pergunta": "Compare, do ponto de vista estrutural, DNA circular e DNA linear: que desafios de organização e manutenção cada um impõe para a célula?",
      "componentes_conhecimento": ["Estrutura química do DNA como polímero de nucleotídeos", "Interações que estabilizam e permitem dinâmica do DNA"],
      "resposta_esperada": "DNA circular: maior impacto de topologia (superenrolamento e necessidade de controle por topoisomerases). DNA linear: presença de extremidades (telômeros) exige estratégias específicas de proteção e replicação. Ambos precisam ser compactados e manter acessibilidade para transcrição e replicação.",
      "erro_critico": "Não mencionar superenrolamento no circular ou não mencionar o problema das extremidades no linear",
      "pontuacao": 3,
      "dificuldade": "avançado"
    },
    {
      "id": "q17_ions_ph_dna",
      "pergunta": "Explique como mudanças no ambiente (íons, força iônica, pH) podem alterar a estrutura do DNA e, por consequência, afetar a expressão gênica ou a replicação.",
      "componentes_conhecimento": ["Interações que estabilizam e permitem dinâmica do DNA", "Estrutura química do DNA como polímero de nucleotídeos"],
      "resposta_esperada": "Íons (ex: Mg²⁺, Na⁺) estabilizam ao neutralizar a repulsão entre os fosfatos negativos do backbone. Variações de pH afetam o pareamento de bases (ionização das bases rompe pontes de hidrogênio). Queda de força iônica desestabiliza a hélice. Essas mudanças podem impedir o acesso de enzimas, alterar a conformação do DNA e comprometer a fidelidade da replicação ou transcrição.",
      "erro_critico": "Não relacionar o efeito dos íons com a repulsão dos fosfatos, ou não mencionar que pH afeta as bases",
      "pontuacao": 3,
      "dificuldade": "avançado"
    },
    {
      "id": "q18_absorbancia_260nm",
      "pergunta": "Por que a absorbância a 260 nm é mais alta para um DNA fita simples do que para um DNA fita dupla? O que isso indica sobre a estrutura das bases?",
      "componentes_conhecimento": ["Estrutura química do DNA como polímero de nucleotídeos", "Organização da dupla hélice: complementaridade e antiparalelismo"],
      "resposta_esperada": "Na fita dupla, o empilhamento das bases nitrogenadas (stacking) e o pareamento reduzem a exposição delas ao solvente e diminuem a absorção de UV (efeito hipocrômico). Na fita simples, as bases ficam mais expostas ao UV, aumentando a absorbância. Quando o DNA se desnatura (separação das fitas), a absorbância a 260 nm aumenta — fenômeno chamado efeito hipercrômico — e pode ser usado para monitorar a temperatura de melting (Tm).",
      "erro_critico": "Inverter e dizer que DNA fita dupla absorve mais, ou não mencionar o empilhamento de bases como causa",
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
