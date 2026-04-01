"""
alerts.py
Sends email alerts when arbitrage opportunities are found.
Uses Gmail SMTP (or any SMTP provider) — no extra libraries needed.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def format_opportunity_email(opportunities):
    """
    Format a list of arb opportunities into a clean HTML email body.
    """
    now = datetime.now().strftime("%d %b %Y %H:%M:%S")
    
    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto;">
    <h2 style="color: #1a7f37; border-bottom: 2px solid #1a7f37; padding-bottom: 8px;">
        🎯 Arbitrage Opportunities Found
    </h2>
    <p style="color: #555;">Scanned at {now}</p>
    """
    
    for i, opp in enumerate(opportunities, 1):
        profit_color = "#1a7f37" if opp["profit_percent"] > 0 else "#cc6600"
        
        html += f"""
        <div style="background:#f8f9fa; border-left:4px solid {profit_color};
                    padding:16px; margin:16px 0; border-radius:4px;">
            <h3 style="margin:0 0 8px 0; color:#222;">
                #{i} {opp['event']}
            </h3>
            <table style="width:100%; font-size:14px; border-collapse:collapse;">
                <tr>
                    <td style="padding:4px 8px; color:#555;">Sport</td>
                    <td style="padding:4px 8px;"><strong>{opp['sport']}</strong></td>
                    <td style="padding:4px 8px; color:#555;">Market</td>
                    <td style="padding:4px 8px;"><strong>{opp['market']}</strong></td>
                </tr>
                <tr>
                    <td style="padding:4px 8px; color:#555;">Kick-off</td>
                    <td style="padding:4px 8px;" colspan="3"><strong>{opp['commence_time']}</strong></td>
                </tr>
                <tr>
                    <td style="padding:4px 8px; color:#555;">Profit %</td>
                    <td style="padding:4px 8px;">
                        <strong style="color:{profit_color}; font-size:16px;">
                            {opp['profit_percent']}%
                        </strong>
                    </td>
                    <td style="padding:4px 8px; color:#555;">Arb %</td>
                    <td style="padding:4px 8px;"><strong>{opp['arb_percent']}%</strong></td>
                </tr>
                <tr>
                    <td style="padding:4px 8px; color:#555;">Total Stake</td>
                    <td style="padding:4px 8px;"><strong>£{opp['total_staked']}</strong></td>
                    <td style="padding:4px 8px; color:#555;">Return</td>
                    <td style="padding:4px 8px;"><strong>£{opp['guaranteed_return']}</strong></td>
                </tr>
                <tr>
                    <td style="padding:4px 8px; color:#555;">Profit</td>
                    <td style="padding:4px 8px;" colspan="3">
                        <strong style="color:{profit_color};">£{opp['guaranteed_profit']}</strong>
                    </td>
                </tr>
            </table>
            
            <h4 style="margin:12px 0 6px 0; color:#444;">Bets to Place:</h4>
            <table style="width:100%; font-size:13px; border-collapse:collapse; 
                          background:white; border-radius:4px;">
                <tr style="background:#e9ecef;">
                    <th style="padding:8px; text-align:left;">Outcome</th>
                    <th style="padding:8px; text-align:left;">Bookmaker</th>
                    <th style="padding:8px; text-align:right;">Odds</th>
                    <th style="padding:8px; text-align:right;">Stake</th>
                </tr>
        """
        
        for j, outcome in enumerate(opp["outcomes"]):
            stake = opp["stakes"][j]
            odds  = opp["best_odds"][j]
            book  = opp["bookmakers"][j]
            html += f"""
                <tr style="border-bottom:1px solid #dee2e6;">
                    <td style="padding:8px;">{outcome}</td>
                    <td style="padding:8px; color:#0066cc;">{book}</td>
                    <td style="padding:8px; text-align:right;">{odds}</td>
                    <td style="padding:8px; text-align:right;"><strong>£{stake}</strong></td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
    
    html += """
    <p style="color:#888; font-size:12px; margin-top:24px; border-top:1px solid #ddd; 
              padding-top:12px;">
        ⚠️ Odds change rapidly. Always verify on the bookmaker site before placing bets.
        This tool is for informational purposes — bet responsibly.
    </p>
    </body></html>
    """
    
    return html


def send_email_alert(opportunities, config):
    """
    Send an HTML email alert with all found arb opportunities.
    
    opportunities: list of opportunity dicts from the scanner
    config: dict with email settings (loaded from .env)
    
    Required config keys:
        EMAIL_SENDER       - your Gmail address
        EMAIL_PASSWORD     - Gmail App Password (NOT your login password)
        EMAIL_RECIPIENT    - address to send alerts to (can be same as sender)
        SMTP_HOST          - default: smtp.gmail.com
        SMTP_PORT          - default: 587
    """
    if not opportunities:
        return
    
    sender    = config.get("EMAIL_SENDER")
    password  = config.get("EMAIL_PASSWORD")
    recipient = config.get("EMAIL_RECIPIENT")
    smtp_host = config.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(config.get("SMTP_PORT", 587))
    
    if not all([sender, password, recipient]):
        logging.error("Email config incomplete. Check EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT in .env")
        return
    
    count = len(opportunities)
    best  = max(opportunities, key=lambda x: x["profit_percent"])
    subject = (
        f"🎯 {count} Arb Opportunit{'y' if count == 1 else 'ies'} Found | "
        f"Best: {best['profit_percent']}% profit on {best['event']}"
    )
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient
    
    html_body = format_opportunity_email(opportunities)
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        logging.info(f"Email alert sent: {count} opportunities to {recipient}")
        return True
    except smtplib.SMTPAuthenticationError:
        logging.error(
            "Gmail authentication failed. You need an App Password, not your Gmail login password. "
            "Go to: Google Account > Security > 2-Step Verification > App Passwords"
        )
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
    
    return False
