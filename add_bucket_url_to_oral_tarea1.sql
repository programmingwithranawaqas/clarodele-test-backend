-- Add bucket_url column to oral_tarea1_set table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='oral_tarea1_set' AND column_name='bucket_url'
    ) THEN
        ALTER TABLE oral_tarea1_set ADD COLUMN bucket_url TEXT;
        COMMENT ON COLUMN oral_tarea1_set.bucket_url IS 'Google Cloud Storage bucket URL after migration (gs://...)';
    END IF;
END$$;
