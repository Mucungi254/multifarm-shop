import pymysql
from werkzeug.security import generate_password_hash

# Your Aiven credentials
DB_CONFIG = {
    'host': 'mysql-18a06b54-multifarm-db.l.aivencloud.com',
    'port': 24814,
    'user': 'avnadmin',
    'password': 'AVNS_2YWGrLyNJJSRvjm_GMF',
    'database': 'defaultdb',
}

# Path to the downloaded CA certificate (adjust if needed)
CA_CERT_PATH = 'ca.pem'  # or full path like 'C:/path/to/ca.pem'

def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_records (
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
                bank_statement DECIMAL(10,2) DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                member_no VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100),
                rider VARCHAR(10) DEFAULT 'B'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS farmer_deliveries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                record_date DATE NOT NULL,
                farmer_id INT NOT NULL,
                litres DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (farmer_id) REFERENCES farmers(id),
                FOREIGN KEY (record_date) REFERENCES daily_records(record_date)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin','agent','secretary') NOT NULL,
                full_name VARCHAR(100)
            )
        """)
        conn.commit()
        print("✅ Tables created (or already exist).")

def insert_users(conn):
    users = [
        ('admin', generate_password_hash('admin123'), 'admin', 'Mucungi'),
        ('sarah', generate_password_hash('sarah123'), 'agent', 'Sarah'),
        ('muchiri', generate_password_hash('muchiri123'), 'secretary', 'Muchiri')
    ]
    with conn.cursor() as cur:
        for username, pwd_hash, role, full_name in users:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                print(f"ℹ️ User {username} already exists, skipping.")
            else:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)",
                    (username, pwd_hash, role, full_name)
                )
        conn.commit()
        print("✅ Default users inserted (admin, sarah, muchiri).")

if __name__ == "__main__":
    try:
        # Connect with SSL using the downloaded CA certificate
        conn = pymysql.connect(
            **DB_CONFIG,
            ssl={'ca': CA_CERT_PATH}
        )
        create_tables(conn)
        insert_users(conn)
        conn.close()
        print("🎉 Database setup complete! You can now deploy and log in.")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your credentials and SSL settings.")