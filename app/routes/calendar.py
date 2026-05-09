"""Vacation calendar API and page."""
import calendar as _cal
import datetime

from flask import session, request, jsonify, render_template

from app import app
from app.auth import login_required
from app.db import query, to_dict
from app.services.company_scope import current_company_id


@app.route('/vacation/calendar')
@login_required
def vacation_calendar():
    return render_template('vacation/calendar.html')


@app.route('/api/vacation/calendar')
@login_required
def api_vacation_calendar():
    """Return vacation events for a month, grouped by ISO date string.

    ?year=2026&month=5&scope=mine|team|all
    """
    today  = datetime.date.today()
    year   = int(request.args.get('year',  today.year))
    month  = int(request.args.get('month', today.month))
    scope  = request.args.get('scope', 'mine')

    emp_id     = session['employee_id']
    company_id = current_company_id() or session.get('company_id')
    roles      = session.get('roles', [])

    # Date range: first day to last day of requested month
    first_day = datetime.date(year, month, 1)
    last_day  = datetime.date(year, month, _cal.monthrange(year, month)[1])

    BASE = """
        SELECT vr.id::text, vr.start_date, vr.end_date, vr.status, vr.working_days,
               vt.name AS type_name, vt.color,
               e.id::text AS employee_id,
               e.first_name || ' ' || e.last_name AS employee_name
        FROM vacation_requests vr
        JOIN vacation_types vt ON vt.id = vr.vacation_type_id
        JOIN employees e ON e.id = vr.employee_id
    """

    # Extra fields for the pending panel (start_date / end_date / working_days / notes)
    BASE_FULL = """
        SELECT vr.id::text, vr.start_date, vr.end_date, vr.status, vr.working_days,
               vr.notes,
               vt.name AS type_name, vt.color,
               e.id::text AS employee_id,
               e.first_name || ' ' || e.last_name AS employee_name
        FROM vacation_requests vr
        JOIN vacation_types vt ON vt.id = vr.vacation_type_id
        JOIN employees e ON e.id = vr.employee_id
    """

    pending_all = []   # all pending for team (no date filter)

    if scope == 'mine':
        rows = query(BASE_FULL + """
            WHERE vr.employee_id = %s::uuid
              AND vr.status IN ('APPROVED','PENDING')
              AND vr.start_date <= %s AND vr.end_date >= %s
            ORDER BY vr.start_date
        """, (emp_id, last_day, first_day))

    elif scope == 'team':
        # Grid: approved + pending within the displayed month
        rows = query(BASE_FULL + """
            JOIN manager_relationships mr
                 ON mr.employee_id = vr.employee_id
                AND mr.manager_id  = %s::uuid
                AND mr.relationship_type = 'SOLID_LINE'
                AND mr.is_current
            WHERE vr.status IN ('APPROVED','PENDING')
              AND vr.start_date <= %s AND vr.end_date >= %s
            ORDER BY vr.start_date
        """, (emp_id, last_day, first_day))

        # Pending panel: ALL pending from reports regardless of date
        pending_rows = query(BASE_FULL + """
            JOIN manager_relationships mr
                 ON mr.employee_id = vr.employee_id
                AND mr.manager_id  = %s::uuid
                AND mr.relationship_type = 'SOLID_LINE'
                AND mr.is_current
            WHERE vr.status = 'PENDING'
            ORDER BY vr.created_at
        """, (emp_id,))
        pending_all = [to_dict(r) for r in pending_rows]

    else:  # all — admin/hr scoped to company
        if company_id:
            rows = query(BASE_FULL + """
                WHERE e.company_id = %s::uuid
                  AND vr.status IN ('APPROVED','PENDING')
                  AND vr.start_date <= %s AND vr.end_date >= %s
                ORDER BY vr.start_date
            """, (company_id, last_day, first_day))
        else:
            rows = []

    # Expand each request into individual calendar dates
    events_by_date = {}
    for r in rows:
        rd = to_dict(r)
        s  = rd['start_date'] if isinstance(rd['start_date'], datetime.date) \
             else datetime.date.fromisoformat(str(rd['start_date']))
        e  = rd['end_date']   if isinstance(rd['end_date'],   datetime.date) \
             else datetime.date.fromisoformat(str(rd['end_date']))

        current     = max(s, first_day)
        end_clamped = min(e, last_day)
        while current <= end_clamped:
            if current.weekday() < 5:  # Mon–Fri only
                key = current.isoformat()
                events_by_date.setdefault(key, []).append({
                    'id':            rd['id'],
                    'employee_name': rd['employee_name'],
                    'employee_id':   rd['employee_id'],
                    'type_name':     rd['type_name'],
                    'color':         rd['color'] or '#3b82f6',
                    'status':        rd['status'],
                    'start_date':    str(s),
                    'end_date':      str(e),
                })
            current += datetime.timedelta(days=1)

    # Serialise dates in pending_all
    for p in pending_all:
        p['start_date'] = str(p['start_date'])
        p['end_date']   = str(p['end_date'])

    return jsonify({
        'year':           year,
        'month':          month,
        'events_by_date': events_by_date,
        'pending_all':    pending_all,   # non-empty only for team scope
    })
