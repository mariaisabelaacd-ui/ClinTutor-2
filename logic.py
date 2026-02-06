import os
import json
from datetime import datetime
from typing import Dict, List, Any, Generator
import google.generativeai as genai
import streamlit as st  

import numpy as np

# =============================
# CONFIGURAÇÃO DA IA (GEMINI)
# =============================
try:
    # A forma correta e segura de carregar a chave a partir dos segredos do Streamlit
    if 'google_api' in st.secrets and 'api_key' in st.secrets['google_api']:
        GOOGLE_API_KEY = st.secrets['google_api']['api_key']
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        # Fallback para variável de ambiente ou erro
        GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", None)
        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
        else:
            raise KeyError("Chave não encontrada")
except (FileNotFoundError, KeyError):
    # Fallback para avisar o usuário se a chave não for encontrada
    st.error("Chave de API do Google não encontrada! Configure-a em .streamlit/secrets.toml")
    GOOGLE_API_KEY = None

# Configurações do modelo de IA
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# =============================
# Constantes do Aplicativo
# =============================
APP_NAME = "ClinTutor"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".clintutor")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_PATH = os.path.join(DATA_DIR, "progresso_gamificado.json")

# =============================
# Base de Conhecimento: Casos Clínicos
# =============================
CASES: List[Dict[str, Any]] = [
    {
        "id": "n1_faringite_viral", "nivel": 1, "titulo": "Jovem com dor de garganta",
        "queixa": "Dor de garganta há 2 dias",
        "hma": "Paciente 19 anos, sem comorbidades, febre até 38,2°C, odinofagia, tosse leve, sem dispneia, sem exsudato.",
        "antecedentes": "Sem alergias conhecidas.", "exame_fisico": "Orofaringe hiperemiada, sem exsudato; sem adenomegalias dolorosas.",
        "sinais_vitais": {"PA": "112/70", "FC": 86, "FR": 16, "Temp": 38.0, "SatO2": 98},
        "sintomas": ["dor de garganta", "febre baixa", "tosse leve", "odinofagia"],
        "exames_relevantes": {"teste_rapido_strep": "Negativo", "hemograma": "Leucócitos 8.500, neutrófilos 60%, linfócitos 30%", "covid_ag": "Negativo"},
        "exames_opcionais": {"pcr": "6 mg/L"},
        "exames_irrelevantes": ["rx torax", "tomografia", "cultura de orofaringe"],
        "dicas": ["A maioria das faringites em jovens é viral.", "Use critérios clínicos (tipo Centor mod.) para decidir testagem para estreptococo.", "Antibiótico sem critérios aumenta riscos e não melhora desfecho."],
        "gabarito": "faringite viral"
    },
    {
        "id": "n1_cistite_simples", "nivel": 1, "titulo": "Mulher com ardência ao urinar",
        "queixa": "Dor e ardência ao urinar há 1 dia",
        "hma": "Paciente 28 anos, sexo feminino, sem comorbidades, apresenta disúria, polaciúria e urgência miccional. Nega febre, dor lombar ou corrimento vaginal.",
        "antecedentes": "Nega alergias. Histórico de ITU há 6 meses.", "exame_fisico": "Abdome indolor à palpação; Giordano negativo bilateralmente.",
        "sinais_vitais": {"PA": "120/80", "FC": 78, "FR": 18, "Temp": 36.8, "SatO2": 99},
        "sintomas": ["disúria", "polaciúria", "urgência miccional"],
        "exames_relevantes": {"eas": "Leucócitos 50/campo, nitrito positivo, hemácias 5/campo", "urocultura": "Crescimento de E. coli > 10^5 UFC/mL (se solicitado, mas não essencial para diagnóstico inicial)"},
        "exames_opcionais": {}, "exames_irrelevantes": ["hemograma", "creatinina", "ultrassom abdominal"],
        "dicas": ["Cistite não complicada em mulheres jovens é um diagnóstico clínico.", "EAS é o exame de escolha para confirmar a suspeita.", "Urocultura é reservada para casos atípicos, falha terapêutica ou recorrência."],
        "gabarito": "cistite aguda não complicada"
    },
    {
        "id": "n1_gastroenterite_viral", "nivel": 1, "titulo": "Adulto jovem com vômitos e diarreia",
        "queixa": "Vômitos e diarreia há 24 horas",
        "hma": "Paciente 22 anos, previamente hígido, iniciou quadro de náuseas, 4 episódios de vômitos e 6 episódios de diarreia aquosa, sem sangue ou muco. Refere cólicas abdominais difusas. Nega febre alta.",
        "antecedentes": "Nega comorbidades ou uso de medicamentos contínuos.",
        "exame_fisico": "Regular estado geral, mucosas secas (+/4+). Abdome flácido, difusamente doloroso à palpação, sem sinais de peritonite. Ruídos hidroaéreos aumentados.",
        "sinais_vitais": {"PA": "110/70", "FC": 95, "FR": 16, "Temp": 37.5, "SatO2": 99},
        "sintomas": ["vômitos", "diarreia aquosa", "cólicas abdominais", "náuseas"],
        "exames_relevantes": {"eletrólitos": "Sódio 137, Potássio 3.4 (limítrofe inferior)"},
        "exames_opcionais": {"hemograma": "Leve hemoconcentração, sem leucocitose", "funcao_renal": "Creatinina 1.1 (discreta elevação)"},
        "exames_irrelevantes": ["raio_x_abdome", "tomografia_computadorizada", "endoscopia"],
        "dicas": ["A grande maioria das gastroenterites agudas é viral e autolimitada.", "O pilar do tratamento é a hidratação e o manejo de sintomas.", "Sinais de alarme para investigar mais a fundo incluem sangue nas fezes, febre alta persistente ou desidratação grave."],
        "gabarito": "gastroenterite viral aguda"
    },
    {
        "id": "n2_dm2_hiperglicemia", "nivel": 2, "titulo": "Idoso com glicemia elevada",
        "queixa": "Glicemia capilar de 350 mg/dL em casa",
        "hma": "Paciente 65 anos, diabético tipo 2 há 10 anos, em uso irregular de metformina. Refere poliúria e polidipsia leves nos últimos dias. Nega dor abdominal, náuseas, vômitos ou dispneia.",
        "antecedentes": "Diabetes Mellitus Tipo 2, Hipertensão Arterial Sistêmica.", "exame_fisico": "Bem hidratado, sem sinais de desidratação. Exame físico sem alterações significativas.",
        "sinais_vitais": {"PA": "130/85", "FC": 88, "FR": 16, "Temp": 36.5, "SatO2": 97},
        "sintomas": ["poliúria", "polidipsia", "hiperglicemia"],
        "exames_relevantes": {"glicemia_capilar": "350 mg/dL", "glicemia_venosa": "345 mg/dL", "hemoglobina_glicada": "9.5%", "eletrólitos": "Na 138, K 4.0, Cl 100", "gasometria_arterial": "pH 7.38, pCO2 40, HCO3 24 (sem acidose)"},
        "exames_opcionais": {"funcao_renal": "Creatinina 1.0, Ureia 30", "urina_tipo_1": "Glicosúria +++, Cetonúria -"},
        "exames_irrelevantes": ["ecg", "raio_x_torax", "cultura_de_escarro"],
        "dicas": ["Avaliar sinais de cetoacidose ou estado hiperosmolar é crucial em hiperglicemia acentuada.", "Ajuste da medicação e educação do paciente são pilares do tratamento.", "Aderência ao tratamento e dieta são fundamentais para o controle glicêmico."],
        "gabarito": "hiperglicemia em dm2 sem cetoacidose"
    },
    {
        "id": "n2_dengue_classica", "nivel": 2, "titulo": "Febre alta e dor no corpo",
        "queixa": "Febre alta, dor de cabeça e dor no corpo há 3 dias.",
        "hma": "Paciente 25 anos, residente em área urbana, refere início súbito de febre alta (39°C), cefaleia intensa, dor retro-orbitária, e dor muscular e articular incapacitante. Nega tosse ou coriza. Refere náuseas e notou algumas manchas vermelhas na pele hoje.",
        "antecedentes": "Nega comorbidades. Relata diversos casos de dengue na vizinhança no último mês.",
        "exame_fisico": "Bom estado geral, corado, hidratado. Prova do laço positiva (25 petéquias em 5 min). Abdome indolor.",
        "sinais_vitais": {"PA": "110/70", "FC": 88, "FR": 18, "Temp": 38.8, "SatO2": 98},
        "sintomas": ["febre alta", "cefaleia", "dor retro-orbitária", "mialgia", "artralgia", "exantema"],
        "exames_relevantes": {"hemograma": "Hb 15.0, Ht 45% (hemoconcentrado), Leucócitos 3.200 (leucopenia), Plaquetas 90.000 (plaquetopenia)", "antigeno_ns1": "Reagente"},
        "exames_opcionais": {"sorologia_dengue_igm": "Não reagente (fase inicial)", "tgo_tgp": "TGO/TGP levemente elevadas"},
        "exames_irrelevantes": ["pcr", "urocultura", "hemocultura"],
        "dicas": ["A identificação dos 'sinais de alarme' (dor abdominal intensa, vômitos persistentes, sangramentos) é crucial.", "O manejo da dengue sem sinais de alarme baseia-se em hidratação vigorosa e controle sintomático.", "AINES e AAS são contraindicados pelo risco de sangramento."],
        "gabarito": "dengue clássica (sem sinais de alarme)"
    },
    {
        "id": "n3_sca", "nivel": 3, "titulo": "Homem com dor torácica opressiva",
        "queixa": "Dor no peito intensa há 1 hora, com irradiação para braço esquerdo",
        "hma": "Paciente 55 anos, sexo masculino, tabagista, hipertenso e dislipidêmico. Apresenta dor torácica opressiva, 9/10, com irradiação para membro superior esquerdo e mandíbula. Associada a sudorese profusa, náuseas e dispneia.",
        "antecedentes": "Tabagismo (30 anos/maço), HAS, Dislipidemia.", "exame_fisico": "Pele fria e pegajosa. Ausculta cardíaca e pulmonar normais.",
        "sinais_vitais": {"PA": "100/60", "FC": 105, "FR": 22, "Temp": 36.6, "SatO2": 92},
        "sintomas": ["dor torácica opressiva", "irradiação para braço esquerdo", "sudorese", "náuseas", "dispneia"],
        "exames_relevantes": {"ecg": "Supradesnivelamento do segmento ST em V2-V5", "troponina": "Elevada (ex: 500 ng/L, ref < 14 ng/L)"},
        "exames_opcionais": {"hemograma": "Leucócitos 9.000", "glicemia": "180 mg/dL"},
        "exames_irrelevantes": ["raio_x_torax", "d-dímero", "hemocultura"],
        "dicas": ["Dor torácica típica em paciente com fatores de risco é SCA até prova em contrário.", "ECG é o exame mais importante para diagnóstico e estratificação inicial.", "Tempo é músculo: reperfusão precoce é fundamental."],
        "gabarito": "síndrome coronariana aguda com supradesnivelamento do st"
    },
    {
        "id": "n3_apendicite_aguda", "nivel": 3, "titulo": "Jovem com dor abdominal",
        "queixa": "Dor abdominal que começou perto do umbigo e agora está na parte de baixo, à direita",
        "hma": "Paciente 20 anos, masculino, hígido, iniciou quadro de dor periumbilical há 24h, que migrou para fossa ilíaca direita (FID) nas últimas 12h, tornando-se mais intensa. Associada a náuseas, anorexia, um episódio de vômito e febre baixa.",
        "antecedentes": "Nenhum digno de nota.",
        "exame_fisico": "Dor à palpação em FID, com descompressão brusca positiva (sinal de Blumberg). Sinal de Rovsing positivo.",
        "sinais_vitais": {"PA": "120/80", "FC": 98, "FR": 18, "Temp": 37.8, "SatO2": 99},
        "sintomas": ["dor abdominal migratória", "náuseas", "vômitos", "febre baixa", "anorexia"],
        "exames_relevantes": {"hemograma": "Leucócitos 14.500, com 85% de neutrófilos", "pcr": "150 mg/L", "ultrassom_abdominal": "Aumento do diâmetro apendicular (>6mm), com parede espessada."},
        "exames_opcionais": {"tomografia_abdome": "Confirma os achados do ultrassom, sendo mais específica.", "eas": "Útil para excluir causa urinária."},
        "exames_irrelevantes": ["endoscopia", "ecg", "gasometria_arterial"],
        "dicas": ["A dor migratória (periumbilical para FID) é o sintoma mais clássico da apendicite.", "Sinais de irritação peritoneal no exame físico (como Blumberg) são altamente sugestivos.", "O tratamento é cirúrgico e o diagnóstico precoce é crucial para evitar complicações."],
        "gabarito": "apendicite aguda"
    }
]

# =============================
# Funções da IA Tutora
# =============================

def _construir_contexto_para_ia(case: Dict[str, Any], chat_history: List[Dict[str, str]]) -> str:
    """Prepara o texto de contexto para ser enviado à IA."""
    ctx = f"**Caso Clínico Atual:** {case['titulo']}\n"
    ctx += f"**Queixa Principal:** {case['queixa']}\n"
    ctx += f"**Resumo do Caso:** {case['hma']}\n"
    ctx += f"**Sintomas-Chave:** {', '.join(case['sintomas'])}\n"
    
    revealed_exams = st.session_state.get("revealed_exams", [])
    if revealed_exams:
        ctx += "**Exames já solicitados pelo aluno e seus resultados:**\n"
        rel_keys = {k.lower(): v for k, v in case.get("exames_relevantes", {}).items()}
        opt_keys = {k.lower(): v for k, v in case.get("exames_opcionais", {}).items()}
        for exam in revealed_exams:
            if exam in rel_keys:
                ctx += f"- {exam.upper()}: {rel_keys[exam]}\n"
            elif exam in opt_keys:
                ctx += f"- {exam.upper()}: {opt_keys[exam]}\n"

    if chat_history:
        ctx += "\n**Histórico da conversa recente:**\n"
        for turn in chat_history[-4:]:
            role = "Tutor" if turn['role'] == 'assistant' else 'Aluno'
            ctx += f"- {role}: {turn['content']}\n"
            
    return ctx

def tutor_reply_com_ia(case: Dict[str, Any], user_msg: str, chat_history: List[Dict[str, str]]) -> Generator[str, None, None]:
    """Função principal da IA. Usa o Gemini com RAG para gerar uma resposta guiada."""
    if not GOOGLE_API_KEY:
        yield "Erro: A chave da API do Google não está configurada. A IA não pode funcionar."
        return

    contexto = _construir_contexto_para_ia(case, chat_history)
    
    # --- OTIMIZAÇÃO DE COTA (Filtro Local) ---
    msg_lower = user_msg.lower().strip()
    
    # Saudações simples
    # Saudações simples (lógica mais estrita para evitar falso positivo)
    greetings = ['oi', 'olá', 'ola', 'ei', 'hello', 'bom dia', 'boa tarde', 'boa noite']
    if msg_lower in greetings or (len(msg_lower) < 10 and msg_lower.split()[0] in greetings):
        yield "Olá! Sou seu tutor virtual. Estou aqui para te ajudar a raciocinar sobre este caso clínico. Qual sua principal dúvida ou hipótese no momento?"
        return

    # Tratamento específico para "não sei" / pedido de ajuda
    help_requests = ['não sei', 'nao sei', 'n sei', 'não faço ideia', 'estou perdido', 'me ajuda', 'socorro']
    if any(h in msg_lower for h in help_requests):
        # Deixa passar para a IA, pois ela saberá guiar melhor com base no contexto do caso
        pass 


    # Agradecimentos
    thanks = ['obrigado', 'obrigada', 'valeu', 'grato', 'thanks', 'ok', 'certo', 'entendi', 'beleza']
    if msg_lower in thanks or (len(msg_lower) < 15 and any(t in msg_lower for t in thanks)):
        yield "De nada! Se tiver mais dúvidas ou quiser discutir outro aspecto do caso, é só falar."
        return
        
    # Mensagens muito curtas/sem sentido (economia)
    if len(msg_lower) < 3:
        yield "Poderia elaborar um pouco mais sua pergunta? Assim consigo te ajudar melhor."
        return
    # -----------------------------------------

    prompt = f"""
    **PERSONA E OBJETIVO:**
    Você é um Tutor de Medicina. Seu objetivo é guiar um estudante a pensar criticamente sobre um caso clínico, NUNCA dando a resposta final. Haja como um preceptor experiente, fazendo perguntas que estimulem o raciocínio e respondendo dúvidas pontuais, seja educado e responda perguntas que sejam introdutórias como oi ou obrigado de forma breve e gentil.

    **REGRAS ABSOLUTAS:**
    1.  **NUNCA REVELE O DIAGNÓSTICO FINAL.** O diagnóstico correto é '{case['gabarito']}', mas você JAMAIS deve mencionar essa informação. Seu papel é fazer o aluno chegar lá sozinho.
    2.  **PREFIRA** responder com uma pergunta que estimule o raciocínio, mas se o aluno estiver muito perdido ou fizer uma pergunta factual, você PODE e DEVE dar uma resposta direta e curta, seguida de uma nova pergunta que devolva o raciocínio para o aluno.
    3.  **SEJA CONCISO.** Responda em 1 ou 2 frases curtas, porém em caso de dúvida sobre um conceito, pode ser mais detalhista na explicação.
    4.  **USE O CONTEXTO.** Baseie sua resposta nos dados do caso clínico e no histórico da conversa fornecidos.
    5.  **NÃO SEJA REPETITIVO.** Varie o tipo de pergunta e a forma de guiar.

    **FLUXO DE RACIOCÍNIO E COMPORTAMENTO:**
    - Se o aluno parece perdido ("o que faço agora?", "e agora?"), pergunte sobre como os dados se conectam. (Ex: "Boa pergunta. Como você relaciona a queixa X com o achado Y no exame físico?")
    - Se o aluno sugere uma hipótese, pergunte o que a confirma ou a descarta. (Ex: "Essa é uma hipótese válida. Que exame seria crucial para diferenciá-la de outras possibilidades?")
    - Se o aluno pede uma dica, devolva com uma pergunta sobre as informações mais importantes que ele já tem. (Ex: "Dos dados que você já coletou, qual deles te parece mais urgente ou significativo para o caso?")
    - Se o aluno sugere um exame, pergunte como o resultado influenciaria o raciocínio. (Ex: "Ótima ideia. E como um resultado positivo (ou negativo) desse exame mudaria sua conduta?")
    - Se o aluno fizer uma saudação ou agradecimento, responda de forma breve e educada. (Ex: "Olá! Vamos analisar este caso juntos. Por onde você gostaria de começar?")
    - Se o aluno fizer uma pergunta sobre o gabarito ou diagnóstico final, recuse educadamente. (Ex: "Essa é a conclusão que estamos tentando construir. Não posso revelar a resposta, mas posso te ajudar a chegar nela.")
    - **PERGUNTAS FACTUAIS (IMPORTANTE):** Se o aluno perguntar o que é um termo técnico, como funciona um exame, qual a referência de um valor, ou sobre fisiologia/anatomia, **responda a pergunta de forma clara e direta**. E então, **imediatamente após a explicação**, devolva o foco para o caso com uma pergunta. (Ex: Aluno: "o que é PCR?". Sua resposta: "A Proteína C Reativa (PCR) é um marcador de inflamação no corpo. Sabendo disso, como um valor alto de PCR te ajuda a pensar neste caso?").

    ---
    **CONTEXTO ATUAL FORNECIDO:**
    {contexto}
    ---

    **PERGUNTA DO ALUNO:**
    "{user_msg}"

    **SUA RESPOSTA:**
    """
    
    # Tenta usar o modelo padrão estável
    try:
        model = genai.GenerativeModel(model_name="gemini-pro",
                                      generation_config=GENERATION_CONFIG,
                                      safety_settings=SAFETY_SETTINGS)
        response_stream = model.generate_content(prompt, stream=True)
        for chunk in response_stream:
            yield chunk.text
            
    except Exception as e:
        # Fallback: Tenta encontrar qualquer modelo disponível
        try:
            print(f"Erro com gemini-pro: {e}. Tentando fallback...")
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            if available_models:
                # Pega o primeiro modelo que parece ser do tipo gemini
                fallback_model = next((m for m in available_models if 'gemini' in m), available_models[0])
                # Remove o prefixo 'models/' se existir, pois o construtor as vezes prefere sem
                if fallback_model.startswith('models/'):
                    fallback_model = fallback_model.replace('models/', '')
                
                model = genai.GenerativeModel(model_name=fallback_model,
                                              generation_config=GENERATION_CONFIG,
                                              safety_settings=SAFETY_SETTINGS)
                response_stream = model.generate_content(prompt, stream=True)
                for chunk in response_stream:
                    yield chunk.text
            else:
                raise e
                
        except Exception as e_final:
            error_message = f"Erro com a IA ({type(e_final).__name__}): {e_final}"
            st.error(error_message)
            yield "Desculpe, a IA está indisponível no momento devido a configurações de modelo da API. Tente novamente mais tarde."

# =============================
# Persistência e Lógica de Jogo
# =============================

def load_progress() -> Dict[str, Any]:
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Se for uma lista (novo formato), retorna a lista
                # Se for um dict (formato antigo), retorna o dict
                return data
        except Exception:
            return {}
    return {}

def save_progress(data: Dict[str, Any]):
    try:
        # Carrega dados existentes
        existing_data = load_progress()
        
        # Se não há dados existentes ou é um dict (formato antigo), cria uma lista
        if not existing_data or isinstance(existing_data, dict):
            if existing_data and isinstance(existing_data, dict):
                # Converte formato antigo para novo
                progress_list = [existing_data] if existing_data else []
            else:
                progress_list = []
        else:
            progress_list = existing_data
        
        # Atualiza ou adiciona progresso do usuário
        user_id = data.get("user_id")
        if user_id:
            # Remove progresso anterior do usuário
            progress_list = [p for p in progress_list if p.get("user_id") != user_id]
            # Adiciona novo progresso
            progress_list.append(data)
        
        # Salva a lista atualizada
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(progress_list, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

LEVEL_THRESHOLDS = {1: 0, 2: 120, 3: 300}
MAX_LEVEL = 3
PTS_DIAG_CORRETO = 10
PTS_EXAME_RELEVANTE = 5
PTS_EXAME_IRRELEVANTE = -3
PTS_CONDUTA_ADEQUADA = 2
BONUS_STREAK3 = 20

CONDUTA_HINTS = {
    "n1_faringite_viral": ["analgesia", "antitérmico", "hidrata", "orientar sinais de alarme", "evitar antibiótico"],
    "n1_cistite_simples": ["nitrofurantoína", "fosfomicina", "analgesia", "hidrata"],
    "n1_gastroenterite_viral": ["hidratação", "antiemético", "sintomáticos", "sinais de alarme"],
    "n2_dm2_hiperglicemia": ["ajuste", "adesão", "educação", "reavaliação", "monitorar"],
    "n2_dengue_classica": ["hidratação", "paracetamol", "dipirona", "orientar", "sinais de alarme"],
    "n3_sca": ["protocolo", "aspirina", "reperfusão", "oxigênio", "nitrato"],
    "n3_apendicite_aguda": ["cirurgia", "apendicectomia", "antibiótico", "jejum", "hidratação"]
}
ALTERNATES = {
    "faringite viral": ["faringite", "virose de garganta", "faringite aguda viral"],
    "cistite aguda não complicada": ["cistite", "itu baixa", "infecção urinária simples"],
    "gastroenterite viral aguda": ["gastroenterite", "virose", "gastroenterocolite"],
    "hiperglicemia em dm2 sem cetoacidose": ["hiperglicemia dm2", "descompensação dm2", "diabetes descompensado"],
    "dengue clássica (sem sinais de alarme)": ["dengue", "dengue a", "dengue b"],
    "síndrome coronariana aguda com supradesnivelamento do st": ["iam com supra", "infarto com supra", "iamcsst", "scacsst"],
    "apendicite aguda": ["apendicite"]
}

def level_from_score(score: int) -> int:
    lvl = 1
    for L in sorted(LEVEL_THRESHOLDS.keys()):
        if score >= LEVEL_THRESHOLDS[L]:
            lvl = L
    return min(lvl, MAX_LEVEL)

def progress_to_next_level(score: int) -> float:
    current_level = level_from_score(score)
    if current_level == MAX_LEVEL:
        return 1.0
    cur_th = LEVEL_THRESHOLDS[current_level]
    next_th = LEVEL_THRESHOLDS[current_level + 1]
    if (next_th - cur_th) == 0: return 1.0
    return (score - cur_th) / (next_th - cur_th)

def get_case_pool(level: int) -> List[Dict[str, Any]]:
    return [c for c in CASES if c["nivel"] <= level]

def pick_new_case(level: int, used_cases: List[str] = None) -> Dict[str, Any]:
    if used_cases is None:
        used_cases = []
    
    pool = get_case_pool(level)
    same_level_pool = [c for c in pool if c["nivel"] == level]
    
    # Remove casos já utilizados do pool
    available_cases = [c for c in same_level_pool if c["id"] not in used_cases]
    
    # Se não há casos disponíveis no nível atual, tenta com todo o pool
    if not available_cases:
        available_cases = [c for c in pool if c["id"] not in used_cases]
    
    # Se ainda não há casos disponíveis, reseta a lista de casos utilizados
    if not available_cases:
        available_cases = same_level_pool if same_level_pool else pool
    
    return np.random.choice(available_cases).copy()

def get_case(cid: str) -> Dict[str, Any]:
    for c in CASES:
        if c["id"] == cid:
            return c
    return CASES[0]

def normalize(s: str) -> str:
    return (s or "").lower().strip().replace('-', ' ')

def normalize_exam_name(exam_name: str) -> str:
    """
    Normaliza nome do exame para comparação, incluindo flexibilidade de underscore
    """
    normalized = (exam_name or "").lower().strip()
    # Remove acentos
    import unicodedata
    normalized = unicodedata.normalize('NFD', normalized).encode('ascii', 'ignore').decode('ascii')
    # Normaliza underscores e espaços
    normalized = normalized.replace('_', ' ').replace(' ', '_')
    return normalized

# =============================
# Sistema de Correção de Exames
# =============================

# Mapeamento de exames com variações de acentos e erros comuns
EXAM_CORRECTIONS = {
    # Variações de acentos
    "eletrolitos": "eletrólitos",
    "eletrolitos": "eletrólitos", 
    "hemograma": "hemograma",
    "hemograma": "hemograma",
    "glicemia": "glicemia",
    "glicemia": "glicemia",
    "creatinina": "creatinina",
    "creatinina": "creatinina",
    "ureia": "ureia",
    "ureia": "ureia",
    "pcr": "pcr",
    "pcr": "pcr",
    "ecg": "ecg",
    "ecg": "ecg",
    "rx": "rx",
    "rx": "rx",
    "ultrassom": "ultrassom",
    "ultrassom": "ultrassom",
    "tomografia": "tomografia",
    "tomografia": "tomografia",
    "gasometria": "gasometria",
    "gasometria": "gasometria",
    "troponina": "troponina",
    "troponina": "troponina",
    "eas": "eas",
    "eas": "eas",
    "urocultura": "urocultura",
    "urocultura": "urocultura",
    "cultura": "cultura",
    "cultura": "cultura",
    "antigeno": "antígeno",
    "antigeno": "antígeno",
    "sorologia": "sorologia",
    "sorologia": "sorologia",
    "tgo": "tgo",
    "tgo": "tgo",
    "tgp": "tgp",
    "tgp": "tgp",
    "covid": "covid",
    "covid": "covid",
    "teste_rapido": "teste_rapido_strep",
    "teste_rapido": "teste_rapido_strep",
    "strep": "teste_rapido_strep",
    "strep": "teste_rapido_strep",
    "glicemia_capilar": "glicemia_capilar",
    "glicemia_capilar": "glicemia_capilar",
    "glicemia_venosa": "glicemia_venosa",
    "glicemia_venosa": "glicemia_venosa",
    "hemoglobina_glicada": "hemoglobina_glicada",
    "hemoglobina_glicada": "hemoglobina_glicada",
    "funcao_renal": "funcao_renal",
    "funcao_renal": "funcao_renal",
    "urina_tipo": "urina_tipo_1",
    "urina_tipo": "urina_tipo_1",
    "ultrassom_abdominal": "ultrassom_abdominal",
    "ultrassom_abdominal": "ultrassom_abdominal",
    "tomografia_abdome": "tomografia_abdome",
    "tomografia_abdome": "tomografia_abdome",
    "antigeno_ns1": "antigeno_ns1",
    "antigeno_ns1": "antigeno_ns1",
    "sorologia_dengue": "sorologia_dengue_igm",
    "sorologia_dengue": "sorologia_dengue_igm",
    "tgo_tgp": "tgo_tgp",
    "tgo_tgp": "tgo_tgp",
    "gasometria_arterial": "gasometria_arterial",
    "gasometria_arterial": "gasometria_arterial",
    
    # Erros comuns de digitação
    "eltrolitos": "eletrólitos",
    "eletrolitos": "eletrólitos",
    "hemogram": "hemograma",
    "hemogram": "hemograma",
    "glicemia": "glicemia",
    "glicemia": "glicemia",
    "creatinina": "creatinina",
    "creatinina": "creatinina",
    "ureia": "ureia",
    "ureia": "ureia",
    "pcr": "pcr",
    "pcr": "pcr",
    "ecg": "ecg",
    "ecg": "ecg",
    "rx": "rx",
    "rx": "rx",
    "ultrassom": "ultrassom",
    "ultrassom": "ultrassom",
    "tomografia": "tomografia",
    "tomografia": "tomografia",
    "gasometria": "gasometria",
    "gasometria": "gasometria",
    "troponina": "troponina",
    "troponina": "troponina",
    "eas": "eas",
    "eas": "eas",
    "urocultura": "urocultura",
    "urocultura": "urocultura",
    "cultura": "cultura",
    "cultura": "cultura",
    "antigeno": "antígeno",
    "antigeno": "antígeno",
    "sorologia": "sorologia",
    "sorologia": "sorologia",
    "tgo": "tgo",
    "tgo": "tgo",
    "tgp": "tgp",
    "tgp": "tgp",
    "covid": "covid",
    "covid": "covid",
    "teste_rapido": "teste_rapido_strep",
    "teste_rapido": "teste_rapido_strep",
    "strep": "teste_rapido_strep",
    "strep": "teste_rapido_strep",
    "glicemia_capilar": "glicemia_capilar",
    "glicemia_capilar": "glicemia_capilar",
    "glicemia_venosa": "glicemia_venosa",
    "glicemia_venosa": "glicemia_venosa",
    "hemoglobina_glicada": "hemoglobina_glicada",
    "hemoglobina_glicada": "hemoglobina_glicada",
    "funcao_renal": "funcao_renal",
    "funcao_renal": "funcao_renal",
    "urina_tipo": "urina_tipo_1",
    "urina_tipo": "urina_tipo_1",
    "ultrassom_abdominal": "ultrassom_abdominal",
    "ultrassom_abdominal": "ultrassom_abdominal",
    "tomografia_abdome": "tomografia_abdome",
    "tomografia_abdome": "tomografia_abdome",
    "antigeno_ns1": "antigeno_ns1",
    "antigeno_ns1": "antigeno_ns1",
    "sorologia_dengue": "sorologia_dengue_igm",
    "sorologia_dengue": "sorologia_dengue_igm",
    "tgo_tgp": "tgo_tgp",
    "tgo_tgp": "tgo_tgp",
    "gasometria_arterial": "gasometria_arterial",
    "gasometria_arterial": "gasometria_arterial",
}

def correct_exam_name(exam_name: str) -> tuple[str, bool]:
    """
    Corrige o nome do exame e retorna (nome_corrigido, foi_corrigido)
    """
    exam_lower = exam_name.lower().strip()
    exam_normalized = normalize_exam_name(exam_name)
    
    # Verifica se há correção direta
    if exam_lower in EXAM_CORRECTIONS:
        return EXAM_CORRECTIONS[exam_lower], True
    
    # Verifica versão normalizada
    if exam_normalized in EXAM_CORRECTIONS:
        return EXAM_CORRECTIONS[exam_normalized], True
    
    # Busca por similaridade (erros de digitação)
    for original, corrected in EXAM_CORRECTIONS.items():
        original_normalized = normalize_exam_name(original)
        if exam_normalized == original_normalized:
            return corrected, True
    
    return exam_name, False

def suggest_exam_corrections(exam_name: str, available_exams: dict) -> str:
    """
    Sugere correções para um exame não encontrado
    """
    suggestions = []
    exam_lower = exam_name.lower().strip()
    exam_normalized = normalize_exam_name(exam_name)
    
    # Busca por exames que contenham parte do nome
    for exam_key in available_exams.keys():
        exam_key_normalized = normalize_exam_name(exam_key)
        if (exam_lower in exam_key or exam_key in exam_lower or 
            exam_normalized in exam_key_normalized or exam_key_normalized in exam_normalized):
            suggestions.append(exam_key)
    
    # Busca por similaridade (primeiras letras)
    if len(exam_lower) >= 3:
        for exam_key in available_exams.keys():
            exam_key_normalized = normalize_exam_name(exam_key)
            if (exam_key.startswith(exam_lower[:3]) or exam_lower.startswith(exam_key[:3]) or
                exam_key_normalized.startswith(exam_normalized[:3]) or exam_normalized.startswith(exam_key_normalized[:3])):
                suggestions.append(exam_key)
    
    if suggestions:
        unique_suggestions = list(set(suggestions))[:3]  # Máximo 3 sugestões
        return f"Você quis dizer: {', '.join(unique_suggestions)}?"
    
    return "Exame não encontrado. Verifique a grafia."

def diagnosis_score(case: Dict[str, Any], user_diag: str) -> int:
    gabarito = normalize(case["gabarito"])
    diag = normalize(user_diag)
    if not diag: return 0
    if gabarito in diag or diag in gabarito: return 10
    
    alternates = ALTERNATES.get(case["gabarito"], [])
    for alt in alternates:
        if alt in diag: return 7
        
    gabarito_tokens = set(gabarito.split())
    diag_tokens = set(diag.split())
    common_tokens = gabarito_tokens.intersection(diag_tokens)
    
    if len(common_tokens) >= len(gabarito_tokens) / 2 and len(common_tokens) > 0: return 5
    return 0

def exams_points(case: Dict[str, Any], requested: List[str]) -> int:
    pts = 0
    rel = {k.lower(): v for k, v in case.get("exames_relevantes", {}).items()}
    opt = {k.lower(): v for k, v in case.get("exames_opcionais", {}).items()}
    requested_norm = [normalize(x) for x in requested if x and normalize(x) != ""]
    
    if not requested_norm and rel: return -5 
    
    for ex in set(requested_norm): 
        if ex in rel: pts += 5
        elif ex in opt: pts += 2
        else: pts -= 3
    return pts

def plan_points(case: Dict[str, Any], plan_text: str) -> int:
    plan = normalize(plan_text)
    if not plan: return 0
    
    hints = CONDUTA_HINTS.get(case["id"], [])
    hits = sum(1 for kw in hints if kw.split()[0] in plan)
    
    if hits == 0: return 0
    if hits == 1: return 2
    return 2 + (hits - 1)

def finalize_case(case: Dict[str, Any], user_diag: str, requested_exams: List[str], plan_text: str, session_state) -> Dict[str, Any]:
    pts_diag = diagnosis_score(case, user_diag)
    pts_exams = exams_points(case, requested_exams)
    pts_plan = plan_points(case, plan_text)
    
    base_points = pts_diag + pts_exams + pts_plan
    
    is_correct = pts_diag >= 10
    
    bonus_streak_points = 0
    if is_correct:
        current_streak = session_state.get('streak', 0)
        if (current_streak + 1) > 0 and (current_streak + 1) % 3 == 0:
            bonus_streak_points = BONUS_STREAK3
            
    gained = max(0, base_points) + bonus_streak_points

    feedback_diag = f"🩺 **Diagnóstico correto:** **{case['gabarito'].upper()}**\n"
    if is_correct:
        feedback_diag += f"✅ Sua hipótese **({user_diag})** está correta. **+{pts_diag} pontos.**"
    else:
        feedback_diag += f"❌ Sua hipótese **({user_diag or 'vazia'})** não correspondeu. Pontuação: **{pts_diag}**."
    feedback_diag += "\n**Raciocínio-chave:** " + "; ".join(case.get("dicas", [])[:2])
    
    return {
        "points_gained": gained,
        "breakdown": {
            "diagnóstico": pts_diag,
            "exames": pts_exams,
            "plano": pts_plan,
            "bônus_streak": bonus_streak_points,
        },
        "feedback": feedback_diag,
    }

