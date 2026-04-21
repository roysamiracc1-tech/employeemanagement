from html.parser import HTMLParser


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
            # Only add rows that contain data (skip header row)
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
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    parser = EmployeeHTMLParser()
    parser.feed(html)
    return parser.employees


def main():
    employees = read_employee_html('index.html')
    print('Employee list from HTML:')
    for emp in employees:
        print(f"{emp['id']}. {emp['name']} - {emp['title']} ({emp['department']}, {emp['location']})")


if __name__ == '__main__':
    main()
