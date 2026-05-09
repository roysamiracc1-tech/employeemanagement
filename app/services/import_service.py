"""Bulk employee import service — CSV parse, validate, and apply."""
import csv
import io
import datetime

from app.db import query, execute, insert_returning, to_dict
from app.helpers import next_employee_number


# Expected CSV columns (case-insensitive header match)
REQUIRED_COLS = {'first_name', 'last_name', 'email'}
OPTIONAL_COLS = {'job_title', 'employment_type', 'gender', 'phone_number', 'join_date'}

ALL_COLS = REQUIRED_COLS | OPTIONAL_COLS

EMPLOYMENT_TYPES = {'FULL_TIME', 'PART_TIME', 'CONTRACTOR', 'INTERN'}
GENDERS          = {'MALE', 'FEMALE', 'OTHER'}


def parse_and_validate(file_bytes: bytes, company_id: str):
    """Parse CSV bytes, validate each row.

    Returns (rows, summary) where rows is a list of dicts with keys:
        row_number, raw_data (dict), validation_errors (list or None), status
    """
    text   = file_bytes.decode('utf-8-sig', errors='replace')
    reader = csv.DictReader(io.StringIO(text))

    # Normalise header names
    if not reader.fieldnames:
        return [], {'error': 'Empty or unreadable CSV'}

    norm_headers = {h.strip().lower(): h for h in reader.fieldnames}
    missing_req  = REQUIRED_COLS - set(norm_headers.keys())
    if missing_req:
        return [], {'error': f"Missing required columns: {', '.join(sorted(missing_req))}"}

    rows    = []
    emails  = set()

    for i, row in enumerate(reader, start=1):
        raw = {norm_headers.get(k, k): v.strip() for k, v in row.items()
               if k and norm_headers.get(k.strip().lower())}

        errors = []
        fn = raw.get('first_name', '').strip()
        ln = raw.get('last_name',  '').strip()
        em = raw.get('email',      '').strip().lower()

        if not fn:  errors.append('first_name is required')
        if not ln:  errors.append('last_name is required')
        if not em:  errors.append('email is required')
        elif '@' not in em: errors.append('email is invalid')
        elif em in emails:  errors.append('duplicate email in this import')
        else:
            # Check DB uniqueness
            exists = query("SELECT 1 FROM employees WHERE LOWER(email)=%s LIMIT 1",
                           (em,), one=True)
            if exists:
                errors.append(f'email {em} already exists in system')
            emails.add(em)

        et = raw.get('employment_type', '').strip().upper() or 'FULL_TIME'
        if et and et not in EMPLOYMENT_TYPES:
            errors.append(f'employment_type must be one of {EMPLOYMENT_TYPES}')
        else:
            raw['employment_type'] = et

        gd = raw.get('gender', '').strip().upper()
        if gd and gd not in GENDERS:
            errors.append(f'gender must be one of {GENDERS}')
        elif gd:
            raw['gender'] = gd

        jd = raw.get('join_date', '').strip()
        if jd:
            try:
                datetime.date.fromisoformat(jd)
            except ValueError:
                errors.append('join_date must be YYYY-MM-DD')

        rows.append({
            'row_number':        i,
            'raw_data':          raw,
            'validation_errors': errors if errors else None,
            'status':            'INVALID' if errors else 'VALID',
        })

    valid   = sum(1 for r in rows if r['status'] == 'VALID')
    invalid = len(rows) - valid
    return rows, {'row_count': len(rows), 'valid_count': valid, 'error_count': invalid}


def create_import_record(company_id, uploaded_by_user_id, filename, rows, summary):
    """Persist import + rows to DB.  Returns import_id."""
    import json

    imp = insert_returning("""
        INSERT INTO employee_imports
            (company_id, uploaded_by, filename, row_count, valid_count, error_count)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s)
        RETURNING id::text
    """, (company_id, uploaded_by_user_id, filename,
          summary.get('row_count', 0),
          summary.get('valid_count', 0),
          summary.get('error_count', 0)))

    import_id = imp['id']

    for r in rows:
        execute("""
            INSERT INTO employee_import_rows
                (import_id, row_number, raw_data, validation_errors, status)
            VALUES (%s::uuid, %s, %s::jsonb, %s::jsonb, %s)
        """, (import_id, r['row_number'],
              json.dumps(r['raw_data']),
              json.dumps(r['validation_errors']) if r['validation_errors'] else None,
              r['status']))

    return import_id


def apply_import(import_id: str, company_id: str):
    """Insert VALID rows as employees.  Updates import status to COMPLETED or FAILED."""
    rows = query(
        "SELECT id::text, raw_data FROM employee_import_rows "
        "WHERE import_id=%s::uuid AND status='VALID'",
        (import_id,),
    )

    imported = 0
    failed   = 0

    for r in rows:
        data = r['raw_data']
        try:
            emp_num = next_employee_number()
            emp_row = insert_returning("""
                INSERT INTO employees
                    (employee_number, first_name, last_name, email,
                     phone_number, job_title, employment_type, gender,
                     join_date, employment_status, company_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s::uuid)
                RETURNING id::text
            """, (
                emp_num,
                data.get('first_name', ''),
                data.get('last_name', ''),
                data.get('email', '').lower(),
                data.get('phone_number') or None,
                data.get('job_title') or None,
                data.get('employment_type', 'FULL_TIME'),
                data.get('gender') or None,
                data.get('join_date') or None,
                company_id,
            ))
            execute(
                "UPDATE employee_import_rows SET status='IMPORTED', employee_id=%s::uuid "
                "WHERE id=%s::uuid",
                (emp_row['id'], r['id']),
            )
            imported += 1
        except Exception:
            execute(
                "UPDATE employee_import_rows SET status='SKIPPED' WHERE id=%s::uuid",
                (r['id'],),
            )
            failed += 1

    new_status = 'COMPLETED' if not failed else ('FAILED' if imported == 0 else 'COMPLETED')
    execute("""
        UPDATE employee_imports
           SET status=%s, imported_count=%s, error_count=%s, processed_at=NOW()
         WHERE id=%s::uuid
    """, (new_status, imported, failed, import_id))

    return {'imported': imported, 'failed': failed}
