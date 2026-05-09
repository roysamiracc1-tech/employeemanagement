"""Notification configuration API + user mute preferences."""
from flask import session, request, jsonify

from app import app
from app.db import query, execute, to_dict
from app.auth import login_required, require_roles
from app.services.company_scope import current_company_id, sub_roles

_ADMIN_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN')

ALL_EVENT_TYPES = [
    'VACATION_REQUESTED', 'VACATION_APPROVED', 'VACATION_REJECTED',
    'VACATION_CANCELLED', 'EMPLOYEE_CREATED', 'SKILL_VALIDATED',
]

ALL_RECIPIENT_ROLES = [
    'EMPLOYEE', 'SOLID_LINE_MANAGER', 'DOTTED_LINE_MANAGER',
    'HR_ADMIN', 'PORTAL_ADMIN', 'DEPARTMENT_HEAD', 'LOCATION_HEAD',
]


@app.route('/api/notifications/settings', methods=['GET'])
@require_roles(*_ADMIN_ROLES)
def api_get_notification_settings():
    company_id = current_company_id() or request.args.get('company_id')
    if not company_id:
        return jsonify({'error': 'company_id required'}), 400

    rows = query(
        "SELECT event_type, recipient_role, is_enabled, allow_mute "
        "FROM notification_settings WHERE company_id=%s::uuid",
        (company_id,),
    )
    matrix = {}
    for r in rows:
        matrix.setdefault(r['event_type'], {})[r['recipient_role']] = {
            'is_enabled': r['is_enabled'],
            'allow_mute': r['allow_mute'],
        }
    return jsonify({
        'event_types':     ALL_EVENT_TYPES,
        'recipient_roles': ALL_RECIPIENT_ROLES,
        'matrix':          matrix,
    })


@app.route('/api/notifications/settings', methods=['POST'])
@require_roles(*_ADMIN_ROLES)
def api_update_notification_settings():
    data       = request.get_json() or {}
    company_id = current_company_id() or data.get('company_id')
    if not company_id:
        return jsonify({'error': 'company_id required'}), 400

    event_type     = data.get('event_type')
    recipient_role = data.get('recipient_role')
    is_enabled     = bool(data.get('is_enabled', True))
    allow_mute     = bool(data.get('allow_mute', True))
    inherit        = bool(data.get('inherit', False))

    if event_type not in ALL_EVENT_TYPES:
        return jsonify({'error': 'invalid event_type'}), 400
    if recipient_role not in ALL_RECIPIENT_ROLES:
        return jsonify({'error': 'invalid recipient_role'}), 400

    roles_to_update = [recipient_role]
    if inherit:
        roles_to_update += sub_roles(recipient_role)

    for role in roles_to_update:
        execute("""
            INSERT INTO notification_settings
                (company_id, event_type, recipient_role, is_enabled, allow_mute, updated_at)
            VALUES (%s::uuid, %s, %s, %s, %s, NOW())
            ON CONFLICT (company_id, event_type, recipient_role) DO UPDATE
              SET is_enabled = EXCLUDED.is_enabled,
                  allow_mute = EXCLUDED.allow_mute,
                  updated_at = NOW()
        """, (company_id, event_type, role, is_enabled, allow_mute))

    return jsonify({'ok': True, 'updated_roles': roles_to_update})


@app.route('/api/notifications/mute', methods=['POST'])
@login_required
def api_mute_notification():
    """Toggle mute for the current user on a specific event type."""
    data       = request.get_json() or {}
    event_type = data.get('event_type')
    mute       = bool(data.get('mute', True))
    company_id = session.get('company_id') or None
    user_id    = session['user_id']

    if event_type not in ALL_EVENT_TYPES:
        return jsonify({'error': 'invalid event_type'}), 400

    # Only allowed if allow_mute = true for this role/event
    if company_id:
        roles = session.get('roles', [])
        allowed = query("""
            SELECT 1 FROM notification_settings
            WHERE company_id=%s::uuid AND event_type=%s
              AND recipient_role = ANY(%s::text[]) AND allow_mute AND is_enabled
        """, (company_id, event_type, roles), one=True)
        if not allowed:
            return jsonify({'error': 'This notification cannot be muted'}), 403

    if mute:
        execute("""
            INSERT INTO notification_mutes (user_id, company_id, event_type)
            VALUES (%s::uuid, %s::uuid, %s)
            ON CONFLICT (user_id, event_type) DO NOTHING
        """, (user_id, company_id or 'ffffffff-ffff-ffff-ffff-ffffffffffff', event_type))
    else:
        execute(
            "DELETE FROM notification_mutes WHERE user_id=%s::uuid AND event_type=%s",
            (user_id, event_type),
        )

    return jsonify({'ok': True, 'muted': mute})


@app.route('/api/notifications/my-mutes')
@login_required
def api_my_mutes():
    rows = query(
        "SELECT event_type FROM notification_mutes WHERE user_id=%s::uuid",
        (session['user_id'],),
    )
    return jsonify([r['event_type'] for r in rows])
