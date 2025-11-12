-- Migration to add lesson tables to the chess training database

-- Lessons table
CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    focus_areas JSONB,
    user_elo_at_creation INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'generating',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_lessons_user_id ON lessons(user_id);
CREATE INDEX idx_lessons_status ON lessons(status);
CREATE INDEX idx_lessons_created_at ON lessons(created_at DESC);

-- Lesson comments table
CREATE TABLE IF NOT EXISTS lesson_comments (
    id SERIAL PRIMARY KEY,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    position_fen VARCHAR(255) NOT NULL,
    move_to_make VARCHAR(10),
    text TEXT NOT NULL,
    annotations JSONB DEFAULT '[]'::jsonb,
    question JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lesson_id, step_number)
);

CREATE INDEX idx_lesson_comments_lesson_id ON lesson_comments(lesson_id);
CREATE INDEX idx_lesson_comments_step_number ON lesson_comments(lesson_id, step_number);

-- User lesson progress table
CREATE TABLE IF NOT EXISTS user_lesson_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    current_step INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    answers JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lesson_id)
);

CREATE INDEX idx_user_lesson_progress_user_id ON user_lesson_progress(user_id);
CREATE INDEX idx_user_lesson_progress_lesson_id ON user_lesson_progress(lesson_id);
CREATE INDEX idx_user_lesson_progress_last_accessed ON user_lesson_progress(last_accessed DESC);
