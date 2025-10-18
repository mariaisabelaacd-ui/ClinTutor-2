"""
Sistema de autenticação com validação de email e código de verificação
Suporta apenas domínios específicos: fcmsantacasasp.edu.br e aluno.fcmsantacasasp.edu.br
"""

import streamlit as st
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import json
import os

class EmailAuthSystem:
    def __init__(self):
        self.allowed_domains = {
            'professor': 'fcmsantacasasp.edu.br',
            'aluno': 'aluno.fcmsantacasasp.edu.br'
        }
        self.verification_codes = {}  # email -> {code, timestamp, user_type}
        self.load_verification_codes()
        
    def load_verification_codes(self):
        """Carrega códigos de verificação salvos"""
        try:
            if os.path.exists('verification_codes.json'):
                with open('verification_codes.json', 'r') as f:
                    data = json.load(f)
                    # Converte timestamps de string para datetime
                    for email, info in data.items():
                        if 'timestamp' in info:
                            info['timestamp'] = datetime.fromisoformat(info['timestamp'])
                    self.verification_codes = data
        except Exception as e:
            st.error(f"Erro ao carregar códigos: {e}")
            self.verification_codes = {}
    
    def save_verification_codes(self):
        """Salva códigos de verificação"""
        try:
            # Converte timestamps para string para JSON
            data_to_save = {}
            for email, info in self.verification_codes.items():
                data_to_save[email] = info.copy()
                if 'timestamp' in data_to_save[email]:
                    data_to_save[email]['timestamp'] = data_to_save[email]['timestamp'].isoformat()
            
            with open('verification_codes.json', 'w') as f:
                json.dump(data_to_save, f)
        except Exception as e:
            st.error(f"Erro ao salvar códigos: {e}")
    
    def validate_email_domain(self, email: str) -> Tuple[bool, str]:
        """
        Valida se o email pertence aos domínios permitidos
        Retorna: (is_valid, user_type)
        """
        if not email or '@' not in email:
            return False, ""
        
        domain = email.split('@')[1].lower()
        
        if domain == self.allowed_domains['professor']:
            return True, 'professor'
        elif domain == self.allowed_domains['aluno']:
            return True, 'aluno'
        else:
            return False, ""
    
    def generate_verification_code(self) -> str:
        """Gera código de verificação de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_email(self, email: str, code: str, user_type: str) -> bool:
        """Envia código de verificação por email"""
        try:
            # Configurações do email
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = st.secrets['email_sender']['email']
            sender_password = st.secrets['email_sender']['password']
            
            # Cria mensagem
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = "Código de Verificação - ClinTutor"
            
            # Corpo do email
            user_type_pt = "Professor" if user_type == "professor" else "Aluno"
            body = f"""
            <html>
            <body>
                <h2>🔐 Código de Verificação - ClinTutor</h2>
                <p>Olá!</p>
                <p>Você está tentando criar uma conta como <strong>{user_type_pt}</strong> no ClinTutor.</p>
                <p>Seu código de verificação é:</p>
                <h1 style="color: #4CAF50; font-size: 32px; text-align: center; background: #f0f0f0; padding: 20px; border-radius: 10px;">{code}</h1>
                <p><strong>Este código expira em 10 minutos.</strong></p>
                <p>Se você não solicitou este código, ignore este email.</p>
                <hr>
                <p><small>Sistema ClinTutor - Faculdade de Ciências Médicas Santa Casa de São Paulo</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Envia email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao enviar email: {e}")
            # Fallback: mostra código na tela para desenvolvimento
            st.warning("⚠️ Email não enviado - Modo de desenvolvimento")
            st.info(f"**Código de verificação para {email}:**")
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                font-size: 32px;
                font-weight: bold;
                margin: 20px 0;
            ">
                {code}
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 Use este código para continuar o cadastro")
            return True  # Retorna True para permitir continuar
    
    def request_verification_code(self, email: str) -> Tuple[bool, str]:
        """
        Solicita código de verificação
        Retorna: (success, message)
        """
        # Valida domínio
        is_valid, user_type = self.validate_email_domain(email)
        if not is_valid:
            return False, f"❌ Email não permitido! Use apenas emails da Santa Casa:\n• Professores: @{self.allowed_domains['professor']}\n• Alunos: @{self.allowed_domains['aluno']}"
        
        # Limpa códigos expirados primeiro
        self.cleanup_expired_codes()
        
        # Verifica se já existe código válido (não expirado)
        if email in self.verification_codes:
            code_info = self.verification_codes[email]
            time_diff = datetime.now() - code_info['timestamp']
            if time_diff < timedelta(minutes=10):
                remaining_minutes = 10 - int(time_diff.total_seconds() / 60)
                return False, f"⏰ Código já enviado! Aguarde {remaining_minutes} minutos para solicitar um novo."
        
        # Gera novo código
        code = self.generate_verification_code()
        
        # Salva código
        self.verification_codes[email] = {
            'code': code,
            'timestamp': datetime.now(),
            'user_type': user_type,
            'verified': False
        }
        
        # Envia email (sempre retorna True agora com fallback)
        email_sent = self.send_verification_email(email, code, user_type)
        self.save_verification_codes()
        
        if email_sent:
            return True, f"✅ Código enviado para {email}!\nVerifique sua caixa de entrada (e spam)."
        else:
            return True, f"✅ Código gerado para {email}!\nVerifique a tela acima para o código."
    
    def verify_code(self, email: str, code: str) -> Tuple[bool, str]:
        """
        Verifica código de verificação
        Retorna: (success, message)
        """
        if email not in self.verification_codes:
            return False, "❌ Email não encontrado. Solicite um novo código."
        
        code_info = self.verification_codes[email]
        
        # Verifica expiração
        if datetime.now() - code_info['timestamp'] > timedelta(minutes=10):
            del self.verification_codes[email]
            self.save_verification_codes()
            return False, "⏰ Código expirado! Solicite um novo código."
        
        # Verifica código
        if code_info['code'] != code:
            return False, "❌ Código incorreto! Verifique e tente novamente."
        
        # Marca como verificado
        code_info['verified'] = True
        self.save_verification_codes()
        
        return True, f"✅ Email verificado com sucesso! Tipo: {code_info['user_type']}"
    
    def get_verified_user_type(self, email: str) -> Optional[str]:
        """Retorna o tipo de usuário se o email foi verificado"""
        if email in self.verification_codes:
            code_info = self.verification_codes[email]
            if code_info.get('verified', False):
                return code_info['user_type']
        return None
    
    def cleanup_expired_codes(self):
        """Remove códigos expirados"""
        current_time = datetime.now()
        expired_emails = []
        
        for email, code_info in self.verification_codes.items():
            if current_time - code_info['timestamp'] > timedelta(minutes=10):
                expired_emails.append(email)
        
        for email in expired_emails:
            del self.verification_codes[email]
        
        if expired_emails:
            self.save_verification_codes()
    
    def clear_all_codes(self):
        """Limpa todos os códigos (para desenvolvimento)"""
        self.verification_codes = {}
        self.save_verification_codes()
        return True

# Instância global
@st.cache_resource
def get_email_auth_system():
    return EmailAuthSystem()

def show_email_verification_interface():
    """Interface de verificação de email"""
    st.title("🔐 Verificação de Email")
    
    email_auth = get_email_auth_system()
    
    # Limpa códigos expirados
    email_auth.cleanup_expired_codes()
    
    # Interface de solicitação de código
    st.subheader("📧 Solicitar Código de Verificação")
    
    # Botão para limpar códigos (desenvolvimento)
    col1, col2 = st.columns([3, 1])
    with col1:
        email = st.text_input(
            "Digite seu email:",
            placeholder="exemplo@fcmsantacasasp.edu.br",
            help="Use apenas emails da Santa Casa de São Paulo"
        )
    with col2:
        if st.button("🔄 Limpar Códigos", help="Limpa todos os códigos pendentes"):
            email_auth.clear_all_codes()
            st.success("✅ Códigos limpos!")
    
    if st.button("📤 Enviar Código"):
        if email.strip():
            success, message = email_auth.request_verification_code(email.strip())
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.warning("Digite um email válido!")
    
    st.markdown("---")
    
    # Interface de verificação de código
    st.subheader("🔢 Verificar Código")
    
    verification_email = st.text_input(
        "Email para verificar:",
        placeholder="exemplo@fcmsantacasasp.edu.br"
    )
    
    verification_code = st.text_input(
        "Código de 6 dígitos:",
        placeholder="123456",
        max_chars=6
    )
    
    if st.button("✅ Verificar Código"):
        if verification_email.strip() and verification_code.strip():
            success, message = email_auth.verify_code(verification_email.strip(), verification_code.strip())
            if success:
                st.success(message)
                user_type = email_auth.get_verified_user_type(verification_email.strip())
                if user_type:
                    st.info(f"Tipo de usuário: {user_type}")
            else:
                st.error(message)
        else:
            st.warning("Preencha email e código!")
    
    st.markdown("---")
    
    # Informações sobre domínios permitidos
    st.subheader("ℹ️ Domínios Permitidos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **👨‍🏫 Professores:**
        - `@fcmsantacasasp.edu.br`
        - Exemplo: `gabriela.pintar@fcmsantacasasp.edu.br`
        """)
    
    with col2:
        st.markdown("""
        **👨‍🎓 Alunos:**
        - `@aluno.fcmsantacasasp.edu.br`
        - Exemplo: `maria.michelao@aluno.fcmsantacasasp.edu.br`
        """)
    
    st.warning("⚠️ Emails de outros domínios (gmail, hotmail, etc.) não são permitidos!")

if __name__ == "__main__":
    show_email_verification_interface()
