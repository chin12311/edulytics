SELECT id, name, is_active, created_at 
FROM main_evaluationperiod 
WHERE evaluation_type = 'student' 
ORDER BY created_at DESC 
LIMIT 10;
