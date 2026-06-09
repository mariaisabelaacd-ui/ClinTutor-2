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
    save_student_progress, load_student_progress, flush_chat_buffer
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
            st.markdown("<div style='height:100%; display:flex; align-items:center; font-weight:600; color:#10b981; margin-top:5px;'>🎓 Questões</div>", unsafe_allow_html=True)
        elif user["user_type"] == "admin":
            st.markdown("<div style='height:100%; display:flex; align-items:center; font-weight:600; color:#10b981; margin-top:5px;'>⚙️ Painel Admin</div>", unsafe_allow_html=True)
            
    with col_stats:
        if user["user_type"] == "aluno":
            overall_pct = int((st.session_state.score / (3.0 * len(QUESTIONS))) * 100) if len(QUESTIONS) > 0 else 0
            overall_pct = min(max(overall_pct, 0), 100)
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; align-items: center; gap: 1rem; height: 100%;'>
                <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; color: #10b981;'>
                    🏆 <b>{overall_pct}%</b> Concluído
                </div>
                <div style='background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 0.9rem; color: #ef4444;'>
                    🔥 Streak <b>{st.session_state.streak}</b>
                </div>
                <div class='nav-user-info'>
                    Olá, <b>{user['name'].split()[0]}</b> <span class='role-badge'>{user['user_type']}</span>
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
        "current_timer_id": None, "case_counter": 0, "current_evaluation": None
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
    st.session_state.current_evaluation = None
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
    if st.session_state.current_case_id is None: start_new_case()
    case = get_case(st.session_state.current_case_id)
    
    # Centraliza o conteúdo com colunas (deixa o chat com largura de leitura de 800px mais elegante)
    col_space1, col_center, col_space2 = st.columns([1, 4, 1])
    
    with col_center:
        # --- STUDENT PROGRESS HEADER ---
        total_q = len(QUESTIONS)
        answered_q = min(len(st.session_state.used_cases), total_q)
        
        prog_col1, prog_col2, prog_col3 = st.columns([3, 1, 1])
        with prog_col1:
            st.markdown(f"**Progresso das Questões:** {answered_q} de {total_q}")
            st.progress(answered_q / total_q if total_q > 0 else 0)
        with prog_col2:
            pass
        with prog_col3:
            if st.button("Pular Questão", key="main_skip_question", use_container_width=True):
                start_new_case()
                st.rerun()
                
        st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 1.5rem; border: 0; border-top: 1px solid rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
        
        # --- CURRENT QUESTION & PROGRESS ---
        eval_data = st.session_state.get("current_evaluation")
        current_pct = 0
        if eval_data:
            level = eval_data.get("level", "Incorreto")
            level_pct_map = {
                "Incorreto": 0,
                "Parcial": 30,
                "Básico": 60,
                "Médio": 80,
                "Intermediário": 80,
                "Avançado": 100
            }
            current_pct = level_pct_map.get(level, 0)
            
        st.markdown(f"#### 📝 Questão Atual: {case['pergunta']}")
        
        st.markdown(f"**Completude da sua Resposta: {current_pct}%**")
        st.progress(current_pct / 100.0)
                    
        st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 1.5rem; border: 0; border-top: 1px solid rgba(128,128,128,0.15);'>", unsafe_allow_html=True)
    
        # --- UNIFIED CHAT INTERFACE ---
        st.markdown("### 💬 Conversa com o Tutor")
        
        chat_container = st.container(height=480)
        with chat_container:
            if not st.session_state.chat:
                intro_text = f"""Olá! Sou seu tutor Helix.AI. Hoje vamos resolver a seguinte questão:

**{case['pergunta']}**

Como você explicaria ou por onde gostaria de começar a responder a essa pergunta?"""
                st.session_state.chat.append({"role": "assistant", "content": intro_text})
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Exibir a avaliação e os botões de ação DENTRO do chat apenas quando atingir 100% (Avançado)
            eval_data = st.session_state.get("current_evaluation")
            if eval_data:
                level = eval_data.get("level", "Incorreto")
                feedback = eval_data.get("feedback", "")
                classification = eval_data.get("classification", "INCORRETO")
                
                if level == "Avançado" and classification != "INCORRETO":
                    with st.chat_message("assistant", avatar="🎓"):
                        st.markdown(f"""
                        🎯 **Conclusão da Resposta: 100%**
                        Excelente explicação conceitual! Você abordou todos os pontos necessários.
                        
                        **Feedback do Tutor:** {feedback}
                        """, unsafe_allow_html=True)
                        st.progress(1.0)
                        
                        student_messages = [m["content"] for m in st.session_state.chat if m["role"] == "user"]
                        combined_ans = "\n".join(student_messages)
                        
                        if st.button("Concluir Questão e Avançar 🚀", key="chat_finish_q", type="primary", use_container_width=True):
                            result = finalize_question_response(case, combined_ans, eval_data)
                            st.session_state.score += result["points_gained"]
                            st.session_state.streak += 1
                            nl = level_from_score(st.session_state.score)
                            if nl > st.session_state.unlocked_level: 
                                st.session_state.unlocked_level = nl
                                st.balloons()
                            persist_now()
                            try:
                                flush_chat_buffer(user['id'], case['id'])
                            except Exception as e:
                                print(f"Erro ao salvar chat log: {e}")
                            try:
                                end_case_timer(st.session_state.current_timer_id, result)
                                st.session_state.current_timer_id = None
                            except:
                                pass
                            start_new_case()
                            st.rerun()
                                    
        # Input do Chat (renderizado dentro do col_center para ficar alinhado no meio!)
        if q_msg := st.chat_input("Responda à questão ou faça uma pergunta ao tutor..."):
            # 1. Adicionar mensagem do aluno
            st.session_state.chat.append({"role": "user", "content": q_msg})
            with chat_container:
                with st.chat_message("user"): 
                    st.markdown(q_msg)
                    
            # 2. Avaliar as respostas acumuladas primeiro, para alimentar o tutor inteligente com o nível real
            with st.spinner("Avaliando seu progresso..."):
                student_messages = [msg["content"] for msg in st.session_state.chat if msg["role"] == "user"]
                combined_ans = "\n".join(student_messages)
                current_level = "Incorreto"
                try:
                    eval_result = evaluate_answer_with_ai(case, combined_ans)
                    if "Erro" in str(eval_result.get("feedback", "")):
                        if st.session_state.current_evaluation:
                            eval_result = st.session_state.current_evaluation
                    else:
                        st.session_state.current_evaluation = eval_result
                    current_level = eval_result.get("level", "Incorreto")
                except Exception as e:
                    print(f"Erro ao avaliar progresso: {e}")
                    if st.session_state.current_evaluation:
                        current_level = st.session_state.current_evaluation.get("level", "Incorreto")
                    
            # 3. Resposta do Tutor baseada no nível atual estimado
            with st.spinner("O Tutor está pensando..."):
                case_adapted = case.copy()
                case_adapted['titulo'] = case['pergunta']
                case_adapted['queixa'] = case['pergunta']
                case_adapted['hma'] = "Questão de Biologia Molecular"
                case_adapted['sintomas'] = case.get('componentes_conhecimento', [])
                case_adapted['gabarito'] = case['resposta_esperada']
                
                full_resp = ""
                try:
                    gen = tutor_reply_com_ia(case_adapted, q_msg, st.session_state.chat, current_level=current_level)
                    with chat_container:
                        with st.chat_message("assistant"):
                            ph = st.empty()
                            for chunk in gen:
                                full_resp += chunk
                                ph.markdown(full_resp + " ▌")
                            ph.markdown(full_resp)
                except Exception as e:
                    full_resp = f"Erro ao gerar resposta do tutor: {e}"
                    st.error(full_resp)
                    
            st.session_state.chat.append({"role": "assistant", "content": full_resp})
            
            # 4. Registrar no Firestore
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
