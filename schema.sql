-- Job Portal Database Schema
-- Compatible with MySQL 8.x

CREATE DATABASE IF NOT EXISTS jobportal;
USE jobportal;

-- ---------------------------
-- Table: users
-- ---------------------------
DROP TABLE IF EXISTS users;
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  mobile VARCHAR(15) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  profile_pic VARCHAR(255) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------
-- Table: employers
-- ---------------------------
DROP TABLE IF EXISTS employers;
CREATE TABLE employers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employer_name VARCHAR(150) NOT NULL,
  organization_name VARCHAR(255) NOT NULL,
  organization_email VARCHAR(150) NOT NULL UNIQUE,
  mobile VARCHAR(15) UNIQUE,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  logo_filename VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------
-- Table: jobs
-- ---------------------------
DROP TABLE IF EXISTS jobs;
CREATE TABLE jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  company VARCHAR(255) NOT NULL,
  logo VARCHAR(255) DEFAULT NULL,
  location VARCHAR(150) NOT NULL,
  description TEXT,
  posted_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  experience VARCHAR(50) NOT NULL,
  salary DECIMAL(10,2) NOT NULL,
  job_type ENUM('Full-Time','Part-Time','Internship','Remote') DEFAULT 'Full-Time',
  deadline DATE DEFAULT NULL,
  logo_filename VARCHAR(255) DEFAULT NULL,
  CONSTRAINT fk_jobs_employer FOREIGN KEY (posted_by) REFERENCES employers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------
-- Table: applications
-- ---------------------------
DROP TABLE IF EXISTS applications;
CREATE TABLE applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  job_id INT NOT NULL,
  resume_path VARCHAR(255) NOT NULL,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_app_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_app_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
