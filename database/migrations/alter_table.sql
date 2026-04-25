-- Add columns without NOT NULL first
ALTER TABLE employees ADD COLUMN designation TEXT;
ALTER TABLE employees ADD COLUMN skills TEXT[];
