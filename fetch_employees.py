import http.server
import json
import os
from urllib.parse import urlparse

EMPLOYEES = [
    {"id": "1", "name": "Priya Shah", "title": "Engineering Manager", "department": "Engineering", "location": "New York"},
    {"id": "2", "name": "James Carter", "title": "Product Designer", "department": "Design", "location": "San Francisco"},
    {"id": "3", "name": "Sara Kim", "title": "Software Engineer", "department": "Engineering", "location": "Boston"},
    {"id": "4", "name": "Rohit Patel", "title": "QA Lead", "department": "Quality Assurance", "location": "Chicago"},
    {"id": "5", "name": "Ashley Jones", "title": "HR Business Partner", "department": "Human Resources", "location": "Seattle"},
    {"id": "6", "name": "Victor Alvarez", "title": "Sales Director", "department": "Sales", "location": "Miami"},
    {"id": "7", "name": "Nadia Khan", "title": "Marketing Manager", "department": "Marketing", "location": "London"},
    {"id": "8", "name": "Ethan Reed", "title": "Customer Success Lead", "department": "Customer Success", "location": "Toronto"},
    {"id": "9", "name": "Olivia Nguyen", "title": "Data Analyst", "department": "Business Intelligence", "location": "Berlin"},
    {"id": "10", "name": "Leonardo Silva", "title": "Operations Coordinator", "department": "Operations", "location": "Sydney"},
]


class EmployeeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/employees':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(EMPLOYEES).encode('utf-8'))
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
