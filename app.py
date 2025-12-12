# app.py - DTA SPACE 2025 - PHIÊN BẢN HOÀN HẢO 100% - ĐÃ SỬA LỖI CHUYỂN CẤP DUYỆT
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from functools import wraps
from datetime import datetime
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "DTA_SPACE_2025_FINAL_SECURE_KEY_999"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = "payment_list.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            must_change_password INTEGER DEFAULT 1
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT,
            department TEXT,
            city TEXT,
            content TEXT,
            current_approver TEXT NOT NULL,
            submitter TEXT NOT NULL,
            submitter_name TEXT NOT NULL,
            submit_date TEXT NOT NULL,
            status TEXT DEFAULT 'Chờ duyệt',
            attachment TEXT,
            total_cost REAL DEFAULT 0,
            history TEXT DEFAULT ''
        )
    ''')

# Danh sách người dùng mặc định (email, tên, mật khẩu mặc định, role, phòng ban)
    defaults = [
    # ==================== BOD ====================
    ("truongkhuong@dieutuongam.com", "TRƯƠNG HUỆ KHƯƠNG",          "123456", "BOD",      "BOD"),
    ("hongtuyet@dieutuongam.com",    "NGUYỄN THỊ HỒNG TUYẾT",      "123456", "BOD",      "BOD"),

    # ==================== PHÒNG HCNS-IT ====================
    ("it@dieutuongam.com",           "TRẦN CÔNG KHÁNH",            "123456", "Employee",  "PHÒNG HCNS-IT"),
    ("haphung.dta@gmail.com",           "PHÙNG THỊ THU HÀ",            "123456", "Employee",  "PHÒNG HCNS-IT"),
    ("anthanh@dieutuongam.com",      "NGUYỄN THỊ AN THANH",        "123456", "Manager",  "PHÒNG HCNS-IT"),
    ("hcns@dieutuongam.com",         "NHÂN SỰ DTA",                "123456", "Employee", "PHÒNG HCNS-IT"),
    ("yennhi@dieutuongam.com",       "TRẦN NGỌC YẾN NHI",          "123456", "Employee", "PHÒNG HCNS-IT"),
    ("info@dieutuongam.com",         "Trung Tâm Nghệ Thuật Phật Giáo Diệu Tướng Am", "123456", "Employee", "PHÒNG HCNS-IT"),

    # ==================== PHÒNG TÀI CHÍNH KẾ TOÁN ====================
    ("ketoan@dieutuongam.com",       "LÊ THỊ MAI ANH",             "123456", "Manager",  "PHÒNG TÀI CHÍNH KẾ TOÁN"),

    # ==================== PHÒNG KINH DOANH HCM ====================
    ("xuanhoa@dieutuongam.com",      "LÊ XUÂN HOA",                "123456", "Manager",  "PHÒNG KINH DOANH HCM"),
    ("salesadmin@dieutuongam.com",   "NGUYỄN DUY ANH",             "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("kho@dieutuongam.com",          "HUỲNH MINH TOÀN",            "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("thoainha@dieutuongam.com",     "TRẦN THOẠI NHÃ",             "123456", "Manager",  "PHÒNG KINH DOANH HCM"),
    ("thanhtuan.dta@gmail.com",      "BÀNH THANH TUẤN",            "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("thientinh.dta@gmail.com",      "BÙI THIỆN TÌNH",             "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("giathanh.dta@gmail.com",       "NGÔ GIA THÀNH",              "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("vannhuann.dta@gmail.com",      "PHẠM VĂN NHUẬN",             "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("minhhieuu.dta@gmail.com",      "LÊ MINH HIẾU",               "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("thanhtrung.dta@gmail.com",     "NGUYỄN THÀNH TRUNG",         "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("khanhngan.dta@gmail.com",      "NGUYỄN NGỌC KHÁNH NGÂN",    "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("thitrang.dta@gmail.com",       "NGUYỄN THỊ TRANG",           "123456", "Employee", "PHÒNG KINH DOANH HCM"),
    ("thanhtienn.dta@gmail.com",     "NGUYỄN THANH TIẾN",          "123456", "Employee", "PHÒNG KINH DOANH HCM"),

    # ==================== PHÒNG KINH DOANH HN ====================
    ("nguyenngoc@dieutuongam.com",   "NGUYỄN THỊ NGỌC",            "123456", "Manager",  "PHÒNG KINH DOANH HN"),
    ("vuthuy@dieutuongam.com",       "VŨ THỊ THÙY",                "123456", "Manager",  "PHÒNG KINH DOANH HN"),
    ("mydung.dta@gmail.com",         "HOÀNG THỊ MỸ DUNG",          "123456", "Employee", "PHÒNG KINH DOANH HN"),

    # ==================== PHÒNG TRUYỀN THÔNG & MARKETING ====================
    ("marketing@dieutuongam.com",    "HUỲNH THỊ BÍCH TUYỀN",       "123456", "Manager",  "PHÒNG TRUYỀN THÔNG & MARKETING"),
    ("lehong.dta@gmail.com",         "LÊ THỊ HỒNG",                "123456", "Employee", "PHÒNG TRUYỀN THÔNG & MARKETING"),

    # ==================== PHÒNG KẾ HOẠCH TỔNG HỢP ====================
    ("lehuyen@dieutuongam.com",      "NGUYỄN THỊ LỆ HUYỀN",        "123456", "Manager",  "PHÒNG KẾ HOẠCH TỔNG HỢP"),
    ("hatrang@dieutuongam.com",      "PHẠM HÀ TRANG",              "123456", "Manager",  "PHÒNG KẾ HOẠCH TỔNG HỢP"),

    # ==================== PHÒNG SÁNG TẠO TỔNG HỢP ====================
    ("thietke@dieutuongam.com",      "ĐẶNG THỊ MINH THÙY",         "123456", "Manager",  "PHÒNG SÁNG TẠO TỔNG HỢP"),
    ("ptsp@dieutuongam.com",         "DƯƠNG NGỌC HIỂU",            "123456", "Manager",  "PHÒNG SÁNG TẠO TỔNG HỢP"),
    ("qlda@dieutuongam.com",         "PHẠM THẾ HẢI",               "123456", "Manager",  "PHÒNG SÁNG TẠO TỔNG HỢP"),
    ("minhdat.dta@gmail.com",        "LÂM MINH ĐẠT",               "123456", "Employee", "PHÒNG SÁNG TẠO TỔNG HỢP"),
    ("thanhvii.dat@gmail.com",       "LÊ THỊ THANH VI",            "123456", "Employee", "PHÒNG SÁNG TẠO TỔNG HỢP"),
    ("quangloi.dta@gmail.com",       "LÊ QUANG LỢI",               "123456", "Employee", "PHÒNG SÁNG TẠO TỔNG HỢP"),
    ("tranlinh.dta@gmail.com",       "NGUYỄN THỊ PHƯƠNG LINH",     "123456", "Employee", "PHÒNG SÁNG TẠO TỔNG HỢP"),

    # ==================== BỘ PHẬN HỖ TRỢ - GIAO NHẬN ====================
    ("hotro1.dta@gmail.com",         "NGUYỄN VĂN MẠNH",            "123456", "Employee", "BỘ PHẬN HỖ TRỢ - GIAO NHẬN"),
    ]
    for email, name, pwd, role, dept in defaults:
        hashed = generate_password_hash(pwd)
        c.execute("INSERT OR IGNORE INTO users (email, name, password_hash, role, department, must_change_password) VALUES (?, ?, ?, ?, ?, 1)",
                  (email.lower(), name, hashed, role, dept))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        if session["user"].get("must_change_password"):
            if request.endpoint not in ["change_password", "logout", "static"]:
                return redirect(url_for("change_password"))
        return f(*args, **kwargs)
    return wrap

def get_approvers():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name, department FROM users WHERE role IN ('Manager', 'BOD') ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [f"{row['name']} - {row['department']}" for row in rows]

# Hàm lấy phòng ban từ tên (dùng trong template)
def get_department_from_name(name):
    if not name:
        return ""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT department FROM users WHERE name = ?", (name.strip(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "Không xác định"

app.jinja_env.globals['get_dept'] = get_department_from_name

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = {
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "department": user["department"],
                "must_change_password": bool(user["must_change_password"])
            }
            if user["must_change_password"]:
                return redirect(url_for("change_password"))
            return redirect(url_for("dashboard"))
        flash("Email hoặc mật khẩu sai!", "danger")
    return render_template("login.html")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]
        if new != confirm:
            flash("Mật khẩu mới không khớp!", "danger")
        elif len(new) < 6:
            flash("Mật khẩu phải ít nhất 6 ký tự!", "danger")
        else:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE email = ?", (session["user"]["email"],))
            user = c.fetchone()
            if not check_password_hash(user[0], old):
                flash("Mật khẩu cũ không đúng!", "danger")
            else:
                new_hash = generate_password_hash(new)
                c.execute("UPDATE users SET password_hash = ?, must_change_password = 0 WHERE email = ?",
                          (new_hash, session["user"]["email"]))
                conn.commit()
                conn.close()
                session["user"]["must_change_password"] = False
                flash("Đổi mật khẩu thành công!", "success")
                return redirect(url_for("dashboard"))
    return render_template("change_password.html", user=session["user"])

@app.route("/dashboard")
@login_required
def dashboard():
    my_full = f"{session['user']['name']} - {session['user']['department']}"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM proposals WHERE current_approver = ? AND status NOT IN ('Đã duyệt', 'Từ chối') ORDER BY id DESC", (my_full,))
    pending = c.fetchall()
    conn.close()
    return render_template("dashboard.html", user=session["user"], pending=pending)

@app.route("/request", methods=["GET", "POST"])
@login_required
def request_payment():
    if session["user"]["email"] == "truongkhuong@dieutuongam.com":
        flash("BOD không được tạo đề nghị thanh toán", "warning")
        return redirect(url_for("dashboard"))

    today = datetime.now()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT department FROM users ORDER BY department")
    departments = [row[0] for row in c.fetchall()]
    conn.close()

    if request.method == "POST":
        title = request.form["title"]
        payment_type = request.form["type"]
        department = request.form["department"]
        city = request.form["city"]
        content = request.form["content"]
        total_cost = float(request.form.get("total_cost", 0) or 0)
        selected_approver = request.form.get("approver")

        if not selected_approver:
            flash("Vui lòng chọn người duyệt đầu tiên!", "danger")
            return redirect(url_for("request_payment"))

        attachment = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                attachment = filename

        submit_date = today.strftime("%d/%m/%Y")
        first_approver_name = selected_approver.split(" - ")[0]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO proposals 
            (title, type, department, city, content, current_approver, submitter, submitter_name, 
             submit_date, attachment, total_cost, history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, payment_type, department, city, content, selected_approver,
              session["user"]["email"], session["user"]["name"], submit_date, attachment, total_cost,
              first_approver_name))

        conn.commit()
        conn.close()
        flash(f"Đã gửi đề nghị thành công! Đang chờ: {first_approver_name} duyệt", "success")
        return redirect(url_for("dashboard"))

    return render_template("request.html", user=session["user"], approvers=get_approvers(), today=today, departments=departments)

# ================== ĐOẠN QUAN TRỌNG NHẤT - ĐÃ SỬA HOÀN HẢO ==================
@app.route("/approve/<int:prop_id>", methods=["GET", "POST"])
@login_required
def approve(prop_id):
    my_full = f"{session['user']['name']} - {session['user']['department']}"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM proposals WHERE id = ?", (prop_id,))
    p = c.fetchone()

    if not p:
        flash("Đề nghị không tồn tại!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if p[6] != my_full:
        flash("Không phải lượt bạn duyệt!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        decision = request.form["decision"]
        current_history = p[13] or ""

        if decision == "reject":
            c.execute("UPDATE proposals SET status = 'Từ chối' WHERE id = ?", (prop_id,))
            conn.commit()
            flash("Đã từ chối đề nghị!", "danger")

        else:  # approve
            if session["user"]["role"] == "BOD":
                c.execute("UPDATE proposals SET status = 'Đã duyệt' WHERE id = ?", (prop_id,))
                conn.commit()
                flash("BOD đã duyệt hoàn tất! Đề nghị được thanh toán ngay.", "success")
            else:
                next_person_full = request.form.get("next_approver")
                if not next_person_full:
                    flash("Vui lòng chọn người duyệt tiếp theo!", "warning")
                    conn.close()
                    return redirect(url_for("approve", prop_id=prop_id))

                next_person_name = next_person_full.split(" - ")[0]

                # Cập nhật lịch sử (chỉ lưu tên)
                new_history = (current_history + " → " + next_person_name) if current_history else next_person_name

                # QUAN TRỌNG: current_approver phải là chuỗi đầy đủ "Tên - Phòng ban"
                c.execute("""UPDATE proposals 
                             SET current_approver = ?, 
                                 history = ? 
                             WHERE id = ?""",
                          (next_person_full, new_history, prop_id))
                conn.commit()
                flash(f"Đã duyệt & chuyển cho: {next_person_name} duyệt tiếp", "success")
        conn.close()
        return redirect(url_for("dashboard"))

    is_bod = session["user"]["role"] == "BOD"
    conn.close()
    return render_template("approve_form.html", request=p, approvers=get_approvers(), is_bod=is_bod)

@app.route("/list")
@login_required
def payment_list():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM proposals ORDER BY id DESC")
    proposals = c.fetchall()
    conn.close()
    return render_template("payment_list.html", user=session["user"], requests=proposals)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/logout")
def logout():
    session.clear()
    flash("Đăng xuất thành công!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    print("="*80)
    print("DTA SPACE 2025 - ĐÃ SỬA XONG LỖI CHUYỂN CẤP DUYỆT - HOẠT ĐỘNG HOÀN HẢO")
    print("Truy cập: http://127.0.0.1:5000")
    print("="*80)
    app.run(host="0.0.0.0", port=5000, debug=False)