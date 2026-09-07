CREATE DATABASE IF NOT EXISTS it_support_ticketing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE it_support_ticketing;

CREATE TABLE IF NOT EXISTS users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(100) NOT NULL UNIQUE,
 email VARCHAR(255) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 role ENUM('admin','technician','customer') NOT NULL,
 full_name VARCHAR(150) NOT NULL,
 phone VARCHAR(30),
 department VARCHAR(120),
 skills VARCHAR(500),
 status ENUM('active','inactive') NOT NULL DEFAULT 'active',
 joining_date DATE NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_users_role_status(role,status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NULL UNIQUE,
 company_name VARCHAR(180) NOT NULL,
 contact_person VARCHAR(150) NOT NULL,
 email VARCHAR(255) NOT NULL,
 phone VARCHAR(30),
 address TEXT,
 status ENUM('active','inactive') NOT NULL DEFAULT 'active',
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_customers_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
 INDEX idx_customers_name(company_name), INDEX idx_customers_email(email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE,
 description VARCHAR(255),
 status ENUM('active','inactive') NOT NULL DEFAULT 'active',
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tickets (
 id INT AUTO_INCREMENT PRIMARY KEY,
 ticket_number VARCHAR(20) NOT NULL UNIQUE,
 customer_id INT NOT NULL,
 created_by INT NOT NULL,
 subject VARCHAR(255) NOT NULL,
 description TEXT NOT NULL,
 category_id INT NOT NULL,
 priority ENUM('Low','Medium','High','Critical') NOT NULL DEFAULT 'Medium',
 status ENUM('Open','Assigned','In Progress','Waiting for Customer','Resolved','Closed','Reopened') NOT NULL DEFAULT 'Open',
 assigned_technician_id INT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 resolved_at DATETIME NULL,
 closed_at DATETIME NULL,
 CONSTRAINT fk_tickets_customer FOREIGN KEY(customer_id) REFERENCES customers(id),
 CONSTRAINT fk_tickets_creator FOREIGN KEY(created_by) REFERENCES users(id),
 CONSTRAINT fk_tickets_category FOREIGN KEY(category_id) REFERENCES categories(id),
 CONSTRAINT fk_tickets_technician FOREIGN KEY(assigned_technician_id) REFERENCES users(id) ON DELETE SET NULL,
 INDEX idx_tickets_status(status), INDEX idx_tickets_priority(priority), INDEX idx_tickets_category(category_id),
 INDEX idx_tickets_customer(customer_id), INDEX idx_tickets_tech(assigned_technician_id), INDEX idx_tickets_created(created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ticket_comments (
 id INT AUTO_INCREMENT PRIMARY KEY,
 ticket_id INT NOT NULL,
 user_id INT NOT NULL,
 comment TEXT NOT NULL,
 is_internal BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_comments_ticket FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
 CONSTRAINT fk_comments_user FOREIGN KEY(user_id) REFERENCES users(id),
 INDEX idx_comments_ticket_created(ticket_id,created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ticket_attachments (
 id INT AUTO_INCREMENT PRIMARY KEY,
 ticket_id INT NOT NULL,
 uploaded_by INT NOT NULL,
 original_name VARCHAR(255) NOT NULL,
 stored_name VARCHAR(255) NOT NULL UNIQUE,
 file_path VARCHAR(500) NOT NULL,
 mime_type VARCHAR(120),
 file_size BIGINT UNSIGNED NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_attachments_ticket FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
 CONSTRAINT fk_attachments_user FOREIGN KEY(uploaded_by) REFERENCES users(id),
 INDEX idx_attachments_ticket(ticket_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ticket_history (
 id INT AUTO_INCREMENT PRIMARY KEY,
 ticket_id INT NOT NULL,
 user_id INT NOT NULL,
 action VARCHAR(120) NOT NULL,
 old_value VARCHAR(255),
 new_value VARCHAR(255),
 details VARCHAR(500),
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_history_ticket FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
 CONSTRAINT fk_history_user FOREIGN KEY(user_id) REFERENCES users(id),
 INDEX idx_history_ticket_created(ticket_id,created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notifications (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL,
 ticket_id INT NULL,
 title VARCHAR(180) NOT NULL,
 message VARCHAR(500) NOT NULL,
 is_read BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_notifications_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_notifications_ticket FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE SET NULL,
 INDEX idx_notifications_user_read(user_id,is_read,created_at)
) ENGINE=InnoDB;
