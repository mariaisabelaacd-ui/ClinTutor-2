import streamlit as st
import extra_streamlit_components as stx
from logic import (
    APP_NAME, QUESTIONS, TOPICS,
    pick_adaptive_case, pick_new_case, get_case,
    evaluate_mcq_answer, finalize_question_response,
    level_from_score, progress_to_next_level,
    save_progress, load_progress, tutor_reply_com_ia
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
    save_student_progress, load_student_progress, flush_chat_buffer
)
from admin_dashboard import show_admin_dashboard
from professor_dashboard import show_advanced_professor_dashboard

TOPIC_KEYS = list(TOPICS.keys()) # ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8']

# --- GERENCIADOR DE COOKIES (SINGLETON) ---
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- CONFIGURAÇÃO DE ESTILO ---
def apply_custom_style():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone" rel="stylesheet">', unsafe_allow_html=True)

def show_login_page():
    """Exibe página de login e cadastro com visual modernizado"""
    apply_custom_style()
    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("<div style='text-align: center; margin-bottom: 2rem;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='color: #11B965; font-size: 3.5em; margin:0;'>Helix.AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.2em; opacity: 0.7;'>Plataforma adaptativa de tutoria em Fisiologia & Membranas</p>", unsafe_allow_html=True)
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
                    consent_given = True
                    
                    if email and '@' in email:
                        domain = email.split('@')[1].lower()
                        if 'professor' in email or domain == 'fcmsantacasasp.edu.br': 
                            user_type = 'professor'
                            prof_code_register = st.text_input("Código de Professor", type="password", placeholder="Código obrigatório para professores")
                        else: 
                            user_type = 'aluno'
                            ra = st.text_input("RA")
                            turma = st.selectbox("Turma", ["Biomedicina A", "Biomedicina B"])
                            
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
            
            # --- ATALHOS TEMPORÁRIOS DE LOGIN PARA TESTE ---
            st.markdown("<hr style='margin 1.5rem 0; opacity: 0.2;'>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 0.85rem; color: #64748b; margin-top: -0.5rem;'><b>Acesso de Desenvolvimento</b></p>", unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🔓 Entrar Professor", use_container_width=True):
                    st.session_state.show_bypass_role = "professor"
                    st.rerun()
            
            with col_b2:
                if st.button("🔑 Entrar Aluno", use_container_width=True):
                    st.session_state.show_bypass_role = "aluno"
                    st.rerun()
            
            active_role = st.session_state.get("show_bypass_role")
            if active_role:
                st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                bypass_code = st.text_input(f"Código de Acesso para {active_role.title()}:", type="password", placeholder="Digite o código...")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("Confirmar Código", type="primary", use_container_width=True):
                        if bypass_code == "admin_":
                            all_users = get_all_users()
                            if active_role == "professor":
                                profs = [u for u in all_users if u.get('user_type') == 'professor']
                                if profs:
                                    login_user(profs[0])
                                else:
                                    login_user({
                                        'id': 'dummy_prof_id',
                                        'name': 'Professor Teste',
                                        'email': 'professor@fcmsantacasasp.edu.br',
                                        'user_type': 'professor'
                                    })
                            else:
                                students = [u for u in all_users if u.get('user_type') == 'aluno']
                                if students:
                                    login_user(students[0])
                                else:
                                    login_user({
                                        'id': 'dummy_student_id',
                                        'name': 'Aluno Teste',
                                        'email': 'aluno@aluno.fcmsantacasasp.edu.br',
                                        'user_type': 'aluno',
                                        'ra': '123456',
                                        'turma': 'Biomedicina A'
                                    })
                            st.session_state.show_bypass_role = None
                            st.rerun()
                        else:
                            st.error("Código incorreto!")
                with col_c2:
                    if st.button("Cancelar Acesso", use_container_width=True):
                        st.session_state.show_bypass_role = None
                        st.rerun()
    st.markdown("<div style='text-align: center; margin-top: 3rem; color: #999; font-size: 0.8em;'>Helix.AI v2.0</div>", unsafe_allow_html=True)

def render_top_navbar():
    user = get_current_user()
    if not user:
        return
    
    col_logo, col_menu, col_stats, col_logout = st.columns([1.5, 2.5, 4, 1])
    
    with col_logo:
        st.markdown("<div class='nav-logo-text'>🧬 Helix.AI</div>", unsafe_allow_html=True)
        
    with col_menu:
        if user["user_type"] == "professor":
            c1, c2 = st.columns(2)
            with c1:
                is_active = st.session_state.get("professor_page", "Questões") == "Questões"
                if st.button("Questões", key="nav_prof_q", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state.professor_page = "Questões"
                    st.rerun()
            with c2:
                is_active = st.session_state.get("professor_page", "Questões") == "Dashboard"
                if st.button("Dashboard", key="nav_prof_dash", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state.professor_page = "Dashboard"
                    st.rerun()
        elif user["user_type"] == "aluno":
            st.markdown("<div style='height:100%; display:flex; align-items:center; font-weight:600; color:#10b981; margin-top:5px;'>🎓 8 Questões de Transporte</div>", unsafe_allow_html=True)
        elif user["user_type"] == "admin":
            st.markdown("<div style='height:100%; display:flex; align-items:center; font-weight:600; color:#10b981; margin-top:5px;'>⚙️ Painel Admin</div>", unsafe_allow_html=True)
            
    with col_stats:
        if user["user_type"] == "aluno":
            diff = st.session_state.get("current_difficulty", "Fácil")
            diff_badge = {
                "Fácil": "<span style='background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; color: #10b981;'>🟢 Fácil</span>",
                "Média": "<span style='background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; color: #f59e0b;'>🟡 Média</span>",
                "Difícil": "<span style='background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; color: #ef4444;'>🔴 Difícil</span>"
            }.get(diff, "")
            
            comp_cnt = len(st.session_state.get("completed_topics", []))
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; align-items: center; gap: 0.8rem; height: 100%;'>
                <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; color: #10b981;'>
                    📊 <b>{comp_cnt}/8</b> Concluídas
                </div>
                {diff_badge}
                <div style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; color: #ef4444;'>
                    🔥 Streak <b>{st.session_state.streak}</b>
                </div>
                <div class='nav-user-info'>
                    Olá, <b>{user['name'].split()[0]}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; align-items: center; height: 100%;'>
                <div class='nav-user-info'>
                    Olá, <b>{user['name'].split()[0]}</b> <span class='role-badge'>{user['user_type']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_logout:
        if st.button("Sair", key="nav_logout_btn", use_container_width=True):
            logout_user()
            cookie_manager.delete('auth_token')
            st.rerun()
            
    st.markdown("<hr class='nav-divider'>", unsafe_allow_html=True)


def init_state():
    if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
    user = get_current_user()
    saved = load_progress()
    user_progress = {}
    if isinstance(saved, list):
        for p in saved:
            if p.get("user_id") == user["id"]: user_progress = p; break

    firebase_progress = {}
    if 'progress_loaded' not in st.session_state:
        firebase_progress = load_student_progress(user["id"])
        st.session_state.progress_loaded = True

    valid_q_ids = {q["id"] for q in QUESTIONS}

    defaults = {
        "score": 0.0, "streak": 0, "unlocked_level": 1,
        "current_difficulty": "Fácil", "topic_filter": "T1",
        "current_topic_idx": 0, "completed_topics": [],
        "current_case_id": None, "case_scored": False, "last_result": None,
        "chat": [], "show_next_case_btn": False, "used_cases": [],
        "current_timer_id": None, "case_counter": 0, "current_evaluation": None,
        "submitted_answer": False, "selected_option": None, "insistence_count": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            if k == "current_case_id" and firebase_progress.get("current_question_id") in valid_q_ids:
                st.session_state[k] = firebase_progress["current_question_id"]
            elif k == "used_cases" and firebase_progress.get("used_cases"):
                st.session_state[k] = [uid for uid in firebase_progress["used_cases"] if uid in valid_q_ids]
            elif k == "score" and firebase_progress.get("score") is not None:
                st.session_state[k] = float(firebase_progress["score"])
            elif k == "streak" and firebase_progress.get("streak") is not None:
                st.session_state[k] = int(firebase_progress["streak"])
            else:
                val = user_progress.get(k, v) if k in ["score", "streak", "unlocked_level", "used_cases"] else v
                if k == "used_cases":
                    val = [uid for uid in val if uid in valid_q_ids]
                st.session_state[k] = val

def persist_now():
    user = get_current_user()
    if not user:
        return
    save_progress({
        "user_id": user["id"],
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "unlocked_level": st.session_state.unlocked_level,
        "used_cases": st.session_state.used_cases,
        "current_difficulty": st.session_state.current_difficulty,
        "completed_topics": st.session_state.get("completed_topics", []),
        "when": datetime.now().isoformat()
    })
    save_student_progress(
        user_id=user["id"],
        current_question_id=st.session_state.get("current_case_id", "") or "",
        used_cases=st.session_state.used_cases,
        score=st.session_state.score,
        streak=st.session_state.streak
    )

def start_new_case(forced_topic=None, forced_diff=None):
    if forced_topic:
        st.session_state.topic_filter = forced_topic
        if forced_topic in TOPIC_KEYS:
            st.session_state.current_topic_idx = TOPIC_KEYS.index(forced_topic)
            
    if forced_diff:
        st.session_state.current_difficulty = forced_diff
        
    diff = st.session_state.get("current_difficulty", "Fácil")
    topic = st.session_state.get("topic_filter", "T1")
    
    new_case = pick_adaptive_case(current_difficulty=diff, used_cases=st.session_state.used_cases, topic_filter=topic)
    st.session_state.current_case_id = new_case["id"]
    if new_case["id"] not in st.session_state.used_cases:
        st.session_state.used_cases.append(new_case["id"])
    
    user = get_current_user()
    try:
        st.session_state.current_timer_id = start_case_timer(user["id"], new_case["id"])
    except:
        pass
    
    cur_topic_key = new_case.get("topico_id", "T1")
    cur_topic_num = TOPIC_KEYS.index(cur_topic_key) + 1 if cur_topic_key in TOPIC_KEYS else 1
    
    # Se já há mensagens no chat, adiciona marcador de transição sem apagar o histórico anterior
    if st.session_state.get("chat"):
        st.session_state.chat.append({
            "role": "assistant",
            "content": f"📍 **Agora estamos na Questão {cur_topic_num} de 8:** *{new_case.get('topico_nome', '')}* ({new_case.get('codigo', '')}). Se tiver dúvidas conceituais, pode me perguntar!"
        })
    else:
        st.session_state.chat = [{
            "role": "assistant",
            "content": f"Olá! Sou seu tutor **Helix.AI**. Estou aqui para tirar dúvidas e ajudar você a entender os conceitos da **Questão {cur_topic_num} de 8** (*{new_case.get('topico_nome', '')}*). Pode me perguntar qualquer dúvida!"
        }]
        
    st.session_state.active_chat_case_id = new_case["id"]
    st.session_state.show_next_case_btn = False
    st.session_state.current_evaluation = None
    st.session_state.submitted_answer = False
    st.session_state.selected_option = None
    st.session_state.insistence_count = 0
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
    user = get_current_user()
    
    render_top_navbar()
    
    if user["user_type"] == "admin": 
        show_admin_dashboard()
        return
        
    if user["user_type"] == "professor":
         active_page = st.session_state.get("professor_page", "Questões")
         if active_page == "Dashboard": 
             show_advanced_professor_dashboard()
             return
    
    # --- MAIN CONTENT ---
    if st.session_state.current_case_id is None:
        start_new_case()
        
    case = get_case(st.session_state.current_case_id)
    cur_topic_key = case.get("topico_id", "T1")
    cur_topic_num = TOPIC_KEYS.index(cur_topic_key) + 1 if cur_topic_key in TOPIC_KEYS else 1
    
    # --- 2-COLUMN SPLIT VIEW LAYOUT ---
    col_question, col_chat = st.columns([1.15, 0.85], gap="large")
    
    # =========================================================================
    # COLUNA ESQUERDA: QUESTÃO DE MÚLTIPLA ESCOLHA & FEEDBACK
    # =========================================================================
    with col_question:
        # Seletor das 8 Questões & Barra de Progresso
        h_col1, h_col2, h_col3 = st.columns([2.6, 1.2, 1.2])
        with h_col1:
            topic_options = [f"Questão {i+1}: {k} — {v}" for i, (k, v) in enumerate(TOPICS.items())]
            current_topic_idx = cur_topic_num - 1
            sel_topic_str = st.selectbox(
                "🎯 Navegar pelas 8 Questões:",
                topic_options,
                index=current_topic_idx,
                key="topic_selector_8"
            )
            selected_topic_key = sel_topic_str.split(":")[1].split("—")[0].strip()
            if selected_topic_key != st.session_state.get("topic_filter"):
                start_new_case(forced_topic=selected_topic_key)
                
        with h_col2:
            comp_cnt = len(st.session_state.get("completed_topics", []))
            st.markdown(f"<div style='margin-top: 1.8rem; font-size: 0.85rem; color: #64748b;'><b>Progresso:</b> {comp_cnt}/8 Questões</div>", unsafe_allow_html=True)
            
        with h_col3:
            st.markdown("<div style='margin-top: 1.6rem;'></div>", unsafe_allow_html=True)
            if st.button("⏭️ Outra do Tópico", key="btn_skip_q", use_container_width=True):
                start_new_case(forced_topic=cur_topic_key)

        st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)
        
        # Card da Questão Atual
        diff_name = case.get("dificuldade", "Fácil")
        diff_color = "#10b981" if diff_name == "Fácil" else ("#f59e0b" if diff_name == "Média" else "#ef4444")
        diff_icon = "🟢" if diff_name == "Fácil" else ("🟡" if diff_name == "Média" else "🔴")
        
        with st.container(border=True):
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                <div style='font-size: 0.95rem; font-weight: 700; color: #10b981; letter-spacing: 0.5px;'>
                    Questão {cur_topic_num} de 8 • {case.get('topico_nome', '')}
                </div>
                <div style='background: rgba(128,128,128,0.1); border: 1px solid rgba(128,128,128,0.2); padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; color: {diff_color};'>
                    {diff_icon} {diff_name} ({case.get('codigo', '')})
                </div>
            </div>
            <div style='font-size: 1.15rem; font-weight: 600; line-height: 1.5; margin-bottom: 1.2rem; color: var(--text-color);'>
                {case.get('pergunta', '')}
            </div>
            """, unsafe_allow_html=True)
            
            opts = ["A", "B", "C", "D"]
            alts = case.get("alternativas", {})
            labels = {k: f"{k}. {alts.get(k, '')}" for k in opts if k in alts}
            
            # Se a resposta ainda NÃO foi confirmada
            if not st.session_state.submitted_answer:
                chosen = st.radio(
                    "Selecione sua resposta:",
                    options=list(labels.keys()),
                    format_func=lambda k: labels[k],
                    key=f"mcq_radio_{case['id']}",
                    index=None if not st.session_state.selected_option else list(labels.keys()).index(st.session_state.selected_option)
                )
                
                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                if st.button("Confirmar Resposta 🎯", type="primary", use_container_width=True):
                    if not chosen:
                        st.warning("⚠️ Por favor, selecione uma alternativa antes de confirmar.")
                    else:
                        st.session_state.selected_option = chosen
                        eval_res = evaluate_mcq_answer(case, chosen)
                        st.session_state.submitted_answer = True
                        st.session_state.current_evaluation = eval_res
                        
                        # Progressão Adaptativa & Conclusão do Tópico
                        if eval_res["is_correct"]:
                            st.session_state.score += eval_res["points_gained"]
                            st.session_state.streak += 1
                            if cur_topic_key not in st.session_state.completed_topics:
                                st.session_state.completed_topics.append(cur_topic_key)
                                
                            if st.session_state.current_difficulty == "Fácil":
                                st.session_state.current_difficulty = "Média"
                            elif st.session_state.current_difficulty == "Média":
                                st.session_state.current_difficulty = "Difícil"
                        else:
                            st.session_state.streak = 0
                            if st.session_state.current_difficulty == "Difícil":
                                st.session_state.current_difficulty = "Média"
                            elif st.session_state.current_difficulty == "Média":
                                st.session_state.current_difficulty = "Fácil"
                                
                        persist_now()
                        
                        # Analytics & Timer
                        user = get_current_user()
                        try:
                            result_log = finalize_question_response(case, eval_res["user_answer"], eval_res)
                            end_case_timer(st.session_state.current_timer_id, result_log)
                        except Exception as e:
                            print(f"Erro ao encerrar timer: {e}")
                            
                        st.rerun()
            else:
                # Resposta confirmada - Exibe feedback detalhado
                eval_res = st.session_state.current_evaluation
                is_corr = eval_res.get("is_correct", False)
                selected_opt = eval_res.get("selected_option", "")
                gab_opt = eval_res.get("correct_option", "")
                
                # Lista com destaque visual nas alternativas
                for k in ["A", "B", "C", "D"]:
                    if k in alts:
                        text = alts[k]
                        if k == gab_opt:
                            st.markdown(f"""
                            <div style='background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;'>
                                <b>✅ {k}.</b> {text} <span style='color: #10b981; font-weight: 700; font-size: 0.85rem;'>(Gabarito Correto)</span>
                            </div>
                            """, unsafe_allow_html=True)
                        elif k == selected_opt and not is_corr:
                            st.markdown(f"""
                            <div style='background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;'>
                                <b>❌ {k}.</b> {text} <span style='color: #ef4444; font-weight: 700; font-size: 0.85rem;'>(Sua Escolha)</span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(128, 128, 128, 0.15); opacity: 0.6; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px;'>
                                <b>{k}.</b> {text}
                            </div>
                            """, unsafe_allow_html=True)
                            
                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                
                if is_corr:
                    st.success(f"🎉 **Parabéns, você acertou a Questão {cur_topic_num}! (+{eval_res['points_gained']:.1f} pts)**\n\n💡 **Justificativa:** {eval_res.get('correct_explanation', '')}")
                    
                    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
                    if cur_topic_num < 8:
                        next_tk = TOPIC_KEYS[cur_topic_num]
                        if st.button(f"Avançar para Questão {cur_topic_num + 1} de 8 ➡️", type="primary", use_container_width=True):
                            start_new_case(forced_topic=next_tk)
                    else:
                        st.balloons()
                        st.markdown("<div style='background: rgba(16, 185, 129, 0.2); padding: 1rem; border-radius: 10px; text-align: center; font-weight: 700; color: #10b981;'>🏆 Parabéns! Você concluiu todas as 8 questões de Transporte e Membranas!</div>", unsafe_allow_html=True)
                        if st.button("🔄 Praticar Novamente em Nível Avançado", use_container_width=True):
                            st.session_state.completed_topics = []
                            start_new_case(forced_topic="T1", forced_diff="Média")
                else:
                    st.error(f"❌ **Você marcou a alternativa {selected_opt}.**\n\n🔍 **Análise Conceitual do Distrator:**\n{eval_res.get('distractor_feedback', '')}")
                    
                    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
                    if st.button("Tentar Outra Questão deste Tópico 🔄", type="primary", use_container_width=True):
                        start_new_case(forced_topic=cur_topic_key)

    # =========================================================================
    # COLUNA DIREITA: TUTOR SOCRÁTICO HELIX.AI (COM PROTEÇÃO 4 INSISTÊNCIAS)
    # =========================================================================
    with col_chat:
        st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;'>
            <div>
                <h3 style='margin: 0; font-size: 1.25rem; display: flex; align-items: center; gap: 0.4rem;'>
                    💬 Tutor Helix.AI
                </h3>
                <p style='margin: 0; font-size: 0.85rem; color: #64748b;'>
                    Tire dúvidas e entenda os conceitos passo a passo.
                </p>
            </div>
            <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 10px; font-size: 0.75rem; color: #10b981; font-weight: 600;'>
                ⚡ Online
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        chat_container = st.container(height=500)
        with chat_container:
            if not st.session_state.get("chat"):
                intro_text = f"""Olá! Sou seu tutor **Helix.AI**. Estou aqui para tirar dúvidas e ajudar você a entender os conceitos da **Questão {cur_topic_num} de 8** (*{case.get('topico_nome', '')}*).

Tem dúvida sobre algum conceito, termo ou mecanismo? Pode me perguntar!"""
                st.session_state.chat = [{"role": "assistant", "content": intro_text}]
                
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
        # Entrada do chat
        if q_msg := st.chat_input("Dúvida sobre a questão? Peça uma explicação ao tutor..."):
            insist_terms = ["resposta", "gabarito", "qual e", "qual é", "qual a", "letra", "diga a resposta", "me da a resposta", "me dá a resposta", "é a a", "é a b", "é a c", "é a d", "fala a resposta"]
            if any(term in q_msg.lower() for term in insist_terms):
                st.session_state.insistence_count = st.session_state.get("insistence_count", 0) + 1
                
            st.session_state.chat.append({"role": "user", "content": q_msg})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(q_msg)
                    
            with st.spinner("Helix.AI está digitando..."):
                full_resp = ""
                try:
                    gen = tutor_reply_com_ia(
                        question=case,
                        user_msg=q_msg,
                        chat_history=st.session_state.chat,
                        insistence_count=st.session_state.insistence_count
                    )
                    with chat_container:
                        with st.chat_message("assistant"):
                            ph = st.empty()
                            for chunk in gen:
                                full_resp += chunk
                                ph.markdown(full_resp + " ▌")
                            ph.markdown(full_resp)
                except Exception as e:
                    full_resp = f"Erro na resposta do tutor: {e}"
                    st.error(full_resp)
                    
            st.session_state.chat.append({"role": "assistant", "content": full_resp})
            
            user = get_current_user()
            if user and st.session_state.current_case_id:
                log_chat_interaction(
                    user_id=user["id"],
                    case_id=st.session_state.current_case_id,
                    user_message=q_msg,
                    bot_response=full_resp,
                    response_time=None
                )
                
            st.rerun()

if __name__ == "__main__":
    main()
