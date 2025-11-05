-- =========================================
-- UniSoruyor.com SQL Database Schema
-- =========================================

CREATE DATABASE IF NOT EXISTS unisoruyor;
USE unisoruyor;

-- Users Table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    university VARCHAR(100) NOT NULL,
    faculty VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    last_question_at TIMESTAMP NULL,
    last_answer_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_university (university),
    INDEX idx_is_admin (is_admin)
);

-- Questions Table
CREATE TABLE questions (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id VARCHAR(36) NOT NULL,
    author_username VARCHAR(50) NOT NULL,
    author_university VARCHAR(100) NOT NULL,
    author_faculty VARCHAR(100) NOT NULL,
    author_department VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    view_count INT DEFAULT 0,
    answer_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_author_id (author_id),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at),
    INDEX idx_university (author_university),
    FULLTEXT idx_search (title, content)
);

-- Answers Table
CREATE TABLE answers (
    id VARCHAR(36) PRIMARY KEY,
    question_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    author_id VARCHAR(36) NOT NULL,
    author_username VARCHAR(50) NOT NULL,
    mentioned_users JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_accepted BOOLEAN DEFAULT FALSE,
    parent_answer_id VARCHAR(36) NULL,
    reply_count INT DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    INDEX idx_question_id (question_id),
    INDEX idx_author_id (author_id),
    INDEX idx_parent_answer_id (parent_answer_id),
    INDEX idx_created_at (created_at)
);

-- File Uploads Table
CREATE TABLE file_uploads (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_by VARCHAR(36) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_uploaded_by (uploaded_by),
    INDEX idx_file_type (file_type)
);

-- Question Attachments (Many-to-Many)
CREATE TABLE question_attachments (
    question_id VARCHAR(36) NOT NULL,
    file_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (question_id, file_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES file_uploads(id) ON DELETE CASCADE
);

-- Answer Attachments (Many-to-Many)
CREATE TABLE answer_attachments (
    answer_id VARCHAR(36) NOT NULL,
    file_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (answer_id, file_id),
    FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES file_uploads(id) ON DELETE CASCADE
);

-- Question Likes (Many-to-Many)
CREATE TABLE question_likes (
    question_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (question_id, user_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_created_at (created_at)
);

-- Notifications Table
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    type ENUM('answer', 'reply', 'mention', 'like') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_question_id VARCHAR(36) NULL,
    related_answer_id VARCHAR(36) NULL,
    from_user_id VARCHAR(36) NOT NULL,
    from_username VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (related_answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);