import streamlit as st
import extra_streamlit_components as stx
from logic import (
    APP_NAME, pick_new_case, get_case,
    finalize_case, level_from_score, progress_to_next_level,
    save_progress, load_progress, tutor_reply_com_ia,
    correct_exam_name, suggest_exam_corrections, normalize_exam_name,
    CONDUTA_HINTS
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
from firebase_config import test_firebase_connection
from analytics import (
    start_case_timer, end_case_timer, log_chat_interaction, 
    get_user_detailed_stats, calculate_accuracy_rate
)
from admin_dashboard import show_admin_dashboard
from professor_dashboard import show_advanced_professor_dashboard

# --- GERENCIADOR DE COOKIES (SINGLETON) ---
@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- CONFIGURAÇÃO DE ESTILO ---
def apply_custom_style():
    # Importa Google Material Icons e define estilos
    st.markdown("""
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined|Material+Icons+Round|Material+Icons+Sharp|Material+Icons+Two+Tone" rel="stylesheet">
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
        }
        /* Ajuste fino para alinhar ícones material com texto */
        .material-icons-outlined {
            vertical-align: middle;
            font-size: 1.2em;
            position: relative;
            top: -2px;
            margin-right: 4px;
        }
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify_content: center;
        }
        .stTextInput input, .stTextArea textarea {
            border-radius: 8px;
        }
        div[data-testid="stCard"] {
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def show_login_page():
    """Exibe página de login e cadastro com visual modernizado"""
    apply_custom_style()
    
    # Coluna central para o Login
    col_left, col_center, col_right = st.columns([1, 1.5, 1])
    
    with col_center:
        st.markdown("<div style='text-align: center; margin-bottom: 2rem;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='color: #11B965; font-size: 3.5em; margin:0;'>BioTutor</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 1.2em;'>Seu Tutor Inteligente de Clínica Geral</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Container estilo "Card"
        with st.container(border=True):
            tab1, tab2 = st.tabs(["Entrar", "Criar Conta"])
            
            with tab1:
                st.markdown("##### <span class='material-icons-outlined'>login</span> Bem-vindo de volta!", unsafe_allow_html=True)
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="seu@email.com")
                    password = st.text_input("Senha", type="password", placeholder="••••••")
                    remember_me = st.checkbox("Manter conectado por 7 dias")
                    
                    st.markdown("")
                    # Botão primário
                    submitted = st.form_submit_button("Acessar Sistema", type="primary", use_container_width=True)
                    
                    if submitted:
                        if email and password:
                            with st.spinner("Autenticando..."):
                                success, message, user_data = authenticate_user(email, password)
                                if success:
                                    login_user(user_data)
                                    
                                    # Lógica de persistência
                                    if remember_me:
                                        token = create_auth_token(user_data['id'])
                                        cookie_manager.set(
                                            'auth_token', 
                                            token, 
                                            expires_at=datetime.now() + timedelta(days=7),
                                            key='set_auth'
                                        )
                                    
                                    st.rerun()
                                else:
                                    st.error(message, icon="🚫")
                        else:
                            st.warning("Preencha todos os campos.", icon="⚠️")

            with tab2:
                st.markdown("##### <span class='material-icons-outlined'>person_add</span> Novo por aqui?", unsafe_allow_html=True)
                st.info("""
                **Instruções de Acesso:**
                *   **Alunos:** Use seu email `@aluno.fcmsantacasasp.edu.br`.
                *   **Professores:** Use seu email `@fcmsantacasasp.edu.br`.
                
                O sistema identificará seu perfil automaticamente.
                """)
                
                with st.form("register_form"):
                    name = st.text_input("Nome Completo", placeholder="Seu nome")
                    email = st.text_input("Email Institucional", placeholder="exemplo@fcmsantacasasp.edu.br")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        password = st.text_input("Senha", type="password", placeholder="Mínimo 6 dígitos")
                    with col_p2:
                        confirm_password = st.text_input("Confirmar", type="password", placeholder="Repita a senha")
                    
                    # Lógica de tipo de usuário
                    user_type = None
                    ra = None
                    if email and '@' in email:
                        domain = email.split('@')[1].lower()
                        if domain == 'fcmsantacasasp.edu.br':
                            user_type = 'professor'
                            st.caption("✅ Identificado como Professor")
                        elif domain == 'aluno.fcmsantacasasp.edu.br':
                            user_type = 'aluno'
                            st.caption("✅ Identificado como Aluno")
                            ra = st.text_input("RA (Registro Acadêmico)", placeholder="Seu RA")
                        else:
                            st.error("Domínio de email não autorizado.", icon="🚫")
                    
                    st.markdown("")
                    reg_submitted = st.form_submit_button("Criar Minha Conta", type="primary", use_container_width=True)
                    
                    if reg_submitted:
                        # Validações mantidas
                        if not user_type:
                            st.error("Use um email institucional válido.", icon="🚫")
                        elif password != confirm_password:
                            st.error("Senhas não conferem.", icon="🚫")
                        elif len(password) < 6:
                            st.error("Senha muito curta.", icon="🚫")
                        else:
                            if user_type == 'aluno' and not ra:
                                st.error("RA é obrigatório para alunos.", icon="🚫")
                            else:
                                call_args = [name, email, password, user_type]
                                if user_type == 'aluno': call_args.append(ra)
                                
                                with st.spinner("Criando conta..."):
                                    success, msg = register_user(*call_args)
                                    if success:
                                        st.success("Conta criada! Acesse a aba 'Entrar'.", icon="✅")
                                    else:
                                        st.error(msg, icon="🚫")

    # Footer discreto
    st.markdown("<div style='text-align: center; margin-top: 3rem; color: #999; font-size: 0.8em;'>BioTutor v2.0 • Desenvolvido para FCMSCSP</div>", unsafe_allow_html=True)

def show_user_profile():
    """Sidebar com perfil simplificado"""
    user = get_current_user()
    
    with st.sidebar:
        st.markdown(f"### <span class='material-icons-outlined'>account_circle</span> Olá, {user['name'].split()[0]}", unsafe_allow_html=True)
        st.caption(f"{user['user_type'].title()} • {user['email']}")
        
        if st.button("Sair", key="logout_btn", use_container_width=True):
            logout_user()
            cookie_manager.delete('auth_token')
            st.rerun()
        st.markdown("---")

def show_professor_dashboard():
    """Dashboard para professores mantido"""
    require_professor()
    
    st.title("Dashboard do Professor")
    st.info("Aqui você gerencia os usuários do sistema.")
    
    # Estatísticas dos usuários
    from auth_firebase import get_all_users
    users = get_all_users()
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Usuários", len(users))
    with col2: st.metric("Alunos", len([u for u in users if u["user_type"] == "aluno"]))
    with col3: st.metric("Professores", len([u for u in users if u["user_type"] == "professor"]))
    
    if is_firebase_connected():
        with st.expander("Ferramentas de Admin", expanded=False):
            if st.button("Migrar Dados Locais para Nuvem"):
                with st.spinner("Migrando..."):
                    success, message = migrate_local_to_firebase()
                    if success: st.success(message)
                    else: st.error(message)

    st.markdown("### Usuários Cadastrados")
    if users:
        for user in users:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{user['name']}** ({user['user_type']})")
                c1.caption(user['email'])
                if user['id'] != st.session_state.user_id:
                    if c2.button("Remover", key=f"del_{user['id']}"):
                        with st.spinner("Removendo..."):
                            delete_user(user['id'])
                            st.rerun()
    else:
        st.info("Nenhum usuário encontrado.")

def init_state():
    """Inicialização de estado"""
    if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
    
    user = get_current_user()
    saved = load_progress()
    
    user_progress = {}
    if isinstance(saved, dict) and saved.get("user_id") == user["id"]: user_progress = saved
    elif isinstance(saved, list):
        for p in saved:
            if p.get("user_id") == user["id"]: 
                user_progress = p; break
    
    defaults = {
        "score": 0, "streak": 0, "unlocked_level": 1,
        "current_case_id": None, "revealed_exams": [], "chat": [],
        "case_scored": False, "last_result": None, "show_next_case_btn": False,
        "used_cases": [], "case_history": [], "reset_fields": False,
        "auto_fill": False, "auto_fill_exams": False, "current_timer_id": None
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = user_progress.get(key, val) if key in ["score", "streak", "unlocked_level"] else val

def persist_now():
    user = get_current_user()
    save_progress({
        "user_id": user["id"],
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "unlocked_level": st.session_state.unlocked_level,
        "when": datetime.now().isoformat(timespec="seconds"),
    })

def start_new_case():
    """Inicia novo caso e limpa estados temporários"""
    # Salva histórico se necessário
    if st.session_state.current_case_id and st.session_state.show_next_case_btn:
        curr = get_case(st.session_state.current_case_id)
        entry = {"id": curr["id"], "titulo": curr["titulo"], "nivel": curr["nivel"]}
        if entry not in st.session_state.case_history:
            st.session_state.case_history.append(entry)
            
    new_case = pick_new_case(st.session_state.unlocked_level, st.session_state.used_cases)
    st.session_state.current_case_id = new_case["id"]
    if new_case["id"] not in st.session_state.used_cases:
        st.session_state.used_cases.append(new_case["id"])
        
    # Timer
    user = get_current_user()
    if user:
        try:
            st.session_state.current_timer_id = start_case_timer(user["id"], new_case["id"])
        except: pass
        
    # Reset
    st.session_state.revealed_exams = []
    st.session_state.chat = []
    st.session_state.case_scored = False
    st.session_state.last_result = None
    st.session_state.show_next_case_btn = False
    st.session_state.reset_fields = True
    st.session_state.auto_fill = False
    st.session_state.auto_fill_exams = False
    st.rerun()

def return_to_case(case_id: str):
    st.session_state.current_case_id = case_id
    st.session_state.revealed_exams = []
    st.session_state.chat = []
    st.session_state.case_scored = False
    st.session_state.last_result = None
    st.session_state.show_next_case_btn = False
    st.session_state.reset_fields = True
    st.session_state.auto_fill = False
    st.session_state.auto_fill_exams = False
    st.rerun()

def auto_fill_fields():
    st.session_state.auto_fill = True
    st.session_state.auto_fill_exams = True
    st.rerun()

# --- FUNÇÃO PRINCIPAL ---
def main():
    st.set_page_config(page_title=f"{APP_NAME}", page_icon="🧬", layout="wide")
    apply_custom_style()
    init_session()
    
    try: create_default_admin()
    except: pass
    
    # --- AUTO LOGIN VIA COOKIE ---
    if not is_logged_in():
        time.sleep(0.1)
        token = cookie_manager.get('auth_token')
        if token:
            user_id = validate_auth_token(token)
            if user_id:
                user_data = get_user_by_id(user_id)
                if user_data:
                    login_user(user_data)
                    st.rerun()

    if not is_logged_in():
        show_login_page()
        return
        
    init_state()
    show_user_profile()
    
    user = get_current_user()
    
    # Roteamento Admin/Professor
    if user["user_type"] == "admin":
        show_admin_dashboard()
        return
    if user["user_type"] == "professor":
        nav = st.sidebar.radio("Navegação", ["Casos Clínicos", "Dashboard", "Analytics"], label_visibility="collapsed")
        if nav == "Dashboard": show_professor_dashboard(); return
        if nav == "Analytics": show_advanced_professor_dashboard(); return

    # --- Sidebar (Barra Lateral) ---
    st.sidebar.markdown("### <span class='material-icons-outlined'>emoji_events</span> Seu Progresso", unsafe_allow_html=True)
    c1, c2 = st.sidebar.columns(2)
    c1.metric("Pontos", st.session_state.score)
    
    # Sistema de streak
    streak_icon = "🔥" 
    if st.session_state.streak >= 3: streak_icon = "🔥" # Mantendo emoji aqui pois é parte da gamificação visual
    
    c2.metric("Streak", f"{st.session_state.streak} {streak_icon}")
    
    lvl_prog = progress_to_next_level(st.session_state.score)
    st.sidebar.caption(f"Nível {st.session_state.unlocked_level} desbloqueado")
    st.sidebar.progress(lvl_prog)
    
    with st.sidebar.expander("Opções", expanded=True):
        if st.button("Pular para Próximo Caso", use_container_width=True): 
             with st.spinner("Carregando caso..."):
                 start_new_case()
        if st.button("Resetar Histórico", use_container_width=True):
             st.session_state.used_cases = []
             st.session_state.case_history = []
             st.rerun()
    
    # --- ÁREA DE TRABALHO (Main) ---
    if st.session_state.current_case_id is None: start_new_case()
    case = get_case(st.session_state.current_case_id)
    
    # Header do Caso
    st.markdown(f"## <span class='material-icons-outlined'>medical_services</span> {case['titulo']}", unsafe_allow_html=True)
    st.markdown(f"<span style='background-color:#e6f4ea; color:#1e8e3e; padding:4px 8px; border-radius:4px; font-size:0.8em; font-weight:bold'>NÍVEL {case['nivel']}</span>", unsafe_allow_html=True)
    st.markdown("")

    # Layout Principal: Esquerda (Dados + Trabalho) | Direita (Chat)
    main_col, chat_col = st.columns([1.8, 1])
    
    with main_col:
        # Cartão do Paciente
        with st.container(border=True):
            st.markdown("#### <span class='material-icons-outlined'>assignment</span> Prontuário do Paciente", unsafe_allow_html=True)
            st.info(f"**Queixa Principal:** {case['queixa']}")
            
            with st.expander("Ver História Completa e Exame Físico", expanded=False):
                st.markdown(f"**HMA:** {case['hma']}")
                st.markdown(f"**Antecedentes:** {case['antecedentes']}")
                st.markdown("---")
                c1, c2 = st.columns(2)
                c1.markdown(f"**Exame Físico:**\n{case['exame_fisico']}")
                c2.markdown(f"**Sinais Vitais:**\n{str(case['sinais_vitais']).replace('{','').replace('}','').replace(chr(39),'')}")

        st.markdown("")
        
        # Área de Trabalho (Abas para Exames e Diagnóstico)
        # Tabs como texto limpo, ícones no conteúdo
        work_tab1, work_tab2 = st.tabs(["Solicitar Exames", "Diagnóstico & Conduta"])
        
        with work_tab1:
            st.markdown("##### <span class='material-icons-outlined'>biotech</span> Exames Complementares", unsafe_allow_html=True)
            st.caption("Quais exames complementares você solicitaria?")
            
            exam_key_suffix = f"_{st.session_state.current_case_id}_{st.session_state.reset_fields}"
            default_exams = ", ".join(case.get("exames_relevantes", {}).keys()) if st.session_state.auto_fill_exams else ""
            
            e_col1, e_col2 = st.columns([3, 1])
            exam_req = e_col1.text_input("Exames (separados por vírgula)", placeholder="Ex: Hemograma, Raio-X...", value=default_exams, key=f"ex_in{exam_key_suffix}", label_visibility="collapsed")
            if e_col2.button("Solicitar", use_container_width=True):
                with st.spinner("Analisando pedido..."):
                    if exam_req.strip():
                        for ex in exam_req.split(","):
                            if ex.strip():
                                corr, was_corr = correct_exam_name(ex)
                                if corr not in st.session_state.revealed_exams: 
                                    st.session_state.revealed_exams.append(corr)
                                    if was_corr: st.toast(f"Corrigido: {ex} -> {corr}")
                    st.rerun()

            # Mostra Resultados
            if st.session_state.revealed_exams:
                st.markdown("---")
                st.markdown("##### 📄 Resultados")
                rel = {k.lower(): v for k,v in case.get("exames_relevantes",{}).items()}
                opt = {k.lower(): v for k,v in case.get("exames_opcionais",{}).items()}
                
                for ex in st.session_state.revealed_exams:
                    norm = normalize_exam_name(ex)
                    found = False
                    # Procura relevante
                    for k,v in rel.items():
                        if normalize_exam_name(k) == norm:
                            st.success(f"**{ex.upper()}**: {v}")
                            found = True; break
                    if not found:
                        for k,v in opt.items():
                            if normalize_exam_name(k) == norm:
                                st.info(f"**{ex.upper()}**: {v}")
                                found = True; break
                    if not found:
                        sug = suggest_exam_corrections(ex, {**rel, **opt})
                        st.warning(f"**{ex.upper()}**: {sug}")

        with work_tab2:
            st.markdown("##### <span class='material-icons-outlined'>healing</span> Diagnóstico & Conduta", unsafe_allow_html=True)
            st.caption("Formule sua hipótese e plano terapêutico.")
            
            fk = f"_{st.session_state.current_case_id}_{st.session_state.reset_fields}"
            def_diag = case["gabarito"] if st.session_state.auto_fill else ""
            def_plan = ", ".join(CONDUTA_HINTS.get(case["id"], [])) if st.session_state.auto_fill else ""
            
            u_diag = st.text_input("Hipótese Diagnóstica", value=def_diag, key=f"diag{fk}", placeholder="Qual a doença?")
            u_plan = st.text_area("Conduta / Tratamento", value=def_plan, key=f"plan{fk}", height=100, placeholder="O que fazer com o paciente?")
            
            valid = bool(u_diag.strip() and u_plan.strip())
            
            # Botão de envio com spinner
            if st.button("Enviar Análise", type="primary", disabled=not valid or st.session_state.case_scored, use_container_width=True, icon="✅"):
                with st.spinner("Analisando resposta..."):
                    res = finalize_case(case, u_diag, st.session_state.revealed_exams, u_plan, st.session_state)
                    st.session_state.score += res["points_gained"]
                    if res["breakdown"]["diagnóstico"] >= 10: st.session_state.streak += 1
                    else: st.session_state.streak = 0
                    
                    nl = level_from_score(st.session_state.score)
                    if nl > st.session_state.unlocked_level: st.session_state.unlocked_level = nl; st.balloons()
                    
                    persist_now()
                    st.session_state.case_scored = True
                    st.session_state.last_result = res
                    st.session_state.show_next_case_btn = res["breakdown"]["diagnóstico"] >= 10
                    st.session_state.auto_fill = False
                    st.session_state.auto_fill_exams = False
                    
                    # Fim timer
                    try: end_case_timer(st.session_state.current_timer_id, res); st.session_state.current_timer_id = None
                    except: pass
                    st.rerun()

            if st.session_state.last_result:
                r = st.session_state.last_result
                st.markdown("---")
                if r["points_gained"] > 0:
                    st.success(f"**Muito bem! +{r['points_gained']} pontos**", icon="🎉")
                else:
                    st.warning(f"**Atenção! +{r['points_gained']} pontos**", icon="⚠️")
                st.write(r["feedback"])
                
                if st.session_state.show_next_case_btn:
                    if st.button("Próximo Caso", type="primary", use_container_width=True, icon="➡️"):
                        with st.spinner("Carregando próximo caso..."):
                            start_new_case()

    with chat_col:
        with st.container(border=True):
            st.markdown("#### <span class='material-icons-outlined'>psychology</span> Tutor IA", unsafe_allow_html=True)
            
            h_cont = st.container(height=400)
            with h_cont:
                if not st.session_state.chat:
                    st.info("Olá! Sou seu tutor virtual. Analise o caso e tire dúvidas comigo.", icon="👋")
                
                for msg in st.session_state.chat:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            if user_msg := st.chat_input("Tire sua dúvida..."):
                st.session_state.chat.append({"role": "user", "content": user_msg})
                with h_cont:
                    with st.chat_message("user"): st.markdown(user_msg)
                
                # Resposta da IA com spinner
                # Nota: st.spinner não funciona bem dentro de containers em loops, mas aqui é acionado pelo input
                # Vamos usar um placeholder ou spinner na coluna
                with st.spinner("Pensando..."):
                    full_resp = ""
                    placeholder = st.empty()
                    
                    # Medir tempo
                    import time; t0 = time.time()
                    
                    try:
                        gen = tutor_reply_com_ia(case, user_msg, st.session_state.chat)
                        with h_cont:
                            with st.chat_message("assistant"):
                                resp_container = st.empty()
                                for chunk in gen:
                                    full_resp += chunk
                                    resp_container.markdown(full_resp + " ▌")
                                resp_container.markdown(full_resp)
                    except Exception as e:
                        full_resp = f"Erro na IA: {e}"
                        st.error(full_resp)
                        
                    t1 = time.time()
                    log_chat_interaction(user["id"], case['id'], user_msg, full_resp, t1-t0)
                    
                    st.session_state.chat.append({"role": "assistant", "content": full_resp})
                    # O rerun recarrega o chat bonito
                    st.rerun()

if __name__ == "__main__":
    main()
