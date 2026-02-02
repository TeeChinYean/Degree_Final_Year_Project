-- Database schema for Green Point
CREATE DATABASE IF NOT EXISTS greenpoint CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE greenpoint;
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  balance INT DEFAULT 0,
  created_at DATETIME
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS item_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  material VARCHAR(80),
  examples TEXT,
  points_per_item INT DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recycling (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  type VARCHAR(80),
  count INT,
  points INT,
  created_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contact_messages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200),
  email VARCHAR(200),
  message TEXT,
  created_at DATETIME
) ENGINE=InnoDB;

-- Seed some item types
INSERT INTO item_types (material,examples,points_per_item) VALUES
('Plastic','Bottles, containers, cups',2),
('Metal','Aluminum cans, tin cans',3),
('Paper','Newspapers, cardboard, packaging',1),
('Glass','Glass bottles, jars',4);
