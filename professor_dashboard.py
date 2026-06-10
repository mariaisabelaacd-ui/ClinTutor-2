import streamlit as st
# Force redeploy v3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import textwrap
from io import BytesIO
from analytics import (
    get_all_users_analytics, get_global_stats,
    get_average_user_level, get_student_complete_profile,
    get_student_weakness_analysis, format_duration,
    get_user_chat_interactions, get_all_answers_by_category,
    get_question_stats, get_hardest_questions
)
from auth_firebase import get_all_users, get_user_by_id, delete_user
from logic import get_case, generate_category_insights
from admin_utils import (
    reset_student_analytics, clear_student_chat_interactions,
    reset_all_students_analytics, clear_all_chat_interactions,
    reset_all_student_progress,
    log_admin_action, get_database_stats
)
from ui_helpers import icon, metric_card


def inject_dashboard_styles():
    """Injeta estilos CSS customizados para uma visualização premium e moderna"""
    style_html = """
    <style>
        /* Custom App Background Override using Streamlit variables */
        .stApp {
            background: linear-gradient(135deg, var(--background-color) 0%, var(--secondary-background-color) 100%) !important;
            color: var(--text-color) !important;
        }

        /* Tipografia e Títulos */
        .dash-title {
            font-family: 'Inter', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        
        .dash-subtitle {
            color: var(--text-color) !important;
            opacity: 0.7 !important;
            font-size: 0.95rem !important;
            margin-bottom: 2rem !important;
        }

        /* Glassmorphism Metric Cards - Adaptable to both light and dark modes */
        .premium-card {
            background: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.15) !important;
            border-radius: 20px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        .premium-card:hover {
            transform: translateY(-5px) !important;
            border-color: rgba(16, 185, 129, 0.3) !important;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.1) !important;
        }
        
        .premium-card-label {
            color: var(--text-color) !important;
            opacity: 0.7 !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 0.75rem !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
        }
        
        .premium-card-value {
            font-size: 2.25rem !important;
            font-weight: 800 !important;
            line-height: 1.1 !important;
            color: var(--text-color) !important;
        }

        /* Question Cards (Q1-Q6) */
        .q-card-green {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.02) 100%) !important;
            border: 1px solid rgba(16, 185, 129, 0.18) !important;
        }
        .q-card-green:hover {
            border-color: rgba(16, 185, 129, 0.45) !important;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.1) !important;
        }
        
        .q-card-yellow {
            background: linear-gradient(135deg, rgba(234, 179, 8, 0.08) 0%, rgba(234, 179, 8, 0.02) 100%) !important;
            border: 1px solid rgba(234, 179, 8, 0.18) !important;
        }
        .q-card-yellow:hover {
            border-color: rgba(234, 179, 8, 0.45) !important;
            box-shadow: 0 10px 25px rgba(234, 179, 8, 0.1) !important;
        }
        
        .q-card-red {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(239, 68, 68, 0.02) 100%) !important;
            border: 1px solid rgba(239, 68, 68, 0.18) !important;
        }
        .q-card-red:hover {
            border-color: rgba(239, 68, 68, 0.45) !important;
            box-shadow: 0 10px 25px rgba(239, 68, 68, 0.1) !important;
        }
        
        .q-card {
            border-radius: 20px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            margin-bottom: 1.5rem !important;
        }
        
        .q-card:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08) !important;
        }

        /* Progress Bar */
        .q-progress-bg {
            background: rgba(128, 128, 128, 0.1) !important;
            border-radius: 10px !important;
            height: 24px !important;
            overflow: hidden !important;
            margin-bottom: 0.75rem !important;
            border: 1px solid rgba(128, 128, 128, 0.05) !important;
        }
        
        .q-progress-bar {
            height: 100% !important;
            border-radius: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            padding-right: 10px !important;
            box-shadow: 0 0 12px rgba(255, 255, 255, 0.1) !important;
        }

        /* Timeline and Student Profiles */
        .student-profile-banner {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, rgba(59, 130, 246, 0.06) 100%) !important;
            border: 1px solid rgba(128, 128, 128, 0.15) !important;
            border-radius: 20px !important;
            padding: 1.5rem !important;
            margin-bottom: 2.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        }

        .chat-bubble-container {
            background: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.12) !important;
            border-radius: 14px !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
            transition: all 0.25s ease !important;
        }
        
        .chat-bubble-container:hover {
            border-color: rgba(139, 92, 246, 0.3) !important;
            background: rgba(139, 92, 246, 0.03) !important;
        }

        /* Danger Zone Block */
        .danger-zone-container {
            background: linear-gradient(135deg, rgba(244, 63, 94, 0.06) 0%, rgba(244, 63, 94, 0.01) 100%) !important;
            border: 1px solid rgba(244, 63, 94, 0.2) !important;
            border-radius: 20px !important;
            padding: 1.5rem !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 4px 12px rgba(244, 63, 94, 0.03) !important;
        }

        /* Form inputs & select boxes styling overrides for dark theme */
        div[data-baseweb="select"] > div {
            background-color: var(--secondary-background-color) !important;
            border-color: rgba(128, 128, 128, 0.15) !important;
            color: var(--text-color) !important;
        }

        div[data-baseweb="select"] > div:hover {
            border-color: #10b981 !important;
        }

        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
            background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border-color: rgba(128, 128, 128, 0.15) !important;
        }

        /* Tables and Dataframes */
        div[data-testid="stDataFrame"] {
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.15) !important;
            border-radius: 16px !important;
        }

        /* Expander headers */
        .streamlit-expanderHeader {
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.15) !important;
            color: var(--text-color) !important;
        }

        /* Custom Chat bubbles styling */
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 20px;
            border-radius: 16px;
            background: var(--background-color);
            border: 1px solid rgba(128, 128, 128, 0.15);
            max-height: 600px;
            overflow-y: auto;
            margin-bottom: 20px;
        }

        .chat-message-row {
            display: flex;
            width: 100%;
            margin-bottom: 4px;
        }

        .chat-message-row.student-row {
            justify-content: flex-end;
        }

        .chat-message-row.tutor-row {
            justify-content: flex-start;
        }

        .chat-bubble {
            max-width: 80%;
            padding: 12px 18px;
            border-radius: 20px;
            font-size: 0.95rem;
            line-height: 1.5;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            position: relative;
        }

        .student-bubble {
            background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%) !important;
            color: #ffffff !important;
            border-bottom-right-radius: 4px;
        }
        
        .student-bubble * {
            color: #ffffff !important;
        }

        .tutor-bubble {
            background: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border-bottom-left-radius: 4px;
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
        }

        .chat-message-info {
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .student-bubble .chat-message-info {
            color: rgba(255, 255, 255, 0.8) !important;
        }

        .tutor-bubble .chat-message-info {
            color: #10b981 !important;
        }
    </style>
    """
    st.markdown(style_html, unsafe_allow_html=True)


def draw_premium_metric_card(label: str, value: str, icon_name: str, icon_color: str, subtitle: str = None):
    icon_html = icon(icon_name, icon_color, 20) if icon_name else ""
    subtitle_html = f"<div style='color: #64748b; font-size: 0.8rem; margin-top: 0.25rem;'>{subtitle}</div>" if subtitle else ""
    card_html = f"""
        <div class="premium-card">
            <div class="premium-card-label">
                {icon_html} <span>{label}</span>
            </div>
            <div class="premium-card-value" style="color: {icon_color};">
                {value}
            </div>
            {subtitle_html}
        </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def generate_student_pdf(student: Dict, basic_stats: Dict, advanced_stats: Dict, 
                         weakness: Dict, history_entries: list) -> bytes:
    """Gera um PDF com o resumo completo do aluno"""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # ---- CABEÇALHO ----
    pdf.set_fill_color(16, 185, 129)  # verde primário
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, 'Helix.AI', ln=True, align='C')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, 'Relatorio do Aluno', ln=True, align='C')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 7, f'Gerado em {datetime.now().strftime("%d/%m/%Y as %H:%M")}', ln=True, align='C')
    pdf.ln(10)
    
    # ---- INFO DO ALUNO ----
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(240, 253, 244)  # verde claro
    pdf.set_draw_color(16, 185, 129)
    pdf.rect(10, pdf.get_y(), 190, 30, 'DF')
    y_info = pdf.get_y() + 3
    
    pdf.set_xy(15, y_info)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(25, 6, 'Nome:', 0, 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(65, 6, student.get('name', 'N/A'), 0, 0)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(15, 6, 'RA:', 0, 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, student.get('ra', 'N/A'), 0, 1)
    
    pdf.set_x(15)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(25, 6, 'Turma:', 0, 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(65, 6, student.get('turma', 'Nao informada'), 0, 0)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(15, 6, 'Email:', 0, 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, student.get('email', 'N/A'), 0, 1)
    
    pdf.ln(12)
    
    # ---- DESEMPENHO GERAL ----
    case_stats = basic_stats.get('case_stats', {})
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 10, 'Desempenho Geral', ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Tabela de métricas
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_fill_color(241, 245, 249)
    col_w = 38
    headers = ['Questoes', 'Pontos (Media)', 'Nivel', 'Tempo Medio', 'Pontos Totais']
    for h in headers:
        pdf.cell(col_w, 8, h, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 9)
    total = case_stats.get('total_cases', 0)
    acc = case_stats.get('accuracy_rate', 0)
    nivel = advanced_stats.get('nivel_estimado', 'N/A') if advanced_stats else 'N/A'
    avg_time = format_duration(case_stats.get('avg_time_per_case', 0))
    # Calcular media de pontos baseada no historico
    total_max_points = 0.0
    points_received = 0.0
    for item in history_entries:
        pts = float(item.get('Pontos', 0))
        points_received += pts
        # Tenta descobrir o maximo da questao
        q_text = item.get('Questao', '')
        # Simplificação: se pts > 3 ou a questao nao esta no novo set, assume 5
        # Mas melhor usar a lista QUESTIONS de logic.py
        from logic import QUESTIONS
        q_obj = next((q for q in QUESTIONS if q['pergunta'][:30] in q_text), None)
        total_max_points += q_obj.get('pontuacao_maxima', 5.0) if q_obj else 5.0

    avg_points = (points_received / total) if total > 0 else 0
    max_label = (total_max_points / total) if total > 0 else 5.0
    values = [str(total), f'{avg_points:.1f} / {max_label:.1f}', str(nivel), avg_time, f'{points_received:.1f}']
    for v in values:
        pdf.cell(col_w, 8, v, 1, 0, 'C')
    pdf.ln(12)
    
    # ---- DESEMPENHO POR COMPONENTE ----
    comp_stats = basic_stats.get('component_stats', {})
    if comp_stats:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 10, 'Desempenho por Componente', ln=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(80, 8, 'Componente', 1, 0, 'C', True)
        pdf.cell(30, 8, 'Total', 1, 0, 'C', True)
        pdf.cell(30, 8, 'Corretas', 1, 0, 'C', True)
        pdf.cell(30, 8, 'Taxa', 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_font('Helvetica', '', 9)
        for comp_name, comp_data in comp_stats.items():
            total_c = comp_data.get('total', 0)
            correct_c = comp_data.get('correct', 0)
            rate = (correct_c / total_c * 100) if total_c > 0 else 0
            display_name = comp_name[:40] if len(comp_name) > 40 else comp_name
            pdf.cell(80, 7, display_name, 1, 0, 'L')
            pdf.cell(30, 7, str(total_c), 1, 0, 'C')
            pdf.cell(30, 7, str(correct_c), 1, 0, 'C')
            # Media local do componente: 'correct_c' já é a soma de acertos. Dividido pelas questoes desse comp.
            # Cada componente avalia de 0.0 a 1.0 (Ausente a Completa). Entao a media ali ja e uma nota fracionada do componente especifico
            comp_avg = (correct_c / total_c) if total_c > 0 else 0
            pdf.cell(30, 7, f'{comp_avg:.1f} / 1.0', 1, 0, 'C')
            pdf.ln()
        pdf.ln(8)
    
    # ---- ANÁLISE DE FRAQUEZAS ----
    weak_comps = weakness.get('componentes_problematicos', [])
    if weak_comps:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(239, 68, 68)  # vermelho
        pdf.cell(0, 10, 'Pontos Fracos Identificados', ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        for i, comp in enumerate(weak_comps[:5], 1):
            name = comp.get('nome', 'N/A')
            acuracia = comp.get('acuracia', 0.0)
            # Mostrando a defasagem (quantos pontos perderam de 1.0)
            avg_lost = 1.0 - (acuracia / 100.0)
            pdf.cell(0, 6, f'  {i}. {name} (perde em media {avg_lost:.2f} pts por questao)', ln=True)
        pdf.ln(5)
    
    # ---- HISTÓRICO DE RESPOSTAS ----
    if history_entries:
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 10, 'Historico de Respostas', ln=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(30, 7, 'Data', 1, 0, 'C', True)
        pdf.cell(65, 7, 'Questao', 1, 0, 'C', True)
        pdf.cell(35, 7, 'Componente', 1, 0, 'C', True)
        pdf.cell(20, 7, 'Status', 1, 0, 'C', True)
        pdf.cell(20, 7, 'Tempo', 1, 0, 'C', True)
        pdf.cell(20, 7, 'Pontos', 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_font('Helvetica', '', 7)
        for item in history_entries[:50]:  # limita a 50 entries
            date_str = item.get('Data', '')
            
            def safe_text(txt):
                if not txt: return ""
                return str(txt).encode('latin-1', 'replace').decode('latin-1')
            
            q_text = safe_text(item.get('Questao', ''))[:35]
            comp = safe_text(item.get('Componente', ''))[:18]
            status = safe_text(item.get('Status', ''))
            tempo = safe_text(item.get('Tempo', ''))
            pts = safe_text(item.get('Pontos', 0))
            ans_text = safe_text(item.get('Resposta do Aluno', '')) # A chave mudou em professor_dashboard_new.py
            ia_feedback = safe_text(item.get('Feedback da IA', ''))
            
            # Cor por status
            if status == 'Correto' or status == 'Correta':
                pdf.set_fill_color(220, 252, 231)
            elif status == 'Parcial':
                pdf.set_fill_color(254, 249, 195)
            else:
                pdf.set_fill_color(254, 226, 226)
            
            pdf.cell(30, 6, date_str, 1, 0, 'C')
            pdf.cell(65, 6, q_text, 1, 0, 'L')
            pdf.cell(35, 6, comp, 1, 0, 'C')
            pdf.cell(20, 6, status, 1, 0, 'C', True)
            pdf.cell(20, 6, tempo, 1, 0, 'C')
            pdf.cell(20, 6, pts, 1, 0, 'C')
            pdf.ln()
            
            # Sub-linha da Resposta do Aluno
            if ans_text and ans_text.lower() != 'n/a':
                pdf.set_font('Helvetica', 'I', 7)
                pdf.set_text_color(80, 80, 80)
                pdf.set_x(40) # margin is at 10, shift right by 30
                pdf.multi_cell(160, 5, f'Resposta do Aluno: {ans_text}', border=0, fill=False)
                
            # Sub-linha do Feedback da IA
            if ia_feedback and ia_feedback.lower() != 'n/a':
                pdf.set_font('Helvetica', 'I', 7)
                pdf.set_text_color(139, 92, 246) # Roxo IA
                pdf.set_x(40)
                pdf.multi_cell(160, 5, f'Avaliacao da IA: {ia_feedback}', border=0, fill=False)
                
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', '', 7)
            # FIX: reset X to default margin (10) so the next table row is not offset
            pdf.set_x(10)
    
    # Rodapé
    pdf.set_y(-15)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, 'Helix.AI - Plataforma de Tutoria em Biologia Molecular', 0, 0, 'C')
    
    return bytes(pdf.output())

def generate_class_pdf(turma_name: str, student_users: List[Dict], global_stats: Dict, question_stats: list) -> bytes:
    """Gera um PDF com a visao geral da turma - versao completa"""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    W = 185

    def safe_text(txt):
        if not txt: return ""
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # ---- CABECALHO ----
    pdf.set_fill_color(16, 185, 129)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, 'Helix.AI', ln=True, align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, safe_text(f'Relatorio da Turma: {turma_name}'), ln=True, align='C')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 7, f'Gerado em {datetime.now().strftime("%d/%m/%Y as %H:%M")}', ln=True, align='C')
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)

    # ---- METRICAS GLOBAIS ----
    pdf.set_fill_color(16, 185, 129)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(W, 7, '  Metricas Gerais da Turma', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('Helvetica', 'B', 9)
    col4 = W / 4
    for h in ['Total de Alunos', 'Media Geral (%)', 'Questoes Respondidas', 'Total de Chats']:
        pdf.cell(col4, 7, h, 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(col4, 8, str(len(student_users)), 1, 0, 'C')
    pdf.cell(col4, 8, f"{global_stats.get('average_accuracy_rate', 0):.1f}%", 1, 0, 'C')
    pdf.cell(col4, 8, str(global_stats.get('total_cases', 0)), 1, 0, 'C')
    pdf.cell(col4, 8, str(global_stats.get('total_chat_interactions', 0)), 1, 0, 'C')
    pdf.ln(12)

    # ---- DESEMPENHO POR QUESTAO (ordenado: pior primeiro) ----
    if question_stats:
        # Ordena por taxa de acerto (pior primeiro)
        sorted_qs = sorted(question_stats, key=lambda x: x.get('taxa_acerto', 0))
        hardest = sorted_qs[0] if sorted_qs else None

        # Destaque da questão mais difícil
        if hardest:
            pdf.set_fill_color(254, 226, 226)
            pdf.set_draw_color(220, 38, 38)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(W, 7, safe_text(f'  Questao Mais Dificil: Questao {hardest["questao_num"]}  —  Taxa de acerto: {hardest["taxa_acerto"]:.1f}%'), 1, 1, 'L', True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(3)

        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(W, 7, '  Desempenho por Questao (do mais dificil ao mais facil)', ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        # Header da tabela
        pdf.set_draw_color(226, 232, 240)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(80, 7, 'Questao / Topico', 1, 0, 'C', True)
        pdf.cell(25, 7, 'Tentativas', 1, 0, 'C', True)
        pdf.cell(25, 7, 'Acertos (Estim.)', 1, 0, 'C', True)
        pdf.cell(30, 7, 'Tempo Medio', 1, 0, 'C', True)
        pdf.cell(25, 7, 'Taxa (%)', 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font('Helvetica', '', 8)
        for i, q in enumerate(sorted_qs):
            taxa = q.get('taxa_acerto', 0)
            total = q.get('total_respostas', 0)
            acertos_estim = (taxa / 100) * total
            titulo = safe_text(f'Questao {q["questao_num"]}: {q["titulo"][:45]}')
            tempo = safe_text(q.get('tempo_medio_formatado', '0s'))

            # Alternating background for general cells
            if i % 2 == 0:
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(248, 250, 252)

            pdf.set_text_color(51, 65, 85)
            pdf.set_draw_color(226, 232, 240)

            pdf.cell(80, 6, titulo, 1, 0, 'L', True)
            pdf.cell(25, 6, str(total), 1, 0, 'C', True)
            
            # Format acertos_estim to 1 decimal place
            acertos_estim_str = f"{acertos_estim:.1f}" if acertos_estim % 1 != 0 else f"{int(acertos_estim)}"
            pdf.cell(25, 6, acertos_estim_str, 1, 0, 'C', True)
            pdf.cell(30, 6, tempo, 1, 0, 'C', True)

            # Badge cell for Taxa (%)
            if taxa >= 70:
                pdf.set_fill_color(220, 252, 231)
                pdf.set_text_color(22, 101, 52)
            elif taxa >= 40:
                pdf.set_fill_color(254, 249, 195)
                pdf.set_text_color(133, 77, 14)
            else:
                pdf.set_fill_color(254, 226, 226)
                pdf.set_text_color(153, 27, 27)

            pdf.cell(25, 6, f"{taxa:.1f}%", 1, 0, 'C', True)
            pdf.ln()
        pdf.ln(8)

    # Ranking de alunos removido por solicitação de repaginação do dashboard.
    pass

    pdf.set_y(-15)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, 'Helix.AI - Plataforma de Tutoria em Biologia Molecular', 0, 0, 'C')

    return bytes(pdf.output())

def generate_global_interactions_pdf(student_users: List[Dict], all_analytics: Dict) -> bytes:
    """Gera PDF completo com todas as interacoes e respostas de todos os alunos"""
    from fpdf import FPDF
    from logic import get_case, level_from_score

    pdf = FPDF()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=15)
    W = 185

    def safe(txt):
        if txt is None: return ""
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # ── CAPA ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(16, 185, 129)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_y(90)
    pdf.set_font('Helvetica', 'B', 36)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, 'Helix.AI', ln=True, align='C')
    pdf.set_font('Helvetica', '', 16)
    pdf.cell(0, 12, 'Relatorio Completo de Interacoes', ln=True, align='C')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 8, f'Gerado em {datetime.now().strftime("%d/%m/%Y as %H:%M")}', ln=True, align='C')
    total_ativos = len([s for s in student_users if all_analytics.get(s['id'], {}).get('case_analytics')])
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, safe(f'{total_ativos} aluno(s) com atividade'), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)

    nivel_map = {1: 'Basico', 2: 'Intermediario', 3: 'Avancado'}

    for student in student_users:
        uid = student['id']
        u_data = all_analytics.get(uid, {})
        case_list = u_data.get('case_analytics', [])
        if not case_list:
            continue

        # ── Calcula stats do aluno ───────────────────────────────
        total_q  = len(case_list)
        correct_full_q = sum(1 for e in case_list if e.get('case_result', {}).get('outcome') == 'correct' or (e.get('case_result', {}).get('is_correct', False) and 'PARCIAL' not in e.get('case_result', {}).get('classification', '').upper()))
        parcial_q = sum(1 for e in case_list if 'PARCIAL' in e.get('case_result', {}).get('classification', '').upper())
        errado_q  = total_q - (correct_full_q + parcial_q)
        total_pts = sum(e.get('case_result', {}).get('points_gained', 0) for e in case_list)
        
        total_possible = 0.0
        from logic import get_case
        for e in case_list:
            q_info = get_case(e.get('case_id'))
            total_possible += q_info.get('pontuacao_maxima', 5.0)

        accuracy  = (total_pts / total_possible * 100) if total_possible > 0 else 0.0
        correct_q = total_pts / (total_possible / total_q) if total_q > 0 and total_possible > 0 else 0.0
        nivel_txt = nivel_map.get(level_from_score(int(total_pts)), 'Basico')
        total_ch  = len(u_data.get('chat_interactions', []))

        # ── PAGINA DO ALUNO ──────────────────────────────────────
        pdf.add_page()

        # Cabecalho verde com nome
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_x(10)
        pdf.cell(W, 10, safe('  ' + student.get('name', 'N/A')), ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        # Card de identificacao
        pdf.set_fill_color(240, 253, 244)
        pdf.set_draw_color(16, 185, 129)
        card_y = pdf.get_y()
        pdf.rect(10, card_y, W, 20, 'DF')
        pdf.set_x(13)
        pdf.set_font('Helvetica', 'B', 8)  ;  pdf.cell(18, 5, 'RA:', 0, 0)
        pdf.set_font('Helvetica', '', 8)   ;  pdf.cell(40, 5, safe(student.get('ra', 'N/A')), 0, 0)
        pdf.set_font('Helvetica', 'B', 8)  ;  pdf.cell(20, 5, 'Turma:', 0, 0)
        pdf.set_font('Helvetica', '', 8)   ;  pdf.cell(0,  5, safe(student.get('turma', 'N/A')), 0, 1)
        pdf.set_x(13)
        pdf.set_font('Helvetica', 'B', 8)  ;  pdf.cell(18, 5, 'Email:', 0, 0)
        pdf.set_font('Helvetica', '', 8)   ;  pdf.cell(0,  5, safe(student.get('email', 'N/A')), 0, 1)
        pdf.set_x(13)
        pdf.set_font('Helvetica', 'B', 8)  ;  pdf.cell(18, 5, 'Nivel:', 0, 0)
        pdf.set_font('Helvetica', '', 8)   ;  pdf.cell(40, 5, nivel_txt, 0, 0)
        pdf.set_font('Helvetica', 'B', 8)  ;  pdf.cell(25, 5, 'Pontos Total:', 0, 0)
        pdf.set_font('Helvetica', '', 8)   ;  pdf.cell(0,  5, str(total_pts), 0, 1)
        pdf.set_draw_color(0, 0, 0)
        pdf.ln(4)

        # Tabela-resumo de desempenho
        pdf.set_draw_color(226, 232, 240)
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font('Helvetica', 'B', 8)
        col = W / 5
        for h in ['Questoes', 'Taxa Acerto', 'Corretas', 'Parciais', 'Erradas']:
            pdf.cell(col, 6, h, 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_text_color(51, 65, 85)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(col, 7, str(total_q),  1, 0, 'C')
        
        # Soft badge coloring for accuracy
        if accuracy >= 70:
            pdf.set_fill_color(220, 252, 231)
            pdf.set_text_color(22, 101, 52)
        elif accuracy >= 40:
            pdf.set_fill_color(254, 249, 195)
            pdf.set_text_color(133, 77, 14)
        else:
            pdf.set_fill_color(254, 226, 226)
            pdf.set_text_color(153, 27, 27)
        pdf.cell(col, 7, f'{accuracy:.1f}%', 1, 0, 'C', True)
        
        pdf.set_text_color(51, 65, 85)
        correct_q_str = f"{correct_q:.1f}" if correct_q % 1 != 0 else f"{int(correct_q)}"
        pdf.cell(col, 7, correct_q_str, 1, 0, 'C')
        pdf.cell(col, 7, str(parcial_q), 1, 0, 'C')
        pdf.cell(col, 7, str(errado_q),  1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

        # Secao de questoes
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(W, 6, '  Historico de Questoes e Interacoes', ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        try:
            case_list.sort(key=lambda x: str(x.get('timestamp', '')))
        except Exception:
            pass

        for idx, entry in enumerate(case_list, 1):
            cid    = entry.get('case_id')
            q_info = get_case(cid)
            result = entry.get('case_result', {})

            is_correct = result.get('is_correct', False)
            is_partial = 'PARCIAL' in result.get('classification', '').upper()
            status_txt = 'Correto' if (is_correct and not is_partial) else ('Parcial' if is_partial else 'Incorreto')
            pts = result.get('points_gained', 0)

            ts = entry.get('timestamp', '')
            date_str = ''
            if isinstance(ts, str):
                try:   date_str = datetime.fromisoformat(ts).strftime('%d/%m/%Y %H:%M')
                except: date_str = ts[:16]

            if status_txt == 'Correto':  status_color = (22, 163, 74)
            elif status_txt == 'Parcial': status_color = (202, 138, 4)
            else:                          status_color = (220, 38, 38)

            # Cabecalho da questao
            pdf.set_x(10)
            pdf.set_fill_color(230, 230, 235)
            pdf.set_font('Helvetica', 'B', 9)
            comps = ', '.join(q_info.get('componentes_conhecimento', []))
            diff = q_info.get('dificuldade', 'N/A').title()
            header_txt = safe(f'  [{idx}] {date_str}  |  {diff}  |  {comps}')
            pdf.cell(W, 6, header_txt, 1, 1, 'L', True)

            pdf.set_x(10)
            pdf.set_font('Helvetica', '', 8)
            pdf.multi_cell(W, 5, safe(q_info.get('pergunta', 'N/A')))

            # Barra status
            pdf.set_x(10)
            pdf.set_fill_color(*status_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 8)
            
            # Mostra o nível no status
            level_label = result.get('level', status_txt)
            pdf.cell(W, 6, safe(f'  Nivel: {level_label}   |   Pontos ganhos: {pts}'), 0, 1, 'L', True)
            pdf.set_text_color(0, 0, 0)

            # Resposta do aluno e Feedback da IA
            ans = result.get('user_answer', 'N/A')
            fbk = result.get('feedback', '')
            pdf.set_x(10)
            pdf.set_fill_color(237, 242, 255)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(W, 5, '  Resposta do Aluno:', 0, 1, 'L', True)
            pdf.set_x(10)
            pdf.set_font('Helvetica', '', 8)
            pdf.multi_cell(W, 5, safe(str(ans) if ans else 'Nao respondeu'))

            if fbk and fbk.upper() != 'N/A':
                pdf.set_x(10)
                pdf.set_fill_color(243, 232, 255)
                pdf.set_font('Helvetica', 'B', 8)
                pdf.cell(W, 5, '  Feedback da IA:', 0, 1, 'L', True)
                pdf.set_x(10)
                pdf.set_font('Helvetica', 'I', 8)
                pdf.set_text_color(139, 92, 246)
                pdf.multi_cell(W, 5, safe(fbk))
                pdf.set_text_color(0, 0, 0)

            # Chat desta questao
            chats = get_user_chat_interactions(uid, cid)
            if chats:
                try:
                    chats.sort(key=lambda x: str(x.get('timestamp', '')))
                except Exception:
                    pass

                pdf.set_x(10)
                pdf.set_fill_color(253, 242, 248)
                pdf.set_font('Helvetica', 'B', 8)
                pdf.cell(W, 5, safe(f'  Chat com o Tutor ({len(chats)} mensagens):'), 0, 1, 'L', True)

                for chat in chats:
                    u_msg = safe(chat.get('user_message', ''))
                    b_msg = safe(chat.get('bot_response',  ''))

                    # Aluno
                    pdf.set_x(10)
                    pdf.set_fill_color(219, 234, 254)
                    pdf.set_font('Helvetica', 'B', 7)
                    pdf.cell(W, 5, '  Aluno:', 0, 1, 'L', True)
                    pdf.set_x(14)
                    pdf.set_font('Helvetica', '', 7)
                    pdf.multi_cell(W - 4, 5, u_msg)

                    # Tutor
                    pdf.set_x(10)
                    pdf.set_fill_color(240, 253, 244)
                    pdf.set_font('Helvetica', 'B', 7)
                    pdf.cell(W, 5, '  Tutor:', 0, 1, 'L', True)
                    pdf.set_x(14)
                    pdf.set_font('Helvetica', 'I', 7)
                    pdf.multi_cell(W - 4, 5, b_msg)
                    pdf.ln(1)

            pdf.ln(5)

    pdf.set_y(-15)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, 'Helix.AI - Plataforma de Tutoria em Biologia Molecular', 0, 0, 'C')

    return bytes(pdf.output())


def generate_ai_insights_pdf(hardest_questions: List[Dict]) -> bytes:
    """Gera PDF com análise pedagógica profunda baseada em IA para as 6 questões"""
    from fpdf import FPDF
    from logic import QUESTIONS as ALL_QUESTIONS, generate_category_insights
    from analytics import get_all_users_analytics_firebase
    
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    W = 180

    def safe(txt):
        if txt is None: return ""
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # ── CAPA ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(139, 92, 246)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_y(80)
    
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, 'Helix.AI', ln=True, align='C')
    
    pdf.set_font('Helvetica', '', 18)
    pdf.cell(0, 12, 'Relatorio Pedagogico - Analise de IA', ln=True, align='C')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 8, f'Gerado em {datetime.now().strftime("%d/%m/%Y as %H:%M")}', ln=True, align='C')
    
    pdf.set_y(150)
    pdf.set_font('Helvetica', 'I', 11)
    texto_capa = "Este relatorio contem uma analise automatizada gerada por Inteligencia Artificial " \
                 "cobrindo o desempenho geral da turma nas 6 questoes fundamentais de Biologia Molecular, " \
                 "baseado em amostras de todas as respostas enviadas."
    pdf.multi_cell(0, 6, safe(texto_capa), align='C')
    pdf.set_text_color(0, 0, 0)
    
    # ── COLETA DE RESPOSTAS POR QUESTÃO ──────────────────────────
    all_analytics_raw = get_all_users_analytics_firebase()
    
    # Organiza respostas por questão (1-6)
    answers_by_question = {i+1: [] for i in range(len(ALL_QUESTIONS))}
    
    for uid, data in all_analytics_raw.items():
        for case in data.get('case_analytics', []):
            cid = case.get('case_id', '')
            result = case.get('case_result', {})
            user_answer = result.get('user_answer', '')
            level = result.get('level', result.get('classification', '')).upper()
            points = result.get('points_gained', 0)
            
            q_idx = next((i for i, q in enumerate(ALL_QUESTIONS) if q['id'] == cid), None)
            if q_idx is not None and user_answer:
                answers_by_question[q_idx + 1].append({
                    'answer': user_answer,
                    'level': level,
                    'points': float(points),
                    'feedback': result.get('feedback', '')
                })
    
    # ── CONTEÚDO: ANÁLISE POR QUESTÃO ────────────────────────────
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(139, 92, 246)
    pdf.cell(0, 10, 'Analise Detalhada por Questao (1 a 6)', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, safe('Cada questao e analisada individualmente com base nas respostas dos alunos. A IA identifica padroes de erro e sugere intervencoes pedagogicas.'))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Mapeia questão -> stats do hardest_questions
    q_stats_map = {q['questao_num']: q for q in hardest_questions} if hardest_questions else {}
    
    for q_num in range(1, len(ALL_QUESTIONS) + 1):
        q_data = ALL_QUESTIONS[q_num - 1]
        q_title = q_data['pergunta'][:120]
        answers = answers_by_question.get(q_num, [])
        stats = q_stats_map.get(q_num, {})
        taxa = stats.get('taxa_acerto', 0)
        total = stats.get('total_respostas', len(answers))
        
        # Header da questão
        if taxa < 45:
            pdf.set_fill_color(254, 226, 226)
        elif taxa < 75:
            pdf.set_fill_color(254, 249, 195)
        else:
            pdf.set_fill_color(220, 252, 231)
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, safe(f"  Questao {q_num}: {q_title[:80]}..."), ln=True, fill=True)
        pdf.ln(3)
        
        # Estatísticas rápidas
        if answers:
            avancado = sum(1 for a in answers if 'AVANCADO' in a['level'] or 'AVANÇADO' in a['level'])
            medio = sum(1 for a in answers if 'MEDIO' in a['level'] or 'MÉDIO' in a['level'])
            basico = sum(1 for a in answers if 'BASICO' in a['level'] or 'BÁSICO' in a['level'])
            parcial = sum(1 for a in answers if 'PARCIAL' in a['level'])
            incorreto = sum(1 for a in answers if 'INCORRETO' in a['level'])
            
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, safe(f'  Respostas: {total} | Taxa: {taxa:.1f}% | Avancado: {avancado} | Medio: {medio} | Basico: {basico} | Parcial: {parcial} | Incorreto: {incorreto}'), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
        
        # Gera análise com IA
        sample_answers = [a['answer'] for a in answers[:15]]
        q_topic = f"Questao {q_num}: {q_title[:80]}"
        insight_text = generate_category_insights(q_topic, sample_answers)
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(139, 92, 246)
        pdf.cell(0, 6, 'Analise Pedagogica:', ln=True)
        pdf.set_text_color(80, 80, 80)
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 5, safe(insight_text))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
        
        # Exemplos de respostas com falhas
        failing = [a for a in answers if a['level'] in ['INCORRETO', 'PARCIAL']]
        if failing:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(0, 6, safe(f'Exemplos de respostas com dificuldade ({min(len(failing), 3)} de {len(failing)}):'), ln=True)
            pdf.set_text_color(0, 0, 0)
            
            for ex in failing[:3]:
                if 'INCORRETO' in ex['level']:
                    pdf.set_fill_color(254, 226, 226)
                    label = 'INCORRETO'
                else:
                    pdf.set_fill_color(254, 249, 195)
                    label = 'PARCIAL'
                
                pdf.set_font('Helvetica', 'B', 8)
                pdf.set_x(20)
                pdf.cell(25, 5, safe(f' [{label}]'), 0, 0, 'L', True)
                pdf.set_font('Helvetica', 'I', 8)
                preview = ex['answer'][:200] + ('...' if len(ex['answer']) > 200 else '')
                pdf.set_x(47)
                pdf.multi_cell(W - 35, 4, safe(f'"{preview}"'))
                pdf.ln(2)
        
        pdf.ln(5)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)

    return bytes(pdf.output())



def show_advanced_professor_dashboard():
    """Dashboard redesenhado para professores com foco em insights acionáveis"""
    # Garante carregamento dos ícones
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined" rel="stylesheet">', unsafe_allow_html=True)
    inject_dashboard_styles()
    
    col_left, col_center, col_right = st.columns([0.6, 5, 0.6])
    
    with col_center:
        col_t, col_b = st.columns([3, 1])
        with col_t:
            st.markdown(f"<div class='dash-title'>{icon('dashboard', '#10b981', 32)} Dashboard do Professor</div>", unsafe_allow_html=True)
        with col_b:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("Atualizar Dados", icon=":material/refresh:", help="Limpar cache e buscar dados em tempo real", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        st.markdown(f"<div class='dash-subtitle'>{icon('info', '#64748b', 16)} Os dados do painel são mantidos em cache por 5 minutos para alta velocidade. Use o botão acima se precisar dos últimos dados exatos.</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        try:
            # Carrega dados
            all_users = get_all_users()
            all_analytics = get_all_users_analytics()
            
            # Filtra apenas alunos
            student_users = [user for user in all_users if user.get('user_type') == 'aluno']
            
            if not student_users:
                st.warning("Nenhum aluno encontrado.")
                return
                
            if not all_analytics:
                st.info("Nenhum dado de analytics encontrado ainda. Os alunos precisam responder questões primeiro.")
                # Ainda permite acesso ao admin mesmo sem dados
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return
        
        # Sistema de tabs redesenhado: 3 tabs (adicionada aba Admin)
        tab1, tab2, tab3 = st.tabs([
            "Visão Geral", 
            "Análise Individual",
            "Admin"
        ])
        
        with tab1:
            if all_analytics:
                show_general_overview_tab(student_users, all_analytics)
            else:
                st.info("Aguardando dados de analytics...")
        
        with tab2:
            if all_analytics:
                show_individual_analysis_tab(student_users, all_analytics)
            else:
                st.info("Aguardando dados de analytics...")
        
        with tab3:
            show_admin_tab(student_users)
def get_completed_cases_data(student_users: List[Dict], all_analytics: Dict) -> Dict[str, Dict[str, Dict]]:
    """
    Retorna um dicionário mapeando student_id -> {case_id -> dados_do_caso}
    onde dados_do_caso inclui:
    - 'duration_seconds': int
    - 'turns': int (total de interações: 1 + chat_turns)
    - 'points_gained': float
    - 'max_points': float
    - 'level': str
    - 'timestamp': datetime
    """
    from logic import QUESTIONS
    q_map = {q['id']: q for q in QUESTIONS}
    
    data_map = {}
    for student in student_users:
        uid = student['id']
        user_data = all_analytics.get(uid, {})
        case_analytics = user_data.get('case_analytics', [])
        chat_interactions = user_data.get('chat_interactions', [])
        
        # Ordena por timestamp para obter o mais recente
        def get_timestamp(x):
            ts = x.get('timestamp')
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts)
                except:
                    return datetime.min
            elif isinstance(ts, (int, float)):
                try:
                    return datetime.fromtimestamp(ts)
                except:
                    return datetime.min
            return datetime.min
            
        sorted_cases = sorted(case_analytics, key=get_timestamp)
        
        student_cases = {}
        for entry in sorted_cases:
            cid = entry.get('case_id')
            if not cid or cid not in q_map:
                continue
                
            result = entry.get('case_result', {})
            duration = entry.get('duration_seconds', 0)
            points = float(result.get('points_gained', 0))
            max_pts = float(q_map[cid].get('pontuacao_maxima', 3.0))
            level = result.get('level', result.get('classification', 'N/A')).strip().upper()
            
            # Conta as interações do chat para esse caso
            chat_turns = 0
            for chat_doc in chat_interactions:
                if chat_doc.get('case_id') == cid:
                    if 'messages' in chat_doc and isinstance(chat_doc['messages'], list):
                        chat_turns += len(chat_doc['messages'])
                    else:
                        chat_turns += 1
                        
            student_cases[cid] = {
                'duration_seconds': duration,
                'turns': 1 + chat_turns,
                'points_gained': points,
                'max_points': max_pts,
                'level': level,
                'timestamp': get_timestamp(entry)
            }
        if student_cases:
            data_map[uid] = student_cases
    return data_map


def show_general_overview_tab(student_users: List[Dict], all_analytics: Dict):
    """Tab de visão geral com estatísticas gerais de todos os alunos"""
    st.markdown(f"## {icon('bar_chart', '#10b981', 28)} Visão Geral da Turma", unsafe_allow_html=True)
    
    # Filtro por turma
    turma_filter = st.selectbox(
        "Filtrar por turma",
        ["Todas", "Biomedicina A", "Biomedicina B"],
        key="turma_filter_overview"
    )
    if turma_filter != "Todas":
        student_users = [s for s in student_users if s.get('turma') == turma_filter]
        if not student_users:
            st.info(f"Nenhum aluno encontrado na turma {turma_filter}.")
            return
    
    # Carrega dados
    global_stats = get_global_stats()
    q_stats_data = []
    try:
        q_stats_data = get_question_stats()
    except Exception:
        q_stats_data = []
    hardest_questions = get_hardest_questions(top_n=6)
    
    # NOVAS MÉTRICAS E KPIs
    completed_cases_data = get_completed_cases_data(student_users, all_analytics)
    
    total_students = len(student_users)
    total_answered = sum(len(cases) for cases in completed_cases_data.values())
    
    from logic import QUESTIONS
    
    # Calcular estatísticas por questão
    hardest_q_id = None
    hardest_q_num = None
    max_avg_turns = -1
    
    question_overview_stats = []
    for i, q in enumerate(QUESTIONS):
        q_id = q['id']
        responses = []
        for uid, cases in completed_cases_data.items():
            if q_id in cases:
                responses.append(cases[q_id])
                
        count = len(responses)
        avg_time = sum(r['duration_seconds'] for r in responses) / count if count > 0 else 0
        avg_turns = sum(r['turns'] for r in responses) / count if count > 0 else 0
        
        question_overview_stats.append({
            'id': q_id,
            'num': i + 1,
            'titulo': q['pergunta'],
            'count': count,
            'avg_time': avg_time,
            'avg_turns': avg_turns
        })
        
        if count > 0 and avg_turns > max_avg_turns:
            max_avg_turns = avg_turns
            hardest_q_id = q_id
            hardest_q_num = i + 1
            
    # ===== KPIs PRINCIPAIS =====
    st.markdown(f"### {icon('push_pin', '#10b981', 24)} Métricas Principais", unsafe_allow_html=True)
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        draw_premium_metric_card(
            "Total de Alunos",
            str(total_students),
            icon_name="people",
            icon_color="#3b82f6"
        )
        
    with col_kpi2:
        draw_premium_metric_card(
            "Questões Respondidas",
            str(total_answered),
            icon_name="assignment",
            icon_color="#8b5cf6"
        )
        
    with col_kpi3:
        if hardest_q_num is not None:
            draw_premium_metric_card(
                "Questão Mais Difícil",
                f"Questão {hardest_q_num}",
                icon_name="warning",
                icon_color="#ef4444",
                subtitle=f"Média: {max_avg_turns:.1f} interações"
            )
        else:
            draw_premium_metric_card(
                "Questão Mais Difícil",
                "N/A",
                icon_name="warning",
                icon_color="#ef4444",
                subtitle="Sem dados"
            )
            
    st.markdown("---")
    
    # ===== PAINEL DE QUESTÕES — VISÃO DETALHADA =====
    st.markdown(f"### {icon('quiz', '#10b981', 24)} Painel de Questões — Visão Geral", unsafe_allow_html=True)
    st.markdown(f"<div style='color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem;'>{icon('info', '#64748b', 16)} Resumo das interações dos alunos para cada uma das 4 questões do módulo.</div>", unsafe_allow_html=True)
    
    for q_stat in question_overview_stats:
        q_id = q_stat['id']
        q_num = q_stat['num']
        titulo = q_stat['titulo']
        count = q_stat['count']
        avg_time = q_stat['avg_time']
        avg_turns = q_stat['avg_turns']
        
        # Calculate Avançado completion rate
        responses = [cases[q_id] for cases in completed_cases_data.values() if q_id in cases]
        avancado_count = sum(1 for r in responses if r['level'] in ['AVANÇADO', 'AVANCADO'])
        avancado_rate = (avancado_count / count * 100) if count > 0 else 0
        
        # Dificuldade baseada em média de interações
        if count == 0:
            card_border_color = "rgba(148, 163, 184, 0.15)"
            badge_bg = "#94a3b8"
            status_label = "Sem respostas"
        elif avg_turns < 3:
            card_border_color = "rgba(16, 185, 129, 0.2)"
            badge_bg = "#10b981"
            status_label = "Fácil"
        elif avg_turns < 5:
            card_border_color = "rgba(234, 179, 8, 0.2)"
            badge_bg = "#eab308"
            status_label = "Moderada"
        else:
            card_border_color = "rgba(239, 68, 68, 0.2)"
            badge_bg = "#ef4444"
            status_label = "Desafiadora"
            
        st.markdown(f"""
        <div style='background: var(--secondary-background-color); border: 1px solid {card_border_color}; 
                    border-radius: 20px; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
                    transition: all 0.3s ease; border-left: 5px solid {badge_bg};'>
            <div style='display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;'>
                <div style='display: flex; align-items: center; gap: 1rem;'>
                    <div style='background: {badge_bg}; color: white; font-weight: 800; font-size: 1.15rem; 
                                width: 46px; height: 46px; border-radius: 12px; display: flex; align-items: center; 
                                justify-content: center; box-shadow: 0 4px 10px {badge_bg}40;'>
                        Q{q_num}
                    </div>
                    <div>
                        <div style='font-size: 1.05rem; font-weight: 700; color: var(--text-color);'>{titulo}</div>
                        <div style='font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;'>Dificuldade: <span style='font-weight: 600; color: {badge_bg};'>{status_label}</span></div>
                    </div>
                </div>
                <div style='display: flex; gap: 1.5rem; flex-wrap: wrap;'>
                    <div style='text-align: center; min-width: 90px;'>
                        <div style='font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>Respondida por</div>
                        <div style='font-size: 1.25rem; font-weight: 700; color: var(--text-color); margin-top: 0.25rem;'>{count} alunos</div>
                    </div>
                    <div style='text-align: center; min-width: 100px;'>
                        <div style='font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>Tempo Médio</div>
                        <div style='font-size: 1.25rem; font-weight: 700; color: var(--text-color); margin-top: 0.25rem;'>{format_duration(avg_time)}</div>
                    </div>
                    <div style='text-align: center; min-width: 100px;'>
                        <div style='font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>Média Interações</div>
                        <div style='font-size: 1.25rem; font-weight: 700; color: {badge_bg}; margin-top: 0.25rem;'>{avg_turns:.1f}</div>
                    </div>
                    <div style='text-align: center; min-width: 100px;'>
                        <div style='font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;'>Taxa Conclusão</div>
                        <div style='font-size: 1.25rem; font-weight: 700; color: #10b981; margin-top: 0.25rem;'>{avancado_rate:.0f}%</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # ===== 3. EXPORTAÇÃO DE RELATÓRIOS (PDFs) =====
    st.markdown(f"### {icon('description', '#10b981', 24)} Exportação de Relatórios", unsafe_allow_html=True)
    st.markdown("Baixe os dados e análises da turma consolidados em arquivos PDF prontos para impressão ou arquivamento.")
    
    col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
    with col_pdf1:
        pdf_bytes_class = generate_class_pdf(turma_filter, student_users, global_stats, q_stats_data)
        st.download_button(
            label=f"Relatório da Turma ({turma_filter})",
            icon=":material/download:",
            data=pdf_bytes_class,
            file_name=f"relatorio_biotutor_{turma_filter.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_class_report_{turma_filter}"
        )
        
    with col_pdf2:
        pdf_bytes_global = generate_global_interactions_pdf(student_users, all_analytics)
        st.download_button(
            label=f"Relatório Completo",
            icon=":material/download:",
            data=pdf_bytes_global,
            file_name=f"relatorio_geral_interacoes_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_global_report"
        )
        
    with col_pdf3:
        if st.button("Gerar PDF de Insights Pedagógicos", icon=":material/auto_awesome:", use_container_width=True, type="primary"):
            with st.spinner("A IA está analisando todas as respostas por categoria. Isso pode levar alguns segundos..."):
                try:
                    pdf_ia = generate_ai_insights_pdf(hardest_questions)
                    st.download_button(
                        label=f"Baixar Insights (PDF)",
                        icon=":material/download:",
                        data=pdf_ia,
                        file_name=f"relatorio_ia_pedagogico_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_btn_ia_pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar o PDF da IA: {e}")
                    
    st.markdown("---")
    
    # ===== 2. INSIGHTS RÁPIDOS COM IA =====
    st.markdown(f"### {icon('auto_awesome', '#8b5cf6', 24)} Insights Rápidos das Interações (Geral)", unsafe_allow_html=True)
    st.markdown("Gere um resumo instantâneo do desempenho da turma e do padrão de uso do Tutor IA.")
    
    if st.button("Atualizar Análises com IA", icon=":material/psychology:", type="secondary", key="btn_run_general_insights"):
        with st.spinner("Analisando respostas e conversas com a IA... Isso pode levar alguns segundos."):
            col_insight1, col_insight2 = st.columns([1.5, 1])
            with col_insight1:
                from logic import generate_class_criteria_analysis
                recent_answers = []
                for uid, data in all_analytics.items():
                    if uid in [s['id'] for s in student_users]:
                        cases = data.get('case_analytics', [])
                        for c in cases[-5:]:
                            ans = c.get('case_result', {}).get('user_answer')
                            if ans:
                                recent_answers.append(ans)
                
                import random
                random.shuffle(recent_answers)
                criteria_analysis = generate_class_criteria_analysis(recent_answers[:15])
                
                st.markdown(f"#### {icon('psychology', '#8b5cf6', 22)} Análise de IA por Eixos de Conhecimento", unsafe_allow_html=True)
                for crit_name, crit_text in criteria_analysis.items():
                    st.info(f"**{crit_name}:**\n{crit_text}")
                    
            with col_insight2:
                from logic import generate_ai_usage_preview
                chat_samples = []
                for uid, data in all_analytics.items():
                    if uid in [s['id'] for s in student_users]:
                        chats = data.get('chat_interactions', [])
                        for chat_doc in chats[-3:]:
                            messages = chat_doc.get('messages', [])
                            for msg in messages:
                                if msg.get('user_message'):
                                    chat_samples.append(msg['user_message'])
                
                if chat_samples:
                    random.shuffle(chat_samples)
                    ai_usage = generate_ai_usage_preview(chat_samples[:10])
                else:
                    ai_usage = "Ainda não há interações suficientes com o Tutor IA para gerar uma análise."
                
                st.markdown("#### Padrão de Uso do Tutor")
                st.success(f"{ai_usage}")
                
    st.markdown("---")
    
    # ===== 3. INSIGHTS PEDAGÓGICOS POR QUESTÃO =====
    st.markdown(f"### {icon('psychology', '#3b82f6', 24)} Insights Pedagógicos por Questão", unsafe_allow_html=True)
    st.markdown("Gere análises pedagógicas baseadas em IA para identificar erros comuns e obter estratégias de intervenção por questão.")
    
    from logic import QUESTIONS as ALL_QUESTIONS_OV
    q_titles = [f"Questão {i+1}: {q['pergunta'][:65]}..." for i, q in enumerate(ALL_QUESTIONS_OV)]
    selected_q_idx = st.selectbox(
        "Selecione a Questão para Análise",
        range(len(q_titles)),
        format_func=lambda x: q_titles[x],
        key="pedagogical_q_select"
    )
    
    if st.button("Gerar Análise Pedagógica da Questão", icon=":material/school:", type="primary", key="btn_run_pedagogical_insights"):
        with st.spinner("A IA está analisando as respostas da turma para esta questão..."):
            selected_q_id = ALL_QUESTIONS_OV[selected_q_idx]['id']
            q_topic = q_titles[selected_q_idx]
            
            sample_answers = []
            for uid, data in all_analytics.items():
                for case in data.get('case_analytics', []):
                    if case.get('case_id') == selected_q_id:
                        ans = case.get('case_result', {}).get('user_answer')
                        if ans:
                            sample_answers.append(ans)
            
            if sample_answers:
                insight_text = generate_category_insights(q_topic, sample_answers[:15])
                st.markdown(f"#### {icon('auto_awesome', '#3b82f6', 20)} Análise Pedagógica da Questão", unsafe_allow_html=True)
                st.info(insight_text)
            else:
                st.warning("Nenhuma resposta enviada para esta questão ainda, impossível gerar insights pedagógicos.")
                
    
def show_individual_analysis_tab(student_users: List[Dict], all_analytics: Dict):
    """Tab de análise individual com perfil detalhado de cada aluno"""
    st.markdown(f"## {icon('person', '#3b82f6', 28)} Análise Individual de Alunos", unsafe_allow_html=True)
    
    # ===== SELEÇÃO DE ALUNO =====
    st.markdown(f"### {icon('search', '#10b981', 24)} Selecione um Aluno", unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("Buscar por nome ou email", "")
    
    with col2:
        turma_filter_ind = st.selectbox(
            "Filtrar por turma",
            ["Todas", "Biomedicina A", "Biomedicina B"],
            key="turma_filter_individual"
        )
    
    with col3:
        filter_performance = st.selectbox(
            "Filtrar por desempenho",
            ["Todos", "Acima da média", "Abaixo da média", "Sem atividade"]
        )
    
    with col4:
        filter_level = st.selectbox(
            "Filtrar por nível",
            ["Todos", "Básico", "Intermediário", "Avançado"]
        )
    
    # Aplica filtros
    filtered_students = student_users.copy()
    
    # Filtro de busca
    if search_term:
        filtered_students = [
            s for s in filtered_students 
            if search_term.lower() in s['name'].lower() or search_term.lower() in s['email'].lower()
        ]
    
    # Filtro de turma
    if turma_filter_ind != "Todas":
        filtered_students = [
            s for s in filtered_students
            if s.get('turma') == turma_filter_ind
        ]
    
    # Prepara lista para seleção
    if not filtered_students:
        st.warning("Nenhum aluno encontrado com os filtros aplicados.")
        return
    
    student_names = [f"{student['name']} — {student.get('turma', 'Sem turma')}" for student in filtered_students]
    selected_student_idx = st.selectbox(
        "Aluno:",
        range(len(student_names)),
        format_func=lambda x: student_names[x]
    )
    
    selected_student = filtered_students[selected_student_idx]
    student_id = selected_student['id']
    
    st.markdown("---")
    
    # ===== PERFIL DO ALUNO =====
    
    # Carrega perfil completo
    try:
        profile = get_student_complete_profile(student_id)
    except Exception as e:
        st.error(f"Erro ao carregar perfil do aluno: {e}")
        return
    
    basic_stats = profile['estatisticas_basicas']
    advanced_stats = profile['estatisticas_avancadas']
    weakness = profile['analise_fraquezas']
    comparison = profile['comparacao_turma']
    evolution = profile['evolucao_temporal']
    
    # Mini Card de Informações do Aluno
    turma_display = selected_student.get('turma', 'Não informada')
    ra_display = selected_student.get('ra', 'N/A')
    
    st.markdown(f"""
    <div class="student-profile-banner">
        <div style='display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;'>
            <div style='flex: 1; min-width: 200px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('person', '#3b82f6', 16)} Nome
                </div>
                <div style='font-size: 1.3rem; font-weight: 700; color: var(--text-color); margin-top: 0.25rem;'>
                    {selected_student['name']}
                </div>
            </div>
            <div style='flex: 0.5; min-width: 100px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('badge', '#8b5cf6', 16)} RA
                </div>
                <div style='font-size: 1.15rem; font-weight: 600; color: var(--text-color); margin-top: 0.25rem;'>
                    {ra_display}
                </div>
            </div>
            <div style='flex: 0.7; min-width: 140px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('school', '#10b981', 16)} Turma
                </div>
                <div style='font-size: 1.15rem; font-weight: 600; color: var(--text-color); margin-top: 0.25rem;'>
                    {turma_display}
                </div>
            </div>
            <div style='flex: 1; min-width: 200px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('email', '#64748b', 16)} Email
                </div>
                <div style='font-size: 0.95rem; font-weight: 500; color: var(--text-color); opacity: 0.85; margin-top: 0.25rem;'>
                    {selected_student['email']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== SEÇÃO: DESEMPENHO GERAL =====
    st.markdown(f"### {icon('analytics', '#10b981', 24)} Desempenho Geral", unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        draw_premium_metric_card(
            "Questões Respondidas",
            str(basic_stats['case_stats']['total_cases']),
            icon_name="assignment",
            icon_color="#8b5cf6"
        )
    
    with col2:
        acc = basic_stats['case_stats']['accuracy_rate']
        draw_premium_metric_card(
            "Taxa de Acertos",
            f"{acc:.1f}%",
            icon_name="track_changes",
            icon_color="#10b981"
        )
    
    with col3:
        draw_premium_metric_card(
            "Tempo Médio",
            basic_stats['case_stats']['average_time_formatted'],
            icon_name="schedule",
            icon_color="#3b82f6"
        )
    
    with col4:
        draw_premium_metric_card(
            "Interações Chat",
            str(basic_stats['total_chat_interactions']),
            icon_name="chat",
            icon_color="#ec4899"
        )
    
    with col5:
        draw_premium_metric_card(
            "vs Turma",
            f"{comparison['performance'].replace('_', ' ').title()}",
            icon_name="compare_arrows",
            icon_color="#6366f1",
            subtitle=f"{comparison['diferenca']:.1f}%"
        )
    
    st.markdown("---")
    
    # ===== SEÇÃO: DESEMPENHO POR QUESTÃO (1 a 6) =====
    st.markdown(f"### {icon('quiz', '#8b5cf6', 24)} Desempenho por Questão (1 a 6)", unsafe_allow_html=True)
    
    # Computa o desempenho do aluno por questão
    case_analytics_ind = all_analytics.get(student_id, {}).get('case_analytics', [])
    from logic import QUESTIONS as ALL_QUESTIONS
    
    student_q_data = {}
    for entry in case_analytics_ind:
        cid = entry.get('case_id', '')
        result = entry.get('case_result', {})
        duration = entry.get('duration_seconds', 0)
        
        # Encontra a questão no banco
        q_idx = next((i for i, q in enumerate(ALL_QUESTIONS) if q['id'] == cid), None)
        if q_idx is None:
            continue
        
        q_num = q_idx + 1
        points = float(result.get('points_gained', 0))
        max_pts = float(ALL_QUESTIONS[q_idx].get('pontuacao_maxima', 3.0))
        level = result.get('level', result.get('classification', 'N/A')).strip().upper()
        feedback = result.get('feedback', '')
        
        # Conta chat turns
        chat_turns = 0
        student_chats = all_analytics.get(student_id, {}).get('chat_interactions', [])
        for chat_doc in student_chats:
            if chat_doc.get('case_id') == cid:
                if 'messages' in chat_doc and isinstance(chat_doc['messages'], list):
                    chat_turns += len(chat_doc['messages'])
                else:
                    chat_turns += 1
        turns = 1 + chat_turns
        
        # Pega a tentativa mais recente de cada questão
        if q_num not in student_q_data or True:  # Mantém a última tentativa
            student_q_data[q_num] = {
                'q_num': q_num,
                'titulo': ALL_QUESTIONS[q_idx]['pergunta'][:70] + '...',
                'points': points,
                'max_pts': max_pts,
                'level': level,
                'feedback': feedback,
                'duration': duration,
                'turns': turns,
                'taxa': (points / max_pts * 100) if max_pts > 0 else 0
            }
    
    if student_q_data:
        # Resumo textual em largura total (sem gráficos)
        answered = len(student_q_data)
        total_q = len(ALL_QUESTIONS)
        total_duration = sum(d['duration'] for d in student_q_data.values())
        avg_duration_student = total_duration / answered if answered > 0 else 0
        total_interactions_student = sum(d['turns'] for d in student_q_data.values())
        
        not_answered = [n for n in range(1, total_q + 1) if n not in student_q_data]
        
        st.markdown(f"""
        <div style='background: var(--secondary-background-color); padding: 1.5rem; border-radius: 20px; 
                    border: 1px solid rgba(59, 130, 246, 0.2); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);'>
            <div style='font-size: 1.15rem; font-weight: 700; margin-bottom: 1.25rem; color: var(--text-color); display: flex; align-items: center; gap: 0.5rem;'>
                {icon('summarize', '#3b82f6', 22)} Resumo do Aluno
            </div>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;'>
                <div style='text-align: center; padding: 1rem; background: rgba(139, 92, 246, 0.06); border-radius: 12px; border: 1px solid rgba(139, 92, 246, 0.1);'>
                    <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;'>Respondidas</div>
                    <div style='font-size: 1.75rem; font-weight: 800; color: #8b5cf6; margin-top: 0.25rem;'>{answered}/{total_q}</div>
                </div>
                <div style='text-align: center; padding: 1rem; background: rgba(59, 130, 246, 0.06); border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.1);'>
                    <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;'>Tempo Médio</div>
                    <div style='font-size: 1.75rem; font-weight: 800; color: #3b82f6; margin-top: 0.25rem;'>{format_duration(avg_duration_student)}</div>
                </div>
                <div style='text-align: center; padding: 1rem; background: rgba(16, 185, 129, 0.06); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.1);'>
                    <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;'>Interações</div>
                    <div style='font-size: 1.75rem; font-weight: 800; color: #10b981; margin-top: 0.25rem;'>{total_interactions_student}</div>
                </div>
                <div style='text-align: center; padding: 1rem; background: rgba(239, 68, 68, 0.06); border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.1);'>
                    <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600;'>Pendentes</div>
                    <div style='font-size: 1.75rem; font-weight: 800; color: #ef4444; margin-top: 0.25rem;'>{len(not_answered)}</div>
                </div>
            </div>
            {"<div style='margin-top: 1rem; font-size: 0.85rem; color: #94a3b8; display: flex; align-items: center; gap: 0.4rem;'>" + icon('pending', '#ef4444', 15) + " Questões não respondidas: " + ", ".join([f"Q{n}" for n in not_answered]) + "</div>" if not_answered else ""}
        </div>
        """, unsafe_allow_html=True)
        
        # Cards por questão respondida
        st.markdown(f"<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        
        for q_num in sorted(student_q_data.keys()):
            qd = student_q_data[q_num]
            
            # Cores por nível
            level_colors = {
                'AVANÇADO': ('#22c55e', 'Avançado', 'star'),
                'MÉDIO': ('#3b82f6', 'Médio', 'trending_up'),
                'MEDIO': ('#3b82f6', 'Médio', 'trending_up'),
                'BÁSICO': ('#eab308', 'Básico', 'check'),
                'BASICO': ('#eab308', 'Básico', 'check'),
                'PARCIAL': ('#f97316', 'Parcial', 'warning'),
                'INCORRETO': ('#ef4444', 'Incorreto', 'close'),
            }
            lc, ll, li = level_colors.get(qd['level'], ('#94a3b8', qd['level'], 'help'))
            bar_w = max(qd['taxa'], 3)
            
            ind_card = f"<div style='background:var(--secondary-background-color);border:1px solid rgba(148,163,184,0.15);border-radius:14px;padding:1rem 1.25rem;margin-bottom:0.5rem;border-left:4px solid {lc};'>"
            ind_card += f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>"
            ind_card += f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
            ind_card += f"<span style='background:{lc};color:white;font-weight:700;font-size:0.9rem;padding:4px 10px;border-radius:8px;'>Q{q_num}</span>"
            ind_card += f"<span style='font-size:0.85rem;color:var(--text-color);font-weight:500;'>{qd['titulo'][:60]}</span>"
            ind_card += "</div>"
            ind_card += f"<div style='display:flex;align-items:center;gap:0.5rem;'>"
            ind_card += f"<span style='background:{lc}18;color:{lc};font-size:0.75rem;font-weight:600;padding:3px 10px;border-radius:16px;'>{icon(li, lc, 13)} {ll}</span>"
            ind_card += f"<span style='font-weight:700;color:{lc};font-size:1rem;'>{qd['points']:.1f}/{qd['max_pts']:.0f} pts</span>"
            ind_card += "</div></div>"
            ind_card += f"<div style='background:rgba(148,163,184,0.12);border-radius:6px;height:10px;overflow:hidden;'>"
            ind_card += f"<div style='background:{lc};height:100%;width:{bar_w}%;border-radius:6px;'></div>"
            ind_card += "</div>"
            ind_card += f"<div style='display:flex;justify-content:space-between;align-items:center;margin-top:0.75rem;font-size:0.8rem;color:#64748b;'>"
            ind_card += f"<span>{icon('schedule', '#64748b', 14)} Tempo: {format_duration(qd['duration'])}</span>"
            ind_card += f"<span>{icon('forum', '#64748b', 14)} Interações: {qd['turns']}</span>"
            ind_card += "</div>"
            ind_card += "</div>"
            st.markdown(ind_card, unsafe_allow_html=True)
        
        # Questões não respondidas
        for q_num in sorted([n for n in range(1, len(ALL_QUESTIONS) + 1) if n not in student_q_data]):
            q_title = ALL_QUESTIONS[q_num - 1]['pergunta'][:60] + '...'
            na_card = f"<div style='background:var(--secondary-background-color);border:1px dashed rgba(148,163,184,0.3);border-radius:14px;padding:0.75rem 1.25rem;margin-bottom:0.5rem;opacity:0.6;'>"
            na_card += f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            na_card += f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
            na_card += f"<span style='background:#94a3b8;color:white;font-weight:700;font-size:0.9rem;padding:4px 10px;border-radius:8px;'>Q{q_num}</span>"
            na_card += f"<span style='font-size:0.85rem;color:#94a3b8;font-weight:500;'>{q_title}</span>"
            na_card += "</div>"
            na_card += f"<span style='color:#94a3b8;font-size:0.8rem;font-style:italic;'>{icon('pending', '#94a3b8', 14)} Não respondida</span>"
            na_card += "</div></div>"
            st.markdown(na_card, unsafe_allow_html=True)
    else:
        st.info("O aluno ainda não respondeu nenhuma questão.")
    
    st.markdown("---")
    
    # ===== SEÇÃO: HISTÓRICO DETALHADO =====
    st.markdown(f"### {icon('history', '#ef4444', 24)} Histórico de Respostas", unsafe_allow_html=True)
    
    case_analytics = all_analytics.get(student_id, {}).get('case_analytics', [])
    
    if case_analytics:
        # Filtros para histórico
        col1, col2 = st.columns(2)
        
        with col1:
            filter_status_hist = st.selectbox(
                "Status",
                ["Todos", "Corretas", "Parciais", "Incorretas"],
                key="hist_status"
            )
        
        with col2:
            q_labels = [f"Q{i+1}" for i in range(len(ALL_QUESTIONS))]
            filter_q_hist = st.selectbox(
                "Questão",
                ["Todas"] + q_labels,
                key="hist_q"
            )

        
        
        # Prepara histórico com detalhes completos
        filtered_entries = []
        for entry in case_analytics:
            cid = entry.get('case_id')
            q_info = get_case(cid)
            result = entry.get('case_result', {})
            
            is_correct = result.get('is_correct', False)
            classification = result.get('classification', '').upper()
            is_partial = 'PARCIAL' in classification
            
            # Dados de filtro
            q_idx_hist = next((i for i, q in enumerate(ALL_QUESTIONS) if q['id'] == cid), None)
            q_num_hist = q_idx_hist + 1 if q_idx_hist is not None else 0
            
            # Aplica filtros
            if filter_status_hist == "Corretas" and (not is_correct or is_partial):
                continue
            if filter_status_hist == "Incorretas" and is_correct:
                continue
            if filter_status_hist == "Parciais" and not is_partial:
                continue
            
            if filter_q_hist != "Todas" and f"Q{q_num_hist}" != filter_q_hist:
                continue

            
            timestamp_ts = entry.get('timestamp')
            if isinstance(timestamp_ts, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp_ts)
                except:
                    timestamp = datetime.now()
            else:
                 # Assumindo timestamp do firebase ou float
                 try:
                     timestamp = datetime.fromtimestamp(timestamp_ts) if isinstance(timestamp_ts, (int, float)) else datetime.now()
                 except:
                     timestamp = datetime.now()
            
            comps = q_info.get('componentes_conhecimento', ['Geral'])
            diff = 'N/A'
            
            filtered_entries.append({
                'entry': entry,
                'q_info': q_info,
                'result': result,
                'timestamp': timestamp,
                'is_correct': is_correct,
                'is_partial': is_partial,
                'classification': classification,
                'q_num': q_num_hist,
                'comps': comps,
                'diff': diff
            })
        
        
        if filtered_entries:
            # Ordena por data (mais recente primeiro)
            filtered_entries.sort(key=lambda x: x['timestamp'], reverse=True)
            
            st.markdown(f"**{len(filtered_entries)} questões encontradas**")
            st.markdown("")
            
            # Agrupa por data
            grouped_entries = {}
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            for item in filtered_entries:
                item_date = item['timestamp'].date()
                if item_date == today:
                    key = "Hoje"
                elif item_date == yesterday:
                    key = "Ontem"
                else:
                    key = f"{item_date.strftime('%d/%m/%Y')}"
                
                label_icon = icon('calendar_today', '#64748b', 24)
                if key not in grouped_entries:
                    grouped_entries[key] = []
                grouped_entries[key].append(item)
            
            # Exibe Timeline
            for date_label, items in grouped_entries.items():
                st.markdown(f"### {icon('event', '#64748b', 28)} {date_label}", unsafe_allow_html=True)
                
                for item in items:
                    entry = item['entry']
                    q_info = item['q_info']
                    result = item['result']
                    timestamp = item['timestamp']
                    is_correct = item['is_correct']
                    is_partial = item['is_partial']
                    classification = item['classification']
                    q_num = item.get('q_num', '?')
                    
                    if is_partial:
                        status_emoji = "🟡"
                    elif entry.get('case_result', {}).get('is_correct'):
                        status_emoji = "🟢"
                    else:
                        status_emoji = "🔴"
                        
                    question_preview = q_info.get('pergunta', 'N/A')[:65] + "..."
                    header_label = f"{status_emoji} [{timestamp.strftime('%H:%M')}] Questão {q_num}: {question_preview}"
                    
                    with st.expander(header_label, expanded=False):
                        # Busca interações do chat para esta questão
                        chat_interactions = get_user_chat_interactions(student_id, entry.get('case_id'))
                        chat_turns = 1 + len(chat_interactions)
                        
                        # Renderiza o cabeçalho da questão e os gabaritos
                        st.markdown(f"""
                        <div style='background: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.15); padding: 1.25rem; border-radius: 12px; margin-bottom: 1rem;'>
                            <div style='font-size: 0.95rem; font-weight: 700; color: var(--text-color); margin-bottom: 0.5rem;'>
                                {icon('quiz', '#3b82f6', 18)} Enunciado da Questão
                            </div>
                            <div style='font-size: 0.9rem; color: var(--text-color); opacity: 0.9; margin-bottom: 0.75rem; white-space: pre-wrap;'>{q_info.get('pergunta', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Expander para ver critérios/gabaritos
                        ref_dict = q_info.get('referencia', {})
                        if isinstance(ref_dict, dict) and ref_dict:
                            with st.expander("Ver Critérios de Avaliação (Gabaritos)", expanded=False):
                                for level_name, level_ref in ref_dict.items():
                                    st.markdown(f"**Nível {level_name}:**")
                                    st.markdown(f"- *Critério:* {level_ref.get('parametros', '')}")
                                    st.markdown(f"- *Resposta Exemplo:* {level_ref.get('resposta_exemplo', '')}")
                                    st.markdown("---")
                                    
                        # Constrói a conversa inteira do aluno com a IA
                        conversation = []
                        
                        # Resposta inicial
                        initial_answer = result.get('user_answer')
                        initial_feedback = result.get('feedback')
                        
                        # Verifica duplicatas com o chat gravado
                        has_initial_in_chat = False
                        if chat_interactions:
                            first_msg = chat_interactions[0].get('user_message', '').strip()
                            if initial_answer and (first_msg == initial_answer.strip() or first_msg in initial_answer or initial_answer in first_msg):
                                has_initial_in_chat = True
                                
                        if not has_initial_in_chat and initial_answer:
                            conversation.append({
                                'sender': 'aluno',
                                'message': initial_answer,
                                'timestamp': timestamp.strftime('%H:%M:%S') if timestamp else ''
                            })
                            if initial_feedback:
                                conversation.append({
                                    'sender': 'tutor',
                                    'message': initial_feedback,
                                    'timestamp': timestamp.strftime('%H:%M:%S') if timestamp else ''
                                })
                                
                        # Adiciona as mensagens subsequentes
                        for interaction in chat_interactions:
                            user_msg = interaction.get('user_message', '')
                            bot_msg = interaction.get('bot_response', '')
                            
                            chat_time = interaction.get('timestamp', '')
                            if isinstance(chat_time, str):
                                try:
                                    chat_time = datetime.fromisoformat(chat_time).strftime('%H:%M:%S')
                                except:
                                    chat_time = ''
                            elif isinstance(chat_time, (int, float)):
                                try:
                                    chat_time = datetime.fromtimestamp(chat_time).strftime('%H:%M:%S')
                                except:
                                    chat_time = ''
                            else:
                                chat_time = ''
                                
                            if user_msg:
                                conversation.append({
                                    'sender': 'aluno',
                                    'message': user_msg,
                                    'timestamp': chat_time
                                })
                            if bot_msg:
                                conversation.append({
                                    'sender': 'tutor',
                                    'message': bot_msg,
                                    'timestamp': chat_time
                                })
                                
                        # RENDERIZA O CHAT
                        st.markdown(f"#### {icon('forum', '#4f46e5', 20)} Histórico de Interações (Tutor Socrático)", unsafe_allow_html=True)
                        
                        chat_html = "<div class='chat-container'>"
                        for msg in conversation:
                            sender = msg['sender']
                            text = msg['message']
                            time_str = msg['timestamp']
                            
                            if sender == 'aluno':
                                row_class = 'student-row'
                                bubble_class = 'student-bubble'
                                sender_label = "Aluno"
                                icon_name = 'person'
                                icon_color = '#c7d2fe'
                            else:
                                row_class = 'tutor-row'
                                bubble_class = 'tutor-bubble'
                                sender_label = "Tutor Helix.AI"
                                icon_name = 'smart_toy'
                                icon_color = '#10b981'
                                
                            time_display = f" <span style='font-size:0.7rem; opacity:0.6; margin-left:6px;'>{time_str}</span>" if time_str else ""
                            
                            chat_html += f"""
                            <div class='chat-message-row {row_class}'>
                                <div class='chat-bubble {bubble_class}'>
                                    <div class='chat-message-info'>
                                        <strong>{icon(icon_name, icon_color, 14)} {sender_label}</strong>{time_display}
                                    </div>
                                    <div style='margin-top: 4px; white-space: pre-wrap; font-size: 0.9rem;'>{text}</div>
                                </div>
                            </div>
                            """
                        chat_html += "</div>"
                        st.markdown(chat_html, unsafe_allow_html=True)
                        
                        # CARD DE STATUS AVALIATIVO FINAL
                        level_colors = {
                            'AVANÇADO': '#22c55e',
                            'AVANCADO': '#22c55e',
                            'MÉDIO': '#3b82f6',
                            'MEDIO': '#3b82f6',
                            'BÁSICO': '#eab308',
                            'BASICO': '#eab308',
                            'PARCIAL': '#f97316',
                            'INCORRETO': '#ef4444',
                        }
                        color_status = level_colors.get(classification, '#94a3b8')
                        
                        st.markdown(f"""
                        <div style='background: rgba(148, 163, 184, 0.08); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.15); padding: 1rem; margin-top: 1rem;'>
                            <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;'>
                                <div>
                                    <span style='color: #64748b; font-size: 0.75rem; text-transform: uppercase;'>Nível Alcançado</span>
                                    <div style='color: {color_status}; font-weight: 700; font-size: 1.15rem; display: flex; align-items: center; gap: 0.3rem;'>
                                        {icon('military_tech', color_status, 20)} {classification.title()}
                                    </div>
                                </div>
                                <div>
                                    <span style='color: #64748b; font-size: 0.75rem; text-transform: uppercase;'>Tempo de Resolução</span>
                                    <div style='color: var(--text-color); font-weight: 600; font-size: 1.1rem; display: flex; align-items: center; gap: 0.3rem;'>
                                        {icon('schedule', '#64748b', 18)} {format_duration(entry.get('duration_seconds', 0))}
                                    </div>
                                </div>
                                <div>
                                    <span style='color: #64748b; font-size: 0.75rem; text-transform: uppercase;'>Interações Socráticas</span>
                                    <div style='color: #8b5cf6; font-weight: 700; font-size: 1.15rem; display: flex; align-items: center; gap: 0.3rem;'>
                                        {icon('forum', '#8b5cf6', 20)} {chat_turns}
                                    </div>
                                </div>
                                <div>
                                    <span style='color: #64748b; font-size: 0.75rem; text-transform: uppercase;'>Pontuação Final</span>
                                    <div style='color: {color_status}; font-weight: 700; font-size: 1.15rem; display: flex; align-items: center; gap: 0.3rem;'>
                                        {icon('emoji_events', color_status, 20)} {result.get('points_gained', 0)} pts
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            
            # Botão de download (tabela resumida)
            st.markdown("---")
            history_summary = []
            for item in filtered_entries:
                status_txt = 'Correto'
                if item['is_partial']:
                    status_txt = 'Parcial'
                elif not item['is_correct']:
                    status_txt = 'Incorreto'
                    
                history_summary.append({
                    'Data': item['timestamp'].strftime('%d/%m/%Y %H:%M'),
                    'Questão': item['q_info'].get('pergunta', 'N/A')[:50] + '...',
                    'Componente': ', '.join(item['comps']),
                    'Dificuldade': item['diff'].title(),
                    'Status': status_txt,
                    'Tempo': format_duration(item['entry'].get('duration_seconds', 0)),
                    'Pontos': item['result'].get('points_gained', 0),
                    'Resposta do Aluno': item['result'].get('user_answer', 'N/A'),
                    'Feedback da IA': item['result'].get('feedback', 'N/A')
                })
            
            df_history = pd.DataFrame(history_summary)
            
            # Gera PDF com resumo do aluno
            pdf_bytes = generate_student_pdf(
                selected_student, basic_stats, advanced_stats, weakness, history_summary
            )
            st.download_button(
                label="Baixar Resumo (PDF)",
                data=pdf_bytes,
                file_name=f"resumo_{selected_student['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("Nenhuma resposta encontrada com os filtros aplicados")
    else:
        st.info("Nenhuma questão respondida ainda")
    
    st.markdown("---")
    
    # ===== SEÇÃO: EVOLUÇÃO TEMPORAL =====
    st.markdown(f"### {icon('trending_up', '#10b981', 24)} Evolução Temporal", unsafe_allow_html=True)
    
    weekly_perf = evolution.get('desempenho_semanal', {})
    trend = evolution.get('tendencia', 'estável')
    
    if weekly_perf:
        # Prepara dados para tabela
        weeks = sorted(weekly_perf.keys())
        accuracies = []
        totals = []
        
        for week in weeks:
            data = weekly_perf[week]
            acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            accuracies.append(f"{acc:.1f}%")
            totals.append(data['total'])
            
        df_evolution = pd.DataFrame({
            'Semana': weeks,
            'Questões Respondidas': totals,
            'Taxa de Acerto': accuracies
        })
        
        st.markdown(f"**Evolução nas Últimas 4 Semanas (Tendência: {trend.title()})**")
        st.dataframe(df_evolution, use_container_width=True, hide_index=True)
        
        # Indicador de tendência
        if trend == 'melhorando':
            st.success("**Tendência Positiva**: O aluno está melhorando!")
        elif trend == 'piorando':
            st.error("**Atenção**: O desempenho está caindo")
        else:
            st.info("**Tendência Estável**: Desempenho consistente")
    else:
        st.info("Dados insuficientes para análise temporal (mínimo 1 semana de atividade)")

def show_admin_tab(student_users: List[Dict]):
    """Tab de administração para gerenciar banco de dados"""
    st.markdown(f"## {icon('admin_panel_settings', '#eab308', 28)} Painel de Administração", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="danger-zone-container">
            <div style="color: #ef4444; font-weight: 700; font-size: 1.25rem; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                {icon('warning', '#ef4444', 24)} Zona de Perigo (Ações Destrutivas)
            </div>
            <div style="color: var(--text-color); opacity: 0.85; font-size: 0.95rem; line-height: 1.4;">
                Esta área contém operações que podem deletar dados permanentemente! Tenha cuidado extra antes de prosseguir.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== ESTATÍSTICAS DO BANCO =====
    st.markdown(f"### {icon('storage', '#3b82f6', 24)} Estatísticas do Banco de Dados", unsafe_allow_html=True)
    
    db_stats = get_database_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style='background: rgba(59, 130, 246, 0.05); padding: 1rem; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);'>
                <div style='color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;'>
                    {icon('library_books', '#3b82f6', 18)} Total de Questões Respondidas
                </div>
                <div style='color: #3b82f6; font-size: 1.5rem; font-weight: 600;'>{db_stats['total_analytics']}</div>
                <div style='color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;'>Registros de case_analytics</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style='background: rgba(236, 72, 153, 0.05); padding: 1rem; border-radius: 12px; border: 1px solid rgba(236, 72, 153, 0.2);'>
                <div style='color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;'>
                    {icon('forum', '#ec4899', 18)} Total de Interações Chat
                </div>
                <div style='color: #ec4899; font-size: 1.5rem; font-weight: 600;'>{db_stats['total_chat_interactions']}</div>
                <div style='color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;'>Interações vinculadas</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style='background: rgba(16, 185, 129, 0.05); padding: 1rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);'>
                <div style='color: #64748b; font-size: 0.875rem; margin-bottom: 0.5rem;'>
                    {icon('group', '#10b981', 18)} Total de Usuários
                </div>
                <div style='color: #10b981; font-size: 1.5rem; font-weight: 600;'>{db_stats['total_users']}</div>
                <div style='color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;'>Usuários cadastrados</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== AÇÕES INDIVIDUAIS =====
    st.markdown(f"### {icon('person', '#3b82f6', 24)} Gerenciar Aluno Individual", unsafe_allow_html=True)
    
    if not student_users:
        st.info("Nenhum aluno cadastrado.")
    else:
        # Seletor de aluno
        student_names = [f"{student['name']} ({student['email']})" for student in student_users]
        selected_student_idx = st.selectbox(
            "Selecione um aluno:",
            range(len(student_names)),
            format_func=lambda x: student_names[x],
            key="admin_student_selector"
        )
        
        selected_student = student_users[selected_student_idx]
        student_id = selected_student['id']
        
        st.markdown(f"**Aluno selecionado:** {selected_student['name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {icon('delete', '#ef4444', 20)} Resetar Questões", unsafe_allow_html=True)
            st.caption("Remove todas as questões respondidas por este aluno")
            
            if st.button("Resetar Questões do Aluno", key="reset_student_analytics", type="secondary"):
                # Confirmação
                if 'confirm_reset_student' not in st.session_state:
                    st.session_state.confirm_reset_student = True
                    st.warning("Clique novamente para confirmar")
                else:
                    with st.spinner("Resetando questões..."):
                        success = reset_student_analytics(student_id)
                        if success:
                            log_admin_action(
                                "reset_student_analytics",
                                f"Resetadas questões do aluno {selected_student['name']} (ID: {student_id})",
                                student_id
                            )
                            st.success(f"Questões de {selected_student['name']} resetadas com sucesso!")
                            del st.session_state.confirm_reset_student
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Erro ao resetar questões")
                            del st.session_state.confirm_reset_student
        
        with col2:
            st.markdown(f"#### {icon('chat_bubble', '#ec4899', 20)} Limpar Chat", unsafe_allow_html=True)
            st.caption("Remove todas as mensagens de chat deste aluno")
            
            if st.button("Limpar Chat do Aluno", key="clear_student_chat", type="secondary"):
                # Confirmação
                if 'confirm_clear_student_chat' not in st.session_state:
                    st.session_state.confirm_clear_student_chat = True
                    st.warning("Clique novamente para confirmar")
                else:
                    with st.spinner("Limpando chat..."):
                        success = clear_student_chat_interactions(student_id)
                        if success:
                            log_admin_action(
                                "clear_student_chat",
                                f"Limpado chat do aluno {selected_student['name']} (ID: {student_id})",
                                student_id
                            )
                            st.success(f"Chat de {selected_student['name']} limpo com sucesso!")
                            del st.session_state.confirm_clear_student_chat
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Erro ao limpar chat")
                            del st.session_state.confirm_clear_student_chat
        
        st.markdown("---")
        
        # ===== EXCLUIR CONTA DO ALUNO =====
        st.markdown(f"#### {icon('person_remove', '#ef4444', 20)} Excluir Conta do Aluno", unsafe_allow_html=True)
        st.caption("Remove o aluno completamente do banco de dados (conta, questões e chat)")
        
        confirm_delete_account = st.checkbox(
            f"Confirmo que desejo EXCLUIR a conta de **{selected_student['name']}** permanentemente",
            key="confirm_delete_account_checkbox"
        )
        
        if st.button(
            "EXCLUIR CONTA DO ALUNO",
            key="delete_student_account",
            type="primary",
            disabled=not confirm_delete_account
        ):
            if 'confirm_delete_account' not in st.session_state:
                st.session_state.confirm_delete_account = True
                st.error("ÚLTIMA CHANCE: Clique novamente para CONFIRMAR a exclusão PERMANENTE desta conta!")
            else:
                with st.spinner("Excluindo conta..."):
                    # Primeiro limpa dados vinculados
                    reset_student_analytics(student_id)
                    clear_student_chat_interactions(student_id)
                    # Depois exclui a conta
                    success, msg = delete_user(student_id)
                    if success:
                        log_admin_action(
                            "delete_student_account",
                            f"Excluída conta do aluno {selected_student['name']} ({selected_student['email']}), ID: {student_id}",
                            student_id
                        )
                        st.success(f"Conta de {selected_student['name']} excluída com sucesso!")
                        del st.session_state.confirm_delete_account
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erro ao excluir conta: {msg}")
                        del st.session_state.confirm_delete_account
    
    st.markdown("---")
    
    # ===== AÇÕES GLOBAIS =====
    st.markdown(f"### {icon('public', '#f59e0b', 24)} Gerenciar Todos os Alunos", unsafe_allow_html=True)
    st.error("**PERIGO**: Estas ações afetam TODOS os alunos e são IRREVERSÍVEIS!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {icon('delete_forever', '#ef4444', 20)} Resetar Todas as Questões", unsafe_allow_html=True)
        st.caption("Remove TODAS as questões respondidas de TODOS os alunos")
        
        # Checkbox de confirmação
        confirm_all_analytics = st.checkbox(
            "Eu entendo que esta ação é irreversível",
            key="confirm_checkbox_all_analytics"
        )
        
        if st.button(
            "RESETAR TODAS AS QUESTÕES",
            key="reset_all_analytics",
            type="primary",
            disabled=not confirm_all_analytics
        ):
            # Dupla confirmação
            if 'confirm_reset_all' not in st.session_state:
                st.session_state.confirm_reset_all = True
                st.error("ÚLTIMA CHANCE: Clique novamente para CONFIRMAR a deleção de TODOS os dados!")
            else:
                with st.spinner("Resetando TODAS as questões..."):
                    result = reset_all_students_analytics()
                    if result['deleted'] > 0:
                        log_admin_action(
                            "reset_all_analytics",
                            f"Resetadas TODAS as questões: {result['deleted']} registros deletados, {result['errors']} erros"
                        )
                        st.success(f"{result['deleted']} questões resetadas com sucesso!")
                        if result['errors'] > 0:
                            st.warning(f"{result['errors']} erros durante a operação")
                        del st.session_state.confirm_reset_all
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Erro ao resetar questões")
                        del st.session_state.confirm_reset_all
    
    with col2:
        st.markdown(f"#### {icon('forum', '#ec4899', 20)} Limpar Todos os Chats", unsafe_allow_html=True)
        st.caption("Remove TODAS as mensagens de chat de TODOS os usuários")
        
        # Checkbox de confirmação
        confirm_all_chat = st.checkbox(
            "Eu entendo que esta ação é irreversível",
            key="confirm_checkbox_all_chat"
        )
        
        if st.button(
            "LIMPAR TODOS OS CHATS",
            key="clear_all_chat",
            type="primary",
            disabled=not confirm_all_chat
        ):
            # Dupla confirmação
            if 'confirm_clear_all_chat' not in st.session_state:
                st.session_state.confirm_clear_all_chat = True
                st.error("ÚLTIMA CHANCE: Clique novamente para CONFIRMAR a deleção de TODAS as mensagens!")
            else:
                with st.spinner("Limpando TODOS os chats..."):
                    result = clear_all_chat_interactions()
                    if result['deleted'] > 0:
                        log_admin_action(
                            "clear_all_chat",
                            f"Limpados TODOS os chats: {result['deleted']} registros deletados, {result['errors']} erros"
                        )
                        st.success(f"{result['deleted']} mensagens deletadas com sucesso!")
                        if result['errors'] > 0:
                            st.warning(f"{result['errors']} erros durante a operação")
                        del st.session_state.confirm_clear_all_chat
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Erro ao limpar chats")
                        del st.session_state.confirm_clear_all_chat
    
    st.markdown("---")

    # RESET COMPLETO — apaga analytics + chat + progresso dos alunos
    st.markdown(f"### {icon('report_problem', '#ef4444', 24)} Reset Completo (Início de Nova Rodada)", unsafe_allow_html=True)
    st.markdown(f"<div style='color: #64748b; font-size: 0.85rem; margin-bottom: 0.5rem;'>{icon('info_outline', '#3b82f6', 16)} Apaga analytics, chats E o progresso salvo de todos os alunos. Use ao iniciar uma nova bateria de questões.</div>", unsafe_allow_html=True)
    confirm_full = st.checkbox("Confirmo que quero apagar TODOS os dados dos alunos", key="confirm_full_reset")
    if st.button("RESET COMPLETO", key="full_reset_btn", type="primary", disabled=not confirm_full):
        if 'confirm_full_reset_stage2' not in st.session_state:
            st.session_state.confirm_full_reset_stage2 = True
            st.error("ÚLTIMA CONFIRMAÇÃO — Clique novamente para apagar TUDO!", icon=":material/warning:")
        else:
            with st.spinner("Apagando todos os dados..."):
                r1 = reset_all_students_analytics()
                r2 = clear_all_chat_interactions()
                r3 = reset_all_student_progress()
                log_admin_action("reset_completo", f"Analytics: {r1['deleted']} docs | Chat: {r2['deleted']} docs | Progress: {r3['updated']} alunos")
                del st.session_state.confirm_full_reset_stage2
                st.cache_data.clear()
                st.success(f"Reset completo! Analytics: {r1['deleted']} | Chat: {r2['deleted']} | Alunos resetados: {r3['updated']}", icon=":material/check_circle:")
                st.rerun()

    st.markdown("---")


    st.markdown(f"### {icon('password', '#f59e0b', 24)} Alterar Sua Senha", unsafe_allow_html=True)
    st.write("Aqui você pode alterar sua própria senha de acesso.")
    
    with st.expander("Abrir painel de alteração de senha", expanded=False):
        current_prof = st.session_state.get('user_id')
        if current_prof:
            with st.form("change_prof_password_form"):
                current_pw = st.text_input("Senha Atual", type="password")
                new_pw = st.text_input("Nova Senha", type="password")
                confirm_pw = st.text_input("Confirmar Nova Senha", type="password")
                
                submit_pw = st.form_submit_button("Alterar Senha")
                
                if submit_pw:
                    if not current_pw or not new_pw or not confirm_pw:
                        st.error("Todos os campos de senha são obrigatórios.")
                    elif new_pw != confirm_pw:
                        st.error("A nova senha e a confirmação não coincidem.")
                    else:
                        from auth_firebase import change_password
                        ok, msg = change_password(current_prof, current_pw, new_pw)
                        if ok:
                            st.success(f"Senha alterada com sucesso! {msg}")
                        else:
                            st.error(f"Falha ao alterar senha: {msg}")
        else:
            st.warning("Usuário não identificado na sessão.")

    st.markdown("---")
    
    # ===== INFORMAÇÕES =====
    st.markdown(f"### {icon('info', '#3b82f6', 24)} Informações", unsafe_allow_html=True)
    
    with st.expander("Sobre as Operações de Admin"):
        st.markdown("""
        **Resetar Questões:**
        - Remove todos os registros de `case_analytics` do aluno
        - O aluno poderá responder as questões novamente
        - Não afeta o cadastro do aluno
        
        **Limpar Chat:**
        - Remove todos os registros de `chat_interactions` do aluno
        - Libera espaço no banco de dados
        - Não afeta as questões respondidas
        
        **Logs de Admin:**
        - Todas as ações são registradas em `admin_logs`
        - Inclui timestamp, ação realizada e usuário admin
        - Útil para auditoria
        
        **Segurança:**
        - Operações individuais requerem confirmação dupla
        - Operações globais requerem checkbox + confirmação dupla
        - Não há como desfazer estas operações
        """)

