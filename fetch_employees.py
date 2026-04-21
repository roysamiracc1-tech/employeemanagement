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


def fetch_employees_from_db():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                'SELECT id, name, title, department, location, designation, skills FROM employees ORDER BY id'
            )
            return [dict(row) for row in cur.fetchall()]


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
