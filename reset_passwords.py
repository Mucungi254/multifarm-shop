from werkzeug.security import generate_password_hash
import MySQLdb

# Connect to your database
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='',          # XAMPP default is empty
    db='multifarm_shop_db'
)

cur = conn.cursor()

# Reset passwords for all three users
users = [
    ('admin', 'admin123', 'admin', 'Mucungi'),
    ('sarah', 'sarah123', 'agent', 'Sarah'),
    ('muchiri', 'muchiri123', 'secretary', 'Muchiri')
]

for username, password, role, full_name in users:
    hashed = generate_password_hash(password)
    # Check if user exists
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.execute("UPDATE users SET password_hash = %s WHERE username = %s", (hashed, username))
    else:
        cur.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)",
                    (username, hashed, role, full_name))
    print(f"✅ {username} updated/inserted.")

conn.commit()
cur.close()
conn.close()
print("🎉 All users are ready.")