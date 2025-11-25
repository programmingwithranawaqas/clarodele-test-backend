-- Add bucket_url column to writing_tarea2_set table if it doesn't exist

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='writing_tarea2_set' 
        AND column_name='bucket_url'
    ) THEN
        ALTER TABLE writing_tarea2_set 
        ADD COLUMN bucket_url TEXT;
        
        COMMENT ON COLUMN writing_tarea2_set.bucket_url 
        IS 'Google Cloud Storage bucket URL after migration (gs://...)';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'writing_tarea2_set' 
ORDER BY ordinal_position;
