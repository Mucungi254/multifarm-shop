-- Main daily records
CREATE TABLE daily_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_date DATE UNIQUE NOT NULL,
    john_am_litres DECIMAL(10,2) DEFAULT 0,
    john_pm_litres DECIMAL(10,2) DEFAULT 0,
    sales_am_litres DECIMAL(10,2) DEFAULT 0,
    sales_am_amount DECIMAL(10,2) DEFAULT 0,
    sales_pm_litres DECIMAL(10,2) DEFAULT 0,
    sales_pm_amount DECIMAL(10,2) DEFAULT 0,
    otc_paybill DECIMAL(10,2) DEFAULT 0,
    sarah_cash_deposit DECIMAL(10,2) DEFAULT 0,
    bank_statement DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Farmers list (imported from Excel)
CREATE TABLE farmers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_no VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    rider VARCHAR(10) DEFAULT 'B'
);

-- Farmer deliveries (per day, per farmer)
CREATE TABLE farmer_deliveries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_date DATE NOT NULL,
    farmer_id INT NOT NULL,
    litres DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (record_date) REFERENCES daily_records(record_date)
);

-- Users table (for login)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','agent','secretary') NOT NULL,
    full_name VARCHAR(100)
);

-- Insert default users (use hashed passwords later)
INSERT INTO users (username, password_hash, role, full_name) VALUES
('admin', 'scrypt:32768:8:1$...', 'admin', 'Mucungi'),
('sarah', 'scrypt:32768:8:1$...', 'agent', 'Sarah'),
('muchiri', 'scrypt:32768:8:1$...', 'secretary', 'Muchiri');