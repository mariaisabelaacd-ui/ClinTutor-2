import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any
from io import BytesIO
from fpdf import FPDF

from analytics import (
    get_all_users_analytics, format_duration
)
from auth_firebase import get_all_users, get_user_by_id
from logic import QUESTIONS, TOPICS
from admin_utils import (
    reset_student_analytics, clear_student_chat_interactions,
    reset_all_students_analytics, clear_all_chat_interactions,
    reset_all_student_progress,
    log_admin_action, get_database_stats
)
from ui_helpers import icon, metric_card

TOPIC_KEYS = list(TOPICS.keys()) # ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8']

# =========================================================================
# HELPER DE LATIN-1 / UTF-8 PARA O GERADOR DE PDF
# =========================================================================
def safe_pdf_str(text: Any) -> str:
    """Substitui caracteres fora do latin-1 para compatibilidade estrita com FPDF"""
    if text is None:
        return ""
    s = str(text)
    trans = {
        '⁺': '+', '⁻': '-', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0',
        '→': '->', '←': '<-', '↔': '<->', '–': '-', '—': '-',
        '“': '"', '”': '"', '‘': "'", '’': "'", '•': '*', '…': '...'
    }
    for k, v in trans.items():
        s = s.replace(k, v)
    return s.encode('latin-1', 'replace').decode('latin-1')


# =========================================================================
# GERAÇÃO DE RELATÓRIO GERAL DA TURMA EM PDF (COM CHAT COMPLETO)
# =========================================================================
def generate_class_full_pdf(students: List[Dict], all_analytics: Dict, category_stats: Dict) -> bytes:
    """
    Gera PDF completo e detalhado da turma com:
    - KPIs Gerais
    - Ranking de Desempenho por Categoria (T1 a T8)
    - Desempenho por Aluno
    - Histórico Completo de Interações com o Tutor
    """
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ── CAPA ──
    pdf.add_page()
    pdf.set_fill_color(16, 185, 129)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_y(80)
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, 'Helix.AI', ln=True, align='C')
    
    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 12, 'Relatorio Pedagogico Completo da Turma', ln=True, align='C')
    
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, 'Biofisica - Transporte em Membranas Biologicas (8 Topicos)', ln=True, align='C')
    pdf.cell(0, 8, f'Gerado em: {datetime.now().strftime("%d/%m/%Y as %H:%M")}', ln=True, align='C')
    
    pdf.set_y(170)
    pdf.set_font('Helvetica', 'I', 10)
    resumo_capa = (
        f"Este documento reune o diagnostico completo de aprendizagem da turma ({len(students)} alunos cadastrados), "
        "incluindo o ranking das categorias por taxa de acerto, desempenho individual e o historico "
        "integral das conversas com o Tutor Socratico Helix.AI."
    )
    pdf.multi_cell(0, 6, safe_pdf_str(resumo_capa), align='C')
    
    # ── PÁGINA 2: VISÃO GERAL & RANKING DAS 8 CATEGORIAS ──
    pdf.add_page()
    pdf.set_text_color(16, 185, 129)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '1. Ranking de Desempenho por Categoria (T1 a T8)', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(15, 8, 'Pos.', 1, 0, 'C', True)
    pdf.cell(20, 8, 'Topico', 1, 0, 'C', True)
    pdf.cell(90, 8, 'Descricao do Topico', 1, 0, 'L', True)
    pdf.cell(25, 8, 'Tentativas', 1, 0, 'C', True)
    pdf.cell(30, 8, 'Taxa Acerto', 1, 0, 'C', True)
    pdf.ln()
    
    ranked_cats = sorted(
        category_stats.values(),
        key=lambda x: (x['correct_attempts'] / x['total_attempts'] * 100) if x['total_attempts'] > 0 else 0.0
    )
    
    pdf.set_font('Helvetica', '', 8)
    for pos, c in enumerate(ranked_cats, 1):
        tot = c['total_attempts']
        corr = c['correct_attempts']
        rate = (corr / tot * 100) if tot > 0 else 0.0
        
        pdf.cell(15, 7, f'{pos}o', 1, 0, 'C')
        pdf.cell(20, 7, c['topico_id'], 1, 0, 'C')
        pdf.cell(90, 7, safe_pdf_str(c['topico_nome'][:50]), 1, 0, 'L')
        pdf.cell(25, 7, str(tot), 1, 0, 'C')
        pdf.cell(30, 7, f'{rate:.1f}% ({corr}/{tot})', 1, 0, 'C')
        pdf.ln()
        
    pdf.ln(6)
    
    # ── PÁGINA 3: RESUMO DE DESEMPENHO DOS ALUNOS ──
    pdf.set_text_color(16, 185, 129)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '2. Desempenho Geral por Aluno', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(65, 8, 'Aluno', 1, 0, 'L', True)
    pdf.cell(25, 8, 'RA', 1, 0, 'C', True)
    pdf.cell(30, 8, 'Questoes Resp.', 1, 0, 'C', True)
    pdf.cell(30, 8, 'Taxa Acerto', 1, 0, 'C', True)
    pdf.cell(30, 8, 'Tempo Total', 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 8)
    for s in students:
        uid = s['id']
        udata = all_analytics.get(uid, {})
        cases = udata.get('case_analytics', [])
        tot_c = len(cases)
        corr_c = sum(1 for c in cases if c.get('case_result', {}).get('is_correct', False) or c.get('case_result', {}).get('points_gained', 0) >= 1.0)
        rate_s = (corr_c / tot_c * 100) if tot_c > 0 else 0.0
        dur_s = sum(c.get('duration_seconds', 0) for c in cases)
        
        pdf.cell(65, 7, safe_pdf_str(s.get('name', 'N/A')[:32]), 1, 0, 'L')
        pdf.cell(25, 7, safe_pdf_str(s.get('ra', 'N/A')), 1, 0, 'C')
        pdf.cell(30, 7, str(tot_c), 1, 0, 'C')
        pdf.cell(30, 7, f'{rate_s:.1f}% ({corr_c}/{tot_c})', 1, 0, 'C')
        pdf.cell(30, 7, format_duration(dur_s), 1, 0, 'C')
        pdf.ln()
        
    pdf.ln(6)
    
    # ── PÁGINAS SEGUINTES: HISTÓRICO DE CHAT ──
    pdf.add_page()
    pdf.set_text_color(59, 130, 246)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, '3. Transcricao de Interacoes com o Tutor Socratico', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    q_title_map = {q['id']: f"{q['codigo']} ({q['topico_id']} - {q['dificuldade']}): {q['pergunta']}" for q in QUESTIONS}
    
    has_any_chat = False
    for s in students:
        uid = s['id']
        udata = all_analytics.get(uid, {})
        chat_docs = udata.get('chat_interactions', [])
        if not chat_docs:
            continue
            
        has_any_chat = True
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(224, 242, 254)
        pdf.cell(0, 8, safe_pdf_str(f"Aluno: {s.get('name', 'N/A')} (RA: {s.get('ra', 'N/A')})"), 0, 1, 'L', True)
        pdf.ln(2)
        
        for doc in chat_docs:
            cid = doc.get('case_id', '')
            q_info = q_title_map.get(cid, f"Questao ID: {cid}")
            
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(71, 85, 105)
            pdf.multi_cell(pdf.epw, 5, safe_pdf_str(f"Questao: {q_info[:120]}"))
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
            
            msgs = doc.get('messages', [])
            if not msgs and 'user_message' in doc:
                msgs = [{'user_message': doc.get('user_message', ''), 'bot_response': doc.get('bot_response', '')}]
                
            for m in msgs:
                u_txt = m.get('user_message', '')
                b_txt = m.get('bot_response', '')
                
                if u_txt:
                    pdf.set_fill_color(239, 246, 255)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.multi_cell(pdf.epw, 5, safe_pdf_str(f"Aluno: {u_txt}"), fill=True)
                    pdf.ln(1)
                    
                if b_txt:
                    pdf.set_fill_color(240, 253, 244)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.multi_cell(pdf.epw, 5, safe_pdf_str(f"Tutor: {b_txt}"), fill=True)
                    pdf.ln(2)
            pdf.ln(3)
            
    if not has_any_chat:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.cell(0, 8, 'Nenhuma interacao de chat registrada para a turma ate o momento.', ln=True)
        
    return bytes(pdf.output())


# =========================================================================
# GERAÇÃO DE RELATÓRIO INDIVIDUAL DO ALUNO EM PDF
# =========================================================================
def generate_student_pdf(student: Dict, udata: Dict) -> bytes:
    """Gera PDF individual minimalista do aluno com histórico de questões e chat"""
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 10, 'Helix.AI - Relatorio Individual do Aluno', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, safe_pdf_str(f"Nome: {student.get('name', 'N/A')} | Email: {student.get('email', 'N/A')}"), ln=True)
    pdf.cell(0, 6, safe_pdf_str(f"RA: {student.get('ra', 'N/A')} | Turma: {student.get('turma', 'Biomedicina')}"), ln=True)
    pdf.cell(0, 6, f'Data: {datetime.now().strftime("%d/%m/%Y as %H:%M")}', ln=True)
    pdf.ln(5)
    
    cases = udata.get('case_analytics', [])
    tot = len(cases)
    corr = sum(1 for c in cases if c.get('case_result', {}).get('is_correct', False) or c.get('case_result', {}).get('points_gained', 0) >= 1.0)
    acc = (corr / tot * 100) if tot > 0 else 0.0
    dur = sum(c.get('duration_seconds', 0) for c in cases)
    pts = sum(float(c.get('case_result', {}).get('points_gained', 0)) for c in cases)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(45, 8, f'Questoes: {tot}', 1, 0, 'C', True)
    pdf.cell(45, 8, f'Acertos: {corr} ({acc:.1f}%)', 1, 0, 'C', True)
    pdf.cell(45, 8, f'Pontos: {pts:.1f}', 1, 0, 'C', True)
    pdf.cell(45, 8, f'Tempo: {format_duration(dur)}', 1, 1, 'C', True)
    pdf.ln(6)
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 8, 'Desempenho por Questao', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    q_map = {q['id']: q for q in QUESTIONS}
    for idx, c in enumerate(cases, 1):
        cid = c.get('case_id', '')
        q = q_map.get(cid, {})
        res = c.get('case_result', {})
        is_c = res.get('is_correct', False)
        
        pdf.set_font('Helvetica', 'B', 9)
        status_txt = "CORRETO (+1.0 pt)" if is_c else "INCORRETO (0.0 pt)"
        pdf.cell(0, 6, safe_pdf_str(f"Questao {idx}: {q.get('codigo', cid)} ({q.get('topico_id', '')} - {q.get('dificuldade', '')}) - {status_txt}"), ln=True)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(pdf.epw, 4, safe_pdf_str(f"Enunciado: {q.get('pergunta', '')[:140]}..."))
        pdf.multi_cell(pdf.epw, 4, safe_pdf_str(f"Resposta do Aluno: {res.get('user_answer', 'N/A')}"))
        if not is_c and res.get('distractor_feedback'):
            pdf.set_text_color(220, 38, 38)
            pdf.multi_cell(pdf.epw, 4, safe_pdf_str(f"Erro Conceitual: {res.get('distractor_feedback', '')}"))
            pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
        
    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 8, 'Historico de Conversas com o Tutor Helix.AI', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    chat_docs = udata.get('chat_interactions', [])
    if not chat_docs:
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(0, 6, 'Nenhuma interacao de chat registrada para este aluno.', ln=True)
    else:
        for doc in chat_docs:
            cid = doc.get('case_id', '')
            q = q_map.get(cid, {})
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 6, safe_pdf_str(f"Topico: {q.get('topico_id', '')} - {q.get('topico_nome', '')} ({q.get('codigo', '')})"), ln=True)
            pdf.set_text_color(0, 0, 0)
            
            msgs = doc.get('messages', [])
            if not msgs and 'user_message' in doc:
                msgs = [{'user_message': doc.get('user_message', ''), 'bot_response': doc.get('bot_response', '')}]
            for m in msgs:
                u_txt = m.get('user_message', '')
                b_txt = m.get('bot_response', '')
                if u_txt:
                    pdf.set_fill_color(239, 246, 255)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.multi_cell(pdf.epw, 5, safe_pdf_str(f"Aluno: {u_txt}"), fill=True)
                    pdf.ln(1)
                if b_txt:
                    pdf.set_fill_color(240, 253, 244)
                    pdf.set_font('Helvetica', '', 8)
                    pdf.multi_cell(pdf.epw, 5, safe_pdf_str(f"Tutor: {b_txt}"), fill=True)
                    pdf.ln(2)
            pdf.ln(2)
            
    return bytes(pdf.output())


# =========================================================================
# DASHBOARD PROFESSOR AVANÇADO (MINIMALISTA, MATERIAL ICONS & 8 TÓPICOS)
# =========================================================================
def show_advanced_professor_dashboard():
    all_users = get_all_users()
    student_users = [u for u in all_users if u.get("user_type") == "aluno"]
    all_analytics = get_all_users_analytics()
    
    # ── AGREGAÇÃO DE DADOS POR CATEGORIA (T1 A T8) ──
    category_stats = {}
    for tk, tname in TOPICS.items():
        category_stats[tk] = {
            "topico_id": tk,
            "topico_nome": tname,
            "total_attempts": 0,
            "correct_attempts": 0,
            "total_duration": 0.0,
            "questions": {}
        }

    for q in QUESTIONS:
        tk = q.get("topico_id")
        if tk in category_stats:
            category_stats[tk]["questions"][q["id"]] = {
                "id": q["id"],
                "codigo": q["codigo"],
                "dificuldade": q["dificuldade"],
                "pergunta": q["pergunta"],
                "gabarito": q["gabarito"],
                "distratores": q["distratores"],
                "alternativas": q["alternativas"],
                "total_attempts": 0,
                "correct_attempts": 0,
                "choices_count": {"A": 0, "B": 0, "C": 0, "D": 0}
            }

    total_chat_messages = 0
    total_answered_cases = 0
    total_correct_cases = 0
    total_time_seconds = 0.0

    for uid, udata in all_analytics.items():
        for cdoc in udata.get("chat_interactions", []):
            if "messages" in cdoc and isinstance(cdoc["messages"], list):
                total_chat_messages += len(cdoc["messages"])
            else:
                total_chat_messages += 1
                
        for case in udata.get("case_analytics", []):
            cid = case.get("case_id")
            result = case.get("case_result", {})
            dur = float(case.get("duration_seconds", 0))
            is_corr = bool(result.get("is_correct", False) or result.get("classification") == "CORRETO" or result.get("points_gained", 0) >= 1.0)
            user_ans = str(result.get("user_answer", ""))
            
            total_answered_cases += 1
            if is_corr:
                total_correct_cases += 1
            total_time_seconds += dur
            
            for tk, cdata in category_stats.items():
                if cid in cdata["questions"]:
                    cdata["total_attempts"] += 1
                    if is_corr:
                        cdata["correct_attempts"] += 1
                    cdata["total_duration"] += dur
                    
                    qdata = cdata["questions"][cid]
                    qdata["total_attempts"] += 1
                    if is_corr:
                        qdata["correct_attempts"] += 1
                    for opt in ["A", "B", "C", "D"]:
                        if user_ans.startswith(f"{opt}.") or user_ans.startswith(f"Opção {opt}") or user_ans.startswith(opt):
                            qdata["choices_count"][opt] += 1
                            break

    # ── INTERFACE PRINCIPAL ──
    col_t1, col_t2 = st.columns([3, 1.2])
    with col_t1:
        st.markdown("<h2 style='margin-bottom:0;'><span class='material-icons-outlined' style='font-size:26px; vertical-align:middle; color:#10b981;'>dashboard</span> Painel do Professor</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; font-size:0.95rem; margin-top:-0.3rem;'>Acompanhe o desempenho da turma nos 8 tópicos de Transporte & Membranas.</p>", unsafe_allow_html=True)
    with col_t2:
        pdf_bytes = generate_class_full_pdf(student_users, all_analytics, category_stats)
        st.download_button(
            label="Baixar Relatório Geral (PDF)",
            data=pdf_bytes,
            file_name=f"Relatorio_Turma_HelixAI_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            icon=":material/download:"
        )

    st.markdown("<hr style='margin: 0.5rem 0 1.2rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "Visão Geral & Ranking de Tópicos",
        "Análise Individual do Aluno",
        "Admin & Limpeza de Dados"
    ])

    # =========================================================================
    # TAB 1: VISÃO GERAL & RANKING DE CATEGORIAS (COM DRILLDOWN)
    # =========================================================================
    with tab1:
        # KPIs Principais
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            st.metric("Alunos Cadastrados", f"{len(student_users)}")
        with kpi2:
            st.metric("Respostas Submetidas", f"{total_answered_cases}")
        with kpi3:
            acc_class = (total_correct_cases / total_answered_cases * 100) if total_answered_cases > 0 else 0.0
            st.metric("Taxa Geral de Acertos", f"{acc_class:.1f}%")
        with kpi4:
            avg_time = (total_time_seconds / total_answered_cases) if total_answered_cases > 0 else 0.0
            st.metric("Tempo Médio / Questão", format_duration(avg_time))
        with kpi5:
            st.metric("Mensagens com Tutor", f"{total_chat_messages}")

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        st.markdown("### <span class='material-icons-outlined' style='font-size:22px; vertical-align:middle; color:#10b981;'>leaderboard</span> Ranking de Desempenho por Categoria (T1 a T8)", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.88rem; color:#64748b;'>Clique em qualquer tópico para ver o detalhamento específico de cada questão e os distratores mais assinalados.</p>", unsafe_allow_html=True)

        ranked_cats = sorted(
            category_stats.values(),
            key=lambda x: (x['correct_attempts'] / x['total_attempts'] * 100) if x['total_attempts'] > 0 else 0.0
        )

        for pos, c in enumerate(ranked_cats, 1):
            tot = c["total_attempts"]
            corr = c["correct_attempts"]
            rate = (corr / tot * 100) if tot > 0 else 0.0
            
            badge_color = "#10b981" if rate >= 70 else ("#f59e0b" if rate >= 40 else "#ef4444")
            
            with st.expander(f"**{pos}º Lugar** — `{c['topico_id']}` {c['topico_nome']}  |  **Taxa de Acerto:** {rate:.1f}% ({corr}/{tot})"):
                col_c1, col_c2, col_c3 = st.columns([1.5, 1, 1])
                with col_c1:
                    st.progress(rate / 100.0)
                with col_c2:
                    st.markdown(f"**Tentativas:** {tot} | **Acertos:** {corr}")
                with col_c3:
                    avg_dur_cat = (c["total_duration"] / tot) if tot > 0 else 0.0
                    st.markdown(f"**Tempo Médio:** {format_duration(avg_dur_cat)}")
                    
                st.markdown("---")
                st.markdown(f"#### <span class='material-icons-outlined' style='font-size:18px; vertical-align:middle;'>search</span> Questões Específicas do Tópico `{c['topico_id']}`:", unsafe_allow_html=True)
                
                q_list = list(c["questions"].values())
                for q in q_list:
                    q_tot = q["total_attempts"]
                    q_corr = q["correct_attempts"]
                    q_rate = (q_corr / q_tot * 100) if q_tot > 0 else 0.0
                    
                    diff_color_q = "#10b981" if q["dificuldade"] == "Fácil" else ("#f59e0b" if q["dificuldade"] == "Média" else "#ef4444")
                    diff_tag = f"<span style='display:inline-block; width:7px; height:7px; border-radius:50%; background:{diff_color_q}; margin-right:4px;'></span> {q['dificuldade']}"
                    
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <b>{q['codigo']} ({diff_tag})</b>
                            <span style='font-weight:700; color:{badge_color};'>Taxa de Acerto: {q_rate:.1f}% ({q_corr}/{q_tot} tentativas)</span>
                        </div>
                        <div style='margin: 0.5rem 0; font-size: 0.95rem; color: var(--text-color);'>
                            {q['pergunta']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"<span class='material-icons-outlined' style='font-size:16px; vertical-align:middle; color:#10b981;'>check_circle</span> <b>Gabarito Oficial:</b> Alternativa <b>{q['gabarito']}</b> — *{q['alternativas'].get(q['gabarito'], '')}*", unsafe_allow_html=True)
                        
                        if q_tot > 0:
                            st.markdown("**Distribuição das Escolhas dos Alunos:**")
                            cols_opt = st.columns(4)
                            for idx_o, opt_k in enumerate(["A", "B", "C", "D"]):
                                cnt = q["choices_count"].get(opt_k, 0)
                                is_gab = (opt_k == q["gabarito"])
                                with cols_opt[idx_o]:
                                    star_tag = "<span class='material-icons-outlined' style='font-size:14px; vertical-align:middle; color:#10b981;'>star</span> " if is_gab else ""
                                    st.markdown(f"{star_tag}<b>Opção {opt_k}:</b> {cnt} aluno(s)", unsafe_allow_html=True)
                                    
                        with st.expander("Ver Análise de Distratores / Erros Conceituais desta Questão"):
                            for opt_k, dist_txt in q["distratores"].items():
                                if opt_k != q["gabarito"]:
                                    st.markdown(f"<span class='material-icons-outlined' style='font-size:14px; vertical-align:middle; color:#ef4444;'>close</span> <b>Distrator {opt_k}:</b> {dist_txt}", unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: ANÁLISE INDIVIDUAL DO ALUNO
    # =========================================================================
    with tab2:
        if not student_users:
            st.info("Nenhum aluno cadastrado no sistema ainda.")
        else:
            student_names = [f"{s.get('name', 'Aluno')} | RA: {s.get('ra', 'N/A')} | Turma: {s.get('turma', 'N/A')} | {s.get('email', '')}" for s in student_users]
            sel_student_idx = st.selectbox("Selecione o Aluno:", range(len(student_users)), format_func=lambda i: student_names[i])
            selected_student = student_users[sel_student_idx]
            uid = selected_student["id"]
            udata = all_analytics.get(uid, {})
            cases = udata.get("case_analytics", [])
            
            student_pdf_bytes = generate_student_pdf(selected_student, udata)
            st.download_button(
                label=f"Baixar Relatório Individual ({selected_student.get('name', 'Aluno')})",
                data=student_pdf_bytes,
                file_name=f"Relatorio_{selected_student.get('ra', 'aluno')}_HelixAI.pdf",
                mime="application/pdf",
                type="secondary",
                icon=":material/download:"
            )
            
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            
            tot_s = len(cases)
            corr_s = sum(1 for c in cases if c.get("case_result", {}).get("is_correct", False) or c.get("case_result", {}).get("points_gained", 0) >= 1.0)
            acc_s = (corr_s / tot_s * 100) if tot_s > 0 else 0.0
            pts_s = sum(float(c.get("case_result", {}).get("points_gained", 0)) for c in cases)
            dur_s = sum(c.get("duration_seconds", 0) for c in cases)
            
            s_kpi1, s_kpi2, s_kpi3, s_kpi4 = st.columns(4)
            with s_kpi1:
                st.metric("Questões Respondidas", f"{tot_s}")
            with s_kpi2:
                st.metric("Taxa de Acerto", f"{acc_s:.1f}% ({corr_s}/{tot_s})")
            with s_kpi3:
                st.metric("Pontos Ganhos", f"{pts_s:.1f} pts")
            with s_kpi4:
                st.metric("Tempo Total", format_duration(dur_s))
                
            st.markdown("---")
            
            col_perf, col_chat = st.columns([1.1, 0.9], gap="large")
            
            with col_perf:
                st.markdown("### <span class='material-icons-outlined' style='font-size:20px; vertical-align:middle;'>assignment</span> Questões Respondidas pelo Aluno", unsafe_allow_html=True)
                if not cases:
                    st.info("Este aluno ainda não respondeu nenhuma questão.")
                else:
                    q_map = {q['id']: q for q in QUESTIONS}
                    for idx, c in enumerate(cases, 1):
                        cid = c.get("case_id", "")
                        q = q_map.get(cid, {})
                        res = c.get("case_result", {})
                        is_c = bool(res.get("is_correct", False) or res.get("points_gained", 0) >= 1.0)
                        dur_c = c.get("duration_seconds", 0)
                        
                        card_border = "#10b981" if is_c else "#ef4444"
                        status_tag = f"<span class='material-icons-outlined' style='font-size:16px; vertical-align:middle; color:{card_border};'>{'check_circle' if is_c else 'cancel'}</span> {'Correto (+1.0 pt)' if is_c else 'Incorreto (0.0 pt)'}"
                        
                        with st.container(border=True):
                            st.markdown(f"""
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <b>Questão {idx}: {q.get('codigo', cid)} ({q.get('topico_id', '')} - {q.get('dificuldade', '')})</b>
                                <span style='font-weight:700; color:{card_border};'>{status_tag}</span>
                            </div>
                            <div style='font-size:0.9rem; margin: 0.4rem 0;'>
                                {q.get('pergunta', '')}
                            </div>
                            <div style='font-size:0.85rem; color:#64748b;'>
                                <b>Resposta do Aluno:</b> {res.get('user_answer', 'N/A')}  |  <b>Tempo:</b> {format_duration(dur_c)}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if not is_c:
                                user_ans_str = str(res.get('user_answer', ''))
                                sel_opt = res.get("selected_option")
                                if not sel_opt and user_ans_str and user_ans_str[0] in ["A", "B", "C", "D"]:
                                    sel_opt = user_ans_str[0]
                                    
                                why_d = res.get("why_distractor")
                                # Se why_d for nulo ou incompleto (ex: "Induz ao erro comum de "), reconstrói com base na questão
                                if not why_d or why_d.strip().endswith("erro comum de") or why_d.strip().endswith("frequente de") or len(why_d.strip()) < 15:
                                    if sel_opt and q.get("distratores") and sel_opt in q["distratores"]:
                                        d_raw = q["distratores"][sel_opt]
                                        if d_raw:
                                            if d_raw.startswith("confundir") or d_raw.startswith("considerar") or d_raw.startswith("generalizar") or d_raw.startswith("assumir"):
                                                why_d = f"Induz ao erro comum de {d_raw}"
                                            else:
                                                why_d = d_raw
                                    if not why_d or len(why_d.strip()) < 10:
                                        why_d = res.get("why_wrong") or res.get("distractor_feedback") or "Esta alternativa aborda um conceito incorreto referente ao enunciado."
                                        
                                st.markdown(f"""
                                <div style='background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; padding: 8px 12px; border-radius: 4px; margin-top: 6px; font-size: 0.85rem;'>
                                    <b>Análise do Distrator (Por que induz ao erro):</b><br>{why_d}
                                </div>
                                """, unsafe_allow_html=True)

            with col_chat:
                st.markdown("### <span class='material-icons-outlined' style='font-size:20px; vertical-align:middle; color:#3b82f6;'>chat</span> Histórico com o Tutor Helix.AI", unsafe_allow_html=True)
                chat_docs = udata.get("chat_interactions", [])
                if not chat_docs:
                    st.info("Nenhuma conversa com o tutor registrada para este aluno.")
                else:
                    q_map = {q['id']: q for q in QUESTIONS}
                    for doc in chat_docs:
                        cid = doc.get("case_id", "")
                        q = q_map.get(cid, {})
                        
                        with st.expander(f"Conversa na Questão: {q.get('codigo', cid)} ({q.get('topico_id', '')})", expanded=True):
                            msgs = doc.get("messages", [])
                            if not msgs and "user_message" in doc:
                                msgs = [{"user_message": doc.get("user_message", ""), "bot_response": doc.get("bot_response", "")}]
                                
                            for m in msgs:
                                u_msg = m.get("user_message", "")
                                b_msg = m.get("bot_response", "")
                                
                                if u_msg:
                                    with st.chat_message("user"):
                                        st.markdown(u_msg)
                                if b_msg:
                                    with st.chat_message("assistant"):
                                        st.markdown(b_msg)

    # =========================================================================
    # TAB 3: ADMIN & LIMPEZA DE DADOS
    # =========================================================================
    with tab3:
        st.markdown("### <span class='material-icons-outlined' style='font-size:22px; vertical-align:middle;'>settings</span> Painel Administrativo de Manutenção", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b;'>Ferramentas para resetar dados de testes e acompanhar a infraestrutura do banco de dados.</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h4 style='color:#ef4444; margin-top:0;'><span class='material-icons-outlined' style='font-size:20px; vertical-align:middle;'>warning</span> Zona de Manutenção (Reset de Dados)</h4>", unsafe_allow_html=True)
            st.markdown("Utilize os botões abaixo para limpar dados de testes e iniciar novas rodadas com os alunos.")
            
            c_adm1, c_adm2, c_adm3 = st.columns(3)
            with c_adm1:
                if st.button("Resetar Analytics da Turma", use_container_width=True, icon=":material/delete:"):
                    res = reset_all_students_analytics()
                    log_admin_action("reset_analytics", f"Deletados {res['deleted']} registros")
                    st.success(f"Sucesso! {res['deleted']} registros de analytics removidos.")
                    st.rerun()
                    
            with c_adm2:
                if st.button("Limpar Interações de Chat", use_container_width=True, icon=":material/delete_sweep:"):
                    res = clear_all_chat_interactions()
                    log_admin_action("clear_chats", f"Deletados {res['deleted']} chats")
                    st.success(f"Sucesso! {res['deleted']} interações de chat limpas.")
                    st.rerun()
                    
            with c_adm3:
                if st.button("Resetar Progresso dos Alunos", use_container_width=True, icon=":material/restart_alt:"):
                    res = reset_all_student_progress()
                    log_admin_action("reset_progress", f"Resetados {res['updated']} alunos")
                    st.success(f"Sucesso! Progresso resetado para {res['updated']} alunos.")
                    st.rerun()
                    
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### Estatísticas do Banco de Dados")
        try:
            db_stats = get_database_stats()
            s1, s2, s3, s4 = st.columns(4)
            with s1: st.metric("Alunos Registrados", db_stats.get("total_students", 0))
            with s2: st.metric("Total de Analytics", db_stats.get("total_analytics", 0))
            with s3: st.metric("Total de Chats", db_stats.get("total_chat_interactions", 0))
            with s4: st.metric("Logs Admin", db_stats.get("total_admin_logs", 0))
        except Exception as e:
            st.info(f"Estatísticas: {e}")

