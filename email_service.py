import smtplib
import requests
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional

def get_firebase_api_key():
    """Obtém a API Key do Firebase dos secrets"""
    try:
        if 'google_api' in st.secrets:
            return st.secrets['google_api']['api_key']
        return None
    except:
        return None

def get_smtp_credentials():
    """Obtém credenciais SMTP dos secrets"""
    try:
        if 'email_sender' in st.secrets:
            return st.secrets['email_sender']['email'], st.secrets['email_sender']['password']
        return None, None
    except:
        return None, None

def send_verification_email_firebase_rest(email: str, password: str, display_name: str) -> Tuple[bool, str, Optional[str]]:
    """
    Cria usuário usando Firebase REST API que envia email automaticamente
    Retorna: (success, message, user_id)
    """
    api_key = get_firebase_api_key()
    
    if not api_key:
        return False, "API Key do Firebase não configurada", None
    
    try:
        # Endpoint para criar usuário
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "displayName": display_name,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            user_id = data.get('localId')
            id_token = data.get('idToken')
            
            # Envia email de verificação
            verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
            verify_payload = {
                "requestType": "VERIFY_EMAIL",
                "idToken": id_token
            }
            
            verify_response = requests.post(verify_url, json=verify_payload)
            
            if verify_response.status_code == 200:
                return True, "Email de verificação enviado com sucesso!", user_id
            else:
                # Usuário criado mas email não enviado - tentar SMTP
                return False, "Usuário criado mas falha ao enviar email via Firebase", user_id
        else:
            error_msg = data.get('error', {}).get('message', 'Erro desconhecido')
            
            # Traduz erros comuns
            if 'EMAIL_EXISTS' in error_msg:
                return False, "Email já cadastrado", None
            elif 'WEAK_PASSWORD' in error_msg:
                return False, "Senha muito fraca (mínimo 6 caracteres)", None
            else:
                return False, f"Erro ao criar usuário: {error_msg}", None
                
    except Exception as e:
        return False, f"Erro na requisição: {str(e)}", None

def send_verification_email_smtp(email: str, verification_link: str, user_name: str) -> Tuple[bool, str]:
    """
    Envia email de verificação via SMTP do Gmail
    Retorna: (success, message)
    """
    sender_email, sender_password = get_smtp_credentials()
    
    if not sender_email or not sender_password:
        return False, "Credenciais SMTP não configuradas"
    
    try:
        # Cria mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🔐 Verifique seu email - BioTutor'
        msg['From'] = f'BioTutor <{sender_email}>'
        msg['To'] = email
        
        # Corpo do email em HTML
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #11B965 0%, #0ea855 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #11B965; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧬 BioTutor</h1>
                    <p>Tutor de Biologia Molecular</p>
                </div>
                <div class="content">
                    <h2>Olá, {user_name}!</h2>
                    <p>Obrigado por se cadastrar no BioTutor! Para começar a usar a plataforma, você precisa verificar seu endereço de email.</p>
                    <p>Clique no botão abaixo para verificar seu email:</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verificar Email</a>
                    </p>
                    <p style="font-size: 12px; color: #666;">
                        Se o botão não funcionar, copie e cole este link no seu navegador:<br>
                        <a href="{verification_link}">{verification_link}</a>
                    </p>
                    <p style="margin-top: 30px; color: #666;">
                        Se você não criou uma conta no BioTutor, ignore este email.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 BioTutor - Faculdade de Ciências Médicas da Santa Casa de São Paulo</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Versão texto simples
        text_body = f"""
        Olá, {user_name}!
        
        Obrigado por se cadastrar no BioTutor!
        
        Para verificar seu email, acesse o link abaixo:
        {verification_link}
        
        Se você não criou uma conta no BioTutor, ignore este email.
        
        ---
        BioTutor - Faculdade de Ciências Médicas da Santa Casa de São Paulo
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Envia email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, "Email enviado com sucesso via SMTP!"
        
    except Exception as e:
        return False, f"Erro ao enviar email via SMTP: {str(e)}"

def resend_verification_email_rest(email: str) -> Tuple[bool, str]:
    """
    Reenvia email de verificação usando Firebase REST API
    Retorna: (success, message)
    """
    api_key = get_firebase_api_key()
    
    if not api_key:
        return False, "API Key do Firebase não configurada"
    
    try:
        # Primeiro, faz login para obter o token
        # Nota: Isso requer a senha, que não temos aqui
        # Alternativa: usar Admin SDK para gerar link e enviar via SMTP
        
        # Por enquanto, retorna erro pedindo para usar Admin SDK
        return False, "Use a função de reenvio via Admin SDK"
        
    except Exception as e:
        return False, f"Erro ao reenviar email: {str(e)}"
