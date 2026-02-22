import streamlit as st
import numpy as np

# Mock definitions
QUESTIONS = [
    {"id": f"q{i}", "dificuldade": "básico", "pergunta": f"Questão {i}"} for i in range(5)
]

def pick_new_case(level, used_cases):
    pool = [q for q in QUESTIONS if q["dificuldade"] == "básico"]
    available = [q for q in pool if q["id"] not in used_cases]
    if not available: available = pool
    return np.random.choice(available).copy()

if "counter" not in st.session_state:
    st.session_state.counter = 0
    st.session_state.used_cases = []
    st.session_state.current_case = pick_new_case(1, st.session_state.used_cases)
    st.session_state.used_cases.append(st.session_state.current_case["id"])

st.write(f"Questão Atual: {st.session_state.current_case['pergunta']}")
st.write(f"Used cases: {st.session_state.used_cases}")

text_key = f"ans_{st.session_state.counter}"
ans = st.text_area("Answer", key=text_key)

if st.button("Enviar"):
    st.success("Enviado!")

if st.button("Próxima"):
    st.session_state.counter += 1
    st.session_state.current_case = pick_new_case(1, st.session_state.used_cases)
    st.session_state.used_cases.append(st.session_state.current_case["id"])
    st.rerun()
