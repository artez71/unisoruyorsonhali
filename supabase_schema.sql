-- =========================================
-- UniSoruyor.com PostgreSQL/Supabase Schema
-- =========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    university VARCHAR(100) NOT NULL,
    faculty VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    last_question_at TIMESTAMP WITH TIME ZONE NULL,
    last_answer_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_username ON public.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_university ON public.users(university);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON public.users(is_admin);

-- Questions Table
CREATE TABLE IF NOT EXISTS public.questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    author_username VARCHAR(50) NOT NULL,
    author_university VARCHAR(100) NOT NULL,
    author_faculty VARCHAR(100) NOT NULL,
    author_department VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    view_count INTEGER DEFAULT 0,
    answer_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0
);

-- Create indexes for questions
CREATE INDEX IF NOT EXISTS idx_questions_author_id ON public.questions(author_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON public.questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON public.questions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_questions_university ON public.questions(author_university);

-- Full-text search index for questions
CREATE INDEX IF NOT EXISTS idx_questions_search ON public.questions USING GIN(to_tsvector('turkish', title || ' ' || content));

-- Answers Table
CREATE TABLE IF NOT EXISTS public.answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    author_username VARCHAR(50) NOT NULL,
    mentioned_users JSONB DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_accepted BOOLEAN DEFAULT FALSE,
    parent_answer_id UUID NULL REFERENCES public.answers(id) ON DELETE CASCADE,
    reply_count INTEGER DEFAULT 0
);

-- Create indexes for answers
CREATE INDEX IF NOT EXISTS idx_answers_question_id ON public.answers(question_id);
CREATE INDEX IF NOT EXISTS idx_answers_author_id ON public.answers(author_id);
CREATE INDEX IF NOT EXISTS idx_answers_parent_answer_id ON public.answers(parent_answer_id);
CREATE INDEX IF NOT EXISTS idx_answers_created_at ON public.answers(created_at DESC);

-- File Uploads Table
CREATE TABLE IF NOT EXISTS public.file_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_by UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for file_uploads
CREATE INDEX IF NOT EXISTS idx_file_uploads_uploaded_by ON public.file_uploads(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_file_uploads_file_type ON public.file_uploads(file_type);

-- Question Attachments (Many-to-Many)
CREATE TABLE IF NOT EXISTS public.question_attachments (
    question_id UUID NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES public.file_uploads(id) ON DELETE CASCADE,
    PRIMARY KEY (question_id, file_id)
);

-- Answer Attachments (Many-to-Many)
CREATE TABLE IF NOT EXISTS public.answer_attachments (
    answer_id UUID NOT NULL REFERENCES public.answers(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES public.file_uploads(id) ON DELETE CASCADE,
    PRIMARY KEY (answer_id, file_id)
);

-- Question Likes (Many-to-Many)
CREATE TABLE IF NOT EXISTS public.question_likes (
    question_id UUID NOT NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (question_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_question_likes_created_at ON public.question_likes(created_at DESC);

-- Notifications Table
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('answer', 'reply', 'mention', 'like')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_question_id UUID NULL REFERENCES public.questions(id) ON DELETE CASCADE,
    related_answer_id UUID NULL REFERENCES public.answers(id) ON DELETE CASCADE,
    from_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    from_username VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON public.notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON public.notifications(created_at DESC);

-- =========================================
-- Row Level Security (RLS) Policies
-- =========================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.answer_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view all profiles" ON public.users
    FOR SELECT USING (true);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Questions policies
CREATE POLICY "Anyone can view questions" ON public.questions
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create questions" ON public.questions
    FOR INSERT WITH CHECK (auth.uid()::text = author_id::text);

CREATE POLICY "Users can update own questions" ON public.questions
    FOR UPDATE USING (auth.uid()::text = author_id::text);

CREATE POLICY "Users can delete own questions" ON public.questions
    FOR DELETE USING (auth.uid()::text = author_id::text);

-- Answers policies
CREATE POLICY "Anyone can view answers" ON public.answers
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create answers" ON public.answers
    FOR INSERT WITH CHECK (auth.uid()::text = author_id::text);

CREATE POLICY "Users can update own answers" ON public.answers
    FOR UPDATE USING (auth.uid()::text = author_id::text);

CREATE POLICY "Users can delete own answers" ON public.answers
    FOR DELETE USING (auth.uid()::text = author_id::text);

-- File uploads policies
CREATE POLICY "Users can view all files" ON public.file_uploads
    FOR SELECT USING (true);

CREATE POLICY "Users can upload files" ON public.file_uploads
    FOR INSERT WITH CHECK (auth.uid()::text = uploaded_by::text);

CREATE POLICY "Users can delete own files" ON public.file_uploads
    FOR DELETE USING (auth.uid()::text = uploaded_by::text);

-- Notifications policies
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own notifications" ON public.notifications
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- =========================================
-- Functions and Triggers
-- =========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON public.questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_answers_updated_at BEFORE UPDATE ON public.answers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment answer count
CREATE OR REPLACE FUNCTION increment_answer_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.questions
    SET answer_count = answer_count + 1
    WHERE id = NEW.question_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for answer count
CREATE TRIGGER trigger_increment_answer_count
    AFTER INSERT ON public.answers
    FOR EACH ROW EXECUTE FUNCTION increment_answer_count();

-- Function to decrement answer count
CREATE OR REPLACE FUNCTION decrement_answer_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.questions
    SET answer_count = answer_count - 1
    WHERE id = OLD.question_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger for answer count decrement
CREATE TRIGGER trigger_decrement_answer_count
    AFTER DELETE ON public.answers
    FOR EACH ROW EXECUTE FUNCTION decrement_answer_count();

-- =========================================
-- Indexes for Performance
-- =========================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_questions_author_created ON public.questions(author_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_answers_question_created ON public.answers(question_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created ON public.notifications(user_id, is_read, created_at DESC);

COMMENT ON TABLE public.users IS 'User accounts and profiles';
COMMENT ON TABLE public.questions IS 'Questions posted by users';
COMMENT ON TABLE public.answers IS 'Answers to questions';
COMMENT ON TABLE public.notifications IS 'User notifications';
