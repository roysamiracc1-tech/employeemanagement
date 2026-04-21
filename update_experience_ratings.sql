-- Add experience and skill ratings columns
ALTER TABLE employees ADD COLUMN years_of_experience INTEGER;
ALTER TABLE employees ADD COLUMN skill_ratings JSONB;

-- Update all employees with experience and skill ratings
UPDATE employees SET 
  years_of_experience = 12,
  skill_ratings = '[{"skill": "Leadership", "rating": 9}, {"skill": "Python", "rating": 8}, {"skill": "Project Management", "rating": 9}]'::jsonb
WHERE id = 1;

UPDATE employees SET 
  years_of_experience = 8,
  skill_ratings = '[{"skill": "UI/UX", "rating": 9}, {"skill": "Figma", "rating": 9}, {"skill": "Prototyping", "rating": 8}]'::jsonb
WHERE id = 2;

UPDATE employees SET 
  years_of_experience = 7,
  skill_ratings = '[{"skill": "JavaScript", "rating": 9}, {"skill": "React", "rating": 8}, {"skill": "Node.js", "rating": 8}]'::jsonb
WHERE id = 3;

UPDATE employees SET 
  years_of_experience = 10,
  skill_ratings = '[{"skill": "Testing", "rating": 9}, {"skill": "Automation", "rating": 8}, {"skill": "Selenium", "rating": 8}]'::jsonb
WHERE id = 4;

UPDATE employees SET 
  years_of_experience = 6,
  skill_ratings = '[{"skill": "Recruitment", "rating": 8}, {"skill": "Employee Relations", "rating": 9}, {"skill": "Compliance", "rating": 7}]'::jsonb
WHERE id = 5;

UPDATE employees SET 
  years_of_experience = 15,
  skill_ratings = '[{"skill": "Sales Strategy", "rating": 9}, {"skill": "Negotiation", "rating": 9}, {"skill": "CRM", "rating": 7}]'::jsonb
WHERE id = 6;

UPDATE employees SET 
  years_of_experience = 7,
  skill_ratings = '[{"skill": "Digital Marketing", "rating": 9}, {"skill": "SEO", "rating": 8}, {"skill": "Content Creation", "rating": 8}]'::jsonb
WHERE id = 7;

UPDATE employees SET 
  years_of_experience = 5,
  skill_ratings = '[{"skill": "Customer Support", "rating": 9}, {"skill": "Retention", "rating": 8}, {"skill": "Analytics", "rating": 7}]'::jsonb
WHERE id = 8;

UPDATE employees SET 
  years_of_experience = 6,
  skill_ratings = '[{"skill": "SQL", "rating": 9}, {"skill": "Python", "rating": 8}, {"skill": "Data Visualization", "rating": 8}]'::jsonb
WHERE id = 9;

UPDATE employees SET 
  years_of_experience = 4,
  skill_ratings = '[{"skill": "Operations", "rating": 8}, {"skill": "Logistics", "rating": 7}, {"skill": "Process Improvement", "rating": 7}]'::jsonb
WHERE id = 10;
