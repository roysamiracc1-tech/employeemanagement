-- Update existing employees with designation and skills
UPDATE employees SET designation = 'Senior Manager', skills = ARRAY['Leadership', 'Python', 'Project Management'] WHERE name = 'Priya Shah';
UPDATE employees SET designation = 'Lead Designer', skills = ARRAY['UI/UX', 'Figma', 'Prototyping'] WHERE name = 'James Carter';
UPDATE employees SET designation = 'Senior Engineer', skills = ARRAY['JavaScript', 'React', 'Node.js'] WHERE name = 'Sara Kim';
UPDATE employees SET designation = 'QA Manager', skills = ARRAY['Testing', 'Automation', 'Selenium'] WHERE name = 'Rohit Patel';
UPDATE employees SET designation = 'HR Specialist', skills = ARRAY['Recruitment', 'Employee Relations', 'Compliance'] WHERE name = 'Ashley Jones';
UPDATE employees SET designation = 'Director', skills = ARRAY['Sales Strategy', 'Negotiation', 'CRM'] WHERE name = 'Victor Alvarez';
UPDATE employees SET designation = 'Marketing Lead', skills = ARRAY['Digital Marketing', 'SEO', 'Content Creation'] WHERE name = 'Nadia Khan';
UPDATE employees SET designation = 'Success Manager', skills = ARRAY['Customer Support', 'Retention', 'Analytics'] WHERE name = 'Ethan Reed';
UPDATE employees SET designation = 'Data Specialist', skills = ARRAY['SQL', 'Python', 'Data Visualization'] WHERE name = 'Olivia Nguyen';
UPDATE employees SET designation = 'Coordinator', skills = ARRAY['Operations', 'Logistics', 'Process Improvement'] WHERE name = 'Leonardo Silva';
