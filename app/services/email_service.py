"""Thin async email sender.

Sends via SMTP in a background thread so the request is never blocked.
Set SMTP_* environment variables (or config.py) to configure.
When SMTP_HOST is empty the email is printed to stdout (dev mode).
"""
import smtplib
import threading
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, render_template

log = logging.getLogger(__name__)


def _smtp_cfg():
    cfg = current_app.config
    return {
        'host':     cfg.get('SMTP_HOST', ''),
        'port':     int(cfg.get('SMTP_PORT', 587)),
        'user':     cfg.get('SMTP_USER', ''),
        'password': cfg.get('SMTP_PASSWORD', ''),
        'from':     cfg.get('SMTP_FROM', 'noreply@hrportal.local'),
        'tls':      cfg.get('SMTP_USE_TLS', True),
    }


def _do_send(host, port, user, password, use_tls, from_addr, to_addr, subject, html_body):
    """Blocking send — called inside a thread."""
    if not host:
        # Dev/test mode: just log
        log.info('[EMAIL] To=%s | Subject=%s', to_addr, subject)
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = from_addr
    msg['To']      = to_addr
    msg.attach(MIMEText(html_body, 'html'))
    try:
        with smtplib.SMTP(host, port, timeout=10) as srv:
            if use_tls:
                srv.starttls()
            if user:
                srv.login(user, password)
            srv.sendmail(from_addr, [to_addr], msg.as_string())
    except Exception as exc:
        log.error('[EMAIL] Failed to send to %s: %s', to_addr, exc)


def send_async(to_addr: str, subject: str, template: str, **ctx):
    """Render *template* with **ctx and send asynchronously.

    Must be called within a Flask application context.
    """
    html_body  = render_template(template, **ctx)
    cfg        = _smtp_cfg()
    app_ctx    = current_app._get_current_object()  # capture before thread

    def worker():
        with app_ctx.app_context():
            _do_send(cfg['host'], cfg['port'], cfg['user'], cfg['password'],
                     cfg['tls'], cfg['from'], to_addr, subject, html_body)

    threading.Thread(target=worker, daemon=True).start()
