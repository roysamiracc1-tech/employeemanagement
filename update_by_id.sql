-- Update employees by ID (assuming IDs 1-10)
UPDATE employees SET designation = 'Senior Manager', skills = ARRAY['Leadership', 'Python', 'Project Management'] WHERE id = 1;
UPDATE employees SET designation = 'Lead Designer', skills = ARRAY['UI/UX', 'Figma', 'Prototyping'] WHERE id = 2;
UPDATE employees SET designation = 'Senior Engineer', skills = ARRAY['JavaScript', 'React', 'Node.js'] WHERE id = 3;
UPDATE employees SET designation = 'QA Manager', skills = ARRAY['Testing', 'Automation', 'Selenium'] WHERE id = 4;
UPDATE employees SET designation = 'HR Specialist', skills = ARRAY['Recruitment', 'Employee Relations', 'Compliance'] WHERE id = 5;
UPDATE employees SET designation = 'Director', skills = ARRAY['Sales Strategy', 'Negotiation', 'CRM'] WHERE id = 6;
UPDATE employees SET designation = 'Marketing Lead', skills = ARRAY['Digital Marketing', 'SEO', 'Content Creation'] WHERE id = 7;
UPDATE employees SET designation = 'Success Manager', skills = ARRAY['Customer Support', 'Retention', 'Analytics'] WHERE id = 8;
UPDATE employees SET designation = 'Data Specialist', skills = ARRAY['SQL', 'Python', 'Data Visualization'] WHERE id = 9;
UPDATE employees SET designation = 'Coordinator', skills = ARRAY['Operations', 'Logistics', 'Process Improvement'] WHERE id = 10;
