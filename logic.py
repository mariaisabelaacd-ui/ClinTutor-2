import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Generator
import random
from groq import Groq
import streamlit as st  
import numpy as np

print("DEBUG: LOADED LOGIC.PY v6 (MCQ TRANSITION - GROQ GPT-OSS 20B & QWEN 3.6 27B)")

def _extract_json(text: str) -> Dict[str, Any]:
    """Extrai e faz parse de JSON mesmo se o modelo gerar tags <think> ou blocos markdown."""
    if not text:
        raise ValueError("Texto vazio recebido para extração de JSON.")
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1:
        cleaned = cleaned[first_brace:last_brace+1]
        
    return json.loads(cleaned)

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
    try:
        if "api_keys" in st.secrets["groq_api"]:
            GROQ_API_KEYS = list(st.secrets["groq_api"]["api_keys"])
        elif "api_key" in st.secrets["groq_api"]:
            GROQ_API_KEYS = [st.secrets["groq_api"]["api_key"]]
    except Exception as e:
        print(f"Erro no Fallback st.secrets: {e}")

def get_groq_client():
    if not GROQ_API_KEYS:
        return None
    key = random.choice(GROQ_API_KEYS)
    safe_key = key[:10] + "..." + key[-5:]
    print(f"[IA LOGGER] Requisição enviada. Usando chave Groq: {safe_key}", flush=True)
    return Groq(api_key=key)

# Modelo Padrão do Groq (para chat socrático rápido e previews)
MODEL_NAME = "openai/gpt-oss-20b"
# Modelo analítico para relatórios e análises aprofundadas
EVAL_MODEL_NAME = "qwen/qwen3.6-27b"

APP_NAME = "Helix.AI"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".clintutor")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_PATH = os.path.join(DATA_DIR, "progresso_gamificado.json")

# =============================
# MAPEAMENTO DE TÓPICOS
# =============================
TOPICS = {
    "T1": "Permeabilidade seletiva da bicamada lipídica",
    "T2": "Gradiente de concentração e fluxo líquido",
    "T3": "Difusão simples e difusão facilitada",
    "T4": "Diferenças entre canais e transportadores",
    "T5": "Osmose, osmolaridade e tonicidade",
    "T6": "Transporte ativo primário",
    "T7": "Transporte ativo secundário: simporte e antiporte",
    "T8": "Função da Na⁺/K⁺-ATPase"
}

# =============================
# BANCO DE QUESTÕES: TRANSPORTE E MEMBRANAS BIOLÓGICAS (46 QUESTÕES)
# =============================
QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "t1_1",
        "codigo": "T1.1",
        "topico_id": "T1",
        "topico_nome": "Permeabilidade seletiva da bicamada lipídica",
        "dificuldade": "Fácil",
        "pergunta": "Uma membrana artificial é constituída apenas por uma bicamada de fosfolipídios, sem proteínas. Qual substância atravessará essa membrana com maior facilidade?",
        "alternativas": {
            "A": "Na⁺",
            "B": "Glicose",
            "C": "O₂",
            "D": "Proteína"
        },
        "gabarito": "C",
        "distratores": {
            "A": "Na⁺: considerar que o pequeno tamanho do íon é suficiente para permitir sua passagem pela bicamada, desconsiderando a elevada barreira energética imposta à carga elétrica.",
            "B": "Glicose: considerar que moléculas pequenas ou metabolicamente importantes atravessam espontaneamente a bicamada, desconsiderando sua polaridade.",
            "C": "Gabarito correto.",
            "D": "Proteína: desconsiderar que o grande tamanho molecular e a elevada quantidade de grupos polares tornam proteínas praticamente impermeáveis à bicamada."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Permeabilidade seletiva da bicamada lipídica",
            "Permeabilidade seletiva da bicamada lipídica (Fácil)"
        ]
    },
    {
        "id": "t1_2",
        "codigo": "T1.2",
        "topico_id": "T1",
        "topico_nome": "Permeabilidade seletiva da bicamada lipídica",
        "dificuldade": "Fácil",
        "pergunta": "Qual característica molecular representa a maior barreira para a passagem direta de uma substância pela região hidrofóbica da bicamada?",
        "alternativas": {
            "A": "Pequeno tamanho molecular",
            "B": "Presença de carga elétrica",
            "C": "Baixa massa molecular",
            "D": "Ausência de ligações peptídicas"
        },
        "gabarito": "B",
        "distratores": {
            "A": "acreditar que moléculas pequenas apresentam menor permeabilidade.",
            "B": "Gabarito correto.",
            "C": "interpretar baixa massa molecular como fator que dificulta, em vez de favorecer, a difusão.",
            "D": "atribuir a permeabilidade principalmente à presença ou ausência de ligações peptídicas, em vez de considerar carga, polaridade e tamanho."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Permeabilidade seletiva da bicamada lipídica",
            "Permeabilidade seletiva da bicamada lipídica (Fácil)"
        ]
    },
    {
        "id": "t1_3",
        "codigo": "T1.3",
        "topico_id": "T1",
        "topico_nome": "Permeabilidade seletiva da bicamada lipídica",
        "dificuldade": "Média",
        "pergunta": "Duas moléculas apresentam tamanhos semelhantes. A molécula X é apolar e a molécula Y possui vários grupos polares. Ambas apresentam o mesmo gradiente através de uma bicamada lipídica sem proteínas. Qual resultado é mais provável?",
        "alternativas": {
            "A": "Y atravessará mais rapidamente porque interage melhor com a água.",
            "B": "Ambas atravessarão com a mesma velocidade porque possuem tamanho semelhante.",
            "C": "Nenhuma atravessará porque a bicamada é impermeável a todas as moléculas.",
            "D": "X atravessará mais rapidamente porque se dissolve melhor na região hidrofóbica da membrana."
        },
        "gabarito": "D",
        "distratores": {
            "A": "confundir solubilidade em água com permeabilidade através da fase lipídica.",
            "B": "considerar o tamanho como único determinante da permeabilidade, ignorando a polaridade.",
            "C": "interpretar a membrana como uma barreira absolutamente impermeável na ausência de proteínas.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Permeabilidade seletiva da bicamada lipídica",
            "Permeabilidade seletiva da bicamada lipídica (Média)"
        ]
    },
    {
        "id": "t1_4",
        "codigo": "T1.4",
        "topico_id": "T1",
        "topico_nome": "Permeabilidade seletiva da bicamada lipídica",
        "dificuldade": "Média",
        "pergunta": "Um hormônio esteroide e um hormônio peptídico estão presentes no meio extracelular. Considerando apenas a capacidade de atravessar diretamente a bicamada plasmática, qual previsão é mais adequada?",
        "alternativas": {
            "A": "O hormônio peptídico atravessará mais facilmente por ser hidrossolúvel.",
            "B": "Ambos atravessarão igualmente porque são moléculas sinalizadoras.",
            "C": "O esteroide atravessará mais facilmente por apresentar elevada lipossolubilidade.",
            "D": "Nenhum atravessará sem hidrólise de ATP."
        },
        "gabarito": "C",
        "distratores": {
            "A": "considerar que maior solubilidade no meio aquoso implica maior passagem pela região hidrofóbica da membrana.",
            "B": "acreditar que a função biológica da molécula determina sua permeabilidade, independentemente de suas propriedades físico-químicas.",
            "C": "Gabarito correto.",
            "D": "considerar que toda passagem através da membrana exige energia metabólica."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Permeabilidade seletiva da bicamada lipídica",
            "Permeabilidade seletiva da bicamada lipídica (Média)"
        ]
    },
    {
        "id": "t1_5",
        "codigo": "T1.5",
        "topico_id": "T1",
        "topico_nome": "Permeabilidade seletiva da bicamada lipídica",
        "dificuldade": "Difícil",
        "pergunta": "Uma base fraca existe nas formas neutra HB e carregada B⁻. Em determinado pH, aumenta a proporção da forma neutra, sem alteração da concentração total da substância. Qual consequência é esperada para sua difusão direta através da bicamada?",
        "alternativas": {
            "A": "A permeabilidade diminui porque moléculas neutras não interagem com fosfolipídios.",
            "B": "A permeabilidade aumenta porque aumenta a fração capaz de entrar na região hidrofóbica.",
            "C": "A permeabilidade permanece necessariamente constante porque a concentração total não mudou.",
            "D": "A difusão deixa de ocorrer porque somente íons atravessam membranas biológicas."
        },
        "gabarito": "B",
        "distratores": {
            "A": "acreditar que a ausência de carga dificulta a interação com a membrana lipídica.",
            "B": "Gabarito correto.",
            "C": "considerar apenas a concentração total e ignorar que o estado de ionização modifica a permeabilidade.",
            "D": "inverter a relação entre carga e permeabilidade, considerando íons mais permeáveis que formas neutras."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Permeabilidade seletiva da bicamada lipídica",
            "Permeabilidade seletiva da bicamada lipídica (Difícil)"
        ]
    },
    {
        "id": "t1_6",
        "codigo": "T1.6",
        "topico_id": "T1",
        "topico_nome": "Permeabilidade seletiva da bicamada lipídica",
        "dificuldade": "Difícil",
        "pergunta": "Uma molécula pequena apresenta coeficiente de difusão elevado em água, mas atravessa muito lentamente uma bicamada lipídica. Qual propriedade explica melhor essa aparente contradição?",
        "alternativas": {
            "A": "Elevada carga ou polaridade da molécula",
            "B": "Pequena massa molecular",
            "C": "Grande diferença de concentração",
            "D": "Elevada mobilidade molecular em solução"
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "interpretar pequena massa molecular como fator capaz de explicar baixa permeabilidade.",
            "C": "acreditar que um gradiente maior diminui a difusão.",
            "D": "confundir mobilidade em solução aquosa com capacidade de partição na membrana lipídica."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Permeabilidade seletiva da bicamada lipídica",
            "Permeabilidade seletiva da bicamada lipídica (Difícil)"
        ]
    },
    {
        "id": "t2_1",
        "codigo": "T2.1",
        "topico_id": "T2",
        "topico_nome": "Gradiente de concentração e fluxo líquido",
        "dificuldade": "Fácil",
        "pergunta": "Um soluto permeável está mais concentrado no compartimento A do que no compartimento B. Não existem outras forças atuando sobre ele. Qual será a direção do fluxo líquido inicial deste soluto?",
        "alternativas": {
            "A": "De B para A",
            "B": "De A para B",
            "C": "Não haverá movimento molecular",
            "D": "Metade das moléculas irá em cada sentido, produzindo fluxo líquido zero"
        },
        "gabarito": "B",
        "distratores": {
            "A": "inverter a relação entre gradiente de concentração e direção do fluxo líquido.",
            "B": "Gabarito correto.",
            "C": "considerar que a difusão exige uma força ou fonte externa de energia.",
            "D": "confundir movimento molecular bidirecional com igualdade dos fluxos nos dois sentidos."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Gradiente de concentração e fluxo líquido",
            "Gradiente de concentração e fluxo líquido (Fácil)"
        ]
    },
    {
        "id": "t2_2",
        "codigo": "T2.2",
        "topico_id": "T2",
        "topico_nome": "Gradiente de concentração e fluxo líquido",
        "dificuldade": "Fácil",
        "pergunta": "Após o equilíbrio de concentração de um soluto permeável entre dois compartimentos:",
        "alternativas": {
            "A": "todas as moléculas permanecem imóveis.",
            "B": "as moléculas atravessam a membrana apenas ocasionalmente.",
            "C": "continua havendo movimento nos dois sentidos, mas sem fluxo líquido.",
            "D": "o soluto passa a mover-se apenas no compartimento que possui maior volume."
        },
        "gabarito": "C",
        "distratores": {
            "A": "interpretar equilíbrio como ausência de movimento molecular.",
            "B": "considerar que a movimentação praticamente cessa quando o equilíbrio é atingido.",
            "C": "Gabarito correto.",
            "D": "acreditar que o volume do compartimento determina sozinho o sentido da movimentação molecular."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Gradiente de concentração e fluxo líquido",
            "Gradiente de concentração e fluxo líquido (Fácil)"
        ]
    },
    {
        "id": "t2_3",
        "codigo": "T2.3",
        "topico_id": "T2",
        "topico_nome": "Gradiente de concentração e fluxo líquido",
        "dificuldade": "Média",
        "pergunta": "Dois recipientes estão separados por uma membrana permeável ao soluto X. Inicialmente: compartimento A: 10 mmol/L de X; compartimento B: 2 mmol/L de X. Qual afirmação descreve corretamente o movimento inicial das moléculas?",
        "alternativas": {
            "A": "As moléculas de X movimentam-se exclusivamente de A para B.",
            "B": "O movimento de B para A é impossível enquanto existir diferença de concentração.",
            "C": "A difusão ocorre somente após a membrana fornecer energia às moléculas.",
            "D": "Há movimento nos dois sentidos, mas mais moléculas passam de A para B por unidade de tempo."
        },
        "gabarito": "D",
        "distratores": {
            "A": "confundir fluxo líquido com movimento unidirecional de todas as moléculas.",
            "B": "acreditar que moléculas não podem se mover contra o gradiente por movimento aleatório individual.",
            "C": "considerar a difusão um processo dependente de energia fornecida pela membrana.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Gradiente de concentração e fluxo líquido",
            "Gradiente de concentração e fluxo líquido (Média)"
        ]
    },
    {
        "id": "t2_4",
        "codigo": "T2.4",
        "topico_id": "T2",
        "topico_nome": "Gradiente de concentração e fluxo líquido",
        "dificuldade": "Média",
        "pergunta": "Dois solutos apresentam o mesmo gradiente de concentração através de uma membrana permeável a ambos. O soluto X possui massa molecular muito menor que o soluto Y. Mantidas as demais propriedades constantes, qual previsão é mais adequada?",
        "alternativas": {
            "A": "X tende a difundir-se mais rapidamente que Y.",
            "B": "Y tende a difundir-se mais rapidamente porque contém mais matéria.",
            "C": "Ambos necessariamente apresentam a mesma velocidade de difusão.",
            "D": "Y não apresentará movimento molecular."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "considerar maior massa molecular como causa de maior velocidade de difusão.",
            "C": "acreditar que apenas o gradiente determina a velocidade, ignorando propriedades do soluto.",
            "D": "transformar uma diferença quantitativa na velocidade em uma ausência completa de movimento."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Gradiente de concentração e fluxo líquido",
            "Gradiente de concentração e fluxo líquido (Média)"
        ]
    },
    {
        "id": "t2_5",
        "codigo": "T2.5",
        "topico_id": "T2",
        "topico_nome": "Gradiente de concentração e fluxo líquido",
        "dificuldade": "Difícil",
        "pergunta": "A concentração de um soluto é inicialmente 12 mmol/L no compartimento A e 4 mmol/L no B. Durante a difusão, passa para 9 mmol/L em A e 7 mmol/L em B. Qual alteração ocorreu no fluxo líquido entre esses dois momentos?",
        "alternativas": {
            "A": "Aumentou porque há mais soluto em B.",
            "B": "Tornou-se zero porque já existem moléculas em ambos os compartimentos.",
            "C": "Inverteu-se porque a concentração em B aumentou.",
            "D": "Diminuiu porque a diferença de concentração ficou menor."
        },
        "gabarito": "D",
        "distratores": {
            "A": "usar a concentração absoluta do compartimento receptor, e não a diferença entre os compartimentos, para prever o fluxo.",
            "B": "considerar que a presença de soluto nos dois lados elimina o fluxo líquido.",
            "C": "acreditar que qualquer aumento de concentração no destino produz automaticamente inversão do fluxo.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Gradiente de concentração e fluxo líquido",
            "Gradiente de concentração e fluxo líquido (Difícil)"
        ]
    },
    {
        "id": "t2_6",
        "codigo": "T2.6",
        "topico_id": "T2",
        "topico_nome": "Gradiente de concentração e fluxo líquido",
        "dificuldade": "Difícil",
        "pergunta": "Dois compartimentos possuem concentrações iguais de um soluto permeável. Algumas moléculas presentes apenas no compartimento A são marcadas radioativamente. Depois de algum tempo, moléculas marcadas são encontradas também em B, embora a concentração total do soluto continue igual nos dois lados. Qual conclusão é correta?",
        "alternativas": {
            "A": "Surgiu um gradiente de concentração total de A para B.",
            "B": "A marcação radioativa fornece energia para o transporte ativo.",
            "C": "O equilíbrio não impede a movimentação individual das moléculas.",
            "D": "A presença de moléculas marcadas em B demonstra fluxo líquido permanente de A para B."
        },
        "gabarito": "C",
        "distratores": {
            "A": "confundir redistribuição de moléculas marcadas com alteração da concentração total.",
            "B": "interpretar o marcador como fonte energética capaz de provocar transporte.",
            "C": "Gabarito correto.",
            "D": "confundir troca molecular bidirecional com fluxo líquido."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Gradiente de concentração e fluxo líquido",
            "Gradiente de concentração e fluxo líquido (Difícil)"
        ]
    },
    {
        "id": "t3_1",
        "codigo": "T3.1",
        "topico_id": "T3",
        "topico_nome": "Difusão simples e difusão facilitada",
        "dificuldade": "Fácil",
        "pergunta": "A glicose entra em determinada célula por GLUT, a favor de seu gradiente e sem gasto direto de ATP. Esse processo é:",
        "alternativas": {
            "A": "difusão simples.",
            "B": "difusão facilitada.",
            "C": "transporte ativo primário.",
            "D": "transporte ativo secundário."
        },
        "gabarito": "B",
        "distratores": {
            "A": "considerar qualquer movimento a favor do gradiente como difusão simples, ignorando a participação do transportador.",
            "B": "Gabarito correto.",
            "C": "considerar que toda proteína transportadora utiliza ATP diretamente.",
            "D": "confundir qualquer transporte mediado por proteína com transporte ativo secundário."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Difusão simples e difusão facilitada",
            "Difusão simples e difusão facilitada (Fácil)"
        ]
    },
    {
        "id": "t3_2",
        "codigo": "T3.2",
        "topico_id": "T3",
        "topico_nome": "Difusão simples e difusão facilitada",
        "dificuldade": "Fácil",
        "pergunta": "Qual característica diferencia diretamente a difusão facilitada da difusão simples pela bicamada?",
        "alternativas": {
            "A": "A difusão facilitada pode ocorrer a favor do gradiente.",
            "B": "A difusão facilitada envolve uma proteína de membrana.",
            "C": "Apenas a difusão simples ocorre espontaneamente.",
            "D": "Apenas a difusão facilitada apresenta movimento molecular aleatório."
        },
        "gabarito": "B",
        "distratores": {
            "A": "considerar o movimento a favor do gradiente exclusivo da difusão facilitada.",
            "B": "Gabarito correto.",
            "C": "acreditar que a participação de uma proteína torna o processo energeticamente não espontâneo.",
            "D": "considerar o movimento aleatório uma propriedade exclusiva de um mecanismo de transporte."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Difusão simples e difusão facilitada",
            "Difusão simples e difusão facilitada (Fácil)"
        ]
    },
    {
        "id": "t3_3",
        "codigo": "T3.3",
        "topico_id": "T3",
        "topico_nome": "Difusão simples e difusão facilitada",
        "dificuldade": "Média",
        "pergunta": "A velocidade de entrada de um soluto aumenta com sua concentração externa, mas aproxima-se progressivamente de um valor máximo. Esse comportamento é mais compatível com:",
        "alternativas": {
            "A": "transporte mediado por um número limitado de proteínas.",
            "B": "difusão simples pela bicamada.",
            "C": "ausência de movimento molecular.",
            "D": "redução progressiva da permeabilidade da bicamada provocada pelo soluto."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "considerar que a difusão simples apresenta saturação por disponibilidade limitada de sítios.",
            "C": "interpretar o platô de velocidade como interrupção do movimento.",
            "D": "atribuir saturação do transporte a uma mudança da própria bicamada, em vez da ocupação dos transportadores."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Difusão simples e difusão facilitada",
            "Difusão simples e difusão facilitada (Média)"
        ]
    },
    {
        "id": "t3_4",
        "codigo": "T3.4",
        "topico_id": "T3",
        "topico_nome": "Difusão simples e difusão facilitada",
        "dificuldade": "Média",
        "pergunta": "Um inibidor bloqueia especificamente os transportadores responsáveis pela entrada de glicose, sem alterar a bicamada. Qual resultado é esperado?",
        "alternativas": {
            "A": "A entrada de glicose por difusão facilitada diminui.",
            "B": "A difusão direta de O₂ também é bloqueada.",
            "C": "A glicose passa necessariamente a utilizar transporte ativo.",
            "D": "A concentração de glicose deixa de influenciar seu transporte."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "considerar que todos os solutos utilizam as mesmas proteínas para atravessar a membrana.",
            "C": "acreditar que a célula automaticamente substitui um mecanismo de transporte por outro.",
            "D": "desconsiderar a influência do gradiente sobre o transporte passivo mediado."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Difusão simples e difusão facilitada",
            "Difusão simples e difusão facilitada (Média)"
        ]
    },
    {
        "id": "t3_5",
        "codigo": "T3.5",
        "topico_id": "T3",
        "topico_nome": "Difusão simples e difusão facilitada",
        "dificuldade": "Difícil",
        "pergunta": "Dois solutos X e Y entram na célula a favor de seus gradientes. Ao dobrar suas concentrações extracelulares a partir de valores já muito elevados, a taxa de entrada de X praticamente dobra, mas a de Y sofre pouca alteração. Qual interpretação é mais provável?",
        "alternativas": {
            "A": "X utiliza transporte ativo e Y difusão simples.",
            "B": "Ambos utilizam necessariamente o mesmo mecanismo.",
            "C": "X utiliza principalmente difusão simples e Y utiliza transporte mediado saturável.",
            "D": "Y não apresenta mais movimento molecular."
        },
        "gabarito": "C",
        "distratores": {
            "A": "associar relação aproximadamente linear entre concentração e fluxo ao transporte ativo.",
            "B": "inferir mecanismos iguais apenas porque ambos os solutos se movem a favor do gradiente.",
            "C": "Gabarito correto.",
            "D": "confundir saturação da taxa com interrupção do movimento molecular."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Difusão simples e difusão facilitada",
            "Difusão simples e difusão facilitada (Difícil)"
        ]
    },
    {
        "id": "t3_6",
        "codigo": "T3.6",
        "topico_id": "T3",
        "topico_nome": "Difusão simples e difusão facilitada",
        "dificuldade": "Difícil",
        "pergunta": "A adição de um composto estruturalmente semelhante ao soluto X reduz fortemente a entrada de X, embora não modifique seu gradiente. Qual observação adicional reforçaria mais a hipótese de difusão facilitada?",
        "alternativas": {
            "A": "X apresenta elevada solubilidade na bicamada lipídica.",
            "B": "A taxa de transporte de X apresenta saturação em concentrações elevadas.",
            "C": "A taxa de X aumenta indefinidamente em proporção ao gradiente.",
            "D": "X atravessa igualmente bem uma membrana artificial sem proteínas."
        },
        "gabarito": "B",
        "distratores": {
            "A": "interpretar elevada lipossolubilidade como evidência de transporte mediado.",
            "B": "Gabarito correto.",
            "C": "considerar comportamento não saturável como evidência de participação de transportadores.",
            "D": "desconsiderar que passagem eficiente por uma bicamada sem proteínas argumenta contra a necessidade de um transportador."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Difusão simples e difusão facilitada",
            "Difusão simples e difusão facilitada (Difícil)"
        ]
    },
    {
        "id": "t4_1",
        "codigo": "T4.1",
        "topico_id": "T4",
        "topico_nome": "Diferenças entre canais e transportadores",
        "dificuldade": "Fácil",
        "pergunta": "Qual característica é típica de um canal iônico?",
        "alternativas": {
            "A": "Forma uma via aquosa pela qual íons podem atravessar a membrana.",
            "B": "Necessariamente hidrolisa ATP a cada íon transportado.",
            "C": "Liga uma molécula e muda de conformação obrigatoriamente a cada íon que atravessa.",
            "D": "Transporta apenas moléculas apolares."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "considerar que transporte de íons necessariamente exige ATP.",
            "C": "confundir o mecanismo de canais com o modelo de acesso alternante dos transportadores.",
            "D": "considerar que canais são vias destinadas a substâncias apolares."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Diferenças entre canais e transportadores",
            "Diferenças entre canais e transportadores (Fácil)"
        ]
    },
    {
        "id": "t4_2",
        "codigo": "T4.2",
        "topico_id": "T4",
        "topico_nome": "Diferenças entre canais e transportadores",
        "dificuldade": "Fácil",
        "pergunta": "Um transportador do tipo carreador difere de um canal porque:",
        "alternativas": {
            "A": "nunca é uma proteína de membrana.",
            "B": "apresenta ligação ao soluto e alterações conformacionais durante o ciclo de transporte.",
            "C": "permite sempre fluxo mais rápido que um canal.",
            "D": "transporta necessariamente contra o gradiente."
        },
        "gabarito": "B",
        "distratores": {
            "A": "não reconhecer transportadores como proteínas integrais de membrana.",
            "B": "Gabarito correto.",
            "C": "inverter a relação típica entre as taxas de condução de canais e transportadores.",
            "D": "considerar que todo carreador realiza transporte ativo."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Diferenças entre canais e transportadores",
            "Diferenças entre canais e transportadores (Fácil)"
        ]
    },
    {
        "id": "t4_4",
        "codigo": "T4.4",
        "topico_id": "T4",
        "topico_nome": "Diferenças entre canais e transportadores",
        "dificuldade": "Média",
        "pergunta": "Uma proteína apresenta um sítio para glicose voltado inicialmente para o meio extracelular. Depois da ligação da glicose, muda de conformação e expõe o sítio ao citoplasma. O mecanismo é característico de:",
        "alternativas": {
            "A": "canal aquoso.",
            "B": "difusão direta pela bicamada.",
            "C": "poro lipídico inespecífico.",
            "D": "transportador."
        },
        "gabarito": "D",
        "distratores": {
            "A": "interpretar qualquer proteína de passagem como canal.",
            "B": "desconsiderar a participação explícita da proteína e da mudança conformacional.",
            "C": "confundir uma proteína específica de transporte com uma abertura inespecífica na membrana.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Diferenças entre canais e transportadores",
            "Diferenças entre canais e transportadores (Média)"
        ]
    },
    {
        "id": "t4_5",
        "codigo": "T4.5",
        "topico_id": "T4",
        "topico_nome": "Diferenças entre canais e transportadores",
        "dificuldade": "Difícil",
        "pergunta": "Duas proteínas permitem fluxo passivo a favor do gradiente. A proteína X conduz aproximadamente 10⁷ partículas por segundo; a proteína Y apresenta uma taxa muito menor e saturação pronunciada. Qual associação é mais plausível?",
        "alternativas": {
            "A": "X é transportador e Y é canal.",
            "B": "X é canal e Y é transportador.",
            "C": "Ambas obrigatoriamente são bombas.",
            "D": "X realiza transporte ativo primário e Y difusão simples."
        },
        "gabarito": "B",
        "distratores": {
            "A": "inverter as características cinéticas típicas de canais e transportadores.",
            "B": "Gabarito correto.",
            "C": "considerar que toda proteína responsável por transporte transmembrana é uma bomba.",
            "D": "confundir fluxo rápido a favor do gradiente com transporte ativo e tratar difusão simples como processo mediado por proteína."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Diferenças entre canais e transportadores",
            "Diferenças entre canais e transportadores (Difícil)"
        ]
    },
    {
        "id": "t4_6",
        "codigo": "T4.6",
        "topico_id": "T4",
        "topico_nome": "Diferenças entre canais e transportadores",
        "dificuldade": "Difícil",
        "pergunta": "Uma mutação impede que um transportador alterne sua abertura entre os lados intra e extracelular, deixando simultaneamente uma passagem contínua entre ambos. Qual consequência funcional transformaria mais profundamente seu mecanismo?",
        "alternativas": {
            "A": "Passaria a comportar-se mais como um canal.",
            "B": "Passaria necessariamente a utilizar ATP.",
            "C": "Deixaria de permitir qualquer fluxo passivo.",
            "D": "Tornaria a bicamada permeável a todas as substâncias."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "associar formação de uma passagem contínua à necessidade de hidrólise de ATP.",
            "C": "acreditar que uma via continuamente aberta impede fluxo passivo.",
            "D": "confundir a seletividade de uma proteína com a permeabilidade global da bicamada."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Diferenças entre canais e transportadores",
            "Diferenças entre canais e transportadores (Difícil)"
        ]
    },
    {
        "id": "t5_1",
        "codigo": "T5.1",
        "topico_id": "T5",
        "topico_nome": "Osmose, osmolaridade e tonicidade",
        "dificuldade": "Fácil",
        "pergunta": "Uma hemácia é colocada em solução hipotônica contendo soluto não penetrante. Qual alteração é esperada?",
        "alternativas": {
            "A": "Perda de água e diminuição de volume",
            "B": "Entrada de água e aumento de volume",
            "C": "Manutenção obrigatória do volume",
            "D": "Saída de água até a célula ficar hipertônica"
        },
        "gabarito": "B",
        "distratores": {
            "A": "inverter a direção osmótica da água.",
            "B": "Gabarito correto.",
            "C": "acreditar que a célula mantém automaticamente seu volume independentemente da tonicidade.",
            "D": "considerar que a água sai de uma célula quando o meio externo apresenta menor concentração efetiva de solutos."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Osmose, osmolaridade e tonicidade",
            "Osmose, osmolaridade e tonicidade (Fácil)"
        ]
    },
    {
        "id": "t5_2",
        "codigo": "T5.2",
        "topico_id": "T5",
        "topico_nome": "Osmose, osmolaridade e tonicidade",
        "dificuldade": "Fácil",
        "pergunta": "Ao ser colocada em uma solução hipertônica contendo apenas solutos não penetrantes, uma célula tende a:",
        "alternativas": {
            "A": "ganhar água.",
            "B": "manter necessariamente o volume.",
            "C": "perder água.",
            "D": "aumentar sua quantidade de água e soluto na mesma proporção."
        },
        "gabarito": "C",
        "distratores": {
            "A": "inverter a direção do fluxo osmótico.",
            "B": "confundir uma solução hipertônica com uma isotônica.",
            "C": "Gabarito correto.",
            "D": "assumir que o soluto não penetrante acompanha a água através da membrana."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Osmose, osmolaridade e tonicidade",
            "Osmose, osmolaridade e tonicidade (Fácil)"
        ]
    },
    {
        "id": "t5_3",
        "codigo": "T5.3",
        "topico_id": "T5",
        "topico_nome": "Osmose, osmolaridade e tonicidade",
        "dificuldade": "Média",
        "pergunta": "Uma célula contendo 300 mOsm/L de solutos não penetrantes é colocada em solução de NaCl efetivamente não penetrante com 400 mOsm/L. Qual alteração inicial é esperada?",
        "alternativas": {
            "A": "Entrada líquida de água",
            "B": "Saída líquida de água",
            "C": "Ausência de fluxo de água",
            "D": "Entrada líquida de NaCl acompanhada obrigatoriamente por água"
        },
        "gabarito": "B",
        "distratores": {
            "A": "inverter a relação entre concentração efetiva de solutos e movimento de água.",
            "B": "Gabarito correto.",
            "C": "considerar que diferenças relativamente pequenas de osmolaridade não produzem fluxo.",
            "D": "supor que o soluto descrito como não penetrante atravessará a membrana junto com a água."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Osmose, osmolaridade e tonicidade",
            "Osmose, osmolaridade e tonicidade (Média)"
        ]
    },
    {
        "id": "t5_4",
        "codigo": "T5.4",
        "topico_id": "T5",
        "topico_nome": "Osmose, osmolaridade e tonicidade",
        "dificuldade": "Média",
        "pergunta": "Uma célula apresenta a mesma osmolaridade total que o meio externo. Entretanto, grande parte do soluto externo atravessa rapidamente a membrana. Qual conclusão é correta?",
        "alternativas": {
            "A": "A solução externa é necessariamente isotônica.",
            "B": "Igual osmolaridade garante sempre volume celular constante.",
            "C": "A tonicidade depende também da permeabilidade da membrana aos solutos.",
            "D": "Solutos penetrantes produzem obrigatoriamente encolhimento permanente."
        },
        "gabarito": "C",
        "distratores": {
            "A": "tratar iso-osmolaridade e isotonicidade como sinônimos.",
            "B": "considerar apenas o número total de partículas e ignorar sua permeabilidade.",
            "C": "Gabarito correto.",
            "D": "atribuir aos solutos penetrantes o mesmo efeito permanente dos solutos não penetrantes."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Osmose, osmolaridade e tonicidade",
            "Osmose, osmolaridade e tonicidade (Média)"
        ]
    },
    {
        "id": "t5_5",
        "codigo": "T5.5",
        "topico_id": "T5",
        "topico_nome": "Osmose, osmolaridade e tonicidade",
        "dificuldade": "Difícil",
        "pergunta": "Uma hemácia é colocada em 300 mOsm/L de ureia. Qual comportamento é mais provável após algum tempo?",
        "alternativas": {
            "A": "Permanência indefinida do volume inicial porque a solução é isosmótica.",
            "B": "Saída permanente de água porque a ureia aumenta a tonicidade externa.",
            "C": "Saída de todos os solutos intracelulares até o equilíbrio.",
            "D": "Entrada de ureia seguida de entrada de água e aumento do volume celular."
        },
        "gabarito": "D",
        "distratores": {
            "A": "confundir iso-osmolaridade com isotonicidade.",
            "B": "considerar todo soluto extracelular como osmólito efetivo, independentemente da permeabilidade.",
            "C": "generalizar a permeabilidade à ureia para todos os solutos intracelulares.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Osmose, osmolaridade e tonicidade",
            "Osmose, osmolaridade e tonicidade (Difícil)"
        ]
    },
    {
        "id": "t5_6",
        "codigo": "T5.6",
        "topico_id": "T5",
        "topico_nome": "Osmose, osmolaridade e tonicidade",
        "dificuldade": "Difícil",
        "pergunta": "Uma célula apresenta inicialmente volume constante em determinada solução. Um soluto extracelular que antes era impermeável torna-se rapidamente permeável após a abertura de um transportador. A concentração total externa não muda. Por que o volume celular pode se alterar?",
        "alternativas": {
            "A": "Porque a osmolaridade, sozinha, determina sempre a tonicidade.",
            "B": "Porque a contribuição do soluto para a tonicidade diminui quando ele passa a atravessar a membrana.",
            "C": "Porque a água deixa de atravessar a membrana quando um soluto se torna permeável.",
            "D": "Porque todo transporte de soluto exige saída simultânea de água."
        },
        "gabarito": "B",
        "distratores": {
            "A": "considerar tonicidade determinada exclusivamente pela osmolaridade.",
            "B": "Gabarito correto.",
            "C": "acreditar que a passagem de soluto impede a passagem de água.",
            "D": "interpretar o movimento de água como obrigatoriamente acoplado estequiometricamente ao transporte de soluto."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Osmose, osmolaridade e tonicidade",
            "Osmose, osmolaridade e tonicidade (Difícil)"
        ]
    },
    {
        "id": "t6_1",
        "codigo": "T6.1",
        "topico_id": "T6",
        "topico_nome": "Transporte ativo primário",
        "dificuldade": "Fácil",
        "pergunta": "Qual condição define transporte ativo primário?",
        "alternativas": {
            "A": "Movimento de água através de uma membrana",
            "B": "Movimento de soluto a favor do gradiente por uma proteína",
            "C": "Movimento de soluto com uso direto de uma fonte de energia, como ATP, pelo transportador",
            "D": "Movimento de um soluto utilizando o gradiente de outro soluto sem hidrólise direta de ATP"
        },
        "gabarito": "C",
        "distratores": {
            "A": "confundir osmose com transporte ativo.",
            "B": "considerar qualquer transporte mediado por proteína como transporte ativo.",
            "C": "Gabarito correto.",
            "D": "confundir transporte ativo primário com transporte ativo secundário."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo primário",
            "Transporte ativo primário (Fácil)"
        ]
    },
    {
        "id": "t6_2",
        "codigo": "T6.2",
        "topico_id": "T6",
        "topico_nome": "Transporte ativo primário",
        "dificuldade": "Fácil",
        "pergunta": "A Ca²⁺-ATPase transporta Ca²⁺ contra seu gradiente utilizando ATP. Ela realiza:",
        "alternativas": {
            "A": "transporte ativo primário.",
            "B": "transporte ativo secundário.",
            "C": "difusão simples.",
            "D": "difusão facilitada."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "não diferenciar uso direto de ATP de utilização de um gradiente previamente estabelecido.",
            "C": "considerar possível difusão simples de um íon contra seu gradiente.",
            "D": "classificar qualquer transporte mediado por proteína como difusão facilitada."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo primário",
            "Transporte ativo primário (Fácil)"
        ]
    },
    {
        "id": "t6_3",
        "codigo": "T6.3",
        "topico_id": "T6",
        "topico_nome": "Transporte ativo primário",
        "dificuldade": "Média",
        "pergunta": "Uma célula sofre queda abrupta na concentração de ATP. Qual processo tende a ser afetado diretamente e imediatamente?",
        "alternativas": {
            "A": "Difusão de O₂ pela bicamada",
            "B": "Fluxo de K⁺ através de um canal aberto",
            "C": "Movimento osmótico de água",
            "D": "Transporte de Ca²⁺ por uma Ca²⁺-ATPase"
        },
        "gabarito": "D",
        "distratores": {
            "A": "considerar que a difusão simples requer ATP.",
            "B": "considerar que canais iônicos utilizam ATP para conduzir cada íon.",
            "C": "considerar a osmose um processo metabolicamente energizado.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo primário",
            "Transporte ativo primário (Média)"
        ]
    },
    {
        "id": "t6_5",
        "codigo": "T6.5",
        "topico_id": "T6",
        "topico_nome": "Transporte ativo primário",
        "dificuldade": "Difícil",
        "pergunta": "Uma ATPase transporta um íon contra seu gradiente. Uma mutação permite que ela continue ligando o íon e ATP, mas impede a hidrólise do ATP. Qual resultado é mais provável?",
        "alternativas": {
            "A": "O transporte contra o gradiente continuará normalmente.",
            "B": "A proteína passará automaticamente a funcionar como canal.",
            "C": "O ciclo de transporte ativo ficará comprometido.",
            "D": "O gradiente será suficiente para levar o íon contra sua própria força eletroquímica."
        },
        "gabarito": "C",
        "distratores": {
            "A": "considerar a simples ligação de ATP suficiente para fornecer energia ao ciclo.",
            "B": "acreditar que a perda da atividade ATPásica transforma automaticamente uma bomba em canal.",
            "C": "Gabarito correto.",
            "D": "considerar que um gradiente pode espontaneamente impulsionar a própria substância contra esse mesmo gradiente."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo primário",
            "Transporte ativo primário (Difícil)"
        ]
    },
    {
        "id": "t6_6",
        "codigo": "T6.6",
        "topico_id": "T6",
        "topico_nome": "Transporte ativo primário",
        "dificuldade": "Difícil",
        "pergunta": "Uma bomba mantém uma concentração de Ca²⁺ citosólico muito menor que a extracelular. Quando a bomba é inibida, ainda existe inicialmente forte gradiente favorecendo a entrada de Ca²⁺. Qual sequência é mais provável se houver vias passivas permeáveis ao Ca²⁺?",
        "alternativas": {
            "A": "O gradiente é mantido indefinidamente porque a bomba não determina concentrações.",
            "B": "O Ca²⁺ começa a acumular-se no citosol e o gradiente diminui progressivamente.",
            "C": "O Ca²⁺ passa espontaneamente a sair contra seu gradiente.",
            "D": "Toda movimentação de Ca²⁺ cessa imediatamente."
        },
        "gabarito": "B",
        "distratores": {
            "A": "não reconhecer que bombas mantêm gradientes contra fluxos passivos contínuos.",
            "B": "Gabarito correto.",
            "C": "inverter a direção espontânea determinada pelo gradiente eletroquímico.",
            "D": "considerar que a inibição do transporte ativo também bloqueia vias passivas independentes."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo primário",
            "Transporte ativo primário (Difícil)"
        ]
    },
    {
        "id": "t7_1",
        "codigo": "T7.1",
        "topico_id": "T7",
        "topico_nome": "Transporte ativo secundário: simporte e antiporte",
        "dificuldade": "Fácil",
        "pergunta": "No transporte ativo secundário, a energia usada para mover uma substância contra seu gradiente provém diretamente:",
        "alternativas": {
            "A": "da hidrólise de ATP pelo próprio cotransportador.",
            "B": "do gradiente eletroquímico de outra substância.",
            "C": "da temperatura corporal.",
            "D": "da bicamada de fosfolipídios."
        },
        "gabarito": "B",
        "distratores": {
            "A": "confundir transporte ativo secundário com transporte ativo primário.",
            "B": "Gabarito correto.",
            "C": "considerar energia térmica como fonte direcionada de trabalho para o cotransporte.",
            "D": "atribuir à bicamada lipídica a energia necessária para o movimento contra gradiente."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo secundário: simporte e antiporte",
            "Transporte ativo secundário: simporte e antiporte (Fácil)"
        ]
    },
    {
        "id": "t7_2",
        "codigo": "T7.2",
        "topico_id": "T7",
        "topico_nome": "Transporte ativo secundário: simporte e antiporte",
        "dificuldade": "Fácil",
        "pergunta": "No SGLT, Na⁺ e glicose atravessam a membrana na mesma direção. O SGLT é um:",
        "alternativas": {
            "A": "uniporte.",
            "B": "antiporte.",
            "C": "simporte.",
            "D": "canal iônico."
        },
        "gabarito": "C",
        "distratores": {
            "A": "não reconhecer que duas espécies são transportadas de maneira acoplada.",
            "B": "confundir simporte, no qual os solutos seguem na mesma direção, com antiporte.",
            "C": "Gabarito correto.",
            "D": "interpretar o cotransportador como um poro aberto."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo secundário: simporte e antiporte",
            "Transporte ativo secundário: simporte e antiporte (Fácil)"
        ]
    },
    {
        "id": "t7_3",
        "codigo": "T7.3",
        "topico_id": "T7",
        "topico_nome": "Transporte ativo secundário: simporte e antiporte",
        "dificuldade": "Média",
        "pergunta": "Um transportador utiliza a entrada espontânea de Na⁺ para promover a saída de Ca²⁺ contra seu gradiente. Como este transporte deve ser classificado?",
        "alternativas": {
            "A": "Transporte ativo primário por simporte",
            "B": "Transporte ativo secundário por antiporte",
            "C": "Difusão facilitada por uniporte",
            "D": "Canal passivo para Na⁺ e Ca²⁺"
        },
        "gabarito": "B",
        "distratores": {
            "A": "errar simultaneamente a fonte de energia e a direção relativa dos solutos.",
            "B": "Gabarito correto.",
            "C": "ignorar o acoplamento energético entre dois solutos.",
            "D": "considerar que Na⁺ e Ca²⁺ simplesmente atravessam por um poro comum a favor de seus gradientes."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo secundário: simporte e antiporte",
            "Transporte ativo secundário: simporte e antiporte (Média)"
        ]
    },
    {
        "id": "t7_4",
        "codigo": "T7.4",
        "topico_id": "T7",
        "topico_nome": "Transporte ativo secundário: simporte e antiporte",
        "dificuldade": "Média",
        "pergunta": "O SGLT intestinal continua estruturalmente normal após a inibição da Na⁺/K⁺-ATPase. Depois de algum tempo, porém, sua capacidade de internalizar glicose diminui. Qual explicação é mais adequada?",
        "alternativas": {
            "A": "A inibição da bomba reduz progressivamente o gradiente de Na⁺ que impulsiona o SGLT.",
            "B": "O SGLT precisa hidrolisar diretamente ATP fornecido pela bomba.",
            "C": "A inibição da bomba aumenta progressivamente o gradiente de Na⁺ que impulsiona o SGLT.",
            "D": "A bomba é fisicamente parte do SGLT."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "acreditar que a Na⁺/K⁺-ATPase transfere ATP diretamente para o SGLT.",
            "C": "confundir o mecanismo de funcionamento da Na+/K+ ATPase.",
            "D": "não distinguir proteínas diferentes que são funcionalmente acopladas por um gradiente."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo secundário: simporte e antiporte",
            "Transporte ativo secundário: simporte e antiporte (Média)"
        ]
    },
    {
        "id": "t7_5",
        "codigo": "T7.5",
        "topico_id": "T7",
        "topico_nome": "Transporte ativo secundário: simporte e antiporte",
        "dificuldade": "Difícil",
        "pergunta": "Um cotransportador utiliza o gradiente de Na⁺ para concentrar um soluto X dentro da célula. Experimentalmente, as concentrações de Na⁺ nos dois lados da membrana são igualadas, mantendo-se o transportador intacto e o ATP celular normal. Qual resultado é mais provável?",
        "alternativas": {
            "A": "O transporte de X contra seu gradiente será favorecido.",
            "B": "A capacidade de acumular X diminuirá porque foi reduzida a fonte imediata de energia do cotransporte.",
            "C": "O transportador passará automaticamente a hidrolisar ATP.",
            "D": "O transporte de X ficará independente das concentrações de Na⁺."
        },
        "gabarito": "B",
        "distratores": {
            "A": "acreditar que reduzir o gradiente impulsionador aumenta o transporte acoplado.",
            "B": "Gabarito correto.",
            "C": "considerar que o cotransportador pode mudar espontaneamente de mecanismo energético.",
            "D": "não compreender que o gradiente de Na⁺ é parte essencial da força motriz do sistema."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo secundário: simporte e antiporte",
            "Transporte ativo secundário: simporte e antiporte (Difícil)"
        ]
    },
    {
        "id": "t7_6",
        "codigo": "T7.6",
        "topico_id": "T7",
        "topico_nome": "Transporte ativo secundário: simporte e antiporte",
        "dificuldade": "Difícil",
        "pergunta": "Uma célula utiliza um simporte Na⁺/X. Em uma situação experimental extrema, o gradiente eletroquímico de Na⁺ é invertido. Qual possibilidade passa a existir?",
        "alternativas": {
            "A": "O transportador necessariamente continua funcionando no mesmo sentido.",
            "B": "Vai haver ativação reativa de atividade de ATPase.",
            "C": "Dependendo dos gradientes dos dois substratos, o ciclo de transporte pode favorecer o sentido inverso de transporte.",
            "D": "O transportador para a realizar co-transporte de X com Ca⁺."
        },
        "gabarito": "C",
        "distratores": {
            "A": "considerar transportadores como dispositivos de direção fixa independentemente das forças termodinâmicas.",
            "B": "acreditar que inversão do gradiente transforma o mecanismo molecular em transporte ativo primário.",
            "C": "Gabarito correto.",
            "D": "não reconhecer o acoplamento energético entre o Na⁺ e o soluto X, bem como especificidade da proteína transportadora."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Transporte ativo secundário: simporte e antiporte",
            "Transporte ativo secundário: simporte e antiporte (Difícil)"
        ]
    },
    {
        "id": "t8_1",
        "codigo": "T8.1",
        "topico_id": "T8",
        "topico_nome": "Função da Na⁺/K⁺-ATPase",
        "dificuldade": "Fácil",
        "pergunta": "A cada ciclo, a Na⁺/K⁺-ATPase normalmente:",
        "alternativas": {
            "A": "transporta 3 Na⁺ para fora e 2 K⁺ para dentro.",
            "B": "transporta 2 Na⁺ para fora e 3 K⁺ para dentro.",
            "C": "transporta 3 Na⁺ e 3 K⁺ na mesma direção.",
            "D": "permite a difusão passiva de Na⁺ e K⁺."
        },
        "gabarito": "A",
        "distratores": {
            "A": "Gabarito correto.",
            "B": "conhecer os números 3:2, mas inverter a estequiometria dos dois íons.",
            "C": "considerar o transporte eletricamente neutro e/ou desconhecer que Na⁺ e K⁺ seguem direções opostas.",
            "D": "interpretar a bomba como canal passivo."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Função da Na⁺/K⁺-ATPase",
            "Função da Na⁺/K⁺-ATPase (Fácil)"
        ]
    },
    {
        "id": "t8_2",
        "codigo": "T8.2",
        "topico_id": "T8",
        "topico_nome": "Função da Na⁺/K⁺-ATPase",
        "dificuldade": "Fácil",
        "pergunta": "A principal função da Na⁺/K⁺-ATPase é:",
        "alternativas": {
            "A": "gerar cada fase do potencial de ação abrindo e fechando rapidamente.",
            "B": "manter ao longo do tempo os gradientes transmembrana de Na⁺ e K⁺.",
            "C": "constituir o principal canal de vazamento de K⁺.",
            "D": "permitir difusão facilitada de glicose."
        },
        "gabarito": "B",
        "distratores": {
            "A": "conceber a bomba como responsável pelos fluxos rápidos de Na⁺ e K⁺ que geram cada potencial de ação.",
            "B": "Gabarito correto.",
            "C": "confundir Na⁺/K⁺-ATPase com canais de K⁺ de vazamento.",
            "D": "confundir uma ATPase iônica com transportadores GLUT."
        },
        "pontuacao_maxima": 1.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Função da Na⁺/K⁺-ATPase",
            "Função da Na⁺/K⁺-ATPase (Fácil)"
        ]
    },
    {
        "id": "t8_3",
        "codigo": "T8.3",
        "topico_id": "T8",
        "topico_nome": "Função da Na⁺/K⁺-ATPase",
        "dificuldade": "Média",
        "pergunta": "A Na⁺/K⁺-ATPase é considerada eletrogênica porque:",
        "alternativas": {
            "A": "transporta apenas partículas sem carga.",
            "B": "move a mesma quantidade de carga em ambas as direções.",
            "C": "existe saída líquida de uma carga positiva a cada ciclo.",
            "D": "produz diretamente um potencial de ação a cada ATP hidrolisado."
        },
        "gabarito": "C",
        "distratores": {
            "A": "não reconhecer Na⁺ e K⁺ como partículas carregadas.",
            "B": "acreditar que a estequiometria 3:2 produz transporte elétrico neutro.",
            "C": "Gabarito correto.",
            "D": "confundir contribuição eletrogênica da bomba com geração do potencial de ação."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Função da Na⁺/K⁺-ATPase",
            "Função da Na⁺/K⁺-ATPase (Média)"
        ]
    },
    {
        "id": "t8_4",
        "codigo": "T8.4",
        "topico_id": "T8",
        "topico_nome": "Função da Na⁺/K⁺-ATPase",
        "dificuldade": "Média",
        "pergunta": "A Na⁺/K⁺-ATPase de um neurônio é subitamente bloqueada. Nos primeiros segundos, qual resultado é mais plausível?",
        "alternativas": {
            "A": "Os gradientes de Na⁺ e K⁺ desaparecem instantaneamente.",
            "B": "Os canais de Na⁺ e K⁺ deixam imediatamente de funcionar.",
            "C": "Os gradientes ainda existem, mas começam progressivamente a se deteriorar.",
            "D": "As concentrações de Na⁺ e K⁺ dentro e fora da célula imediatamente se tornam iguais."
        },
        "gabarito": "C",
        "distratores": {
            "A": "considerar que os gradientes dependem da atividade instantânea da bomba e desaparecem imediatamente quando ela para.",
            "B": "acreditar que a Na⁺/K⁺-ATPase controla diretamente a abertura ou funcionamento dos canais.",
            "C": "Gabarito correto.",
            "D": "superestimar enormemente a quantidade de íons que cruza a membrana em poucos segundos."
        },
        "pontuacao_maxima": 2.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Função da Na⁺/K⁺-ATPase",
            "Função da Na⁺/K⁺-ATPase (Média)"
        ]
    },
    {
        "id": "t8_5",
        "codigo": "T8.5",
        "topico_id": "T8",
        "topico_nome": "Função da Na⁺/K⁺-ATPase",
        "dificuldade": "Difícil",
        "pergunta": "A inibição prolongada da Na⁺/K⁺-ATPase provoca aumento progressivo de Na⁺ intracelular. Qual processo secundário tende a ser diretamente prejudicado por essa alteração?",
        "alternativas": {
            "A": "Difusão de O₂ pela bicamada",
            "B": "Transporte impulsionado pelo gradiente de Na⁺",
            "C": "Movimento browniano das moléculas",
            "D": "Difusão simples de hormônios esteroides"
        },
        "gabarito": "B",
        "distratores": {
            "A": "acreditar que a Na⁺/K⁺-ATPase fornece energia à difusão simples através da bicamada.",
            "B": "Gabarito correto.",
            "C": "considerar que movimento térmico molecular depende dos gradientes mantidos pela bomba.",
            "D": "considerar a difusão de substâncias lipossolúveis dependente da atividade da Na⁺/K⁺-ATPase."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Função da Na⁺/K⁺-ATPase",
            "Função da Na⁺/K⁺-ATPase (Difícil)"
        ]
    },
    {
        "id": "t8_6",
        "codigo": "T8.6",
        "topico_id": "T8",
        "topico_nome": "Função da Na⁺/K⁺-ATPase",
        "dificuldade": "Difícil",
        "pergunta": "Considere duas intervenções independentes em um neurônio: I. Bloqueio súbito da Na⁺/K⁺-ATPase. II. Bloqueio súbito da maioria dos canais de vazamento de K⁺. Qual comparação é mais adequada para o efeito inicial sobre o potencial de membrana?",
        "alternativas": {
            "A": "I tende a produzir alteração mais rápida porque a bomba é a única responsável pelo potencial de repouso.",
            "B": "Ambas obrigatoriamente produzem o mesmo efeito e na mesma velocidade.",
            "C": "Nenhuma pode alterar o potencial de membrana.",
            "D": "II pode produzir alteração mais imediata, enquanto I compromete progressivamente os gradientes que sustentam o potencial."
        },
        "gabarito": "D",
        "distratores": {
            "A": "considerar que o potencial de repouso é produzido diretamente e exclusivamente pela Na⁺/K⁺-ATPase, em vez de resultar principalmente das permeabilidades seletivas sobre gradientes mantidos pela bomba.",
            "B": "não distinguir o papel imediato da permeabilidade da membrana do papel de manutenção dos gradientes ao longo do tempo.",
            "C": "desconsiderar tanto a contribuição da permeabilidade ao K⁺ quanto a contribuição indireta e eletrogênica da Na⁺/K⁺-ATPase.",
            "D": "Gabarito correto."
        },
        "pontuacao_maxima": 3.0,
        "tipo": "multipla_escolha",
        "componentes_conhecimento": [
            "Função da Na⁺/K⁺-ATPase",
            "Função da Na⁺/K⁺-ATPase (Difícil)"
        ]
    }
]

# =============================
# SELEÇÃO ADAPTATIVA DE QUESTÕES
# =============================
def pick_adaptive_case(current_difficulty: str = "Fácil", used_cases: List[str] = None, topic_filter: str = None) -> Dict[str, Any]:
    """
    Seleciona a próxima questão adaptativamente com base na dificuldade atual do aluno
    e no filtro de tópico (se houver).
    """
    used_cases = used_cases or []
    
    # 1. Filtra por tópico se especificado
    pool = QUESTIONS
    if topic_filter and topic_filter != "Todos":
        pool = [q for q in pool if q.get("topico_id") == topic_filter]
        
    if not pool:
        pool = QUESTIONS
        
    # 2. Tenta pegar questão não respondida na dificuldade atual
    matching = [q for q in pool if q.get("dificuldade") == current_difficulty and q["id"] not in used_cases]
    
    # 3. Se esgotou na dificuldade atual, tenta qualquer não respondida do pool
    if not matching:
        matching = [q for q in pool if q["id"] not in used_cases]
        
    # 4. Se todas foram respondidas, sorteia qualquer uma da dificuldade atual
    if not matching:
        matching = [q for q in pool if q.get("dificuldade") == current_difficulty]
        
    # 5. Fallback final: qualquer questão do pool
    if not matching:
        matching = pool
        
    chosen = random.choice(matching)
    return chosen.copy()

def pick_new_case(level: int = 1, used_cases: List[str] = None, current_difficulty: str = "Fácil", topic_filter: str = None) -> Dict[str, Any]:
    """Função compatível com a assinatura anterior."""
    return pick_adaptive_case(current_difficulty=current_difficulty, used_cases=used_cases, topic_filter=topic_filter)

def get_case(cid: str) -> Dict[str, Any]:
    """Busca questão por ID."""
    for q in QUESTIONS:
        if q["id"] == cid:
            res = q.copy()
            if "resposta_esperada" not in res:
                res["resposta_esperada"] = f"Alternativa {res.get('gabarito')}: {res.get('alternativas', {}).get(res.get('gabarito'), '')}"
            return res
    res = QUESTIONS[0].copy()
    if "resposta_esperada" not in res:
        res["resposta_esperada"] = f"Alternativa {res.get('gabarito')}: {res.get('alternativas', {}).get(res.get('gabarito'), '')}"
    return res

# =============================
# AVALIAÇÃO DE RESPOSTAS (MÚLTIPLA ESCOLHA)
# =============================
def evaluate_mcq_answer(question: Dict[str, Any], selected_option: str) -> Dict[str, Any]:
    """
    Avalia a alternativa selecionada pelo aluno para a questão de múltipla escolha.
    Retorna estrutura padronizada para registro analítico e feedback pedagógico.
    """
    opt = str(selected_option).upper().strip()
    gabarito = str(question.get("gabarito", "A")).upper().strip()
    is_correct = (opt == gabarito)
    
    distratores = question.get("distratores", {})
    distractor_feedback = distratores.get(opt, "Alternativa incorreta.")
    correct_explanation = distratores.get(gabarito, "Gabarito correto.")
    
    pts = float(question.get("pontuacao_maxima", 1.0)) if is_correct else 0.0
    
    alt_text = question.get("alternativas", {}).get(opt, "")
    gab_text = question.get("alternativas", {}).get(gabarito, "")
    
    classification = "CORRETO" if is_correct else "INCORRETO"
    level = "Avançado" if is_correct else "Incorreto"
    
    if is_correct:
        feedback_text = f"**Excelente!** A alternativa **{gabarito}** está correta.\n\n💡 *Justificativa:* {correct_explanation}"
    else:
        feedback_text = f"**Atenção:** A alternativa **{opt}** está incorreta.\n\n🔍 *Análise Conceitual:* {distractor_feedback}\n\n✅ *Gabarito Correto:* **{gabarito}** — {gab_text}"
    
    return {
        "is_correct": is_correct,
        "is_partial": False,
        "level": level,
        "classification": classification,
        "points": pts,
        "points_gained": pts,
        "selected_option": opt,
        "correct_option": gabarito,
        "user_answer": f"{opt}. {alt_text}",
        "expected_answer": f"{gabarito}. {gab_text}",
        "distractor_feedback": distractor_feedback,
        "correct_explanation": correct_explanation,
        "feedback": feedback_text
    }

def evaluate_answer_with_ai(question_data: Dict, user_answer: str) -> Dict[str, Any]:
    """Fallback para compatibilidade: se user_answer for uma letra (A, B, C, D), avalia diretamente."""
    clean_ans = user_answer.strip().upper()
    if len(clean_ans) == 1 and clean_ans in ["A", "B", "C", "D"]:
        return evaluate_mcq_answer(question_data, clean_ans)
    elif clean_ans.startswith(("A.", "B.", "C.", "D.", "A)", "B)", "C)", "D)")):
        opt = clean_ans[0]
        return evaluate_mcq_answer(question_data, opt)
    else:
        gabarito = question_data.get("gabarito", "A")
        is_corr = (gabarito in clean_ans)
        return {
            "level": "Avançado" if is_corr else "Incorreto",
            "points": question_data.get("pontuacao_maxima", 1.0) if is_corr else 0.0,
            "classification": "CORRETO" if is_corr else "INCORRETO",
            "feedback": f"Resposta processada. Gabarito oficial: {gabarito}."
        }

def finalize_question_response(question: Dict[str, Any], user_answer: str, evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
    """Registra a conclusão da questão e formata o resultado final."""
    return {
        "user_answer": user_answer,
        "points_gained": evaluation_result.get("points_gained", 0),
        "is_correct": evaluation_result.get("is_correct", False),
        "is_partial": evaluation_result.get("is_partial", False),
        "classification": evaluation_result.get("classification", "INCORRETO"),
        "feedback": evaluation_result.get("feedback", ""),
        "expected_answer": evaluation_result.get("expected_answer", question.get("resposta_esperada", "N/A"))
    }

# =============================
# TUTOR SOCRÁTICO HELIX.AI (COM REGRA DE 4 INSISTÊNCIAS)
# =============================
def tutor_reply_com_ia(
    question: Dict[str, Any], 
    user_msg: str, 
    chat_history: List[Dict[str, str]], 
    insistence_count: int = 0
) -> Generator[str, None, None]:
    """
    Gera resposta socrática do tutor Helix.AI.
    Regra de proteção: Nunca dá a resposta diretamente, A NÃO SER QUE o aluno
    insista 4 ou mais vezes pedindo o gabarito.
    """
    topico_id = question.get("topico_id", "T1")
    topico_nome = question.get("topico_nome", "")
    dificuldade = question.get("dificuldade", "Fácil")
    pergunta = question.get("pergunta", "")
    alts = question.get("alternativas", {})
    gabarito = question.get("gabarito", "")
    distratores = question.get("distratores", {})
    
    alt_lines = []
    for k in ["A", "B", "C", "D"]:
        if k in alts:
            alt_lines.append(f"{k}. {alts[k]}")
    alt_str = "\n".join(alt_lines)
    
    dist_lines = []
    for k in ["A", "B", "C", "D"]:
        if k in distratores:
            dist_lines.append(f"- Opção {k}: {distratores[k]}")
    dist_str = "\n".join(dist_lines)
    
    system_prompt = f"""Você é o Tutor Helix.AI, um tutor socrático inteligente e acolhedor especialista em Genética e Fisiologia/Transporte em Membranas Biológicas.

CONTEXTO DA QUESTÃO QUE O ALUNO ESTÁ RESOLVENDO:
- Tópico: {topico_id} — {topico_nome}
- Dificuldade: {dificuldade}
- Enunciado: {pergunta}

ALTERNATIVAS:
{alt_str}

GABARITO CORRETO: Alternativa {gabarito}

ANÁLISE DE DISTRATORES E ERROS CONCEITUAIS:
{dist_str}

NÚMERO DE VEZES QUE O ALUNO INSISTIU PEDINDO A RESPOSTA: {insistence_count}

DIRETRIZES PEDAGÓGICAS ABSOLUTAS:
1. REGRA DAS 4 INSISTÊNCIAS:
   - Se o número de insistências for MENOR que 4 (insistence_count < 4):
     NUNCA revele a resposta correta, NUNCA diga qual é a letra certa ou errada e NUNCA resolva a questão diretamente para o aluno.
     Em vez disso, faça tutoria socrática: faça 1 ou 2 perguntas reflexivas, dê pistas conceituais sobre as forças físicas/químicas envolvidas (ex: polaridade, carga elétrica, solubilidade na fase lipídica, gradiente eletroquímico, necessidade de transportadores, etc.) e ajude o aluno a descartar alternativas equivocadas por raciocínio próprio.
   - Se o número de insistências for 4 ou MAIS (insistence_count >= 4):
     O aluno insistiu repetidamente pela resposta direta. Revele agora com clareza e acolhimento qual é a alternativa correta ({gabarito}) e explique didaticamente o porquê dela estar correta e onde residem os erros das demais alternativas.

2. ESTILO E TOM:
   - Seja conciso (2 a 4 linhas por resposta). Vá direto ao cerne da dúvida do aluno.
   - Tom encorajador, científico e acessível.
   - Não use saudações repetitivas se a conversa já estiver em andamento.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history[-8:]:
        role = msg["role"]
        api_role = "assistant" if role == "assistant" else "user"
        messages.append({"role": api_role, "content": msg["content"]})
        
    if user_msg and (not chat_history or chat_history[-1].get("content") != user_msg):
        messages.append({"role": "user", "content": user_msg})
        
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
                messages=messages,
                temperature=0.2,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            return 
        except Exception as e:
            print(f"[Tutor Chat] Tentativa {attempt+1}/{max_retries} falhou: {e}")
            if attempt == max_retries - 1:
                yield f"Erro ao comunicar com a IA: {e}"
                return
            time.sleep(1)

# =============================
# PERSISTÊNCIA & GAMIFICAÇÃO
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

LEVEL_THRESHOLDS = {1: 0, 2: 15, 3: 40}
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

# =============================
# INSIGHTS & ANÁLISES ANALÍTICAS DO PROFESSOR
# =============================
def correct_exam_name(n): return n, False
def normalize_exam_name(n): return n
def suggest_exam_corrections(n, a): return ""

def generate_category_insights(category_name: str, sample_answers: List[str]) -> str:
    answers_str = "\n".join([f"- \"{ans}\"" for ans in sample_answers[:5]])
    prompt = f"""Você é um coordenador pedagógico. Analise o desempenho dos alunos no tópico '{category_name}'.
Amostras:
{answers_str if sample_answers else "Sem amostras suficientes."}

Escreva 2 a 3 frases sintetizando as principais dificuldades conceituais observadas."""

    import time
    max_retries = 2
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client: return "Assistente não configurado."
        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return res.choices[0].message.content.strip()
        except:
            if attempt == max_retries - 1: return "Análise temporariamente indisponível."
            time.sleep(1)

def generate_difficulty_preview(category_name: str, sample_answers: List[str]) -> str:
    answers_str = "\n".join([f"- \"{ans}\"" for ans in sample_answers[:5]])
    prompt = f"""Resuma em UMA frase curta e direta a principal dúvida dos alunos no tópico '{category_name}':
{answers_str if sample_answers else "Nenhuma amostra disponível."}"""
    import time
    max_retries = 2
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client: return "Assistente não configurado."
        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=100
            )
            return res.choices[0].message.content.strip()
        except:
            if attempt == max_retries - 1: return "Erro ao gerar preview."
            time.sleep(1)

def generate_ai_usage_preview(chat_samples: List[str]) -> str:
    chat_str = "\n".join([f"- Aluno: \"{ans}\"" for ans in chat_samples[:10]])
    prompt = f"""Escreva UMA frase curta resumindo como os alunos estão usando o tutor IA:
{chat_str if chat_samples else "Nenhuma interação registrada."}"""
    import time
    max_retries = 2
    for attempt in range(max_retries):
        client = get_groq_client()
        if not client: return "Assistente não configurado."
        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=100
            )
            return res.choices[0].message.content.strip()
        except:
            if attempt == max_retries - 1: return "Erro ao gerar preview."
            time.sleep(1)

def generate_class_criteria_analysis(answers_list: List[str]) -> Dict[str, str]:
    default_resp = {f"{k} — {v}": "Sem dados suficientes para análise profunda." for k, v in TOPICS.items()}
    if not answers_list:
        return default_resp
    answers_str = "\n\n".join([f"Resposta do Aluno {i+1}:\n\"{ans}\"" for i, ans in enumerate(answers_list[:20])])
    prompt = f"""Analise as respostas dos alunos sobre Transporte e Membranas Biológicas e retorne um JSON com os 8 tópicos:
{json.dumps(list(TOPICS.keys()))}

Respostas:
{answers_str}

Retorne estritamente um JSON com as chaves correspondentes aos 8 tópicos."""
    import time
    for attempt in range(3):
        client = get_groq_client()
        if not client: return default_resp
        try:
            res = client.chat.completions.create(
                model=EVAL_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096
            )
            text = res.choices[0].message.content.strip()
            return _extract_json(text)
        except Exception as e:
            if attempt == 2: return default_resp
            time.sleep(1)
