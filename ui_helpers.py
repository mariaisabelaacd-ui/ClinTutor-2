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
