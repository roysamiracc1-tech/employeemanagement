# Employee Management

This repository serves a simple employee directory frontend backed by a Python HTTP server. It includes employee competencies (designation and skills) for future dashboard visualization.

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
  location TEXT NOT NULL,
  designation TEXT NOT NULL,
  skills TEXT[] NOT NULL
);
INSERT INTO employees (name, title, department, location, designation, skills) VALUES
  ('Priya Shah', 'Engineering Manager', 'Engineering', 'New York', 'Senior Manager', ARRAY['Leadership', 'Python', 'Project Management']),
  ('James Carter', 'Product Designer', 'Design', 'San Francisco', 'Lead Designer', ARRAY['UI/UX', 'Figma', 'Prototyping']),
  ('Sara Kim', 'Software Engineer', 'Engineering', 'Boston', 'Senior Engineer', ARRAY['JavaScript', 'React', 'Node.js']),
  ('Rohit Patel', 'QA Lead', 'Quality Assurance', 'Chicago', 'QA Manager', ARRAY['Testing', 'Automation', 'Selenium']),
  ('Ashley Jones', 'HR Business Partner', 'Human Resources', 'Seattle', 'HR Specialist', ARRAY['Recruitment', 'Employee Relations', 'Compliance']),
  ('Victor Alvarez', 'Sales Director', 'Sales', 'Miami', 'Director', ARRAY['Sales Strategy', 'Negotiation', 'CRM']),
  ('Nadia Khan', 'Marketing Manager', 'Marketing', 'London', 'Marketing Lead', ARRAY['Digital Marketing', 'SEO', 'Content Creation']),
  ('Ethan Reed', 'Customer Success Lead', 'Customer Success', 'Toronto', 'Success Manager', ARRAY['Customer Support', 'Retention', 'Analytics']),
  ('Olivia Nguyen', 'Data Analyst', 'Business Intelligence', 'Berlin', 'Data Specialist', ARRAY['SQL', 'Python', 'Data Visualization']),
  ('Leonardo Silva', 'Operations Coordinator', 'Operations', 'Sydney', 'Coordinator', ARRAY['Operations', 'Logistics', 'Process Improvement']);
```

3. Run the backend:

```bash
PGHOST=localhost PGPORT=5432 PGDATABASE=employee PGUSER=samirroy python3 fetch_employees.py
```

4. Open the app:

```bash
open http://127.0.0.1:8000
```

## Notes

- The backend serves the frontend static files and exposes `/employees`.
- The frontend fetches employee data from `/employees` and renders the list.
