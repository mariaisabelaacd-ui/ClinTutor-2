import streamlit as st
# Force redeploy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import textwrap
from io import BytesIO
from analytics import (
    get_all_users_analytics, get_global_stats,
    get_global_knowledge_component_stats, get_average_user_level,
    get_hardest_categories, get_student_complete_profile,
    get_student_weakness_analysis, format_duration,
    get_user_chat_interactions, get_worst_answers_by_category
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
    headers = ['Questoes', 'Taxa Acertos', 'Nivel', 'Tempo Medio', 'Pontos']
    for h in headers:
        pdf.cell(col_w, 8, h, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 9)
    total = case_stats.get('total_cases', 0)
    acc = case_stats.get('accuracy_rate', 0)
    nivel = advanced_stats.get('nivel_estimado', 'N/A') if advanced_stats else 'N/A'
    avg_time = format_duration(case_stats.get('avg_time_per_case', 0))
    points = case_stats.get('total_points', 0)
    values = [str(total), f'{acc:.1f}%', str(nivel), avg_time, str(points)]
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
            pdf.cell(30, 7, f'{rate:.0f}%', 1, 0, 'C')
            pdf.ln()
        pdf.ln(8)
    
    # ---- ANÁLISE DE FRAQUEZAS ----
    weak_comps = weakness.get('weakest_components', [])
    if weak_comps:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(239, 68, 68)  # vermelho
        pdf.cell(0, 10, 'Pontos Fracos Identificados', ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        for i, comp in enumerate(weak_comps[:5], 1):
            name = comp.get('component', 'N/A')
            rate = comp.get('accuracy_rate', 0)
            pdf.cell(0, 6, f'  {i}. {name} (acerto: {rate:.0f}%)', ln=True)
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
            ans_text = safe_text(item.get('Resposta_Aluno', ''))
            
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

def generate_class_pdf(turma_name: str, student_users: List[Dict], global_stats: Dict, component_stats: list) -> bytes:
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

    # ---- DESEMPENHO POR CATEGORIA (ordenado: pior primeiro) ----
    if component_stats:
        sorted_comps = sorted(component_stats, key=lambda x: x.get('taxa_acerto', 0))
        hardest = sorted_comps[0] if sorted_comps else None

        # Destaque da categoria mais dificil
        if hardest:
            pdf.set_fill_color(254, 226, 226)
            pdf.set_draw_color(220, 38, 38)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(W, 7, safe_text(f'  Categoria Mais Dificil: {hardest["componente"]}  —  Taxa de acerto: {hardest["taxa_acerto"]:.1f}%'), 1, 1, 'L', True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(3)

        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(W, 7, '  Desempenho por Categoria de Conhecimento (do mais dificil ao mais facil)', ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        # Header da tabela
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(80, 7, 'Categoria', 1, 0, 'C', True)
        pdf.cell(28, 7, 'Tentativas', 1, 0, 'C', True)
        pdf.cell(28, 7, 'Acertos', 1, 0, 'C', True)
        pdf.cell(28, 7, 'Erros', 1, 0, 'C', True)
        pdf.cell(26, 7, 'Taxa (%)', 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font('Helvetica', '', 8)
        for comp in sorted_comps:
            taxa = comp.get('taxa_acerto', 0)
            total = comp.get('total_questoes', comp.get('total_attempts', 0))
            acertos = comp.get('acertos', comp.get('total_correct', 0))
            erros = total - acertos
            nome = safe_text(comp.get('componente', 'N/A'))[:40]

            # Cor de fundo pela taxa
            if taxa < 40:
                pdf.set_fill_color(254, 226, 226)  # vermelho claro
            elif taxa < 65:
                pdf.set_fill_color(254, 249, 195)  # amarelo claro
            else:
                pdf.set_fill_color(220, 252, 231)  # verde claro

            pdf.cell(80, 6, nome, 1, 0, 'L', True)
            pdf.cell(28, 6, str(total), 1, 0, 'C', True)
            pdf.cell(28, 6, str(acertos), 1, 0, 'C', True)
            pdf.cell(28, 6, str(erros), 1, 0, 'C', True)
            pdf.cell(26, 6, f'{taxa:.1f}%', 1, 0, 'C', True)
            pdf.ln()
        pdf.ln(8)

    # ---- RANKING DOS ALUNOS ----
    from analytics import get_all_users_analytics, get_user_case_analytics
    all_analytics = get_all_users_analytics()

    pdf.set_fill_color(16, 185, 129)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(W, 7, '  Ranking de Alunos', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)

    pdf.set_fill_color(241, 245, 249)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(55, 7, 'Nome', 1, 0, 'C', True)
    pdf.cell(30, 7, 'Turma', 1, 0, 'C', True)
    pdf.cell(20, 7, 'RA', 1, 0, 'C', True)
    pdf.cell(25, 7, 'Questoes', 1, 0, 'C', True)
    pdf.cell(25, 7, 'Acertos', 1, 0, 'C', True)
    pdf.cell(35, 7, 'Taxa Acerto (%)', 1, 0, 'C', True)
    pdf.ln()

    ranking = []
    for s in student_users:
        uid = s['id']
        cas = all_analytics.get(uid, {}).get('case_analytics', [])
        if not cas: continue
        total_q = len(cas)
        corr_q = sum(1 for e in cas if e.get('case_result', {}).get('is_correct', False))
        acc = (corr_q / total_q * 100) if total_q > 0 else 0
        ranking.append((s, total_q, corr_q, acc))

    ranking.sort(key=lambda x: x[3], reverse=True)

    pdf.set_font('Helvetica', '', 8)
    for i, (s, total_q, corr_q, acc) in enumerate(ranking):
        if acc >= 70:
            pdf.set_fill_color(220, 252, 231)
        elif acc >= 40:
            pdf.set_fill_color(254, 249, 195)
        else:
            pdf.set_fill_color(254, 226, 226)

        nome = safe_text(s.get('name', 'N/A'))[:25]
        turma = safe_text(s.get('turma', '-'))[:14]
        ra = safe_text(s.get('ra', '-'))[:10]
        pdf.cell(55, 6, nome, 1, 0, 'L', True)
        pdf.cell(30, 6, turma, 1, 0, 'C', True)
        pdf.cell(20, 6, ra, 1, 0, 'C', True)
        pdf.cell(25, 6, str(total_q), 1, 0, 'C', True)
        pdf.cell(25, 6, str(corr_q), 1, 0, 'C', True)
        pdf.cell(35, 6, f'{acc:.1f}%', 1, 0, 'C', True)
        pdf.ln()

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
        correct_q = sum(1 for e in case_list if e.get('case_result', {}).get('is_correct', False))
        parcial_q = sum(1 for e in case_list if 'PARCIAL' in e.get('case_result', {}).get('classification', '').upper())
        errado_q  = total_q - correct_q
        total_pts = sum(e.get('case_result', {}).get('points_gained', 0) for e in case_list)
        accuracy  = (correct_q / total_q * 100) if total_q > 0 else 0.0
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
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font('Helvetica', 'B', 8)
        col = W / 5
        for h in ['Questoes', 'Taxa Acerto', 'Corretas', 'Parciais', 'Erradas']:
            pdf.cell(col, 6, h, 1, 0, 'C', True)
        pdf.ln()
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(col, 7, str(total_q),  1, 0, 'C')
        pdf.cell(col, 7, f'{accuracy:.1f}%', 1, 0, 'C')
        pdf.cell(col, 7, str(correct_q), 1, 0, 'C')
        pdf.cell(col, 7, str(parcial_q), 1, 0, 'C')
        pdf.cell(col, 7, str(errado_q),  1, 0, 'C')
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
            pdf.cell(W, 6, safe(f'  Status: {status_txt}   |   Pontos ganhos: {pts}'), 0, 1, 'L', True)
            pdf.set_text_color(0, 0, 0)

            # Resposta do aluno
            ans = result.get('user_answer', 'N/A')
            pdf.set_x(10)
            pdf.set_fill_color(237, 242, 255)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(W, 5, '  Resposta do Aluno:', 0, 1, 'L', True)
            pdf.set_x(10)
            pdf.set_font('Helvetica', '', 8)
            pdf.multi_cell(W, 5, safe(str(ans) if ans else 'Nao respondeu'))

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


def generate_ai_insights_pdf(hardest_categories: List[Dict]) -> bytes:
    """Gera PDF com análise pedagógica profunda baseada em IA para as piores categorias"""
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    W = 180

    def safe(txt):
        if txt is None: return ""
        return str(txt).encode('latin-1', 'replace').decode('latin-1')

    # ── CAPA ─────────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(139, 92, 246) # Roxo (Cor da "IA")
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
                 "focada exclusivamente nos topicos onde a turma demonstrou maior dificuldade."
    pdf.multi_cell(0, 6, safe(texto_capa), align='C')
    pdf.set_text_color(0, 0, 0)
    
    # ── CONTEÚDO ──────────────────────────────────────────────────
    
    worst_answers_dict = get_worst_answers_by_category(limit_per_category=10)
    categories_to_analyze = [c['componente'] for c in hardest_categories[:3]]
    
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(139, 92, 246)
    pdf.cell(0, 10, 'Foco de Intervencao Recomendado', ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    if not categories_to_analyze:
         pdf.set_font('Helvetica', '', 11)
         pdf.cell(0, 10, "Dados insuficientes para analise de dificuldades no momento.", ln=True)
         return bytes(pdf.output())
    
    for idx, cat_name in enumerate(categories_to_analyze, 1):
        samples = worst_answers_dict.get(cat_name, [])
        insight_text = generate_category_insights(cat_name, samples)
        
        pdf.set_fill_color(243, 232, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, safe(f"  Top {idx} Dificuldade: {cat_name}"), ln=True, fill=True)
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, safe(insight_text))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)
        
        if samples:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, "Exemplos reais de respostas dos alunos:", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', 'I', 9)
            for i, ans in enumerate(samples[:2]):
                pdf.set_x(20)
                pdf.multi_cell(W-20, 5, safe(f'"{ans}"'))
        
        pdf.ln(10)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(10)

    pdf.set_y(-15)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, 'Helix.AI - Plataforma de Tutoria em Biologia Molecular', 0, 0, 'C')

    return bytes(pdf.output())


def show_advanced_professor_dashboard():
    """Dashboard redesenhado para professores com foco em insights acionáveis"""
    # Garante carregamento dos ícones
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined" rel="stylesheet">', unsafe_allow_html=True)
    
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.markdown(f"# {icon('dashboard', '#10b981', 32)} Dashboard do Professor", unsafe_allow_html=True)
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Dados", help="Limpar cache e buscar dados em tempo real", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.caption("ℹ️ Os dados do painel são mantidos em cache por 5 minutos para alta velocidade. Use o botão acima se precisar dos últimos dados exatos.")
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
    
    # Carrega estatísticas globais
    global_stats = get_global_stats()
    component_stats = get_global_knowledge_component_stats()
    level_stats = get_average_user_level()
    hardest_categories = get_hardest_categories(top_n=5)
    
    # ===== KPIs PRINCIPAIS =====
    st.markdown(f"### {icon('push_pin', '#10b981', 24)} Métricas Principais", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(metric_card(
            "Total de Alunos",
            str(len(student_users)),
            icon_name="people",
            icon_color="#3b82f6"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(metric_card(
            "Média Geral",
            f"{global_stats.get('average_accuracy_rate', 0):.1f}%",
            icon_name="track_changes", # Fixed: target -> track_changes
            icon_color="#10b981"
        ), unsafe_allow_html=True)
    
    
    with col3:
        # Categoria com maior dificuldade - Custom display para evitar truncamento
        if hardest_categories:
            hardest_cat = hardest_categories[0]['componente']
            hardest_acc = hardest_categories[0]['taxa_acerto']
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%); 
                            padding: 1rem; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3);'>
                    <div style='color: #475569; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;'>
                        {icon('warning', '#ef4444', 18)} Categoria Mais Difícil
                    </div>
                    <div style='color: #ef4444; font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; 
                                word-wrap: break-word; line-height: 1.2;'>
                        {hardest_cat}
                    </div>
                    <div style='color: #ef4444; font-size: 0.875rem;'>
                        Taxa: {hardest_acc:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.metric("Categoria Mais Difícil", "N/A", help="Componente com menor taxa de acerto geral")
    
    
    with col4:
        # Nível médio - Custom display para consistência visual
        nivel_map = {1: "Básico", 2: "Intermediário", 3: "Avançado"}
        nivel_medio = nivel_map.get(level_stats.get('nivel_medio', 1), "Básico")
        
        # Cores por nível
        nivel_colors = {
            "Básico": "#3b82f6",
            "Intermediário": "#eab308", 
            "Avançado": "#22c55e"
        }
        color = nivel_colors.get(nivel_medio, "#3b82f6")
        
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%); 
                        padding: 1rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2);'>
                <div style='color: #475569; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;'>
                    {icon('bar_chart', '#475569', 18)} Nível Médio
                </div>
                <div style='color: {color}; font-size: 1.875rem; font-weight: 600;'>
                    {nivel_medio}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(metric_card(
            "Questões Respondidas",
            str(global_stats.get('total_cases', 0)),
            icon_name="quiz",
            icon_color="#8b5cf6"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PDF de Visão Geral (Agora em 3 colunas)
    col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
    with col_pdf1:
        pdf_bytes_class = generate_class_pdf(turma_filter, student_users, global_stats, component_stats)
        st.download_button(
            label=f"📥 Relatório da Turma ({turma_filter})",
            data=pdf_bytes_class,
            file_name=f"relatorio_turma_{turma_filter.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    with col_pdf2:
        pdf_bytes_global = generate_global_interactions_pdf(student_users, all_analytics)
        st.download_button(
            label=f"📥 Relatório Completo",
            data=pdf_bytes_global,
            file_name=f"relatorio_completo_interacoes_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    with col_pdf3:
        if st.button("✨ Gerar Insights Pedagógicos com IA (PDF)", use_container_width=True, type="primary"):
            with st.spinner("A IA está analisando as piores respostas por categoria. Isso pode levar alguns segundos..."):
                try:
                    pdf_ia = generate_ai_insights_pdf(hardest_categories)
                    st.download_button(
                        label=f"📥 Baixar Insights com IA",
                        data=pdf_ia,
                        file_name=f"relatorio_ia_pedagogico_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_btn_ia_pdf"
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar o PDF da IA: {e}")
            
    st.markdown("---")
    
    # ===== VISUALIZAÇÕES =====
    
    # Linha 1: Desempenho por Componente e Distribuição por Nível
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {icon('menu_book', '#8b5cf6', 24)} Desempenho por Componente de Conhecimento", unsafe_allow_html=True)
        if component_stats:
            df_comp = pd.DataFrame(component_stats)
            
            # Trunca nomes muito longos para melhor visualização
            df_comp['componente_display'] = df_comp['componente'].apply(
                lambda x: x if len(x) <= 30 else x[:27] + '...'
            )
            
            fig_comp = px.bar(
                df_comp,
                x='taxa_acerto',
                y='componente_display',
                orientation='h',
                title="Taxa de Acerto por Componente (%)",
                text_auto='.1f',
                color='taxa_acerto',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                hover_data={'componente': True, 'componente_display': False}  # Mostra nome completo no hover
            )
            fig_comp.update_layout(
                xaxis_title="Taxa de Acerto (%)",
                yaxis_title=None,
                showlegend=False,
                height=400,
                margin=dict(l=200, r=20, t=40, b=40),  # Mais espaço à esquerda para labels
                yaxis=dict(tickfont=dict(size=11))  # Fonte menor para caber melhor
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tooltip explicativo
            st.caption(f"{icon('lightbulb', '#eab308', 16)} Componentes no topo têm menor taxa de acerto (mais difíceis)", unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes para análise por componente")
    
    with col2:
        st.markdown(f"### {icon('bar_chart', '#3b82f6', 24)} Distribuição de Alunos por Nível", unsafe_allow_html=True)
        if level_stats.get('total_alunos', 0) > 0:
            dist = level_stats['distribuicao']
            
            df_level = pd.DataFrame({
                'Nível': ['Básico', 'Intermediário', 'Avançado'],
                'Quantidade': [dist['basico'], dist['intermediario'], dist['avancado']]
            })
            
            fig_level = px.pie(
                df_level,
                values='Quantidade',
                names='Nível',
                title="Distribuição de Alunos",
                color='Nível',
                color_discrete_map={
                    'Básico': '#3b82f6',
                    'Intermediário': '#eab308',
                    'Avançado': '#22c55e'
                }
            )
            fig_level.update_traces(textposition='inside', textinfo='percent+label')
            fig_level.update_layout(height=400)
            st.plotly_chart(fig_level, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    st.markdown("---")
    
    # Linha 2: Top 5 Categorias Mais Difíceis
    st.markdown(f"### {icon('warning', '#ef4444', 24)} Top 5 Categorias Mais Difíceis", unsafe_allow_html=True)
    if hardest_categories:
        df_hardest = pd.DataFrame(hardest_categories)
        
        # Trunca nomes muito longos
        df_hardest['componente_display'] = df_hardest['componente'].apply(
            lambda x: x if len(x) <= 30 else x[:27] + '...'
        )
        
        fig_hardest = px.bar(
            df_hardest,
            x='taxa_acerto',
            y='componente_display',
            orientation='h',
            title="Componentes que Precisam de Mais Atenção",
            text_auto='.1f',
            color='taxa_acerto',
            color_continuous_scale='Reds_r',
            range_color=[0, 100],
            hover_data={'componente': True, 'componente_display': False}
        )
        fig_hardest.update_layout(
            xaxis_title="Taxa de Acerto (%)",
            yaxis_title=None,
            showlegend=False,
            height=300,
            margin=dict(l=200, r=20, t=40, b=40),
            yaxis=dict(tickfont=dict(size=11))
        )
        st.plotly_chart(fig_hardest, use_container_width=True)
        
        # Tabela detalhada
        with st.expander("Detalhes das Categorias Difíceis"):
            df_display = df_hardest[['componente', 'taxa_acerto', 'total_questoes', 'acertos', 'tempo_medio_formatado']].copy()
            df_display.columns = ['Componente', 'Taxa de Acerto (%)', 'Total de Questões', 'Acertos', 'Tempo Médio']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Dados insuficientes")
    
    st.markdown("---")
    
    # Linha 3: Ranking de Alunos
    st.markdown(f"### {icon('emoji_events', '#f59e0b', 24)} Ranking de Alunos", unsafe_allow_html=True)
    
    # Prepara dados para ranking
    ranking_data = []
    for user in student_users:
        uid = user['id']
        u_data = all_analytics.get(uid, {})
        case_analytics = u_data.get('case_analytics', [])
        
        if not case_analytics:
            continue
        
        total_cases = len(case_analytics)
        correct_cases = sum(1 for c in case_analytics 
                           if c.get("case_result", {}).get("is_correct", False))
        acc_rate = (correct_cases / total_cases * 100) if total_cases > 0 else 0.0
        
        ranking_data.append({
            'Nome': user['name'],
            'Email': user['email'],
            'Questões': total_cases,
            'Acertos': correct_cases,
            'Taxa de Acerto': acc_rate
        })
    
    if ranking_data:
        df_ranking = pd.DataFrame(ranking_data)
        df_ranking = df_ranking.sort_values('Taxa de Acerto', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {icon('star', '#eab308', 20)} Top 10 Melhores Desempenhos", unsafe_allow_html=True)
            top_10 = df_ranking.head(10).copy()
            top_10['Taxa de Acerto'] = top_10['Taxa de Acerto'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(top_10, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown(f"#### {icon('priority_high', '#ef4444', 20)} Alunos que Precisam de Atenção", unsafe_allow_html=True)
            # Alunos com taxa de acerto < 50% ou menos de 3 questões respondidas
            need_attention = df_ranking[
                (df_ranking['Taxa de Acerto'] < 50) | (df_ranking['Questões'] < 3)
            ].head(10).copy()
            
            if not need_attention.empty:
                need_attention['Taxa de Acerto'] = need_attention['Taxa de Acerto'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(need_attention, use_container_width=True, hide_index=True)
            else:
                st.success("Todos os alunos estão com bom desempenho!")
    else:
        st.info("Nenhum aluno respondeu questões ainda")

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
    <div style='background: var(--secondary-background-color); padding: 1.25rem; border-radius: 12px; 
                border: 1px solid rgba(16, 185, 129, 0.2); margin-bottom: 1.5rem;'>
        <div style='display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;'>
            <div style='flex: 1; min-width: 200px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('person', '#3b82f6', 16)} Nome
                </div>
                <div style='font-size: 1.25rem; font-weight: 600; color: var(--text-color);'>
                    {selected_student['name']}
                </div>
            </div>
            <div style='flex: 0.5; min-width: 100px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('badge', '#8b5cf6', 16)} RA
                </div>
                <div style='font-size: 1.1rem; font-weight: 500; color: var(--text-color);'>
                    {ra_display}
                </div>
            </div>
            <div style='flex: 0.7; min-width: 140px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('school', '#10b981', 16)} Turma
                </div>
                <div style='font-size: 1.1rem; font-weight: 500; color: var(--text-color);'>
                    {turma_display}
                </div>
            </div>
            <div style='flex: 1; min-width: 200px;'>
                <div style='font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {icon('email', '#64748b', 16)} Email
                </div>
                <div style='font-size: 0.9rem; font-weight: 400; color: var(--text-color); opacity: 0.8;'>
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
        st.markdown(metric_card(
            "Questões Respondidas",
            str(basic_stats['case_stats']['total_cases']),
            icon_name="assignment",
            icon_color="#8b5cf6"
        ), unsafe_allow_html=True)
    
    with col2:
        acc = basic_stats['case_stats']['accuracy_rate']
        st.markdown(metric_card(
            "Taxa de Acertos",
            f"{acc:.1f}%",
            icon_name="track_changes",
            icon_color="#10b981"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(metric_card(
            "Tempo Médio",
            basic_stats['case_stats']['average_time_formatted'],
            icon_name="schedule",
            icon_color="#3b82f6"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(metric_card(
            "Interações Chat",
            str(basic_stats['total_chat_interactions']),
            icon_name="chat",
            icon_color="#ec4899"
        ), unsafe_allow_html=True)
    
    with col5:
        # Comparação com turma
        perf_icons = {
            'acima': icon('trending_up', '#10b981', 20),
            'abaixo': icon('trending_down', '#ef4444', 20),
            'na_media': icon('trending_flat', '#64748b', 20)
        }
        perf_icon = perf_icons.get(comparison['performance'], perf_icons['na_media'])
        
        st.markdown(metric_card(
            "vs Turma",
            f"{comparison['performance'].replace('_', ' ').title()}",
            subtitle=f"{comparison['diferenca']:.1f}%",
            icon_name="compare_arrows",
            icon_color="#6366f1"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== SEÇÃO: ANÁLISE DE DIFICULDADES =====
    st.markdown(f"### {icon('warning', '#ef4444', 24)} Análise de Dificuldades", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {icon('error', '#ef4444', 20)} Componente Mais Difícil", unsafe_allow_html=True)
        worst_comp = weakness.get('componente_mais_dificil')
        if worst_comp:
            st.error(f"**{worst_comp['nome']}**")
            st.write(f"- Taxa de acerto: **{worst_comp['acuracia']:.1f}%**")
            st.write(f"- Questões: {worst_comp['acertos']}/{worst_comp['total']}")
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.markdown(f"#### {icon('trending_up', '#3b82f6', 20)} Nível Mais Difícil", unsafe_allow_html=True)
        worst_diff = weakness.get('nivel_mais_dificil')
        if worst_diff:
            st.error(f"**{worst_diff['nivel'].title()}**")
            st.write(f"- Taxa de acerto: **{worst_diff['acuracia']:.1f}%**")
            st.write(f"- Questões: {worst_diff['acertos']}/{worst_diff['total']}")
        else:
            st.info("Dados insuficientes")
    
    # Componentes problemáticos
    problematic = weakness.get('componentes_problematicos', [])
    if problematic:
        st.markdown(f"#### {icon('error_outline', '#ef4444', 20)} Componentes Problemáticos (Taxa < 50%)", unsafe_allow_html=True)
        for comp in problematic[:5]:  # Top 5
            st.warning(f"**{comp['nome']}**: {comp['acuracia']:.1f}% ({comp['acertos']}/{comp['total']})")
    
    # Padrões de erro
    patterns = weakness.get('padroes_erro', [])
    if patterns:
        st.markdown(f"#### {icon('search', '#6366f1', 20)} Padrões Identificados", unsafe_allow_html=True)
        for pattern in patterns:
            st.info(f"**{pattern['padrao']}**: {pattern['descricao']}")
    
    st.markdown("---")
    
    # ===== SEÇÃO: DESEMPENHO POR CATEGORIA =====
    st.markdown(f"### {icon('menu_book', '#8b5cf6', 24)} Desempenho por Categoria", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Por Componente de Conhecimento")
        if advanced_stats['componentes']:
            df_comp = pd.DataFrame(advanced_stats['componentes'])
            
            # Trunca nomes longos
            df_comp['nome_display'] = df_comp['nome'].apply(
                lambda x: x if len(x) <= 25 else x[:22] + '...'
            )
            
            fig_comp = px.bar(
                df_comp,
                x='acuracia',
                y='nome_display',
                orientation='h',
                text_auto='.1f',
                color='acuracia',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                hover_data={'nome': True, 'nome_display': False}
            )
            fig_comp.update_layout(
                xaxis_title="Acurácia (%)",
                yaxis_title=None,
                showlegend=False,
                height=400,
                margin=dict(l=180, r=20, t=20, b=40),
                yaxis=dict(tickfont=dict(size=10))
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    with col2:
        st.markdown("#### Por Nível de Dificuldade")
        if advanced_stats['dificuldade']:
            df_diff = pd.DataFrame(advanced_stats['dificuldade'])
            
            fig_diff = px.bar(
                df_diff,
                x='nivel',
                y='acuracia',
                text_auto='.1f',
                color='nivel',
                color_discrete_map={
                    'básico': '#22c55e',
                    'intermediário': '#eab308',
                    'avançado': '#ef4444'
                }
            )
            fig_diff.update_layout(
                xaxis_title="Nível",
                yaxis_title="Acurácia (%)",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig_diff, use_container_width=True)
        else:
            st.info("Dados insuficientes")
    
    # Tabela detalhada
    with st.expander("Tabela Detalhada por Componente"):
        if advanced_stats['componentes']:
            df_comp_table = pd.DataFrame(advanced_stats['componentes'])
            df_comp_table.columns = ['Componente', 'Acurácia (%)', 'Total', 'Acertos']
            df_comp_table = df_comp_table.sort_values('Acurácia (%)')
            st.dataframe(df_comp_table, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ===== SEÇÃO: HISTÓRICO DETALHADO =====
    st.markdown(f"### {icon('history', '#ef4444', 24)} Histórico de Respostas", unsafe_allow_html=True)
    
    case_analytics = all_analytics.get(student_id, {}).get('case_analytics', [])
    
    if case_analytics:
        # Filtros para histórico
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_status_hist = st.selectbox(
                "Status",
                ["Todos", "Corretas", "Parciais", "Incorretas"],
                key="hist_status"
            )
        
        with col2:
            # Pega componentes únicos
            all_comps = list(set([c['nome'] for c in advanced_stats['componentes']]))
            filter_comp_hist = st.selectbox(
                "Componente",
                ["Todos"] + sorted(all_comps),
                key="hist_comp"
            )
        
        with col3:
            filter_difficulty = st.selectbox(
                "Dificuldade",
                ["Todos", "básico", "intermediário", "avançado"],
                key="hist_diff"
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
            comps = q_info.get('componentes_conhecimento', [])
            diff = q_info.get('dificuldade', 'desconhecido')
            
            # Aplica filtros
            if filter_status_hist == "Corretas" and (not is_correct or is_partial):
                continue
            if filter_status_hist == "Incorretas" and is_correct:
                continue
            if filter_status_hist == "Parciais" and not is_partial:
                continue
            
            if filter_comp_hist != "Todos" and filter_comp_hist not in comps:
                continue
            
            if filter_difficulty != "Todos" and diff != filter_difficulty:
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
            
            filtered_entries.append({
                'entry': entry,
                'q_info': q_info,
                'result': result,
                'timestamp': timestamp,
                'is_correct': is_correct,
                'is_partial': is_partial,
                'classification': classification,
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
                    key = "📅 Hoje"
                elif item_date == yesterday:
                    key = "📅 Ontem"
                else:
                    key = f"📅 {item_date.strftime('%d/%m/%Y')}"
                
                if key not in grouped_entries:
                    grouped_entries[key] = []
                grouped_entries[key].append(item)
            
            # Exibe Timeline
            for date_label, items in grouped_entries.items():
                st.markdown(f"### {date_label}")
                
                for item in items:
                    entry = item['entry']
                    q_info = item['q_info']
                    result = item['result']
                    timestamp = item['timestamp']
                    is_correct = item['is_correct']
                    is_partial = item['is_partial']
                    classification = item['classification']
                    comps = item['comps']
                    diff = item['diff']
                    
                    # Layout de Timeline
                    col_time, col_content = st.columns([0.15, 0.85])
                    
                    with col_time:
                        st.markdown(f"""
                            <div style="text-align: right; padding-top: 10px; color: #475569; font-size: 0.85rem;">
                                {timestamp.strftime('%H:%M')}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_content:
                        # Título do expander mais limpo
                        if is_partial:
                            status_icon = icon('circle', '#eab308', 14)
                        elif entry.get('case_result', {}).get('is_correct'):
                            status_icon = icon('circle', '#10b981', 14)
                        else:
                            status_icon = icon('circle', '#ef4444', 14)
                            
                        question_preview = q_info.get('pergunta', 'N/A')[:60] + "..."
                        
                        # Usando container para simular timeline visual
                        with st.container():
                            st.markdown(f"""
                                <div style="border-left: 2px solid #e2e8f0; margin-left: -10px; padding-left: 20px; padding-bottom: 20px;">
                                    <div style="font-weight: 500; margin-bottom: 5px; color: #334155;">
                                        {status_icon} {question_preview}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Detalhes (expansível)
                            with st.expander("Ver detalhes (Completo)", expanded=False):
                                # Busca interações do chat para esta questão
                                # Tenta buscar por case_id primeiro
                                chat_interactions = get_user_chat_interactions(student_id, entry.get('case_id'))
                                
                                # Fallback simples se não achar (opcional, pode ser complexo implementar aqui agora)
                                
                                # Exibe card detalhado
                                from ui_helpers import answer_detail_card
                                
                                detail_html = answer_detail_card(
                                    question_text=q_info.get('pergunta', 'N/A'),
                                    student_answer=result.get('user_answer', None), # Passa None para ativar fallback
                                    expected_answer=q_info.get('resposta_esperada', None),
                                    feedback=result.get('feedback', None),
                                    classification=classification if classification else ('CORRETA' if is_correct else 'INCORRETA'),
                                    components=comps,
                                    difficulty=diff,
                                    time_spent=format_duration(entry.get('duration_seconds', 0)),
                                    points=result.get('points_gained', 0)
                                )
                                
                                st.markdown(detail_html, unsafe_allow_html=True)
                                
                                # Mostra interações do chat se houver
                                if chat_interactions:
                                    st.markdown(f"#### {icon('chat', '#ec4899', 20)} Interações do Chat ({len(chat_interactions)})", unsafe_allow_html=True)
                                    
                                    for chat_idx, interaction in enumerate(chat_interactions):
                                        chat_time = interaction.get('timestamp', '')
                                        if isinstance(chat_time, str):
                                            try:
                                                chat_time = datetime.fromisoformat(chat_time).strftime('%H:%M:%S')
                                            except:
                                                chat_time = 'N/A'
                                        
                                        user_msg = interaction.get('user_message', '')
                                        bot_msg = interaction.get('bot_response', '')
                                        
                                        st.markdown(f"""
<div style='background: #fdf2f8; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #ec4899;'>
<div style='color: #475569; font-size: 0.75rem; margin-bottom: 0.25rem;'>
{icon('schedule', '#64748b', 14)} {chat_time}
</div>
<div style='color: #1e293b; font-size: 0.875rem; margin-bottom: 0.5rem;'>
<strong>{icon('person', '#3b82f6', 16)} Aluno:</strong> {user_msg}
</div>
<div style='color: #475569; font-size: 0.875rem;'>
<strong>{icon('smart_toy', '#ec4899', 16)} Tutor:</strong> {bot_msg}
</div>
</div>""", unsafe_allow_html=True)

            
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
                    'Resposta_Aluno': item['result'].get('user_answer', 'N/A')
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
        # Prepara dados para gráfico
        weeks = sorted(weekly_perf.keys())
        accuracies = []
        
        for week in weeks:
            data = weekly_perf[week]
            acc = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            accuracies.append(acc)
        
        df_evolution = pd.DataFrame({
            'Semana': weeks,
            'Taxa de Acerto (%)': accuracies
        })
        
        fig_evolution = px.line(
            df_evolution,
            x='Semana',
            y='Taxa de Acerto (%)',
            title=f"Evolução nas Últimas 4 Semanas (Tendência: {trend.title()})",
            markers=True
        )
        fig_evolution.update_layout(height=400)
        st.plotly_chart(fig_evolution, use_container_width=True)
        
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
    
    st.warning("**ATENÇÃO**: Esta área contém operações que podem deletar dados permanentemente!")
    
    st.markdown("---")
    
    # ===== ESTATÍSTICAS DO BANCO =====
    st.markdown(f"### {icon('storage', '#3b82f6', 24)} Estatísticas do Banco de Dados", unsafe_allow_html=True)
    
    db_stats = get_database_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📚 Total de Questões Respondidas",
            db_stats['total_analytics'],
            help="Total de registros de case_analytics no banco"
        )
    
    with col2:
        st.metric(
            "Total de Interações Chat",
            db_stats['total_chat_interactions'],
            help="Total de registros de chat_interactions no banco"
        )
    
    with col3:
        st.metric(
            "👥 Total de Usuários",
            db_stats['total_users'],
            help="Total de usuários cadastrados"
        )
    
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
    st.markdown(f"### 🚨 Reset Completo (Início de Nova Rodada)")
    st.caption("Apaga analytics, chats E o progresso salvo de todos os alunos. Use ao iniciar uma nova bateria de questões.")
    confirm_full = st.checkbox("Confirmo que quero apagar TODOS os dados dos alunos", key="confirm_full_reset")
    if st.button("RESET COMPLETO", key="full_reset_btn", type="primary", disabled=not confirm_full):
        if 'confirm_full_reset_stage2' not in st.session_state:
            st.session_state.confirm_full_reset_stage2 = True
            st.error("⚠️ ÚLTIMA CONFIRMAÇÃO — Clique novamente para apagar TUDO!")
        else:
            with st.spinner("Apagando todos os dados..."):
                r1 = reset_all_students_analytics()
                r2 = clear_all_chat_interactions()
                r3 = reset_all_student_progress()
                log_admin_action("reset_completo", f"Analytics: {r1['deleted']} docs | Chat: {r2['deleted']} docs | Progress: {r3['updated']} alunos")
                del st.session_state.confirm_full_reset_stage2
                st.cache_data.clear()
                st.success(f"✅ Reset completo! Analytics: {r1['deleted']} | Chat: {r2['deleted']} | Alunos resetados: {r3['updated']}")
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

