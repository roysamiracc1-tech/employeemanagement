"""Bulk employee import — upload, preview, approve, process."""
import json

from flask import session, request, jsonify, render_template, redirect, url_for, flash

from app import app
from app.auth import login_required, require_roles
from app.db import query, execute, to_dict
from app.services.company_scope import current_company_id
from app.services import import_service

_UPLOAD_ROLES  = ('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')
_APPROVE_ROLES = ('SYSTEM_ADMIN', 'PORTAL_ADMIN')


@app.route('/admin/imports')
@require_roles(*_UPLOAD_ROLES)
def imports_list():
    company_id = current_company_id() or session.get('company_id')
    imports = []
    if company_id:
        rows = query("""
            SELECT ei.id::text, ei.filename, ei.status, ei.row_count,
                   ei.valid_count, ei.error_count, ei.imported_count,
                   ei.created_at, ei.processed_at,
                   u.email AS uploaded_by_email
            FROM employee_imports ei
            JOIN users u ON u.id = ei.uploaded_by
            WHERE ei.company_id = %s::uuid
            ORDER BY ei.created_at DESC LIMIT 50
        """, (company_id,))
        imports = [to_dict(r) for r in rows]
    return render_template('imports/list.html', imports=imports)


@app.route('/admin/imports/upload', methods=['GET'])
@require_roles(*_UPLOAD_ROLES)
def imports_upload_page():
    return render_template('imports/upload.html')


@app.route('/api/admin/imports/upload', methods=['POST'])
@require_roles(*_UPLOAD_ROLES)
def api_imports_upload():
    company_id = current_company_id() or session.get('company_id')
    if not company_id:
        return jsonify({'error': 'No company context'}), 400

    file = request.files.get('csv_file')
    if not file or not file.filename:
        return jsonify({'error': 'No file uploaded'}), 400
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only CSV files are accepted'}), 400

    rows, summary = import_service.parse_and_validate(file.read(), company_id)
    if 'error' in summary:
        return jsonify({'error': summary['error']}), 400

    import_id = import_service.create_import_record(
        company_id, session['user_id'], file.filename, rows, summary)

    # HR_ADMIN uploads go straight to PENDING_REVIEW (need approval).
    # PORTAL_ADMIN / SYSTEM_ADMIN auto-approve if no errors.
    roles  = session.get('roles', [])
    is_admin = any(r in roles for r in ('SYSTEM_ADMIN', 'PORTAL_ADMIN'))
    if is_admin and summary['error_count'] == 0:
        execute(
            "UPDATE employee_imports SET status='APPROVED', approved_by=%s::uuid, "
            "approved_at=NOW() WHERE id=%s::uuid",
            (session['user_id'], import_id))

    return jsonify({
        'import_id':   import_id,
        'summary':     summary,
        'needs_approval': not is_admin,
        'preview_url': f'/admin/imports/{import_id}/preview',
    })


@app.route('/admin/imports/<import_id>/preview')
@require_roles(*_UPLOAD_ROLES)
def imports_preview(import_id):
    company_id = current_company_id() or session.get('company_id')
    imp = query(
        "SELECT id::text, filename, status, row_count, valid_count, error_count, "
        "imported_count, company_id::text FROM employee_imports WHERE id=%s::uuid",
        (import_id,), one=True)
    if not imp:
        flash('Import not found.', 'error')
        return redirect(url_for('imports_list'))

    # Company scoping guard
    if company_id and imp['company_id'] != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('imports_list'))

    rows = query(
        "SELECT row_number, raw_data, validation_errors, status "
        "FROM employee_import_rows WHERE import_id=%s::uuid ORDER BY row_number LIMIT 200",
        (import_id,))
    rows_list = [to_dict(r) for r in rows]

    return render_template('imports/preview.html',
                           imp=to_dict(imp),
                           rows=rows_list,
                           import_id=import_id)


@app.route('/api/admin/imports/<import_id>/approve', methods=['POST'])
@require_roles(*_APPROVE_ROLES)
def api_imports_approve(import_id):
    company_id = current_company_id() or session.get('company_id')
    imp = query(
        "SELECT status, company_id::text FROM employee_imports WHERE id=%s::uuid",
        (import_id,), one=True)
    if not imp:
        return jsonify({'error': 'Not found'}), 404
    if company_id and imp['company_id'] != company_id:
        return jsonify({'error': 'Access denied'}), 403
    if imp['status'] != 'PENDING_REVIEW':
        return jsonify({'error': f"Cannot approve import in status '{imp['status']}'"}), 400

    execute(
        "UPDATE employee_imports SET status='APPROVED', approved_by=%s::uuid, "
        "approved_at=NOW() WHERE id=%s::uuid",
        (session['user_id'], import_id))
    return jsonify({'ok': True})


@app.route('/api/admin/imports/<import_id>/reject', methods=['POST'])
@require_roles(*_APPROVE_ROLES)
def api_imports_reject(import_id):
    company_id = current_company_id() or session.get('company_id')
    data   = request.get_json() or {}
    reason = data.get('reason', '').strip()
    imp    = query(
        "SELECT status, company_id::text FROM employee_imports WHERE id=%s::uuid",
        (import_id,), one=True)
    if not imp:
        return jsonify({'error': 'Not found'}), 404
    if company_id and imp['company_id'] != company_id:
        return jsonify({'error': 'Access denied'}), 403

    execute(
        "UPDATE employee_imports SET status='REJECTED', reject_reason=%s WHERE id=%s::uuid",
        (reason or None, import_id))
    return jsonify({'ok': True})


@app.route('/api/admin/imports/<import_id>/process', methods=['POST'])
@require_roles(*_APPROVE_ROLES)
def api_imports_process(import_id):
    company_id = current_company_id() or session.get('company_id')
    imp = query(
        "SELECT status, company_id::text FROM employee_imports WHERE id=%s::uuid",
        (import_id,), one=True)
    if not imp:
        return jsonify({'error': 'Not found'}), 404
    if company_id and imp['company_id'] != company_id:
        return jsonify({'error': 'Access denied'}), 403
    if imp['status'] != 'APPROVED':
        return jsonify({'error': 'Import must be approved before processing'}), 400

    execute(
        "UPDATE employee_imports SET status='PROCESSING' WHERE id=%s::uuid",
        (import_id,))
    result = import_service.apply_import(import_id, imp['company_id'])
    return jsonify({'ok': True, **result})
