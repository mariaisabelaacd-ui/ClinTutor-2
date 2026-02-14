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
    get_user_detailed_stats, calculate_accuracy_rate
)
from admin_dashboard import show_admin_dashboard
from professor_dashboard import show_advanced_professor_dashboard

# --- DEBUG MARKER ---
# st.toast("Versão V3 Carregada Corretamente!", icon="✅")

# --- GERENCIADOR DE COOKIES (SINGLETON) ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = None # Will be initialized in main()

# --- CONFIGURAÇÃO DE ESTILO ---
def apply_custom_style():
    # Tenta carregar estilo, se falhar usa básico
    try:
        with open( "assets/style.css" ) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone" rel="stylesheet">', unsafe_allow_html=True)

def show_login_page():
    """Exibe página de login e cadastro com visual modernizado"""
    apply_custom_style()
    global cookie_manager
    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("<div style='text-align: center; margin-bottom: 2rem;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='color: #11B965; font-size: 3.5em; margin:0;'>BioTutor v3</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 1.2em;'>Tutor de Biologia Molecular (Nova Versão)</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        with st.container(border=True):
            tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
            with tab1:
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="seu@email.com")
                    password = st.text_input("Senha", type="password", placeholder="••••••")
                    remember_me = st.checkbox("Manter conectado por 7 dias")
                    st.markdown("")
                    if st.form_submit_button("Acessar Sistema", type="primary", use_container_width=True):
                        if email and password:
                            with st.spinner("Autenticando..."):
                                success, message, user_data = authenticate_user(email, password)
                                if success:
                                    login_user(user_data)
                                    if remember_me:
                                        token = create_auth_token(user_data['id'])
                                        cookie_manager.set('auth_token', token, expires_at=datetime.now() + timedelta(days=7), key='set_auth')
                                        time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(message, icon="🚫")
                        else:
                            st.warning("Preencha todos os campos.", icon="⚠️")
            with tab2:
                st.info("Use seu email institucional para criar conta.")
                with st.form("register_form"):
                    name = st.text_input("Nome Completo")
                    email = st.text_input("Email Institucional")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1: password = st.text_input("Senha", type="password")
                    with col_p2: confirm_password = st.text_input("Confirmar", type="password")
                    
                    user_type = None
                    ra = None
                    if email and '@' in email:
                        domain = email.split('@')[1].lower()
                        if 'professor' in email or domain == 'fcmsantacasasp.edu.br': user_type = 'professor' # Simplificação
                        else: user_type = 'aluno'; ra = st.text_input("RA")

                    if st.form_submit_button("Criar Minha Conta", type="primary", use_container_width=True):
                        if password != confirm_password: st.error("Senhas não conferem.")
                        elif len(password) < 6: st.error("Senha curta.")
                        else:
                            success, msg = register_user(name, email, password, user_type or 'aluno', ra)
                            if success: st.success("Conta criada! Acesse a aba 'Entrar'.")
                            else: st.error(msg)
    st.markdown("<div style='text-align: center; margin-top: 3rem; color: #999; font-size: 0.8em;'>BioTutor v3.0</div>", unsafe_allow_html=True)

def show_user_profile():
    user = get_current_user()
    global cookie_manager
    with st.sidebar:
        st.markdown(f"### <span class='material-icons-outlined'>account_circle</span> {user['name'].split()[0]}", unsafe_allow_html=True)
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
    
    defaults = {
        "score": 0, "streak": 0, "unlocked_level": 1,
        "current_case_id": None, "case_scored": False, "last_result": None,
        "chat": [], "show_next_case_btn": False, "used_cases": [],
        "current_timer_id": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = user_progress.get(k, v) if k in ["score", "streak", "unlocked_level"] else v

def persist_now():
    user = get_current_user()
    save_progress({
        "user_id": user["id"],
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "unlocked_level": st.session_state.unlocked_level,
        "when": datetime.now().isoformat()
    })

def start_new_case():
    new_case = pick_new_case(st.session_state.unlocked_level, st.session_state.used_cases)
    st.session_state.current_case_id = new_case["id"]
    if new_case["id"] not in st.session_state.used_cases: st.session_state.used_cases.append(new_case["id"])
    
    # Timer
    user = get_current_user()
    try: st.session_state.current_timer_id = start_case_timer(user["id"], new_case["id"])
    except: pass
    
    st.session_state.case_scored = False
    st.session_state.last_result = None
    st.session_state.chat = []
    st.session_state.show_next_case_btn = False
    st.rerun()

def main():
    st.set_page_config(page_title="BioTutor v3", page_icon="🧬", layout="wide")
    global cookie_manager
    cookie_manager = get_cookie_manager()
    # st.toast("Versão V3 Carregada!", icon="✅")
    apply_custom_style()
    init_session()
    create_default_admin()
    
    if not is_logged_in():
        time.sleep(0.5)
        token = cookie_manager.get('auth_token')
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
         nav = st.sidebar.radio("Navegação", ["Questões", "Dashboard", "Analytics"], label_visibility="collapsed")
         if nav == "Dashboard": show_advanced_professor_dashboard(); return 
         if nav == "Analytics": show_advanced_professor_dashboard(); return
    
    # --- SIDEBAR ---
    st.sidebar.markdown("### <span class='material-icons-outlined'>emoji_events</span> Progresso", unsafe_allow_html=True)
    c1, c2 = st.sidebar.columns(2)
    c1.metric("Pontos", st.session_state.score)
    c2.metric("Streak", f"{st.session_state.streak} 🔥")
    st.sidebar.progress(progress_to_next_level(st.session_state.score))
    
    if st.sidebar.button("Pular Questão", use_container_width=True): start_new_case()

    # --- MAIN CONTENT ---
    if st.session_state.current_case_id is None: start_new_case()
    case = get_case(st.session_state.current_case_id)
    
    # OLD CODE MARKER CHECK
    if 'queixa' in case:
        st.error("ERRO: Carregando dados antigos! Verifique logic.py")
        st.write(case)
        return

    st.markdown(f"## <span class='material-icons-outlined'>help_outline</span> {case['pergunta']}", unsafe_allow_html=True)
    
    # Tags de conhecimento
    tags = " ".join([f"<span style='background-color:#e0e7ff; color:#3730a3; padding:4px 8px; border-radius:12px; font-size:0.8em; margin-right:5px'>{tag}</span>" for tag in case.get("componentes_conhecimento", [])])
    st.markdown(tags, unsafe_allow_html=True)
    st.markdown("")
    
    main_col, chat_col = st.columns([1.8, 1])
    
    with main_col:
        with st.container(border=True):
            st.markdown("### Sua Resposta")
            user_answer = st.text_area("Escreva sua explicação detalhada:", height=150, key="ans_input", disabled=st.session_state.case_scored)
            
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
                outcome = res.get("outcome", "").lower()
                if outcome == "partial":
                    st.warning(f"**⚠️ Parcialmente Correta. +{res['points_gained']} pontos**")
                elif res["is_correct"] and outcome != "partial":
                    st.success(f"**✅ Correto! +{res['points_gained']} pontos**")
                else:
                    st.error(f"**❌ Incorreto. +{res['points_gained']} pontos**")
                
                st.markdown(f"**Feedback da IA:** {res['feedback']}")
                
                with st.expander("Ver Gabarito Esperado"):
                    st.info(case['resposta_esperada'])
                
                if st.button("Próxima Questão ➡️", type="primary"):
                    start_new_case()

    with chat_col:
        with st.container(border=True):
            st.markdown("#### <span class='material-icons-outlined'>psychology</span> Tutor IA", unsafe_allow_html=True)
            h_cont = st.container(height=400)
            with h_cont:
                if not st.session_state.chat:
                    st.info("Dúvidas sobre a questão? Pergunte ao Tutor!", icon="👋")
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
                        # Fake adaptation for safe calling
                        case_adapted = case.copy()
                        # Campos fake para garantir que não quebre se logic.py estiver antigo
                        case_adapted['titulo'] = case['pergunta']
                        case_adapted['queixa'] = case['pergunta']
                        case_adapted['hma'] = "Questão de Biologia Molecular"
                        case_adapted['sintomas'] = case.get('componentes_conhecimento', [])
                        case_adapted['gabarito'] = case.get('resposta_esperada', "")
                        
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
                
                st.session_state.chat.append({"role": "assistant", "content": full_resp})
                st.rerun()

if __name__ == "__main__":
    main()
