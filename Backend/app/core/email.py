import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from app.core.config import settings
from pathlib import Path

# Configuration du logger
logger = logging.getLogger(__name__)

def send_reset_password_email(email: str, full_name: str, otp_code: str):
    """
    Envoie un email de réinitialisation de mot de passe avec le logo BIAT IT
    """
    try:
        # Configuration SMTP
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_username = settings.SMTP_USERNAME
        smtp_password = settings.SMTP_PASSWORD
        
        # Création du message
        msg = MIMEMultipart('alternative')  # Important: 'alternative' pour texte + html
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = email
        msg['Subject'] = "🔐 Réinitialisation de votre mot de passe - BIAT IT"
        
        # Version texte simple
        text = f"""
BIAT IT - Innovation & Technology
=================================

Bonjour {full_name},

Vous avez demandé la réinitialisation de votre mot de passe pour votre espace BIAT IT.

Votre code de vérification est : {otp_code}

Ce code expire dans 15 minutes.

⚠️ IMPORTANT :
• Ne partagez jamais ce code
• Notre équipe ne vous le demandera jamais
• Ignorez cet email si vous n'êtes pas à l'origine de la demande

Support: support@biat-it.com.tn


---
BIAT IT · Innovation & Technology
© 2026 BIAT IT - Tous droits réservés
"""
        
        # Charger le logo
        logo_path = Path(__file__).parent.parent / "Biat.png"
        logo_cid = "biatlogo"
        
        print(f"🔍 Recherche du logo à: {logo_path}")
        
        # Version HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #003087 0%, #00AEEF 100%);
                    color: white;
                    padding: 30px 30px;
                    text-align: center;
                }}
                .logo-img {{
                    max-width: 180px;
                    height: auto;
                    margin-bottom: 15px;
                    background: white;
                    padding: 8px 20px;
                    border-radius: 8px;
                    display: inline-block;
                }}
                .header h1 {{
                    margin: 10px 0 0;
                    font-size: 28px;
                    font-weight: 600;
                    letter-spacing: 1px;
                }}
                .header .subtitle {{
                    margin: 5px 0 0;
                    opacity: 0.95;
                    font-size: 14px;
                    font-weight: 300;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                }}
                .header .innovation-badge {{
                    display: inline-block;
                    background: rgba(255,255,255,0.15);
                    padding: 5px 15px;
                    border-radius: 50px;
                    margin-top: 10px;
                    font-size: 12px;
                    font-weight: 500;
                    border: 1px solid rgba(255,255,255,0.3);
                }}
                .content {{
                    padding: 40px 30px;
                    background: #ffffff;
                }}
                .otp-container {{
                    background: #f8f9fa;
                    border: 2px dashed #003087;
                    border-radius: 10px;
                    padding: 25px;
                    text-align: center;
                    margin: 25px 0;
                }}
                .otp-code {{
                    font-size: 48px;
                    font-weight: 800;
                    letter-spacing: 10px;
                    color: #003087;
                    font-family: 'Courier New', monospace;
                    background: white;
                    padding: 15px 20px;
                    border-radius: 8px;
                    display: inline-block;
                    border: 1px solid #e0e0e0;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 25px 0;
                    border-radius: 5px;
                }}
                .warning p {{
                    margin: 0;
                    color: #856404;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 25px 30px;
                    text-align: center;
                    border-top: 1px solid #e0e0e0;
                }}
                .footer p {{
                    margin: 5px 0;
                    color: #666;
                    font-size: 13px;
                }}
                .footer .company-name {{
                    color: #003087;
                    font-weight: 600;
                }}
                .innovation-tag {{
                    text-align: center;
                    margin-top: 20px;
                    padding: 10px;
                    background: #e6f3ff;
                    border-radius: 5px;
                    color: #003087;
                    font-size: 13px;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
        """
        
        # Ajouter le logo si trouvé
        if logo_path.exists():
            with open(logo_path, 'rb') as f:
                img_data = f.read()
                img = MIMEImage(img_data)
                img.add_header('Content-ID', f'<{logo_cid}>')
                img.add_header('Content-Disposition', 'inline', filename='biat.png')
                msg.attach(img)
                html += f'<img src="cid:{logo_cid}" alt="BIAT IT" class="logo-img">'
                logger.info(f"✅ Logo BIAT IT attaché avec succès")
                print(f"✅ Logo trouvé et attaché")
        else:
            html += '<h1 style="margin:0; color:white;">BIAT IT</h1>'
            logger.warning(f"⚠️ Logo non trouvé à: {logo_path}")
            print(f"❌ Logo non trouvé à: {logo_path}")
        
        # Suite du HTML
        html += f"""
                    <h1>BIAT IT</h1>
                    <div class="subtitle">Innovation & Technology</div>
                    <div class="innovation-badge">⚡ Digital Banking Solutions</div>
                </div>
                
                <div class="content">
                    <h2 style="color: #003087; margin-top: 0;">Bonjour {full_name},</h2>
                    
                    <p>Vous avez récemment demandé la réinitialisation de votre mot de passe pour accéder à votre espace <strong>BIAT IT</strong>.</p>
                    
                    <p>Pour des raisons de sécurité, nous vous envoyons un code de vérification unique :</p>
                    
                    <div class="otp-container">
                        <div style="font-size: 14px; color: #666; margin-bottom: 15px;">
                            Votre code de vérification
                        </div>
                        <div class="otp-code">{otp_code}</div>
                        <p style="margin: 15px 0 0; color: #666; font-size: 14px;">
                            Ce code expire dans <strong>15 minutes</strong>
                        </p>
                    </div>
                    
                    <div class="warning">
                        <p style="font-weight: 600; margin-bottom: 10px;">⚠️ Important :</p>
                        <p>• Ne partagez jamais ce code avec personne</p>
                        <p>• Notre équipe ne vous demandera jamais ce code</p>
                        <p>• Si vous n'êtes pas à l'origine de cette demande, ignorez cet email</p>
                    </div>
                    
                    <p>Pour des raisons de sécurité, ce code est à usage unique et expire dans 15 minutes.</p>
                    
                    <div class="innovation-tag">
                        🚀 BIAT IT - L'innovation bancaire au service de vos projets
                    </div>
                    
                    <p style="margin-top: 25px;">
                        Si vous avez des questions ou besoin d'aide, contactez notre support à 
                        <a href="mailto:support@biat-it.com.tn" style="color: #003087; text-decoration: none;">
                            support@biat-it.com.tn
                        </a>
                    </p>
                </div>
                
                <div class="footer">
                    <p class="company-name">BIAT IT · Innovation & Technology</p>
                    <p>© 2026 BIAT IT - Tous droits réservés</p>
                    <p>Ceci est un email automatique, merci de ne pas y répondre.</p>
                    <p style="font-size: 11px; color: #999;">
                        Conformément à la réglementation en vigueur, vous disposez d'un droit d'accès, 
                        de rectification et d'opposition aux données vous concernant.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attacher les parties texte et HTML
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        # Envoi de l'email
        logger.info(f"📧 Tentative d'envoi d'email à {email}")
        
        if smtp_username and smtp_password:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"✅ Email envoyé avec succès à {email}")
        else:
            # Mode développement
            logger.warning("⚠️ Mode développement - Email non envoyé")
            print(f"\n🔐 CODE OTP pour {email}: {otp_code}\n")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email: {e}")
        if settings.ENVIRONMENT == "development":
            print(f"\n🔐 CODE OTP pour {email}: {otp_code}\n")
        raise