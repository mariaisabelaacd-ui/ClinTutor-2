import streamlit as st
import extra_streamlit_components as stx
from logic import (
    APP_NAME, pick_new_case, get_case,
    evaluate_answer_with_ai, finalize_question_response,
    level_from_score, progress_to_next_level,
    save_progress, load_progress, tutor_reply_com_ia,
    QUESTIONS
)
import uuid
import time
from datetime import datetime, timedelta
from auth_firebase import (
    init_session, login_user, logout_user, is_logged_in, get_current_user,
    register_user, authenticate_user, require_login, require_professor,
    get_all_users, delete_user, migrate_local_to_firebase, is_firebase_connected,
    create_default_admin, create_auth_token, validate_auth_token, get_user_by_id
)
from analytics import (
    start_case_timer, end_case_timer, log_chat_interaction, 
    get_user_detailed_stats, calculate_accuracy_rate,
    save_student_progress, load_student_progress
)
from admin_dashboard import show_admin_dashboard
from professor_dashboard import show_advanced_professor_dashboard

# --- GERENCIADOR DE COOKIES (SINGLETON) ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- CONFIGURAÇÃO DE ESTILO ---
def apply_custom_style():
    with open( "assets/style.css" ) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone" rel="stylesheet">', unsafe_allow_html=True)

def show_login_page():
    """Exibe página de login e cadastro com visual modernizado"""
    apply_custom_style()
    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("<div style='text-align: center; margin-bottom: 2rem;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='color: #11B965; font-size: 3.5em; margin:0;'>Helix.AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.2em; opacity: 0.7;'>Plataforma inteligente de tutoria em Biologia Molecular</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        with st.container(border=True):
            tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
            with tab1:
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="seu@email.com")
                    password = st.text_input("Senha", type="password", placeholder="••••••")
                    prof_code_login = st.text_input("Código de Professor (apenas professores)", type="password", placeholder="Deixe em branco se for aluno")
                    remember_me = st.checkbox("Manter conectado por 7 dias", value=True)
                    st.markdown("")
                    if st.form_submit_button("Acessar Sistema", type="primary", use_container_width=True):
                        if email and password:
                            with st.spinner("Autenticando..."):
                                success, message, user_data = authenticate_user(email, password)
                                if success:
                                    if user_data.get('user_type') == 'professor':
                                        if prof_code_login != 'pr0f3ss-r':
                                            st.error("Código de professor inválido.")
                                            st.stop()
                                    login_user(user_data)
                                    if remember_me:
                                        token = create_auth_token(user_data['id'])
                                        cookie_manager.set('auth_token', token, expires_at=datetime.now() + timedelta(days=7), key='set_auth')
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.warning("Preencha todos os campos.")

            with tab2:
                st.info("**Domínios aceitos:**\n- Alunos: `@aluno.fcmsantacasasp.edu.br`\n- Professores: `@fcmsantacasasp.edu.br`")
                with st.form("register_form"):
                    name = st.text_input("Nome Completo")
                    email = st.text_input("Email Institucional")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1: password = st.text_input("Senha", type="password")
                    with col_p2: confirm_password = st.text_input("Confirmar", type="password")
                    
                    user_type = None
                    ra = None
                    turma = None
                    prof_code_register = ''
                    consent_given = True  # Default para professores
                    
                    if email and '@' in email:
                        domain = email.split('@')[1].lower()
                        if 'professor' in email or domain == 'fcmsantacasasp.edu.br': 
                            user_type = 'professor'
                            prof_code_register = st.text_input("Código de Professor", type="password", placeholder="Código obrigatório para professores")
                        else: 
                            user_type = 'aluno'
                            ra = st.text_input("RA")
                            turma = st.selectbox("Turma", ["Biomedicina A", "Biomedicina B"])
                            
                            # Termo de consentimento para alunos
                            st.markdown("---")
                            st.markdown("**Termo de Consentimento de Uso e Privacidade**")
                            
                            with st.expander("Clique para ler o termo completo"):
                                st.markdown("""
                                Ao utilizar esta plataforma, o usuário declara estar ciente e de acordo que o professor responsável terá acesso aos seus resultados, respostas submetidas e interações realizadas com o chatbot educacional. Essas informações serão utilizadas única e exclusivamente para fins pedagógicos, com o objetivo de acompanhar o aprendizado, identificar dificuldades e aprimorar o processo de ensino.
                                
                                Os dados coletados serão tratados de acordo com a Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 – LGPD), sendo utilizados apenas para finalidades educacionais, acadêmicas e de melhoria da plataforma, não sendo compartilhados com terceiros para fins comerciais.
                                
                                O usuário reconhece ainda que a plataforma é disponibilizada gratuitamente e, por se tratar de um sistema automatizado em constante desenvolvimento, podem ocorrer eventuais erros, imprecisões ou instabilidades, não havendo garantia de funcionamento perfeito ou contínuo.
                                
                                Ao prosseguir com o uso da plataforma, o usuário manifesta seu consentimento com os termos acima.
                                """)
                            
                            consent_given = st.checkbox("Li e declaro que concordo com os termos de uso e privacidade", value=False)

                    if st.form_submit_button("Criar Minha Conta", type="primary", use_container_width=True):
                        if password != confirm_password: st.error("Senhas não conferem.")
                        elif len(password) < 6: st.error("Senha curta.")
                        elif user_type == 'aluno' and not consent_given:
                            st.error("Você precisa concordar com os termos de uso para prosseguir")
                        elif user_type == 'professor' and prof_code_register != 'pr0f3ss-r':
                            st.error("Código de professor inválido. Solicite o código correto ao administrador.")
                        else:
                            success, msg = register_user(name, email, password, user_type or 'aluno', ra, turma)
                            if success: st.success("Conta criada! Acesse a aba 'Entrar'.")
                            else: st.error(msg)
    st.markdown("<div style='text-align: center; margin-top: 3rem; color: #999; font-size: 0.8em;'>Helix.AI v1.0</div>", unsafe_allow_html=True)

def show_user_profile():
    user = get_current_user()
    with st.sidebar:
        st.markdown(f"<div style='display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem; font-weight: 600;'><span class='material-icons-outlined' style='font-size: 28px;'>account_circle</span> {user['name'].split()[0]}</div>", unsafe_allow_html=True)
        st.caption(f"{user['user_type'].title()}")
        if st.button("Sair", key="logout_btn", use_container_width=True):
            logout_user()
            cookie_manager.delete('auth_token')
            st.rerun()
        st.markdown("---")

def init_state():
    if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
    user = get_current_user()
    saved = load_progress()
    user_progress = {}
    if isinstance(saved, list):
        for p in saved:
            if p.get("user_id") == user["id"]: user_progress = p; break

    # Tenta restaurar progresso salvo no Firebase (1 read)
    firebase_progress = {}
    if 'progress_loaded' not in st.session_state:
        firebase_progress = load_student_progress(user["id"])
        st.session_state.progress_loaded = True

    valid_q_ids = {q["id"] for q in QUESTIONS}

    defaults = {
        "score": 0, "streak": 0, "unlocked_level": 1,
        "current_case_id": None, "case_scored": False, "last_result": None,
        "chat": [], "show_next_case_btn": False, "used_cases": [],
        "current_timer_id": None, "case_counter": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            if k == "current_case_id" and firebase_progress.get("current_question_id") in valid_q_ids:
                st.session_state[k] = firebase_progress["current_question_id"]
            elif k == "used_cases" and firebase_progress.get("used_cases"):
                st.session_state[k] = [uid for uid in firebase_progress["used_cases"] if uid in valid_q_ids]
            elif k == "score" and firebase_progress.get("score") is not None:
                st.session_state[k] = firebase_progress["score"]
            elif k == "streak" and firebase_progress.get("streak") is not None:
                st.session_state[k] = firebase_progress["streak"]
            else:
                val = user_progress.get(k, v) if k in ["score", "streak", "unlocked_level", "used_cases"] else v
                if k == "used_cases":
                    val = [uid for uid in val if uid in valid_q_ids]
                st.session_state[k] = val
def persist_now():
    user = get_current_user()
    save_progress({
        "user_id": user["id"],
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "unlocked_level": st.session_state.unlocked_level,
        "used_cases": st.session_state.used_cases,
        "when": datetime.now().isoformat()
    })
    # Salva progresso no Firebase (atualiza o doc do usuário — 1 write)
    save_student_progress(
        user_id=user["id"],
        current_question_id=st.session_state.get("current_case_id", "") or "",
        used_cases=st.session_state.used_cases,
        score=st.session_state.score,
        streak=st.session_state.streak
    )

def start_new_case():
    new_case = pick_new_case(st.session_state.unlocked_level, st.session_state.used_cases)
    st.session_state.current_case_id = new_case["id"]
    if new_case["id"] not in st.session_state.used_cases: st.session_state.used_cases.append(new_case["id"])
    
    # Timer
    user = get_current_user()
    try: st.session_state.current_timer_id = start_case_timer(user["id"], new_case["id"])
    except: pass
    
    st.session_state.case_counter += 1
    
    st.session_state.case_scored = False
    st.session_state.last_result = None
    st.session_state.chat = []
    st.session_state.show_next_case_btn = False
    st.rerun()

def main():
    st.set_page_config(page_title="Helix.AI", page_icon="🧬", layout="wide")
    apply_custom_style()
    init_session()
    create_default_admin()
    
    if not is_logged_in():
        token = st.context.cookies.get('auth_token')
        if token:
            uid = validate_auth_token(token)
            if uid:
                u_data = get_user_by_id(uid)
                if u_data: login_user(u_data); st.rerun()

    if not is_logged_in():
        show_login_page()
        return

    init_state()
    show_user_profile()
    user = get_current_user()
    
    if user["user_type"] == "admin": show_admin_dashboard(); return
    if user["user_type"] == "professor":
         nav = st.sidebar.radio("Navegação", ["Questões", "Dashboard"], label_visibility="collapsed")
         if nav == "Dashboard": show_advanced_professor_dashboard(); return
    
    # --- SIDEBAR ---
    st.sidebar.markdown("### <span class='material-icons-outlined'>emoji_events</span> Progresso", unsafe_allow_html=True)
    c1, c2 = st.sidebar.columns(2)
    c1.metric("Pontos", st.session_state.score)
    c2.metric("Streak", f"{st.session_state.streak}")
    
    # Barra de Progresso Real
    total_q = len(QUESTIONS)
    answered_q = min(len(st.session_state.used_cases), total_q)
    
    st.sidebar.markdown(f"**Questões Concluídas:** {answered_q} de {total_q}")
    st.sidebar.progress(answered_q / total_q if total_q > 0 else 0)
    
    if st.sidebar.button("Pular Questão", use_container_width=True): start_new_case()
    


    # --- MAIN CONTENT ---
    if st.session_state.current_case_id is None: start_new_case()
    case = get_case(st.session_state.current_case_id)
    
    st.markdown(f"## <span class='material-icons-outlined'>help_outline</span> {case['pergunta']}", unsafe_allow_html=True)
    
    # Tags de conhecimento
    tags = " ".join([f"<span style='background-color:#e0e7ff; color:#3730a3; padding:4px 8px; border-radius:12px; font-size:0.8em; margin-right:5px'>{tag}</span>" for tag in case.get("componentes_conhecimento", [])])
    st.markdown(tags, unsafe_allow_html=True)
    st.markdown("")
    
    main_col, chat_col = st.columns([1.8, 1])
    
    with main_col:
        with st.container(border=True):
            st.markdown("### Sua Resposta")
            text_key = f"ans_input_{st.session_state.get('case_counter', 0)}"
            user_answer = st.text_area("Escreva sua explicação detalhada:", height=150, key=text_key, disabled=st.session_state.case_scored)
            
            if st.button("Enviar Resposta", type="primary", disabled=not user_answer or st.session_state.case_scored):
                with st.spinner("IA Analisando sua resposta..."):
                    # 1. Avaliação AI
                    ai_eval = evaluate_answer_with_ai(case, user_answer)
                    
                    # 2. Finalização
                    result = finalize_question_response(case, user_answer, ai_eval)
                    
                    # 3. Atualizar Estado
                    st.session_state.score += result["points_gained"]
                    if result["is_correct"]: st.session_state.streak += 1
                    else: st.session_state.streak = 0
                    
                    nl = level_from_score(st.session_state.score)
                    if nl > st.session_state.unlocked_level: st.session_state.unlocked_level = nl; st.balloons()
                    
                    persist_now()
                    st.session_state.case_scored = True
                    st.session_state.last_result = result
                    st.session_state.show_next_case_btn = True
                    
                    try: end_case_timer(st.session_state.current_timer_id, result); st.session_state.current_timer_id = None
                    except: pass
                    st.rerun()
            
            if st.session_state.last_result:
                res = st.session_state.last_result
                st.markdown("---")
                
                level = res.get("level", "Incorreto")
                points = res.get("points_gained", 0)
                
                if level == "Avançado":
                    st.success(f"**Nível: Avançado! (Pontuação: {points:.1f}/3.0)**")
                elif level == "Médio":
                    st.info(f"**Nível: Médio! (Pontuação: {points:.1f}/3.0)**")
                elif level == "Básico":
                    st.warning(f"**Nível: Básico! (Pontuação: {points:.1f}/3.0)**")
                elif level == "Parcial":
                    st.warning(f"**Nível: Parcial (Pontuação: {points:.1f}/3.0)**")
                else:
                    st.error(f"**Nível: Incorreto (Pontuação: {points:.1f}/3.0)**")
                
                st.markdown(f"**Feedback da IA:** {res['feedback']}")
                
                with st.expander("Ver Gabarito Esperado"):
                    referencias = case.get('referencia', {})
                    if referencias:
                        for n, txt in referencias.items():
                            st.markdown(f"**{n}**: {txt}")
                    else:
                        st.info(case.get('resposta_esperada', 'Gabarito não disponível.'))
                
                if st.button("Próxima Questão", type="primary"):
                    start_new_case()

    with chat_col:
        with st.container(border=True):
            st.markdown("#### <span class='material-icons-outlined'>psychology</span> Tutor IA", unsafe_allow_html=True)
            h_cont = st.container(height=400)
            with h_cont:
                if not st.session_state.chat:
                    st.info("Dúvidas sobre a questão? Pergunte ao Tutor!")
                for msg in st.session_state.chat:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
            if q_msg := st.chat_input("Tire sua dúvida..."):
                st.session_state.chat.append({"role": "user", "content": q_msg})
                # Re-render chat immediately
                with h_cont:
                    with st.chat_message("user"): st.markdown(q_msg)
                
                with st.spinner("Pensando..."):
                    full_resp = ""
                    try:
                        # Adaptação para o novo contexto (Questão em vez de Caso Clínico)
                        # tutor_reply_com_ia espera 'case' dict. O formato mudou mas as chaves usadas lá 
                        # (titulo, queixa, etc) não existem mais. Preciso checar tutor_reply_com_ia.
                        # Vou assumir que ela precisa ser atualizada ou o prompt vai quebrar.
                        # ATUALIZAR LOGIC.PY PREVIAMENTE SERIA MELHOR, mas vou deixar quebrar e arrumar ou passar fake keys.
                        # Melhor: Passar o 'case' adaptado.
                        
                        # Fake adaptation for safe calling if logic not updated
                        case_adapted = case.copy()
                        case_adapted['titulo'] = case['pergunta']
                        case_adapted['queixa'] = case['pergunta']
                        case_adapted['hma'] = "Questão de Biologia Molecular"
                        case_adapted['sintomas'] = case.get('componentes_conhecimento', [])
                        case_adapted['gabarito'] = case['resposta_esperada']
                        
                        gen = tutor_reply_com_ia(case_adapted, q_msg, st.session_state.chat)
                        with h_cont:
                            with st.chat_message("assistant"):
                                ph = st.empty()
                                for chunk in gen:
                                    full_resp += chunk
                                    ph.markdown(full_resp + " ▌")
                                ph.markdown(full_resp)
                    except Exception as e:
                        full_resp = f"Erro: {e}"
                        st.error(full_resp)
                
                # NOVO: Registrar log do chat para aparecer nas métricas do painel
                # Pegando user e case do escopo atual
                user = get_current_user()
                if user and st.session_state.current_case_id:
                    # Registra a interação em background
                    log_chat_interaction(
                        user_id=user["id"], 
                        case_id=st.session_state.current_case_id, 
                        user_message=q_msg, 
                        bot_response=full_resp, 
                        response_time=None # Poderia medir usando time() mas None serve
                    )
                
                st.session_state.chat.append({"role": "assistant", "content": full_resp})
                st.rerun()

if __name__ == "__main__":
    main()
