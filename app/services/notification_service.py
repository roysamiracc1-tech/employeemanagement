"""Notification dispatch service.

Usage (from a route after a state change):
    from app.services.notification_service import dispatch
    dispatch('VACATION_APPROVED', company_id=co_id,
             employee_id=emp_id, manager_id=mgr_id,
             extra_ctx={'requester_name': '...', 'dates': '...'})
"""
import logging

from app.db import query, execute, to_dict
from app.services import email_service

log = logging.getLogger(__name__)

# Maps event → template file
_TEMPLATE = {
    'VACATION_REQUESTED':  'email/vacation_event.html',
    'VACATION_APPROVED':   'email/vacation_event.html',
    'VACATION_REJECTED':   'email/vacation_event.html',
    'VACATION_CANCELLED':  'email/vacation_event.html',
    'EMPLOYEE_CREATED':    'email/employee_created.html',
    'SKILL_VALIDATED':     'email/skill_validated.html',
}

_SUBJECT = {
    'VACATION_REQUESTED':  'Vacation request submitted',
    'VACATION_APPROVED':   'Your vacation has been approved',
    'VACATION_REJECTED':   'Your vacation request was not approved',
    'VACATION_CANCELLED':  'Vacation request cancelled',
    'EMPLOYEE_CREATED':    'New employee joined',
    'SKILL_VALIDATED':     'Your skill has been validated',
}

# Maps event → which session-context participants might receive it
# Values are keys in the dispatch() kwargs (employee_id, manager_id, hr_id …)
_ROLE_TO_PARTICIPANT = {
    'EMPLOYEE':            'employee_id',
    'SOLID_LINE_MANAGER':  'manager_id',
    'DOTTED_LINE_MANAGER': 'manager_id',
    'HR_ADMIN':            None,          # all HR admins in company
    'PORTAL_ADMIN':        None,          # all portal admins
    'HR_ADMIN_LIST':       'hr_ids',
}


def _get_settings(company_id, event_type):
    rows = query(
        "SELECT recipient_role, is_enabled, allow_mute "
        "FROM notification_settings "
        "WHERE company_id=%s::uuid AND event_type=%s AND is_enabled",
        (company_id, event_type),
    )
    return [dict(r) for r in rows]


def _is_muted(user_id, event_type):
    row = query(
        "SELECT 1 FROM notification_mutes WHERE user_id=%s::uuid AND event_type=%s",
        (user_id, event_type), one=True,
    )
    return row is not None


def _hr_admins(company_id):
    """Return list of (user_id, email) for active HR_ADMIN users in a company."""
    rows = query("""
        SELECT u.id::text AS user_id, u.email
        FROM users u
        JOIN employees e ON e.id = u.employee_id AND e.company_id = %s::uuid
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id AND r.name = 'HR_ADMIN'
        WHERE u.is_active AND e.employment_status = 'ACTIVE'
    """, (company_id,))
    return [(r['user_id'], r['email']) for r in rows]


def _portal_admins(company_id):
    rows = query("""
        SELECT u.id::text AS user_id, u.email
        FROM users u
        JOIN employees e ON e.id = u.employee_id AND e.company_id = %s::uuid
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id AND r.name = 'PORTAL_ADMIN'
        WHERE u.is_active
    """, (company_id,))
    return [(r['user_id'], r['email']) for r in rows]


def _user_email(employee_id):
    """Return (user_id, email) for the user linked to an employee."""
    row = query(
        "SELECT u.id::text AS user_id, u.email FROM users u "
        "WHERE u.employee_id = %s::uuid AND u.is_active LIMIT 1",
        (employee_id,), one=True,
    )
    return (row['user_id'], row['email']) if row else (None, None)


# ── In-app user notifications ────────────────────────────────────────────────

def create_user_notification(user_id: str, event_type: str, message: str,
                              link: str = None, related_type: str = None,
                              related_id: str = None) -> None:
    """Insert one unread in-app notification row for *user_id*.

    Pass *related_type* / *related_id* whenever the notification is ABOUT
    something that can later be decided (an approval request, a leave request).
    That is what lets `resolve_related()` retire it once it is no longer
    actionable — without the tag it lives in the bell until the user reads it,
    which for a call to action is the wrong behaviour (DEF-003).
    """
    execute(
        "INSERT INTO user_notifications "
        "(user_id, event_type, message, link, related_type, related_id) "
        "VALUES (%s::uuid, %s, %s, %s, %s, %s::uuid)",
        (user_id, event_type, message, link, related_type, related_id),
    )


def resolve_related(related_type: str, related_id: str,
                    event_types: list = None) -> None:
    """Retire the still-unread notifications about one entity.

    Called when the entity reaches a state where the notification is no longer
    a live call to action — e.g. a position change is rejected, so every
    "awaiting your approval" for it is now history and must leave the bell for
    EVERY approver, not just the one who happened to decide it.

    *event_types* narrows it to the calls to action; pass None to retire all
    notifications about the entity. Outcome notifications ("… was rejected")
    are deliberately NOT retired here — the user has not seen them yet.
    """
    if not related_type or not related_id:
        return
    if event_types:
        execute(
            "UPDATE user_notifications SET is_read=TRUE "
            "WHERE related_type=%s AND related_id=%s::uuid "
            "  AND event_type = ANY(%s) AND NOT is_read",
            (related_type, related_id, list(event_types)),
        )
    else:
        execute(
            "UPDATE user_notifications SET is_read=TRUE "
            "WHERE related_type=%s AND related_id=%s::uuid AND NOT is_read",
            (related_type, related_id),
        )


def get_unread_count(user_id: str) -> int:
    row = query(
        "SELECT COUNT(*)::int AS cnt FROM user_notifications "
        "WHERE user_id=%s::uuid AND NOT is_read",
        (user_id,), one=True,
    )
    return row['cnt'] if row else 0


def get_unread_notifications(user_id: str, limit: int = 20) -> list:
    rows = query(
        "SELECT id::text, event_type, message, link, created_at "
        "FROM user_notifications "
        "WHERE user_id=%s::uuid AND NOT is_read "
        "ORDER BY created_at DESC LIMIT %s",
        (user_id, limit),
    )
    return [to_dict(r) for r in rows]


def mark_all_read(user_id: str) -> None:
    execute(
        "UPDATE user_notifications SET is_read=TRUE "
        "WHERE user_id=%s::uuid AND NOT is_read",
        (user_id,),
    )


# ── Email notifications ───────────────────────────────────────────────────────

def dispatch(event_type: str, *, company_id: str, extra_ctx: dict = None,
             employee_id: str = None, manager_id: str = None):
    """Dispatch notification emails for *event_type*.

    Looks up enabled notification_settings for the company, resolves recipient
    email addresses, checks mute preferences, and fires async sends.
    """
    if not company_id:
        return

    settings   = _get_settings(company_id, event_type)
    template   = _TEMPLATE.get(event_type, 'email/vacation_event.html')
    subject    = _SUBJECT.get(event_type, 'HR Portal notification')
    ctx        = dict(extra_ctx or {}, event_type=event_type)

    sent_to = set()

    for setting in settings:
        role       = setting['recipient_role']
        allow_mute = setting['allow_mute']

        # Resolve the concrete list of (user_id, email) for this role
        recipients = []
        if role == 'EMPLOYEE' and employee_id:
            uid, email = _user_email(employee_id)
            if uid and email:
                recipients.append((uid, email))
        elif role in ('SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER') and manager_id:
            uid, email = _user_email(manager_id)
            if uid and email:
                recipients.append((uid, email))
        elif role == 'HR_ADMIN':
            recipients = _hr_admins(company_id)
        elif role == 'PORTAL_ADMIN':
            recipients = _portal_admins(company_id)

        for uid, email in recipients:
            if email in sent_to:
                continue
            if allow_mute and uid and _is_muted(uid, event_type):
                continue
            sent_to.add(email)
            try:
                email_service.send_async(email, subject, template, **ctx)
            except Exception as exc:
                log.error('notification dispatch failed for %s: %s', email, exc)
