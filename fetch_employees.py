import http.server
import json
import os
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras


DB_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'port': int(os.getenv('PGPORT', 5432)),
    'dbname': os.getenv('PGDATABASE', 'employee'),
    'user': os.getenv('PGUSER', 'samirroy'),
    'password': os.getenv('PGPASSWORD', None),
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def parse_skills(raw):
    if not raw:
        return []
    return [s.strip() for s in raw.split(',') if s.strip()]


def parse_skill_ratings(raw):
    if not raw:
        return []
    ratings = []
    for part in raw.split(','):
        part = part.strip()
        if ':' in part:
            skill, _, score = part.rpartition(':')
            try:
                ratings.append({'skill': skill.strip(), 'rating': int(score.strip())})
            except ValueError:
                pass
    return ratings


def fetch_employees_from_db():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                '''SELECT e.employee_id            AS id,
                          e.employee_name          AS name,
                          e.designation            AS title,
                          e.department,
                          e.product_unit_department,
                          e.location,
                          e.designation,
                          e.skills,
                          e.experience_years       AS years_of_experience,
                          e.skill_ratings,
                          e.solid_line_manager_name,
                          sm.designation           AS solid_line_manager_designation,
                          e.dotted_line_manager_name,
                          dm.designation           AS dotted_line_manager_designation
                   FROM employee_directory e
                   LEFT JOIN employee_directory sm ON sm.employee_id = e.solid_line_manager_id
                   LEFT JOIN employee_directory dm ON dm.employee_id = e.dotted_line_manager_id
                   ORDER BY e.employee_id'''
            )
            rows = []
            for row in cur.fetchall():
                r = dict(row)
                r['skills'] = parse_skills(r.get('skills'))
                r['skill_ratings'] = parse_skill_ratings(r.get('skill_ratings'))
                rows.append(r)
            return rows


class EmployeeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/employees':
            try:
                employees = fetch_employees_from_db()
            except Exception as exc:
                print(f"DB Error: {exc}")  # Debug print
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(
                    json.dumps({'error': str(exc)}).encode('utf-8')
                )
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(employees).encode('utf-8'))
        else:
            super().do_GET()


def run(server_class=http.server.ThreadingHTTPServer, handler_class=EmployeeRequestHandler, port=8000):
    os.chdir(os.path.dirname(__file__))
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving on http://127.0.0.1:{port}')
    print(f'Connecting to Postgres at {DB_CONFIG["host"]}:{DB_CONFIG["port"]} database={DB_CONFIG["dbname"]}')
    print('Press Ctrl+C to stop')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
