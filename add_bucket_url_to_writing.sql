-- Add bucket_url column to writing_tarea1_set table if it doesn't exist
-- Run this SQL in your Supabase SQL Editor

-- Check if column exists, if not add it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='writing_tarea1_set' 
        AND column_name='bucket_url'
    ) THEN
        ALTER TABLE writing_tarea1_set 
        ADD COLUMN bucket_url TEXT;
        
        COMMENT ON COLUMN writing_tarea1_set.bucket_url 
        IS 'Google Cloud Storage bucket URL after migration (gs://...)';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'writing_tarea1_set' 
ORDER BY ordinal_position;
