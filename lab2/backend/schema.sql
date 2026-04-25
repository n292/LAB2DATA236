CREATE DATABASE IF NOT EXISTS linkedin_sim;
USE linkedin_sim;

CREATE TABLE IF NOT EXISTS members (
  member_id VARCHAR(64) PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(50) NULL,
  city VARCHAR(100) NULL,
  state VARCHAR(100) NULL,
  country VARCHAR(100) NULL,
  headline VARCHAR(255) NULL,
  about_summary TEXT NULL,
  experience_json JSON NULL,
  education_json JSON NULL,
  skills_json JSON NULL,
  profile_photo_url TEXT NULL,
  resume_text LONGTEXT NULL,
  connections_count INT NOT NULL DEFAULT 0,
  profile_views_daily INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_members_email (email),
  INDEX idx_members_location (city, state, country)
);
