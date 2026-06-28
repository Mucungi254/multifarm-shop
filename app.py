from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime, date, timedelta
import openpyxl
import MySQLdb.cursors

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in.'

# ---------- User Class ----------
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user['id'], user['username'], user['role'])
    return None

# ---------- Ensure users exist ----------
def init_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)",
            ('admin', generate_password_hash('admin123'), 'admin', 'Mucungi')
        )
    cur.execute("SELECT id FROM users WHERE username = 'sarah'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)",
            ('sarah', generate_password_hash('sarah123'), 'agent', 'Sarah')
        )
    cur.execute("SELECT id FROM users WHERE username = 'muchiri'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)",
            ('muchiri', generate_password_hash('muchiri123'), 'secretary', 'Muchiri')
        )
    mysql.connection.commit()
    cur.close()

# ---------- Routes ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user['password_hash'], password):
            login_user(User(user['id'], user['username'], user['role']))
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Get date from request
    date_str = request.args.get('date', date.today().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        selected_date = date.today()

    cur = mysql.connection.cursor()

    # ===== POST: Save Record =====
    if request.method == 'POST':
        if current_user.role not in ['admin', 'agent']:
            flash('Not allowed.', 'danger')
            return redirect(url_for('dashboard', date=selected_date))

        # Read form values
        john_am = float(request.form.get('john_am_litres', 0) or 0)
        john_pm = float(request.form.get('john_pm_litres', 0) or 0)

        sales_am_litres = float(request.form.get('sales_am_litres', 0) or 0)
        sales_pm_litres = float(request.form.get('sales_pm_litres', 0) or 0)

        # ---- BACKEND AUTO-CALCULATION ----
        sales_am_amount = sales_am_litres * 60
        sales_pm_amount = sales_pm_litres * 60

        otc_paybill = float(request.form.get('otc_paybill', 0) or 0)
        sarah_cash = float(request.form.get('sarah_cash_deposit', 0) or 0)
        bank_stmt = float(request.form.get('bank_statement', 0) or 0)

        # Check if record exists
        cur.execute("SELECT id FROM daily_records WHERE record_date = %s", (selected_date,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE daily_records SET
                    john_am_litres = %s, john_pm_litres = %s,
                    sales_am_litres = %s, sales_am_amount = %s,
                    sales_pm_litres = %s, sales_pm_amount = %s,
                    otc_paybill = %s, sarah_cash_deposit = %s,
                    bank_statement = %s
                WHERE record_date = %s
            """, (john_am, john_pm,
                  sales_am_litres, sales_am_amount,
                  sales_pm_litres, sales_pm_amount,
                  otc_paybill, sarah_cash, bank_stmt, selected_date))
        else:
            cur.execute("""
                INSERT INTO daily_records (
                    record_date, john_am_litres, john_pm_litres,
                    sales_am_litres, sales_am_amount,
                    sales_pm_litres, sales_pm_amount,
                    otc_paybill, sarah_cash_deposit, bank_statement
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (selected_date, john_am, john_pm,
                  sales_am_litres, sales_am_amount,
                  sales_pm_litres, sales_pm_amount,
                  otc_paybill, sarah_cash, bank_stmt))

        mysql.connection.commit()
        cur.close()
        flash('Record saved.', 'success')
        return redirect(url_for('dashboard', date=selected_date.isoformat()))

    # ===== GET: Load Record =====
    cur.execute("SELECT * FROM daily_records WHERE record_date = %s", (selected_date,))
    record = cur.fetchone()

    # Get farmer deliveries
    cur.execute("""
        SELECT fd.*, f.member_no, f.name
        FROM farmer_deliveries fd
        JOIN farmers f ON fd.farmer_id = f.id
        WHERE fd.record_date = %s
        ORDER BY f.member_no
    """, (selected_date,))
    deliveries = cur.fetchall()

    # Get all farmers for search
    cur.execute("SELECT id, member_no, name FROM farmers ORDER BY member_no")
    farmers = cur.fetchall()
    cur.close()

    # ---- Calculate totals ----
    if record:
        farmer_total = sum(d['litres'] for d in deliveries)
        john_total = (record['john_am_litres'] or 0) + (record['john_pm_litres'] or 0)
        total_milk_in = john_total + farmer_total
        total_sold = (record['sales_am_litres'] or 0) + (record['sales_pm_litres'] or 0)
        total_revenue = (record['sales_am_amount'] or 0) + (record['sales_pm_amount'] or 0)
        reported_deposits = (record['otc_paybill'] or 0) + (record['sarah_cash_deposit'] or 0)
        money_not_deposited = total_revenue - reported_deposits
        milk_left = total_milk_in - total_sold
        bank_stmt = record['bank_statement'] or 0
        deposit_discrepancy = bank_stmt - reported_deposits if bank_stmt else None
    else:
        farmer_total = 0
        john_total = 0
        total_milk_in = 0
        total_sold = 0
        total_revenue = 0
        reported_deposits = 0
        money_not_deposited = 0
        milk_left = 0
        bank_stmt = 0
        deposit_discrepancy = None

    return render_template('dashboard.html',
                           date=selected_date,
                           record=record,
                           deliveries=deliveries,
                           farmers=farmers,
                           farmer_total=farmer_total,
                           john_total=john_total,
                           total_milk_in=total_milk_in,
                           total_sold=total_sold,
                           total_revenue=total_revenue,
                           reported_deposits=reported_deposits,
                           money_not_deposited=money_not_deposited,
                           milk_left=milk_left,
                           bank_stmt=bank_stmt,
                           deposit_discrepancy=deposit_discrepancy,
                           timedelta=timedelta)

# ---------- Manage Farmers (List + Manual Add) ----------
@app.route('/farmers', methods=['GET', 'POST'])
@login_required
def manage_farmers():
    if current_user.role != 'admin':
        flash('Admin access only.', 'danger')
        return redirect(url_for('dashboard'))

    # Handle manual add (optional – you can skip this if you only want import)
    if request.method == 'POST' and 'add_farmer' in request.form:
        member_no = request.form.get('member_no')
        name = request.form.get('name')
        rider = request.form.get('rider', 'B')
        if member_no and name:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO farmers (member_no, name, rider) VALUES (%s, %s, %s)",
                        (member_no, name, rider))
            mysql.connection.commit()
            cur.close()
            flash('Farmer added manually.', 'success')
        else:
            flash('Member No and Name are required.', 'warning')
        return redirect(url_for('manage_farmers'))

    # Get all farmers
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM farmers ORDER BY member_no")
    farmers = cur.fetchall()
    cur.close()

    return render_template('farmers_list.html', farmers=farmers)

@app.route('/add_farmer_delivery', methods=['POST'])
@login_required
def add_farmer_delivery():
    if current_user.role not in ['admin', 'agent']:
        flash('Not allowed.', 'danger')
        return redirect(url_for('dashboard'))

    date_str = request.form.get('date')
    farmer_id = request.form.get('farmer_id')
    litres = float(request.form.get('litres', 0) or 0)

    if not date_str or not farmer_id or litres <= 0:
        flash('Please fill all fields.', 'warning')
        return redirect(url_for('dashboard', date=date_str))

    cur = mysql.connection.cursor()

    # --- Ensure daily record exists for this date ---
    cur.execute("SELECT id FROM daily_records WHERE record_date = %s", (date_str,))
    if not cur.fetchone():
        # Create a blank record (all columns default to 0)
        cur.execute("INSERT INTO daily_records (record_date) VALUES (%s)", (date_str,))
        mysql.connection.commit()
        flash('Note: A blank daily record was created for this date.', 'info')

    # Now insert the farmer delivery
    cur.execute("INSERT INTO farmer_deliveries (record_date, farmer_id, litres) VALUES (%s, %s, %s)",
                (date_str, farmer_id, litres))
    mysql.connection.commit()
    cur.close()
    flash('Farmer delivery added.', 'success')
    return redirect(url_for('dashboard', date=date_str))

# ---------- Delete Farmer Delivery ----------
@app.route('/delete_farmer_delivery/<int:delivery_id>')
@login_required
def delete_farmer_delivery(delivery_id):
    if current_user.role not in ['admin', 'agent']:
        flash('Not allowed.', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT record_date FROM farmer_deliveries WHERE id = %s", (delivery_id,))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM farmer_deliveries WHERE id = %s", (delivery_id,))
        mysql.connection.commit()
        flash('Delivery removed.', 'info')
        date_str = row['record_date'].isoformat()
    else:
        date_str = date.today().isoformat()
    cur.close()
    return redirect(url_for('dashboard', date=date_str))

@app.route('/import_farmers', methods=['GET', 'POST'])
@login_required
def import_farmers():
    if current_user.role != 'admin':
        flash('Admin access only.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Please select a file.', 'warning')
            return redirect(url_for('import_farmers'))

        if not file.filename.lower().endswith('.xlsx'):
            flash('Please upload an Excel (.xlsx) file.', 'danger')
            return redirect(url_for('import_farmers'))

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
        except Exception as e:
            flash(f'Error reading file: {e}', 'danger')
            return redirect(url_for('import_farmers'))

        # Find header row – store the row number
        header_row = None
        header_row_num = None
        for row_num, row in enumerate(ws.iter_rows(min_row=1, max_row=5, values_only=True), start=1):
            if row and any(cell and ('member' in str(cell).lower() or 'name' in str(cell).lower()) for cell in row):
                header_row = row
                header_row_num = row_num
                break

        if not header_row:
            flash('Could not find header row with "member_no" and "name".', 'danger')
            return redirect(url_for('import_farmers'))

        # Map columns
        col_map = {}
        for idx, col in enumerate(header_row):
            col_lower = str(col).lower().strip()
            if col_lower in ['member_no', 'memberno', 'member no', 'member number']:
                col_map['member_no'] = idx
            elif col_lower in ['name', 'fullname', 'farmer name']:
                col_map['name'] = idx
            elif col_lower in ['rider']:
                col_map['rider'] = idx

        if 'member_no' not in col_map or 'name' not in col_map:
            flash('Excel must have "member_no" and "name" columns.', 'danger')
            return redirect(url_for('import_farmers'))

        added = 0
        skipped = 0
        cur = mysql.connection.cursor()

        # Iterate from the row after the header
        for row in ws.iter_rows(min_row=header_row_num + 1, values_only=True):
            member_no = str(row[col_map['member_no']]).strip() if row[col_map['member_no']] else ''
            name = str(row[col_map['name']]).strip() if row[col_map['name']] else ''
            rider = str(row[col_map.get('rider')]).strip() if (col_map.get('rider') is not None and row[col_map['rider']]) else 'B'
            if not member_no:
                continue
            cur.execute("SELECT id FROM farmers WHERE member_no = %s", (member_no,))
            if cur.fetchone():
                skipped += 1
                continue
            cur.execute("INSERT INTO farmers (member_no, name, rider) VALUES (%s, %s, %s)", (member_no, name, rider))
            added += 1

        mysql.connection.commit()
        cur.close()
        flash(f'Imported {added} farmers. Skipped {skipped} duplicates.', 'success')
        return redirect(url_for('manage_farmers'))  # redirect to farmers list

    return render_template('import_farmers.html')

# ---------- Reports ----------
@app.route('/reports')
@login_required
def reports():
    month_str = request.args.get('month', date.today().strftime('%Y-%m'))
    try:
        year, month = map(int, month_str.split('-'))
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year+1, 1, 1)
        else:
            end_date = date(year, month+1, 1)
    except:
        flash('Invalid month format.', 'danger')
        return redirect(url_for('reports'))

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM daily_records
        WHERE record_date >= %s AND record_date < %s
        ORDER BY record_date DESC
    """, (start_date, end_date))
    records = cur.fetchall()

    processed = []
    for rec in records:
        cur.execute("SELECT SUM(litres) as total FROM farmer_deliveries WHERE record_date = %s", (rec['record_date'],))
        farmer_sum = cur.fetchone()['total'] or 0
        john_total = (rec['john_am_litres'] or 0) + (rec['john_pm_litres'] or 0)
        total_milk_in = john_total + farmer_sum
        total_sold = (rec['sales_am_litres'] or 0) + (rec['sales_pm_litres'] or 0)
        revenue = (rec['sales_am_amount'] or 0) + (rec['sales_pm_amount'] or 0)
        reported_deposits = (rec['otc_paybill'] or 0) + (rec['sarah_cash_deposit'] or 0)
        milk_left = total_milk_in - total_sold
        processed.append({
            'date': rec['record_date'],
            'milk_left': milk_left,
            'total_sold': total_sold,
            'revenue': revenue,
            'reported_deposits': reported_deposits,
            'bank_statement': rec['bank_statement'] or 0,
            'not_deposited': revenue - reported_deposits,
            'discrepancy': (rec['bank_statement'] or 0) - reported_deposits if rec['bank_statement'] else None
        })
    cur.close()

    return render_template('reports.html', records=processed, month=month_str)

# ---------- Init ----------
with app.app_context():
    init_users()

if __name__ == '__main__':
    app.run(debug=True)