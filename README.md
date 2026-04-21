# Employee Management

This repository serves a simple employee directory frontend backed by a Python HTTP server.

## Local PostgreSQL setup

1. Install dependencies:

```bash
python3 -m pip install --user -r requirements.txt
```

2. Create a local PostgreSQL database and table, for example:

```sql
CREATE DATABASE employee;
\c employee
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  title TEXT NOT NULL,
  department TEXT NOT NULL,
  location TEXT NOT NULL
);
INSERT INTO employees (name, title, department, location) VALUES
  ('Priya Shah', 'Engineering Manager', 'Engineering', 'New York'),
  ('James Carter', 'Product Designer', 'Design', 'San Francisco'),
  ('Sara Kim', 'Software Engineer', 'Engineering', 'Boston'),
  ('Rohit Patel', 'QA Lead', 'Quality Assurance', 'Chicago'),
  ('Ashley Jones', 'HR Business Partner', 'Human Resources', 'Seattle'),
  ('Victor Alvarez', 'Sales Director', 'Sales', 'Miami'),
  ('Nadia Khan', 'Marketing Manager', 'Marketing', 'London'),
  ('Ethan Reed', 'Customer Success Lead', 'Customer Success', 'Toronto'),
  ('Olivia Nguyen', 'Data Analyst', 'Business Intelligence', 'Berlin'),
  ('Leonardo Silva', 'Operations Coordinator', 'Operations', 'Sydney');
```

3. Run the backend:

```bash
PGHOST=localhost PGPORT=5432 PGDATABASE=employee PGUSER=postgres python3 fetch_employees.py
```

4. Open the app:

```bash
open http://127.0.0.1:8000
```

## Notes

- The backend serves the frontend static files and exposes `/employees`.
- The frontend fetches employee data from `/employees` and renders the list.
