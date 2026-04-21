import http.server
import json
import os
from html.parser import HTMLParser
from urllib.parse import urlparse


class EmployeeHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_tbody = False
        self.in_td = False
        self.current_row = []
        self.employees = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tbody' and self.in_table:
            self.in_tbody = True
        elif tag == 'td' and self.in_tbody:
            self.in_td = True

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tbody':
            self.in_tbody = False
        elif tag == 'td':
            self.in_td = False
        elif tag == 'tr' and self.current_row:
            if len(self.current_row) == 5:
                self.employees.append({
                    'id': self.current_row[0],
                    'name': self.current_row[1],
                    'title': self.current_row[2],
                    'department': self.current_row[3],
                    'location': self.current_row[4],
                })
            self.current_row = []

    def handle_data(self, data):
        if self.in_td:
            text = data.strip()
            if text:
                self.current_row.append(text)


def read_employee_html(path='index.html'):
    path = os.path.join(os.path.dirname(__file__), path)
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    parser = EmployeeHTMLParser()
    parser.feed(html)
    return parser.employees


class EmployeeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/employees':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            employees = read_employee_html('index.html')
            self.wfile.write(json.dumps(employees).encode('utf-8'))
        else:
            super().do_GET()


def run(server_class=http.server.ThreadingHTTPServer, handler_class=EmployeeRequestHandler, port=8000):
    os.chdir(os.path.dirname(__file__))
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving on http://127.0.0.1:{port}')
    print('Press Ctrl+C to stop')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
