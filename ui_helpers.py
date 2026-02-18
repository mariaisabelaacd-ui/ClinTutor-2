"""
Helper functions for UI components
"""

def icon(name: str, color: str = "#10b981", size: int = 20) -> str:
    """
    Gera um ícone Material Icons colorido em HTML
    
    Args:
        name: Nome do ícone Material Icons (ex: 'people', 'analytics', 'warning')
        color: Cor hex do ícone (padrão: verde primário)
        size: Tamanho em pixels (padrão: 20)
    
    Returns:
        String HTML do ícone
    """
    return f'<span class="material-icons-outlined" style="color: {color}; font-size: {size}px; vertical-align: middle;">{name}</span>'


def metric_card(label: str, value: str, icon_name: str = None, icon_color: str = "#10b981", 
                subtitle: str = None, gradient_from: str = "rgba(16, 185, 129, 0.05)", 
                gradient_to: str = "rgba(5, 150, 105, 0.05)", border_color: str = "rgba(16, 185, 129, 0.2)") -> str:
    """
    Gera um card de métrica customizado com ícone
    
    Args:
        label: Texto do label
        value: Valor principal a exibir
        icon_name: Nome do ícone Material Icons
        icon_color: Cor do ícone
        subtitle: Texto adicional abaixo do valor
        gradient_from: Cor inicial do gradiente de fundo
        gradient_to: Cor final do gradiente de fundo
        border_color: Cor da borda
    
    Returns:
        String HTML do card
    """
    icon_html = icon(icon_name, icon_color, 24) if icon_name else ""
    subtitle_html = f"<div style='color: {icon_color}; font-size: 0.875rem; margin-top: 0.25rem;'>{subtitle}</div>" if subtitle else ""
    
    return f"""
        <div style='background: linear-gradient(135deg, {gradient_from} 0%, {gradient_to} 100%); 
                    padding: 1rem; border-radius: 12px; border: 1px solid {border_color};'>
            <div style='color: #94a3b8; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem;'>
                {icon_html} {label}
            </div>
            <div style='color: {icon_color}; font-size: 1.875rem; font-weight: 600; 
                        word-wrap: break-word; line-height: 1.2;'>
                {value}
            </div>
            {subtitle_html}
        </div>
    """


def answer_detail_card(question_text: str, student_answer: str, expected_answer: str, 
                       feedback: str, classification: str, components: list, difficulty: str,
                       time_spent: str, points: float) -> str:
    """
    Gera um card detalhado mostrando a resposta do aluno
    
    Args:
        question_text: Texto da pergunta
        student_answer: Resposta fornecida pelo aluno
        expected_answer: Resposta esperada/correta
        feedback: Feedback da IA
        classification: Classificação (CORRETA/PARCIALMENTE CORRETA/INCORRETA)
        components: Lista de componentes de conhecimento
        difficulty: Nível de dificuldade
        time_spent: Tempo gasto formatado
        points: Pontos ganhos
    
    Returns:
        String HTML do card detalhado
    """
    # Define cores baseadas na classificação
    if "CORRETA" in classification and "INCORRETA" not in classification:
        color = "#10b981"  # Verde
        bg_gradient_from = "rgba(16, 185, 129, 0.05)"
        bg_gradient_to = "rgba(5, 150, 105, 0.05)"
        border_color = "rgba(16, 185, 129, 0.3)"
        icon_name = "check_circle"
        status_label = "Correta"
    elif "PARCIAL" in classification:
        color = "#eab308"  # Amarelo
        bg_gradient_from = "rgba(234, 179, 8, 0.05)"
        bg_gradient_to = "rgba(202, 138, 4, 0.05)"
        border_color = "rgba(234, 179, 8, 0.3)"
        icon_name = "check_circle_outline"
        status_label = "Parcialmente Correta"
    else:
        color = "#ef4444"  # Vermelho
        bg_gradient_from = "rgba(239, 68, 68, 0.05)"
        bg_gradient_to = "rgba(220, 38, 38, 0.05)"
        border_color = "rgba(239, 68, 68, 0.3)"
        icon_name = "cancel"
        status_label = "Incorreta"
    
    # Ícone de dificuldade
    diff_colors = {
        "básico": "#3b82f6",
        "intermediário": "#eab308",
        "avançado": "#ef4444"
    }
    diff_color = diff_colors.get(difficulty.lower(), "#64748b")
    
    components_html = ", ".join(components) if components else "Geral"
    
    
    # Tratamento de dados ausentes (robusteza)
    student_answer = student_answer if student_answer else "<em style='color:#94a3b8'>Resposta não registrada (dado anterior à atualização)</em>"
    expected_answer = expected_answer if expected_answer else "<em style='color:#94a3b8'>Gabarito não disponível</em>"
    feedback = feedback if feedback else "<em style='color:#94a3b8'>Feedback não disponível</em>"
    
    return f"""<div style='background: linear-gradient(135deg, {bg_gradient_from} 0%, {bg_gradient_to} 100%); 
            padding: 1.5rem; border-radius: 12px; border: 2px solid {border_color}; margin-bottom: 1rem;'>
    
    <!-- Header com status -->
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;'>
        <div style='display: flex; align-items: center; gap: 0.5rem;'>
            {icon(icon_name, color, 28)}
            <span style='color: {color}; font-size: 1.25rem; font-weight: 600;'>{status_label}</span>
        </div>
        <div style='display: flex; gap: 1rem; align-items: center;'>
            <span style='color: #64748b; font-size: 0.875rem;'>
                {icon('schedule', '#64748b', 18)} {time_spent}
            </span>
            <span style='color: {color}; font-size: 1rem; font-weight: 600;'>
                {icon('emoji_events', color, 20)} {points} pts
            </span>
        </div>
    </div>
    
    <!-- Metadados da questão -->
    <div style='background: rgba(255, 255, 255, 0.5); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;'>
        <div style='color: #475569; font-size: 0.875rem; margin-bottom: 0.25rem;'>
            {icon('label', diff_color, 16)} <strong>Dificuldade:</strong> {difficulty.title()}
        </div>
        <div style='color: #475569; font-size: 0.875rem;'>
            {icon('category', '#8b5cf6', 16)} <strong>Componentes:</strong> {components_html}
        </div>
    </div>
    
    <!-- Pergunta -->
    <div style='background: rgba(255, 255, 255, 0.7); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
        <div style='color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; 
                    letter-spacing: 0.05em; margin-bottom: 0.5rem;'>
            {icon('help_outline', '#64748b', 16)} Pergunta
        </div>
        <div style='color: #1e293b; font-size: 0.95rem; line-height: 1.5;'>
            {question_text}
        </div>
    </div>
    
    <!-- Respostas lado a lado -->
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;'>
        
        <!-- Resposta do Aluno -->
        <div style='background: rgba(255, 255, 255, 0.7); padding: 1rem; border-radius: 8px; 
                    border-left: 3px solid {color};'>
            <div style='color: {color}; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; 
                        letter-spacing: 0.05em; margin-bottom: 0.5rem;'>
                {icon('person', color, 16)} Resposta do Aluno
            </div>
            <div style='color: #1e293b; font-size: 0.9rem; line-height: 1.5;'>
                {student_answer}
            </div>
        </div>
        
        <!-- Resposta Esperada -->
        <div style='background: rgba(255, 255, 255, 0.7); padding: 1rem; border-radius: 8px; 
                    border-left: 3px solid #10b981;'>
            <div style='color: #10b981; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; 
                        letter-spacing: 0.05em; margin-bottom: 0.5rem;'>
                {icon('verified', '#10b981', 16)} Resposta Esperada
            </div>
            <div style='color: #1e293b; font-size: 0.9rem; line-height: 1.5;'>
                {expected_answer}
            </div>
        </div>
    </div>
    
    <!-- Feedback da IA -->
    <div style='background: rgba(99, 102, 241, 0.1); padding: 1rem; border-radius: 8px; 
                border-left: 3px solid #6366f1;'>
        <div style='color: #6366f1; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; 
                    letter-spacing: 0.05em; margin-bottom: 0.5rem;'>
            {icon('psychology', '#6366f1', 16)} Feedback da IA
        </div>
        <div style='color: #1e293b; font-size: 0.9rem; line-height: 1.5;'>
            {feedback}
        </div>
    </div>
    
</div>"""

