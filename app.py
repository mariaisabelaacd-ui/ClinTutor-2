import streamlit as st
from logic import (
    APP_NAME, pick_new_case, get_case,
    finalize_case, level_from_score, progress_to_next_level,
    save_progress, load_progress, tutor_reply_com_ia,
    correct_exam_name, suggest_exam_corrections, normalize_exam_name,
    CONDUTA_HINTS
)
import uuid
from datetime import datetime
from auth_firebase import (
    init_session, login_user, logout_user, is_logged_in, get_current_user,
    register_user, authenticate_user, require_login, require_professor,
    get_all_users, delete_user, migrate_local_to_firebase, is_firebase_connected,
    create_default_admin
)
from firebase_config import test_firebase_connection
from analytics import (
    start_case_timer, end_case_timer, log_chat_interaction, 
    get_user_detailed_stats, calculate_accuracy_rate
)
from admin_dashboard import show_admin_dashboard
from professor_dashboard import show_advanced_professor_dashboard

def show_login_page():
    """Exibe página de login e cadastro"""
    
    # Título BioTutor na esquerda com cor verde água
    st.markdown("<h1 style='text-align: left; color: #11B965; font-size: 3em; margin-bottom: 5px;'>BioTutor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: left; color: #666; font-size: 18px; margin-top: 0px;'>Tutor de Clínica Geral</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Status do Firebase com debug
    st.write("### 🔍 Debug de Conexão Firebase")
    
    # Verifica secrets
    if hasattr(st, 'secrets'):
        if 'firebase_credentials' in st.secrets:
            st.success("✅ Credenciais do Streamlit Secrets encontradas")
            cred = st.secrets['firebase_credentials']
            st.write(f"**Project ID:** {cred.get('project_id', 'N/A')}")
        else:
            st.error("❌ Credenciais do Streamlit Secrets NÃO encontradas")
            
        # Verifica Google API
        if 'google_api' in st.secrets and 'api_key' in st.secrets['google_api']:
            st.success("✅ Chave do Google API encontrada")
            api_key = st.secrets['google_api']['api_key']
            st.write(f"**API Key:** {api_key[:10]}...{api_key[-10:]}")
        else:
            st.warning("⚠️ Chave de API do Google não encontrada! Configure-a em .streamlit/secrets.toml")
    else:
        st.error("❌ st.secrets não disponível")
    
    # Verifica conexão Firebase
    if is_firebase_connected():
        st.success("✅ Conectado ao Firebase - Dados na nuvem")
    else:
        st.error("❌ Modo local - Dados salvos localmente")
    
    st.markdown("---")
    
    # Tabs para login e cadastro
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    
    with tab1:
        # Formulário de login mais compacto
        with st.container():
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px; color: #11B965;'>Fazer Login</h3>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                # Campos mais compactos
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    email = st.text_input("Email", placeholder="seu@email.com", label_visibility="collapsed")
                    password = st.text_input("Senha", type="password", placeholder="Sua senha", label_visibility="collapsed")
                    
                    # Botão centralizado
                    login_submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if login_submitted:
                if email and password:
                    success, message, user_data = authenticate_user(email, password)
                    if success:
                        login_user(user_data)
                        st.success(f"Bem-vindo(a), {user_data['name']}!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Preencha todos os campos")
    
    with tab2:
        # Formulário de cadastro mais compacto
        with st.container():
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px; color: #11B965;'>Criar Conta</h3>", unsafe_allow_html=True)
            
            with st.form("register_form"):
                # Campos mais compactos
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    name = st.text_input("Nome Completo", placeholder="Seu nome completo", label_visibility="collapsed")
                    email = st.text_input("Email", placeholder="seu@email.com", label_visibility="collapsed")
                    password = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", label_visibility="collapsed")
                    confirm_password = st.text_input("Confirmar Senha", type="password", placeholder="Digite a senha novamente", label_visibility="collapsed")
                    
                    user_type = st.selectbox("Tipo de Usuário", ["aluno", "professor"], 
                                          help="Alunos: acessam casos clínicos\nProfessores: podem gerenciar usuários e ver estatísticas")
                    
                    # Campo RA aparece apenas para alunos
                    if user_type == "aluno":
                        ra = st.text_input("RA (Registro Acadêmico)", placeholder="Digite seu RA", label_visibility="collapsed")
                    else:
                        ra = None
                    
                    # Botão centralizado
                    register_submitted = st.form_submit_button("Cadastrar", type="primary", use_container_width=True)
            
            if register_submitted:
                # Validação específica para alunos (inclui RA)
                if user_type == "aluno":
                    if not all([name, email, password, confirm_password, ra]):
                        st.error("Preencha todos os campos, incluindo o RA")
                    elif password != confirm_password:
                        st.error("As senhas não coincidem")
                    elif len(password) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres")
                    elif not ra.strip():
                        st.error("O RA é obrigatório para alunos")
                    else:
                        success, message = register_user(name, email, password, user_type, ra)
                        if success:
                            st.success(message)
                            st.info("Agora você pode fazer login na aba 'Login'")
                        else:
                            st.error(message)
                else:
                    # Validação para professores (sem RA)
                    if not all([name, email, password, confirm_password]):
                        st.error("Preencha todos os campos")
                    elif password != confirm_password:
                        st.error("As senhas não coincidem")
                    elif len(password) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres")
                    else:
                        success, message = register_user(name, email, password, user_type)
                        if success:
                            st.success(message)
                            st.info("Agora você pode fazer login na aba 'Login'")
                        else:
                            st.error(message)

def show_user_profile():
    """Exibe perfil do usuário e opções de logout"""
    user = get_current_user()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**👤 {user['name']}**")
        st.markdown(f"**📧 {user['email']}**")
        st.markdown(f"**🎓 {user['user_type'].title()}**")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

def show_professor_dashboard():
    """Dashboard para professores"""
    require_professor()
    
    st.title("Dashboard do Professor")
    st.markdown("---")
    
    # Estatísticas dos usuários
    from auth_firebase import get_all_users
    users = get_all_users()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Usuários", len(users))
    
    with col2:
        alunos = len([u for u in users if u["user_type"] == "aluno"])
        st.metric("Alunos", alunos)
    
    with col3:
        professores = len([u for u in users if u["user_type"] == "professor"])
        st.metric("Professores", professores)
    
    # Seção de migração (apenas se Firebase estiver conectado)
    if is_firebase_connected():
        st.subheader("🔄 Migração de Dados")
        with st.expander("Migrar dados locais para Firebase", expanded=False):
            st.info("Esta função migra todos os usuários salvos localmente para o Firebase.")
            if st.button("🚀 Migrar Dados Locais", type="primary"):
                success, message = migrate_local_to_firebase()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    # Lista de usuários
    if users:
        st.subheader("Lista de Usuários")
        
        for user in users:
            with st.expander(f"{user['name']} ({user['user_type']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Tipo:** {user['user_type'].title()}")
                    # Formatação de data baseada no tipo de armazenamento
                    created_at = user.get('created_at')
                    if isinstance(created_at, str):
                        st.write(f"**Cadastrado em:** {created_at[:10]}")
                    else:
                        st.write(f"**Cadastrado em:** {created_at.strftime('%Y-%m-%d') if created_at else 'N/A'}")
                    
                    last_login = user.get('last_login')
                    if last_login:
                        if isinstance(last_login, str):
                            st.write(f"**Último login:** {last_login[:10]}")
                        else:
                            st.write(f"**Último login:** {last_login.strftime('%Y-%m-%d')}")
                
                with col2:
                    if user['id'] != st.session_state.user_id:  # Não pode deletar a si mesmo
                        if st.button(f"Remover", key=f"delete_{user['id']}"):
                            success, message = delete_user(user['id'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    else:
        st.info("Nenhum usuário cadastrado ainda.")

def init_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Carrega o progresso salvo ANTES de inicializar o resto
    user = get_current_user()
    saved = load_progress()
    
    # Filtra progresso do usuário atual
    user_progress = {}
    if isinstance(saved, dict) and saved.get("user_id") == user["id"]:
        user_progress = saved
    elif isinstance(saved, list):
        # Se for uma lista, busca o progresso do usuário atual
        for progress in saved:
            if progress.get("user_id") == user["id"]:
                user_progress = progress
                break
    
    # Inicializa o estado com valores salvos ou padrões
    if "score" not in st.session_state:
        st.session_state.score = user_progress.get("score", 0)
    if "streak" not in st.session_state:
        st.session_state.streak = user_progress.get("streak", 0)
    if "unlocked_level" not in st.session_state:
        st.session_state.unlocked_level = user_progress.get("unlocked_level", 1)
        
    # Estado da sessão que não é salvo entre execuções do navegador
    if "current_case_id" not in st.session_state:
        st.session_state.current_case_id = None
    if "revealed_exams" not in st.session_state:
        st.session_state.revealed_exams = []
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "case_scored" not in st.session_state:
        st.session_state.case_scored = False
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "show_next_case_btn" not in st.session_state:
        st.session_state.show_next_case_btn = False
    if "used_cases" not in st.session_state:
        st.session_state.used_cases = []
    if "case_history" not in st.session_state:
        st.session_state.case_history = []
    if "reset_fields" not in st.session_state:
        st.session_state.reset_fields = False
    if "auto_fill" not in st.session_state:
        st.session_state.auto_fill = False
    if "auto_fill_exams" not in st.session_state:
        st.session_state.auto_fill_exams = False

# Função para salvar o progresso atual
def persist_now():
    user = get_current_user()
    save_progress({
        "user_id": user["id"],
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "unlocked_level": st.session_state.unlocked_level,
        "when": datetime.now().isoformat(timespec="seconds"),
    })

# Função para resetar e ir para um novo caso
def start_new_case():
    # Salva o caso atual no histórico apenas se foi acertado (conseguiu prosseguir)
    if st.session_state.current_case_id and st.session_state.show_next_case_btn:
        current_case = get_case(st.session_state.current_case_id)
        case_entry = {
            "id": current_case["id"],
            "titulo": current_case["titulo"],
            "nivel": current_case["nivel"]
        }
        if case_entry not in st.session_state.case_history:
            st.session_state.case_history.append(case_entry)
    
    new_case = pick_new_case(st.session_state.unlocked_level, st.session_state.used_cases)
    st.session_state.current_case_id = new_case["id"]
    
    # Adiciona o caso atual à lista de casos utilizados
    if new_case["id"] not in st.session_state.used_cases:
        st.session_state.used_cases.append(new_case["id"])
    
    # Inicia timer para o novo caso
    user = get_current_user()
    if user:
        try:
            timer_id = start_case_timer(user["id"], new_case["id"])
            st.session_state.current_timer_id = timer_id
            st.info(f"Timer iniciado para o caso: {new_case['titulo']}")
        except Exception as e:
            st.error(f"Erro ao iniciar timer: {e}")
            st.session_state.current_timer_id = None
    
    st.session_state.revealed_exams = []
    st.session_state.chat = []
    st.session_state.case_scored = False
    st.session_state.last_result = None
    st.session_state.show_next_case_btn = False
    st.session_state.reset_fields = True
    st.session_state.auto_fill = False
    st.session_state.auto_fill_exams = False
    st.rerun()

# Função para voltar a um caso específico
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

# Função para preencher automaticamente os campos com as respostas corretas
def auto_fill_fields():
    st.session_state.auto_fill = True
    st.session_state.auto_fill_exams = True
    st.rerun()

# Função principal da aplicação
def main():
    st.set_page_config(page_title=f"{APP_NAME} – Clínica Geral", page_icon="🧬", layout="wide")
    
    # Inicializa sistema de autenticação
    init_session()
    
    # Cria administrador padrão se não existir
    try:
        create_default_admin()
    except Exception as e:
        pass  # Ignora erros na criação do admin
    
    # Se não estiver logado, mostra página de login
    if not is_logged_in():
        show_login_page()
        return
    
    # Se estiver logado, inicializa o estado da aplicação
    init_state()
    
    # Mostra informações do usuário na sidebar
    show_user_profile()

    # --- Navegação Principal ---
    user = get_current_user()
    
    # Navegação para administradores
    if user["user_type"] == "admin":
        show_admin_dashboard()
        return
    
    # Navegação para professores
    if user["user_type"] == "professor":
        nav_option = st.sidebar.selectbox(
            "Navegação",
            ["Casos Clínicos", "Dashboard Professor", "Analytics Avançado"],
            key="nav_select"
        )
        
        if nav_option == "Dashboard Professor":
            show_professor_dashboard()
            return
        elif nav_option == "Analytics Avançado":
            show_advanced_professor_dashboard()
            return
    
    # --- Sidebar (Barra Lateral) ---
    st.sidebar.title("Progresso do Aluno")
    st.sidebar.metric("Score", st.session_state.score)
    
    # Sistema de streak com emoji de foguinho a cada 3 acertos
    streak_display = str(st.session_state.streak)
    if st.session_state.streak > 0 and st.session_state.streak % 3 == 0:
        streak_display = f"{st.session_state.streak} 🔥"
    elif st.session_state.streak > 0:
        streak_display = f"{st.session_state.streak}"
    
    st.sidebar.metric("Streak", streak_display)
    st.sidebar.metric("Casos Utilizados", len(st.session_state.used_cases))
    
    # Estatísticas detalhadas para alunos
    if user["user_type"] == "aluno":
        user_stats = get_user_detailed_stats(user["id"])
        
        with st.sidebar.expander("Minhas Estatísticas", expanded=False):
            st.metric("Taxa de Acertos", f"{user_stats['case_stats']['accuracy_rate']:.1f}%")
            st.metric("Tempo Médio", user_stats['case_stats']['average_time_formatted'])
            st.metric("Interações Chat", user_stats['total_chat_interactions'])
            st.metric("Casos Resolvidos", user_stats['case_stats']['total_cases'])
            
            if user_stats['case_stats']['total_cases'] > 0:
                st.progress(user_stats['case_stats']['accuracy_rate'] / 100)
                st.caption(f"Progresso: {user_stats['case_stats']['correct_cases']}/{user_stats['case_stats']['total_cases']} casos acertados")
    
    # Lista de casos acertados
    if st.session_state.case_history:
        with st.sidebar.expander("Casos Acertados", expanded=False):
            for case in reversed(st.session_state.case_history[-10:]):  # Mostra os últimos 10
                if st.button(f"{case['titulo']} (Nível {case['nivel']})", 
                           key=f"return_to_{case['id']}", 
                           help="Clique para voltar a este caso"):
                    return_to_case(case['id'])
    
    next_progress = progress_to_next_level(st.session_state.score)
    st.sidebar.markdown(f"**Nível desbloqueado:** {st.session_state.unlocked_level} / 3")
    st.sidebar.progress(next_progress)

    with st.sidebar.expander("Configurações", expanded=True):
        if st.button("🔄 Novo Caso"):
            start_new_case()

        if st.button("🔄 Resetar Lista de Casos"):
            st.session_state.used_cases = []
            st.session_state.case_history = []
            st.success("Lista de casos acertados foi resetada!")
            st.rerun()

        if st.button("🔁 Resetar Progresso Total"):
            st.session_state.score = 0
            st.session_state.streak = 0
            st.session_state.unlocked_level = 1
            st.session_state.used_cases = []
            st.session_state.case_history = []
            persist_now()
            start_new_case()

    # Botão de desenvolvimento para demonstrações
    with st.sidebar.expander("Dev Tools", expanded=False):
        if st.button("Preencher Campos Automaticamente", help="Preenche diagnóstico, plano e exames com as respostas corretas do caso atual"):
            auto_fill_fields()

    # --- Lógica do Caso Atual ---
    if st.session_state.current_case_id is None:
        start_new_case()
    
    case = get_case(st.session_state.current_case_id)
    
    # Inicia timer se não existe
    if not hasattr(st.session_state, 'current_timer_id') or not st.session_state.current_timer_id:
        user = get_current_user()
        if user:
            try:
                timer_id = start_case_timer(user["id"], case["id"])
                st.session_state.current_timer_id = timer_id
            except Exception as e:
                st.error(f"Erro ao iniciar timer: {e}")
                st.session_state.current_timer_id = None

    st.title(f"BioTutor – Tutor de Clínica Geral")
    st.caption(f"Bem-vindo(a), {user['name']}! Simulador com IA para treinar raciocínio clínico.")
    
    # Card com informações do caso atual
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Caso Atual:** {case['titulo']}")
        
        with col2:
            st.markdown(f"**Nível:** {case['nivel']}")
        
        with col3:
            if hasattr(st.session_state, 'current_timer_id') and st.session_state.current_timer_id:
                st.markdown("**Status:** Ativo")
            else:
                st.markdown("**Status:** Inativo")
    
    st.markdown("---")

    col_quiz, col_chat = st.columns([2, 1])

    # --- Coluna da Esquerda (Caso Clínico e Ações) ---
    with col_quiz:
        st.subheader("1) Caso Clínico")
        with st.container(border=True):
            st.markdown(f"#### {case['titulo']}")
            st.write(f"**Queixa principal:** {case['queixa']}")
            with st.expander("História e dados iniciais", expanded=True):
                st.write("**HMA:**", case["hma"])
                st.write("**Antecedentes:**", case["antecedentes"])
                st.write("**Exame físico:**", case["exame_fisico"])
                st.write("**Sinais vitais:**", case["sinais_vitais"])

        st.subheader("2) Solicitar Exames")
        
        # Usa chave dinâmica para resetar o campo de exames
        exam_key_suffix = f"_{st.session_state.current_case_id}_{st.session_state.reset_fields}_{st.session_state.auto_fill_exams}"
        
        # Preenchimento automático dos exames
        if st.session_state.auto_fill_exams:
            # Pega os exames relevantes do caso
            relevant_exams = list(case.get("exames_relevantes", {}).keys())
            default_exams = ", ".join(relevant_exams)
        else:
            default_exams = ""
            
        exam_req = st.text_input(
            "Digite o(s) nome(s) do(s) exame(s), separados por vírgula (ex.: hemograma, ecg)",
            value=default_exams,
            key=f"exam_request_input{exam_key_suffix}"
        )
        if st.button("Pedir exame(s)"):
            if exam_req.strip():
                exames = [e.strip().lower() for e in exam_req.split(",") if e.strip()]
                for ex in exames:
                    # Aplica correção automática
                    corrected_exam, was_corrected = correct_exam_name(ex)
                    if corrected_exam not in st.session_state.revealed_exams:
                        st.session_state.revealed_exams.append(corrected_exam)
                        # Mostra mensagem de correção se aplicável
                        if was_corrected:
                            st.info(f"Corrigido automaticamente: '{ex}' → '{corrected_exam}'")
                st.rerun()
        
        if st.session_state.revealed_exams:
            with st.container(border=True):
                st.markdown("**Resultados dos exames:**")
                rel_keys = {k.lower(): v for k, v in case.get("exames_relevantes", {}).items()}
                opt_keys = {k.lower(): v for k, v in case.get("exames_opcionais", {}).items()}
                all_available_exams = {**rel_keys, **opt_keys}
                
                for ex in st.session_state.revealed_exams:
                    # Normaliza o exame para comparação
                    ex_normalized = normalize_exam_name(ex)
                    found = False
                    
                    # Busca em exames relevantes
                    for rel_key, rel_value in rel_keys.items():
                        if normalize_exam_name(rel_key) == ex_normalized:
                            st.success(f"**{ex.upper()}:** {rel_value}")
                            found = True
                            break
                    
                    # Se não encontrou em relevantes, busca em opcionais
                    if not found:
                        for opt_key, opt_value in opt_keys.items():
                            if normalize_exam_name(opt_key) == ex_normalized:
                                st.info(f"**{ex.upper()}:** {opt_value}")
                                found = True
                                break
                    
                    # Se não encontrou em nenhum, sugere correções
                    if not found:
                        suggestion = suggest_exam_corrections(ex, all_available_exams)
                        st.error(f"**{ex.upper()}:** {suggestion}")

        st.subheader("3) Sua hipótese e plano")
        # Usa chaves dinâmicas para resetar os campos
        field_key_suffix = f"_{st.session_state.current_case_id}_{st.session_state.reset_fields}_{st.session_state.auto_fill}"
        
        # Valores padrão para preenchimento automático
        default_diag = case["gabarito"] if st.session_state.auto_fill else ""
        default_plan = ", ".join(CONDUTA_HINTS.get(case["id"], [])) if st.session_state.auto_fill else ""
        
        user_diag = st.text_input("Hipótese diagnóstica principal", 
                                 value=default_diag, 
                                 key=f"user_diag_input{field_key_suffix}")
        user_plan = st.text_area("Plano inicial (condutas)", 
                                value=default_plan, 
                                height=100, 
                                key=f"user_plan_input{field_key_suffix}")

        # Validação dos campos obrigatórios
        campos_preenchidos = bool(user_diag.strip() and user_plan.strip())
        botao_disabled = st.session_state.case_scored or not campos_preenchidos
        
        # Mensagem de orientação se campos não estão preenchidos
        if not campos_preenchidos and not st.session_state.case_scored:
            st.warning("Preencha todos os campos acima antes de enviar para análise.")

        if st.button("Enviar para avaliação e pontuar", disabled=botao_disabled):
            res = finalize_case(case, user_diag, st.session_state.revealed_exams, user_plan, st.session_state)
            
            # Finaliza o timer do caso ANTES de atualizar o estado
            if hasattr(st.session_state, 'current_timer_id') and st.session_state.current_timer_id:
                try:
                    analytics_data = end_case_timer(st.session_state.current_timer_id, res)
                    if analytics_data:
                        # Mensagem destacada com o tempo de resolução
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #4CAF50, #45a049);
                            color: white;
                            padding: 20px;
                            border-radius: 10px;
                            text-align: center;
                            font-size: 18px;
                            font-weight: bold;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                            margin: 20px 0;
                        ">
                            🎉 <strong>Caso Resolvido!</strong><br>
                            ⏱️ Tempo de resolução: <strong>{analytics_data['duration_formatted']}</strong><br>
                            📊 Pontos ganhos: <strong>{res['points_gained']}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erro ao salvar analytics: {e}")
                finally:
                    st.session_state.current_timer_id = None
            
            # Atualiza score e streak
            st.session_state.score += res["points_gained"]
            if res["breakdown"]["diagnóstico"] >= 10: # Acerto total
                st.session_state.streak += 1
            else:
                st.session_state.streak = 0
            
            # Atualiza nível se necessário
            new_level = level_from_score(st.session_state.score)
            if new_level > st.session_state.unlocked_level:
                st.session_state.unlocked_level = new_level
                st.balloons()
            
            persist_now()
            st.session_state.case_scored = True
            st.session_state.last_result = res
            st.session_state.show_next_case_btn = res["breakdown"]["diagnóstico"] >= 10
            st.session_state.auto_fill = False  # Reset do auto_fill após envio
            st.session_state.auto_fill_exams = False  # Reset do auto_fill_exams após envio
            st.rerun()

        # Mostra o resultado da avaliação se o caso já foi pontuado
        if st.session_state.last_result:
            res = st.session_state.last_result
            gained = res["points_gained"]
            bd = res["breakdown"]
            with st.container(border=True):
                st.success(f"Você ganhou **{gained}** pontos! (Diag: {bd['diagnóstico']}, Exames: {bd['exames']}, Plano: {bd['plano']} + Bônus: {bd['bônus_streak']})")
                st.info(res["feedback"])

        # Mostra o botão de próximo caso se aplicável
        if st.session_state.show_next_case_btn:
            if st.button("Próximo Caso", type="primary"):
                start_new_case()

    # --- Coluna da Direita (Chat com IA) ---
    with col_chat:
        st.subheader("Chat com a IA Tutora")
        
        with st.container(height=500):
            for turn in st.session_state.chat:
                with st.chat_message(turn["role"]):
                    st.markdown(turn["content"])

        chat_in = st.chat_input("Pergunte sobre hipóteses, exames, conduta...")
        if chat_in:
            st.session_state.chat.append({"role": "user", "content": chat_in})
            
            # Inicia timer para resposta da IA
            start_time = datetime.now()
            
            with st.spinner("Tutor está digitando..."):
                response_generator = tutor_reply_com_ia(case, chat_in, st.session_state.chat)
                
                # Coleta a resposta completa para salvar no estado
                full_response_chunks = []
                for chunk in response_generator:
                    full_response_chunks.append(chunk)
                
                full_response = "".join(full_response_chunks)
            
            # Calcula tempo de resposta
            response_time = (datetime.now() - start_time).total_seconds()
            
            st.session_state.chat.append({"role": "assistant", "content": full_response})
            
            # Registra interação com o chatbot
            user = get_current_user()
            if user:
                log_chat_interaction(
                    user["id"], 
                    case["id"], 
                    chat_in, 
                    full_response, 
                    response_time
                )
            
            st.rerun()

if __name__ == "__main__":
    main()

