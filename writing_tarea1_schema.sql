-- ===========================================================
-- WRITING TAREA 1 SCHEMA
-- Each set contains one writing task and one model solution
-- ===========================================================

-- 1️⃣ Table: writing_tarea1_set
CREATE TABLE IF NOT EXISTS public.writing_tarea1_set (
  tarea1_set_id SERIAL PRIMARY KEY,
  title TEXT,                        -- optional name, example: "Informe sobre los servicios públicos"
  situation TEXT NOT NULL,           -- full situation description
  task_instructions TEXT NOT NULL,   -- full task text (bullets included)
  word_limit TEXT,                   -- example: "150–180 palabras"
  text_type TEXT,                    -- example: "Informe formal"
  register TEXT,                     -- example: "formal"
  reminders TEXT,                    -- "Recuerde: ..."
  audio_url TEXT,                    -- optional audio material
  module_type_id INT NOT NULL
      REFERENCES public.module_type(module_type_id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 2️⃣ Table: writing_tarea1_solution
CREATE TABLE IF NOT EXISTS public.writing_tarea1_solution (
  solution_id SERIAL PRIMARY KEY,
  tarea1_set_id INT NOT NULL
      REFERENCES public.writing_tarea1_set(tarea1_set_id) ON DELETE CASCADE,
  solution_text TEXT NOT NULL        -- the full model answer
);

-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_writing_tarea1_set_module_type 
ON public.writing_tarea1_set(module_type_id);

CREATE INDEX IF NOT EXISTS idx_writing_tarea1_solution_tarea1_set 
ON public.writing_tarea1_solution(tarea1_set_id);

-- Add comments for documentation
COMMENT ON TABLE public.writing_tarea1_set IS 'Writing Tarea 1 tasks with situation, instructions, and metadata';
COMMENT ON TABLE public.writing_tarea1_solution IS 'Model solutions for Writing Tarea 1 tasks';

COMMENT ON COLUMN public.writing_tarea1_set.title IS 'Optional descriptive title for the task';
COMMENT ON COLUMN public.writing_tarea1_set.situation IS 'Complete situation/context description for the writing task';
COMMENT ON COLUMN public.writing_tarea1_set.task_instructions IS 'Full task instructions including all bullet points';
COMMENT ON COLUMN public.writing_tarea1_set.word_limit IS 'Word count requirement (e.g., "150–180 palabras")';
COMMENT ON COLUMN public.writing_tarea1_set.text_type IS 'Type of text to write (e.g., "Informe formal", "Carta", "Email")';
COMMENT ON COLUMN public.writing_tarea1_set.register IS 'Language register (e.g., "formal", "informal")';
COMMENT ON COLUMN public.writing_tarea1_set.reminders IS 'Special reminders or notes for the task';
COMMENT ON COLUMN public.writing_tarea1_set.audio_url IS 'Optional URL to audio material (Google Drive or GCS bucket)';
COMMENT ON COLUMN public.writing_tarea1_solution.solution_text IS 'Complete model answer text';
