# app/services/email_service.py
"""
Service d'envoi d'emails HTML — Simulation du module de notification iTop.
En mode développement, TOUS les emails sont redirigés vers SMTP_USERNAME (benguizamehdi3@gmail.com)
mais le contenu mentionne les vraies données de l'employé, pour un rendu réaliste en PFE.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from pathlib import Path
from app.core.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Templates HTML
# ─────────────────────────────────────────────────────────────────────────────

def _html_base(content: str, title: str) -> str:
    """Enveloppe HTML commune pour tous les emails BIAT."""
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:40px 0;">
    <tr><td align="center">
      <table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.10);">

        <!-- En-tête BIAT -->
        <tr>
          <td style="background:linear-gradient(135deg,#003087 0%,#00AEEF 100%);padding:30px 40px;text-align:center;">
             <img src="cid:biatlogo" alt="BIAT IT" style="max-width:180px;height:auto;background:white;padding:8px 20px;border-radius:8px;display:inline-block;margin-bottom:15px;">
             <div style="color:#ffffff;font-size:24px;font-weight:600;letter-spacing:1px;margin:10px 0 0;">BIAT IT</div>
             <div style="color:rgba(255,255,255,0.95);font-size:14px;font-weight:300;letter-spacing:2px;text-transform:uppercase;margin:5px 0 0;">Innovation & Technology</div>
             <div style="display:inline-block;background:rgba(255,255,255,0.15);padding:5px 15px;border-radius:50px;margin-top:10px;font-size:12px;font-weight:500;border:1px solid rgba(255,255,255,0.3);color:white;">⚡ Digital Banking Solutions</div>
          </td>
        </tr>

        <!-- Corps -->
        <tr><td style="padding:36px 40px 28px 40px;">{content}</td></tr>

        <!-- Pied de page -->
        <tr>
          <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="color:#94a3b8;font-size:11px;line-height:1.6;">
                  Cet email a été généré automatiquement par le Système de Gestion des Habilitations BIAT (iTop ITSM).<br/>
                  Ne pas répondre à cet email — Pour toute question, contactez la DSI : <strong>dsi-helpdesk@biat.com.tn</strong>
                </td>
                <td align="right" style="color:#cbd5e1;font-size:10px;white-space:nowrap;">
                  {datetime.now().strftime('%d/%m/%Y %H:%M')} — iTop v4.2
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def build_approval_email(
    employee_name: str,
    employee_email: str,
    ticket_ref: str,
    system_name: str,
    application: str,
    environments: list,
    access_types: list,
    account_name: str,
    temp_password: str,
    approved_by: str,
) -> tuple[str, str]:
    """
    Construit l'email HTML d'approbation.
    Retourne (sujet, html_body).
    """
    env_badges = "".join(
        f'<span style="display:inline-block;background:#dbeafe;color:#1e40af;font-size:12px;font-weight:600;'
        f'padding:3px 10px;border-radius:20px;margin:2px;">{e}</span>'
        for e in environments
    )
    access_badges = "".join(
        f'<span style="display:inline-block;background:#d1fae5;color:#065f46;font-size:12px;font-weight:600;'
        f'padding:3px 10px;border-radius:20px;margin:2px;">{a}</span>'
        for a in access_types
    )

    content = f"""
    <!-- Bannière succès -->
    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px 20px;margin-bottom:28px;display:flex;align-items:center;">
      <span style="font-size:28px;margin-right:12px;">✅</span>
      <div>
        <div style="color:#166534;font-size:16px;font-weight:700;">Demande d'habilitation APPROUVÉE</div>
        <div style="color:#15803d;font-size:13px;margin-top:2px;">Ticket N° <strong>{ticket_ref}</strong></div>
      </div>
    </div>

    <p style="color:#1e293b;font-size:15px;line-height:1.7;margin:0 0 24px 0;">
      Bonjour <strong>{employee_name}</strong>,<br/><br/>
      Nous avons le plaisir de vous informer que votre demande d'accès a été 
      <strong style="color:#166534;">approuvée</strong> par <strong>{approved_by}</strong>.<br/>
      Votre profil d'habilitation est désormais actif sur le système cible.
    </p>

    <!-- Bloc Système cible -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:24px;">
      <tr><td style="padding:20px 24px;">
        <div style="color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px;">
          🖥️ Périmètre d'accès accordé
        </div>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding:6px 0;color:#475569;font-size:13px;width:40%;"><strong>Système :</strong></td>
            <td style="padding:6px 0;color:#1e293b;font-size:13px;font-weight:600;">{system_name}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#475569;font-size:13px;"><strong>Application :</strong></td>
            <td style="padding:6px 0;color:#1e293b;font-size:13px;font-weight:600;">{application}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#475569;font-size:13px;vertical-align:top;"><strong>Environnements :</strong></td>
            <td style="padding:6px 0;">{env_badges}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#475569;font-size:13px;vertical-align:top;"><strong>Droits accordés :</strong></td>
            <td style="padding:6px 0;">{access_badges}</td>
          </tr>
        </table>
      </td></tr>
    </table>

    <!-- Bloc Credentials -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#1e3a5f,#2563eb);border-radius:8px;margin-bottom:24px;">
      <tr><td style="padding:24px;">
        <div style="color:#93c5fd;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px;">
          🔐 Vos identifiants de connexion
        </div>
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="color:#bfdbfe;font-size:13px;padding:6px 0;width:45%;">Nom de compte :</td>
            <td style="padding:6px 0;">
              <code style="background:rgba(255,255,255,0.15);color:#ffffff;padding:4px 12px;border-radius:4px;font-size:15px;font-weight:700;letter-spacing:1px;">{account_name}</code>
            </td>
          </tr>
          <tr>
            <td style="color:#bfdbfe;font-size:13px;padding:6px 0;">Mot de passe temporaire :</td>
            <td style="padding:6px 0;">
              <code style="background:rgba(255,255,255,0.15);color:#fbbf24;padding:4px 12px;border-radius:4px;font-size:15px;font-weight:700;letter-spacing:2px;">{temp_password}</code>
            </td>
          </tr>
        </table>
        <div style="margin-top:16px;padding:12px;background:rgba(251,191,36,0.15);border-radius:6px;border-left:3px solid #fbbf24;">
          <span style="color:#fde68a;font-size:12px;">⚠️ Ce mot de passe est <strong>temporaire et à usage unique</strong>. Vous serez invité à le modifier lors de votre première connexion. Ne le partagez avec personne.</span>
        </div>
      </td></tr>
    </table>

    <!-- Infos ticket -->
    <div style="background:#f8fafc;border-left:4px solid #2563eb;padding:12px 16px;border-radius:0 6px 6px 0;margin-bottom:8px;">
      <span style="color:#64748b;font-size:12px;">N° Ticket : <strong style="color:#1e293b;">{ticket_ref}</strong> — 
      Approuvé par : <strong style="color:#1e293b;">{approved_by}</strong> — 
      Email associé : <strong style="color:#1e293b;">{employee_email}</strong></span>
    </div>
    """

    subject = f"[BIAT iTop] ✅ Habilitation approuvée — {ticket_ref} — {application}"
    return subject, _html_base(content, subject)


def build_rejection_email(
    employee_name: str,
    employee_email: str,
    ticket_ref: str,
    application: str,
    environments: list,
    access_types: list,
    reason: str,
    rejected_by: str,
) -> tuple[str, str]:
    """
    Construit l'email HTML de rejet.
    Retourne (sujet, html_body).
    """
    env_text = ", ".join(environments) if environments else "Non spécifié"
    access_text = ", ".join(access_types) if access_types else "Non spécifié"

    content = f"""
    <!-- Bannière rejet -->
    <div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:16px 20px;margin-bottom:28px;">
      <span style="font-size:28px;margin-right:12px;">❌</span>
      <div style="display:inline-block;vertical-align:middle;">
        <div style="color:#991b1b;font-size:16px;font-weight:700;">Demande d'habilitation REJETÉE</div>
        <div style="color:#b91c1c;font-size:13px;margin-top:2px;">Ticket N° <strong>{ticket_ref}</strong></div>
      </div>
    </div>

    <p style="color:#1e293b;font-size:15px;line-height:1.7;margin:0 0 24px 0;">
      Bonjour <strong>{employee_name}</strong>,<br/><br/>
      Nous vous informons que votre demande d'accès pour l'application 
      <strong>{application}</strong> (environnements : {env_text}, droits : {access_text})
      a été <strong style="color:#991b1b;">rejetée</strong> par <strong>{rejected_by}</strong>.
    </p>

    <!-- Motif -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff5f5;border:1px solid #fca5a5;border-radius:8px;margin-bottom:24px;">
      <tr><td style="padding:20px 24px;">
        <div style="color:#b91c1c;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">
          📋 Motif du rejet
        </div>
        <p style="color:#7f1d1d;font-size:14px;line-height:1.7;margin:0;font-style:italic;">
          "{reason}"
        </p>
      </td></tr>
    </table>

    <!-- Que faire -->
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;margin-bottom:24px;">
      <tr><td style="padding:20px 24px;">
        <div style="color:#92400e;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
          💡 Que faire maintenant ?
        </div>
        <ul style="color:#78350f;font-size:13px;line-height:2;margin:0;padding-left:20px;">
          <li>Contactez votre responsable hiérarchique pour discuter de votre besoin d'accès.</li>
          <li>Si votre besoin est justifié, soumettez une nouvelle demande en précisant le contexte métier dans iTop.</li>
          <li>Pour toute question, contactez la DSI : <strong>dsi-helpdesk@biat.com.tn</strong></li>
        </ul>
      </td></tr>
    </table>

    <!-- Infos ticket -->
    <div style="background:#f8fafc;border-left:4px solid #ef4444;padding:12px 16px;border-radius:0 6px 6px 0;">
      <span style="color:#64748b;font-size:12px;">N° Ticket : <strong style="color:#1e293b;">{ticket_ref}</strong> — 
      Décidé par : <strong style="color:#1e293b;">{rejected_by}</strong> — 
      Email : <strong style="color:#1e293b;">{employee_email}</strong></span>
    </div>
    """

    subject = f"[BIAT iTop] ❌ Habilitation rejetée — {ticket_ref} — {application}"
    return subject, _html_base(content, subject)


# ─────────────────────────────────────────────────────────────────────────────
# Envoi SMTP
# ─────────────────────────────────────────────────────────────────────────────

def send_email(to_address: str, subject: str, html_body: str) -> bool:
    """
    Envoie un email HTML via SMTP Gmail.

    En mode développement : l'adresse réelle de l'employé est loggée mais
    l'email physique est envoyé à SMTP_USERNAME (test local).
    En production : l'email va directement à to_address.

    Retourne True si succès, False sinon.
    """
    actual_recipient = settings.SMTP_USERNAME if settings.ENVIRONMENT == "development" else to_address

    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        print(f"⚠️  [EMAIL] SMTP non configuré. Email non envoyé (destinataire simulé : {to_address})")
        print(f"   Sujet : {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"BIAT iTop ITSM <{settings.EMAIL_FROM}>"
        msg["To"]      = actual_recipient

        # Ajouter version texte simple pour les clients sans HTML
        text_body = (
            f"{subject}\n\n"
            f"Destinataire réel : {to_address}\n"
            f"(Email redirigé vers {actual_recipient} en mode développement)\n\n"
            f"Connectez-vous au portail BIAT iTop pour les détails complets."
        )
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        
        # Integration du logo BIAT IT
        logo_path = Path(__file__).parent.parent.parent / "Biat.png"
        logo_cid = "biatlogo"
        
        if logo_path.exists():
            try:
                with open(logo_path, 'rb') as f:
                    img_data = f.read()
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', f'<{logo_cid}>')
                    img.add_header('Content-Disposition', 'inline', filename='biat.png')
                    msg.attach(img)
            except Exception as e:
                print(f"⚠️ Erreur lors de l'attachement du logo: {e}")

        # Ajouter le corps HTML (qui fait reference au cid:biatlogo)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, actual_recipient, msg.as_string())

        if settings.ENVIRONMENT == "development":
            print(f"✅ [EMAIL] Envoyé à {actual_recipient} (destinataire réel : {to_address})")
        else:
            print(f"✅ [EMAIL] Envoyé à {to_address}")

        return True

    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ [EMAIL] Destinataire refusé : {e}")
    except smtplib.SMTPAuthenticationError:
        print("❌ [EMAIL] Erreur d'authentification SMTP — Vérifiez SMTP_USERNAME/SMTP_PASSWORD dans .env")
    except smtplib.SMTPException as e:
        print(f"❌ [EMAIL] Erreur SMTP : {e}")
    except Exception as e:
        print(f"❌ [EMAIL] Erreur inattendue : {e}")

    return False
