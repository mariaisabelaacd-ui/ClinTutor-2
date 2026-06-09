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
    print(f"[IA LOGGER] Requisição enviada. Usando chave Groq: {safe_key}", flush=True)
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
# =====================
QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q1_expressao_genica_eucariotos",
        "pergunta": "Explique como a expressão gênica pode ser regulada em eucariotos.",
        "componentes_conhecimento": ["Regulação Gênica", "Promotores e Fatores de Transcrição", "Organização da Cromatina"],
        "referencia": {
            "Básico": {
                "parametros": "O aluno reconhece que a regulação gênica eucariótica é mais complexa que a bacteriana (controlada por promotores, fatores de transcrição, organização da cromatina, enhancers, silenciadores e ligantes/receptores).",
                "resposta_exemplo": "Em eucariotos, a expressão gênica pode ser controlada por promotores, fatores de transcrição e pela organização da cromatina. Regiões como enhancers podem aumentar a transcrição, enquanto silenciadores podem reduzi-la. Alguns ligantes também podem ativar receptores que influenciam a expressão de genes."
            },
            "Intermediário": {
                "parametros": "O aluno explica os principais elementos regulatórios (interação de promotores como organizadores da maquinaria, enhancers com fatores ativadores, silenciadores com repressores, e papel da acetilação de histonas deixando o DNA acessível vs desacetilação compactando a cromatina).",
                "resposta_exemplo": "A transcrição em eucariotos depende da interação entre promotores, fatores de transcrição, enhancers e silenciadores. Promotores são regiões próximas ao gene onde a maquinaria de transcrição se organiza. Enhancers aumentam a transcrição ao favorecer a ação de fatores ativadores, enquanto silenciadores reduzem a expressão gênica. A cromatina também influencia esse processo: histonas acetiladas tendem a deixar o DNA mais acessível, favorecendo a transcrição, enquanto a desacetilação tende a compactar a cromatina e reduzir a expressão."
            },
            "Avançado": {
                "parametros": "O aluno integra cromatina (hiperacetilação vs desacetilação), regulação combinatória transcricional (promotores basais, enhancers/silenciadores modulam intensidade por fatores ativadores/repressores) e sinalização celular (ligantes lipofílicos ativando receptores intracelulares como fatores de transcrição vs ligantes hidrofílicos ativando receptores de membrana e cascatas de sinalização/fosforilação).",
                "resposta_exemplo": "A regulação gênica em eucariotos é combinatória e pode ocorrer em vários níveis. No nível transcricional, promotores recrutam a maquinaria basal, enquanto enhancers e silenciadores modulam a intensidade da transcrição por meio da ligação de fatores ativadores ou repressores. A conformação da cromatina é decisiva: hiperacetilação de histonas favorece uma cromatina mais aberta e transcrição mais eficiente; desacetilação favorece compactação e repressão. Ligantes lipofílicos podem atravessar a membrana e ativar receptores intracelulares que atuam como fatores de transcrição. Ligantes hidrofílicos, por sua vez, geralmente ativam receptores de membrana, iniciando cascatas de sinalização que podem fosforilar fatores reguladores e alterar a expressão gênica."
            }
        },
        "pontuacao_maxima": 3
    },
    {
        "id": "q2_mrna_trna_sintese_proteica",
        "pergunta": "Explique como o RNA mensageiro é interpretado durante a síntese proteica e qual é o papel dos tRNAs nesse processo.",
        "componentes_conhecimento": ["Síntese Proteica", "Códons e Anticódons", "tRNA e Tradução"],
        "referencia": {
            "Básico": {
                "parametros": "O aluno compreende a ideia geral de que o mRNA orienta a produção de proteínas, sendo lido em códons (trincas de bases) que indicam aminoácidos, e os tRNAs transportam os aminoácidos até o ribossomo.",
                "resposta_exemplo": "O RNA mensageiro carrega a informação genética copiada do DNA. Durante a tradução, ele é lido em grupos de três bases chamados códons. Cada códon indica um aminoácido. Os tRNAs transportam os aminoácidos até o ribossomo e ajudam a formar a proteína."
            },
            "Intermediário": {
                "parametros": "O aluno explica a relação entre códon, anticódon e aminoácido (mRNA lido 5' para 3' em códons, tRNAs com anticódons complementares, e papel crítico das aminoacil-tRNA sintetases na ligação correta entre aminoácido e tRNA).",
                "resposta_exemplo": "O mRNA é lido no sentido 5' para 3', em trincas chamadas códons. Cada códon corresponde a um aminoácido ou a um sinal de parada. Os tRNAs possuem anticódons complementares aos códons do mRNA e carregam aminoácidos específicos. A ligação correta entre aminoácido e tRNA é feita pelas aminoacil-tRNA sintetases, que são essenciais para a fidelidade da tradução."
            },
            "Avançado": {
                "parametros": "O aluno explica a fidelidade da tradução e propriedades do código genético (código degenerado, universal e não sobreposto, tRNAs como adaptadores moleculares, papel da aminoacil-tRNA sintetase e flexibilidade de pareamento da terceira base - wobble position).",
                "resposta_exemplo": "Durante a tradução, o mRNA é lido no sentido 5' para 3', em códons de três nucleotídeos. O código genético é degenerado, pois mais de um códon pode codificar o mesmo aminoácido; é praticamente universal; e não é lido de forma sobreposta. Os tRNAs funcionam como adaptadores moleculares: seus anticódons reconhecem códons do mRNA e sua extremidade carrega o aminoácido correspondente. A aminoacil-tRNA sintetase garante que cada tRNA receba o aminoácido correto. A wobble position permite certa flexibilidade no pareamento da terceira base do códon, contribuindo para que um mesmo tRNA reconheça mais de um códon sinônimo."
            }
        },
        "pontuacao_maxima": 3
    },
    {
        "id": "q3_etapas_traducao_sitios",
        "pergunta": "Descreva as principais etapas da tradução e explique a função dos sítios A, P e E do ribossomo.",
        "componentes_conhecimento": ["Etapas da Tradução", "Ribossomo e Sítios A, P, E", "Iniciação e Elongação"],
        "referencia": {
            "Básico": {
                "parametros": "O aluno identifica as etapas principais da tradução (iniciação onde começa a leitura, elongação onde aminoácidos são adicionados, e terminação onde a proteína é liberada no códon de parada).",
                "resposta_exemplo": "A tradução ocorre no ribossomo e possui três etapas principais: iniciação, elongação e terminação. Na iniciação, o ribossomo começa a leitura do mRNA. Na elongação, os aminoácidos são adicionados à cadeia em crescimento. Na terminação, a proteína é liberada quando o ribossomo encontra um códon de parada."
            },
            "Intermediário": {
                "parametros": "O aluno descreve os sítios ribossômicos e o movimento dos tRNAs (sítio A recebe o aminoacil-tRNA, sítio P mantém o peptidil-tRNA com a cadeia em crescimento, sítio E permite a saída do tRNA descarregado, formação de ligações peptídicas e deslocamento/translocação do ribossomo).",
                "resposta_exemplo": "Durante a tradução, o ribossomo organiza a entrada e saída dos tRNAs. O sítio A recebe o aminoacil-tRNA com o próximo aminoácido. O sítio P mantém o tRNA ligado à cadeia polipeptídica em crescimento. O sítio E permite a saída do tRNA descarregado. Na elongação, o ribossomo forma ligações peptídicas e se desloca ao longo do mRNA. A tradução termina quando um códon de parada é reconhecido por fatores de liberação."
            },
            "Avançado": {
                "parametros": "O aluno integra direção de leitura (mRNA 5' para 3', cadeia N-terminal para C-terminal), iniciação específica (sequência Shine-Dalgarno em procariotos vs quepe 5'/cap em eucariotos), fatores de liberação na terminação, e o impacto regulatório de estruturas secundárias estáveis do mRNA.",
                "resposta_exemplo": "A tradução começa com a iniciação, quando o ribossomo se posiciona no mRNA e reconhece o códon de início. Em procariotos, a sequência Shine-Dalgarno ajuda a alinhar o ribossomo ao códon inicial. Em eucariotos, a iniciação depende de fatores específicos e do reconhecimento da extremidade 5' do mRNA. Durante a elongação, o mRNA é lido no sentido 5' para 3', enquanto a cadeia polipeptídica cresce do N-terminal para o C-terminal. O sítio A recebe o novo aminoacil-tRNA, o sítio P mantém a cadeia em crescimento e o sítio E libera o tRNA descarregado. Na terminação, fatores de liberação reconhecem códons de parada e promovem a liberação da proteína. Estruturas secundárias muito estáveis no mRNA podem dificultar a iniciação ou o avanço do ribossomo, reduzindo a eficiência da tradução."
            }
        },
        "pontuacao_maxima": 3
    },
    {
        "id": "q4_operons_lac_trp",
        "pergunta": "Explique o que é um operon e compare o funcionamento geral do operon lac e do operon do triptofano.",
        "componentes_conhecimento": ["Operons Lac/Trp", "Metabolismo Bacteriano", "Repressão e Indução"],
        "referencia": {
            "Básico": {
                "parametros": "O aluno reconhece que operons são conjuntos de genes bacterianos regulados juntos, e distingue que o operon lac é ativado por lactose e o operon trp é reprimido por triptofano.",
                "resposta_exemplo": "Um operon é um conjunto de genes bacterianos regulados em conjunto. O operon lac está relacionado ao metabolismo da lactose e tende a ser ativado quando há lactose disponível. O operon do triptofano está relacionado à síntese de triptofano e tende a ser reprimido quando há triptofano suficiente."
            },
            "Intermediário": {
                "parametros": "O aluno explica a lógica regulatória dos dois operons (lac: repressor bloqueia operador; lactose/alolactose inativa repressor liberando a transcrição - indutível; trp: triptofano atua como correpressor e ativa o repressor bloqueando a transcrição - regressível/repressível).",
                "resposta_exemplo": "No operon lac, o repressor normalmente bloqueia a transcrição ao se ligar ao operador. Quando há lactose, seu derivado alolactose liga-se ao repressor e impede sua ligação ao DNA, permitindo a transcrição dos genes envolvidos no metabolismo da lactose. Por isso, o operon lac é indutível. No operon do triptofano, o triptofano atua como correpressor: quando está abundante, liga-se ao repressor e favorece o bloqueio da transcrição. Por isso, é um sistema repressível."
            },
            "Avançado": {
                "parametros": "O aluno integra estrutura, função e lógica metabólica dos operons (mRNA policistrônico contendo promotor, operador e genes estruturais; regulação alostérica dos repressores; e o mecanismo de atenuação específico do operon trp regulado pela velocidade do ribossomo).",
                "resposta_exemplo": "Operons são unidades de regulação típicas de procariotos, nas quais genes relacionados são transcritos em um mesmo mRNA policistrônico. Em geral, incluem promotor, operador e genes estruturais. O operon lac é ativado quando a lactose está disponível, pois a alolactose inativa o repressor e permite a transcrição dos genes necessários ao uso da lactose. Já o operon trp é reprimido quando o triptofano está abundante, pois o triptofano atua como correpressor e ativa o repressor. Além disso, o operon trp pode sofrer atenuação, ajustando a transcrição conforme a disponibilidade de triptofano."
            }
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
    
    ref_basico = referencias.get('Básico', {})
    if isinstance(ref_basico, dict):
        basico_p = ref_basico.get('parametros', '')
        basico_e = ref_basico.get('resposta_exemplo', '')
        ref_basico_str = f"Parâmetros: {basico_p}\nExemplo de resposta: {basico_e}"
    else:
        ref_basico_str = str(ref_basico)
        
    ref_medio = referencias.get('Intermediário', referencias.get('Médio', {}))
    if isinstance(ref_medio, dict):
        medio_p = ref_medio.get('parametros', '')
        medio_e = ref_medio.get('resposta_exemplo', '')
        ref_medio_str = f"Parâmetros: {medio_p}\nExemplo de resposta: {medio_e}"
    else:
        ref_medio_str = str(ref_medio)
        
    ref_avancado = referencias.get('Avançado', {})
    if isinstance(ref_avancado, dict):
        avancado_p = ref_avancado.get('parametros', '')
        avancado_e = ref_avancado.get('resposta_exemplo', '')
        ref_avancado_str = f"Parâmetros: {avancado_p}\nExemplo de resposta: {avancado_e}"
    else:
        ref_avancado_str = str(ref_avancado)

    prompt = f"""
Você é um avaliador acadêmico extremamente rígido e criterioso para uma plataforma de ensino de Genética e Biologia Molecular.
Sua tarefa é avaliar a resposta acumulada do aluno para a pergunta abaixo e classificá-la em um de cinco níveis: "Avançado", "Médio", "Básico", "Parcial" ou "Incorreto".

Pergunta: {question_data.get('pergunta')}

---
**CRITÉRIOS DE AVALIAÇÃO RÍGIDOS:**

1. **NÍVEL BÁSICO**:
   - Parâmetro exigido: {ref_basico_str}
   - Para obter este nível, o aluno precisa atingir o parâmetro básico de forma clara.

2. **NÍVEL MÉDIO / INTERMEDIÁRIO**:
   - Parâmetro exigido: {ref_medio_str}
   - Para obter este nível, o aluno deve atender plenamente o parâmetro básico E o parâmetro intermediário.

3. **NÍVEL AVANÇADO**:
   - Parâmetro exigido: {ref_avancado_str}
   - Para obter este nível, o aluno deve integrar com precisão todos os parâmetros anteriores E demonstrar domínio avançado conforme o parâmetro avançado.

4. **PARCIAL**:
   - Se o aluno mencionou alguns conceitos ou termos corretos, mas não atendeu por completo sequer o critério "Básico".

5. **INCORRETO**:
   - Se a resposta é incorreta, vaga, irrelevante ou não atende a nenhum parâmetro.

---
**REGRA DE AVALIAÇÃO ESTRITA**:
- Seja rigoroso. Se faltar qualquer detalhe mencionado nos parâmetros do nível intermediário, o aluno NÃO pode obter nível "Médio". Se faltar qualquer detalhe do avançado, ele NÃO pode obter nível "Avançado".
- Se a resposta for genérica, classifique no nível inferior aplicável.

**RESPOSTA DO ALUNO:**
{user_answer}

Retorne sua avaliação estritamente neste formato JSON:
{{
  "level": "Avançado" | "Médio" | "Básico" | "Parcial" | "Incorreto",
  "points": 3.0, 2.0, 1.0, 0.5 ou 0.0,
  "classification": "AVANÇADO", "MÉDIO", "BÁSICO", "PARCIAL" ou "INCORRETO",
  "feedback": "Feedback detalhado contendo APENAS a lista dos erros ou pontos de omissão cometidos pelo aluno na resposta, guiando-o de forma construtiva sobre o que ele precisa adicionar ou corrigir para melhorar, sem revelar a resposta pronta."
}}
NÃO RETORNE NENHUM OUTRO TEXTO FORA DO OBJETO JSON.
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
                    return {"level": "Avançado", "points": 3.0, "classification": "AVANÇADO", "feedback": text}
                elif "médio" in lower_text or "medio" in lower_text:
                    return {"level": "Médio", "points": 2.0, "classification": "MÉDIO", "feedback": text}
                elif "básico" in lower_text or "basico" in lower_text:
                    return {"level": "Básico", "points": 1.0, "classification": "BÁSICO", "feedback": text}
                elif "parcial" in lower_text:
                    return {"level": "Parcial", "points": 0.5, "classification": "PARCIAL", "feedback": text}
                else:
                    return {"level": "Incorreto", "points": 0.0, "classification": "INCORRETO", "feedback": text}
                
        except Exception as e:
            print(f"[Avaliador IA] Tentativa {attempt+1}/{max_retries} falhou: {e}")
            if attempt == max_retries - 1:
                return {"level": "Incorreto", "points": 0.0, "classification": "INCORRETO", "feedback": f"Erro IA: {e}"}
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

def tutor_reply_com_ia(question: Dict[str, Any], user_msg: str, chat_history: List[Dict[str, str]], current_level: str = "Incorreto") -> Generator[str, None, None]:
    contexto = _construir_contexto_para_ia(question, chat_history)
    
    referencias = question.get('referencia', {})
    
    ref_basico = referencias.get('Básico', {})
    basico_p = ref_basico.get('parametros', '') if isinstance(ref_basico, dict) else str(ref_basico)
    
    ref_medio = referencias.get('Intermediário', referencias.get('Médio', {}))
    medio_p = ref_medio.get('parametros', '') if isinstance(ref_medio, dict) else str(ref_medio)
    
    ref_avancado = referencias.get('Avançado', {})
    avancado_p = ref_avancado.get('parametros', '') if isinstance(ref_avancado, dict) else str(ref_avancado)

    prompt = f"""
SITUAÇÃO: Você é um Tutor Inteligente estritamente Socrático de Biologia Molecular da plataforma Helix.AI.
Sua missão é guiar o aluno passo a passo para construir a melhor resposta possível para a pergunta: "{question['pergunta']}".

**INSTRUÇÕES DE DIRECIONAMENTO POR NÍVEL (LEIA COM ATENÇÃO EXTREMA):**
O nível atual estimado da resposta do aluno é: **{current_level}**.

1. **Se o nível atual for "Incorreto" ou "Parcial"**:
   - Seu foco exclusivo é ajudar o aluno a atingir o nível **BÁSICO**.
   - Os parâmetros para o nível Básico são: {basico_p}
   - Faça perguntas simples, instigue-o e forneça pistas discretas para que ele compreenda essa base. Não comente sobre termos intermediários ou avançados ainda.

2. **Se o nível atual for "Básico"**:
   - Reconheça sutilmente o progresso dele (sem dizer o nível explicitamente) e passe a instigá-lo a atingir o nível **INTERMEDIÁRIO / MÉDIO**.
   - Os parâmetros para o nível Intermediário são: {medio_p}
   - Pergunte sobre o que está faltando para atingir esses conceitos intermediários (ex: detalhes de regulação, enzimas, mecanismos de pareamento, sítios, etc., dependendo da questão).

3. **Se o nível atual for "Médio" ou "Intermediário"**:
   - Reconheça sutilmente que a resposta está excelente, mas que ele pode se aprofundar ainda mais para atingir o nível **AVANÇADO**.
   - Os parâmetros para o nível Avançado são: {avancado_p}
   - Faça perguntas que o levem a refletir sobre os detalhes mecânicos, termodinâmicos, evolutivos ou de sinalização avançados exigidos por este nível.

4. **Se o nível atual for "Avançado"**:
   - Parabenize-o pela resposta irretocável e diga que ele atingiu a perfeição (100% de conclusão).
   - Incentive-o a clicar no botão de concluir e avançar.

**REGRAS DE CONDUTA DO TUTOR:**
- NUNCA, JAMAIS DÊ A RESPOSTA PRONTA OU DIGA "A RESPOSTA É X". Seu papel é induzir o raciocínio.
- NUNCA mostre pontuação como "0.5", "1.0", "3.0" ou termos de nível no seu texto. Apenas ajude-o a progredir.
- Suas réplicas devem ser curtas (no máximo 3 a 4 linhas). Seja direto e conversacional.

Contexto da conversa até agora:
{contexto}

Mensagem Atual do Aluno: "{user_msg}"
Responda aplicando estritamente as regras acima de acordo com o nível atual dele.
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
            print(f"[Tutor Chat] Tentativa {attempt+1}/{max_retries} falhou: {e}")
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
    outcome = "correct" if points >= 1 else "incorrect"
    if points == 0.5 or points == 2: outcome = "partial" # Parcial ou Médio contam como parcial no sistema interno
    
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
            print(f"[Insight de PDF IA (Categoria)] Tentativa {attempt+1}/{max_retries} falhou: {e}")
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

Sua tarefa é analisar DETALHADAMENTE as respostas dos alunos abaixo, que cobrem 6 questões fundamentais de Biologia Molecular 

Respostas dos Alunos:
{answers_str}

INSTRUÇÕES DETALHADAS:

Para CADA um dos 6 eixos de conhecimento abaixo, escreva uma análise RICA e PROFUNDA contendo:
- Domínio Coletivo: O que a turma demonstra ter consolidado.
- Pontos de Atenção: Quais as confusões conceituais ou simplificações excessivas recorrentes.
- Lacunas Estruturais: Detalhes técnicos importantes (ex: nomes de enzimas, direcionalidade, tipos de ligações) que foram ignorados.

REGRAS ABSOLUTAS:
- NÃO mencione os 5 critérios antigos (antiparalelismo, direcionalidade, lagging, primer, integracao) se a resposta não for sobre eles.
- Baseie-se ESTRITAMENTE na amostra de respostas fornecida.

Os 6 Eixos de Conhecimento:
1. Estabilidade e Interações do DNA (Ligações de H, Empilhamento, Backbone)
2. Replicação: Direcionalidade e Limitações da Polimerase
3. Fita Atrasada e Fragmentos de Okazaki
4. Problemas Mecânicos e Papel das Topoisomerases
5. Mecanismos de Reparo (BER/NER) e Lesões
6. Checkpoints do Ciclo Celular e Evolução Tumoral

Devolva ESTRITAMENTE um JSON com as 6 chaves acima. Cada valor deve ter uma análise pedagógica de 3 a 5 frases.
{{
    "1. Estabilidade e Interações do DNA": "...",
    "2. Replicação: Direcionalidade e Limitações da Polimerase": "...",
    "3. Fita Atrasada e Fragmentos de Okazaki": "...",
    "4. Problemas Mecânicos e Papel das Topoisomerases": "...",
    "5. Mecanismos de Reparo (BER/NER) e Lesões": "...",
    "6. Checkpoints do Ciclo Celular e Evolução Tumoral": "..."
}}
NÃO RETORNE TEXTO FORA DO JSON.
"""

    import time
    import json
    max_retries = 3
    default_resp = {
        "1. Estabilidade e Interações do DNA": "Sem dados suficientes para análise profunda.",
        "2. Replicação: Direcionalidade e Limitações da Polimerase": "Sem dados suficientes.",
        "3. Fita Atrasada e Fragmentos de Okazaki": "Sem dados suficientes.",
        "4. Problemas Mecânicos e Papel das Topoisomerases": "Sem dados suficientes.",
        "5. Mecanismos de Reparo (BER/NER) e Lesões": "Sem dados suficientes.",
        "6. Checkpoints do Ciclo Celular e Evolução Tumoral": "Sem dados suficientes."
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
            print(f"[Class Criteria Analysis] Tentativa {attempt+1}/{max_retries} falhou: {e}")
            if attempt == max_retries - 1:
                return default_resp
            time.sleep(1)
