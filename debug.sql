-- Check current table structure
\d employees

-- Check current data
SELECT id, name, designation, skills FROM employees ORDER BY id;

-- Check if columns exist
SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'employees' AND table_schema = 'public' ORDER BY ordinal_position;
