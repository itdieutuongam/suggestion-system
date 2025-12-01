# app.py - HỆ THỐNG ĐỀ NGHỊ THANH TOÁN - DUYỆT 2 CẤP HOÀN HẢO
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from functools import wraps
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "DTA_SPACE_2025_FINAL_SECRET_KEY"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_NAME = "payment_requests.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT,
            department TEXT,
            city TEXT,
            content TEXT,
            approver TEXT NOT NULL,
            submitter TEXT NOT NULL,
            submitter_name TEXT NOT NULL,
            submit_date TEXT NOT NULL,
            status TEXT DEFAULT 'Chờ duyệt',
            attachment TEXT,
            total_cost REAL DEFAULT 0,
            next_approver TEXT
        )
    ''')
    for col in ["total_cost REAL DEFAULT 0", "next_approver TEXT"]:
        try:
            col_name = col.split()[0]
            c.execute(f"ALTER TABLE payment_requests ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

# === DANH SÁCH NGƯỜI DÙNG (giữ nguyên) ===
# === NGƯỜI DÙNG ===
USERS = {
    # ==================== BOD ====================
    "truongkhuong@dieutuongam.com": {"name": "TRƯƠNG HUỆ KHƯƠNG",           "role": "BOD",       "department": "BOD",                                   "password": "123456"},
     "hongtuyet@dieutuongam.com": {"name": "NGUYỄN THỊ HỒNG TUYẾT", "role": "BOD", "department": "BOD", "password": "123456"},

    # ==================== PHÒNG HCNS-IT ====================
    "it@dieutuongam.com":           {"name": "TRẦN CÔNG KHÁNH",             "role": "Manager",   "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "anthanh@dieutuongam.com":      {"name": "NGUYỄN THỊ AN THANH",         "role": "Manager",   "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "hcns@dieutuongam.com":         {"name": "NHÂN SỰ DTA",                 "role": "Employee",  "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "yennhi@dieutuongam.com":       {"name": "TRẦN NGỌC YẾN NHI",           "role": "Employee",  "department": "PHÒNG HCNS-IT",                         "password": "123456"},
    "info@dieutuongam.com":         {"name": "Trung Tâm Nghệ Thuật Phật Giáo Diệu Tướng Am", "role": "Employee", "department": "PHÒNG HCNS-IT",              "password": "123456"},

    # ==================== PHÒNG TÀI CHÍNH KẾ TOÁN ====================
    "ketoan@dieutuongam.com":       {"name": "LÊ THỊ MAI ANH",              "role": "Manager",   "department": "PHÒNG TÀI CHÍNH KẾ TOÁN",                "password": "123456"},

    # ==================== PHÒNG KINH DOANH HCM ====================
    "xuanhoa@dieutuongam.com":      {"name": "LÊ XUÂN HOA",                 "role": "Manager",   "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "salesadmin@dieutuongam.com":   {"name": "NGUYỄN DUY ANH",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "kho@dieutuongam.com":          {"name": "HUỲNH MINH TOÀN",             "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thoainha@dieutuongam.com":     {"name": "TRẦN THOẠI NHÃ",              "role": "Manager",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thanhtuan.dta@gmail.com":      {"name": "BÀNH THANH TUẤN",             "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thientinh.dta@gmail.com":      {"name": "BÙI THIỆN TÌNH",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "giathanh.dta@gmail.com":       {"name": "NGÔ GIA THÀNH",               "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "vannhuann.dta@gmail.com":      {"name": "PHẠM VĂN NHUẬN",              "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "minhhieuu.dta@gmail.com":      {"name": "LÊ MINH HIẾU",                "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thanhtrung.dta@gmail.com":     {"name": "NGUYỄN THÀNH TRUNG",          "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "khanhngan.dta@gmail.com":      {"name": "NGUYỄN NGỌC KHÁNH NGÂN",      "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thitrang.dta@gmail.com":       {"name": "NGUYỄN THỊ TRANG",            "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},
    "thanhtienn.dta@gmail.com":     {"name": "NGUYỄN THANH TIẾN",           "role": "Employee",  "department": "PHÒNG KINH DOANH HCM",                  "password": "123456"},

    # ==================== PHÒNG KINH DOANH HN ====================
    "nguyenngoc@dieutuongam.com":   {"name": "NGUYỄN THỊ NGỌC",             "role": "Manager",   "department": "PHÒNG KINH DOANH HN",                   "password": "123456"},
    "vuthuy@dieutuongam.com":       {"name": "VŨ THỊ THÙY",                 "role": "Manager",  "department": "PHÒNG KINH DOANH HN",                   "password": "123456"},
    "mydung.dta@gmail.com":         {"name": "HOÀNG THỊ MỸ DUNG",           "role": "Employee",  "department": "PHÒNG KINH DOANH HN",                   "password": "123456"},

    # ==================== PHÒNG TRUYỀN THÔNG & MARKETING ====================
    "marketing@dieutuongam.com":    {"name": "HUỲNH THỊ BÍCH TUYỀN",                 "role": "Manager",   "department": "PHÒNG TRUYỀN THÔNG & MARKETING",         "password": "123456"},
    "lehong.dta@gmail.com":         {"name": "LÊ THỊ HỒNG",                 "role": "Employee",  "department": "PHÒNG TRUYỀN THÔNG & MARKETING",         "password": "123456"},
    # ==================== PHÒNG KẾ HOẠCH TỔNG HỢP ====================
    "lehuyen@dieutuongam.com":      {"name": "NGUYỄN THỊ LỆ HUYỀN",         "role": "Manager",   "department": "PHÒNG KẾ HOẠCH TỔNG HỢP",               "password": "123456"},
    "hatrang@dieutuongam.com": {"name": "PHẠM HÀ TRANG", "role": "Manager", "department": "PHÒNG KẾ HOẠCH TỔNG HỢP", "password": "123456"},

    # ==================== PHÒNG SÁNG TẠO TỔNG HỢP ====================
    "thietke@dieutuongam.com":      {"name": "ĐẶNG THỊ MINH THÙY",          "role": "Manager",   "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "ptsp@dieutuongam.com":         {"name": "DƯƠNG NGỌC HIỂU",             "role": "Manager",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "qlda@dieutuongam.com":         {"name": "PHẠM THẾ HẢI",                "role": "Manager",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "minhdat.dta@gmail.com":        {"name": "LÂM MINH ĐẠT",                "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "thanhvii.dat@gmail.com":       {"name": "LÊ THỊ THANH VI",             "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "quangloi.dta@gmail.com":       {"name": "LÊ QUANG LỢI",                "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},
    "tranlinh.dta@gmail.com":       {"name": "NGUYỄN THỊ PHƯƠNG LINH",      "role": "Employee",  "department": "PHÒNG SÁNG TẠO TỔNG HỢP",                "password": "123456"},

    # ==================== BỘ PHẬN HỖ TRỢ - GIAO NHẬN ====================
    "hotro1.dta@gmail.com":         {"name": "NGUYỄN VĂN MẠNH",             "role": "Employee",  "department": "BỘ PHẬN HỖ TRỢ - GIAO NHẬN",              "password": "123456"},
}

DEPARTMENTS = ["PHÒNG HCNS-IT", "PHÒNG KINH DOANH HCM", "PHÒNG KINH DOANH HN",
               "PHÒNG TRUYỀN THÔNG & MARKETING", "PHÒNG TÀI CHÍNH KẾ TOÁN",
               "PHÒNG KẾ HOẠCH TỔNG HỢP", "PHÒNG SÁNG TẠO TỔNG HỢP", "BOD"]

# Login required decorator (giữ nguyên)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email in USERS and USERS[email]["password"] == password:
            session["user"] = {
                "email": email,
                "name": USERS[email]["name"],
                "role": USERS[email]["role"],
                "department": USERS[email]["department"]
            }
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("dashboard"))
        flash("Email hoặc mật khẩu sai!", "danger")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    my_name = f"{user['name']} - {user['department']}"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT * FROM payment_requests 
        WHERE (approver = ? OR next_approver = ?) 
        AND status IN ('Chờ duyệt', 'Chờ duyệt cấp 2')
        ORDER BY id DESC
    """, (my_name, my_name))
    pending = c.fetchall()
    conn.close()
    return render_template("dashboard.html", user=user, pending=pending)

@app.route("/request", methods=["GET", "POST"])
@login_required
def request_payment():
    user = session["user"]
    if user["email"] == "truongkhuong@dieutuongam.com":
        flash("Tài khoản BOD không được phép tạo đề nghị thanh toán mới.", "warning")
        return redirect(url_for("dashboard"))
    
    today = datetime.now().strftime("%d/%m/%Y")

    if request.method == "POST":
        title = request.form.get("title")
        dept = request.form.get("department")
        city = request.form.get("city")
        ptype = request.form.get("type")
        content = request.form.get("content")
        approver = request.form.get("approver")
        total_cost = float(request.form.get("total_cost", 0))
        file = request.files.get("attachment")

        if not all([title, dept, ptype, content, approver]):
            flash("Vui lòng điền đầy đủ các trường bắt buộc!", "danger")
            return redirect(url_for("request_payment"))

        filename = None
        if file and file.filename:
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO payment_requests 
            (title, type, department, city, content, approver, 
             submitter, submitter_name, submit_date, total_cost, attachment, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Chờ duyệt')
        ''', (title, ptype, dept, city, content, approver,
              user["email"], user["name"], today, total_cost, filename))
        conn.commit()
        conn.close()
        flash(f"Đề nghị thanh toán '{title}' đã được gửi thành công!", "success")
        return redirect(url_for("request_payment"))

    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
    return render_template("request.html", user=user, approvers=approvers, today=today,departments=DEPARTMENTS)

@app.route("/list")
@login_required
def payment_list():
    user = session["user"]
    if user["role"] not in ["Manager", "BOD"]:
        flash("Bạn không có quyền xem trang này!", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM payment_requests ORDER BY id DESC")
    requests = c.fetchall()
    conn.close()
    return render_template("payment_list.html", user=user, requests=requests)

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/approve/<int:req_id>", methods=["GET", "POST"])
@login_required
def approve(req_id):
    # Logic duyệt giữ nguyên 100%, chỉ đổi tên biến và thông báo
    user = session["user"]
    if user["role"] not in ["Manager", "BOD"]:
        flash("Bạn không có quyền duyệt!", "danger")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM payment_requests WHERE id = ?", (req_id,))
    req = c.fetchone()
    if not req:
        flash("Đề nghị không tồn tại!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    my_full = f"{user['name']} - {user['department']}"
    original_approver = req[6]      # approver
    next_approver = req[13] if len(req) > 13 else None
    status = req[10]

    current_turn = next_approver if next_approver else original_approver
    if current_turn != my_full:
        flash("Chưa đến lượt bạn duyệt đề nghị này!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        decision = request.form.get("decision")
        next_person = request.form.get("next_approver")

        if decision == "reject":
            c.execute("UPDATE payment_requests SET status = 'Từ chối', next_approver = NULL WHERE id = ?", (req_id,))
            conn.commit()
            flash(f"Đề nghị thanh toán #{req_id} đã bị TỪ CHỐI!", "danger")

        elif decision == "approve":
            if user["role"] == "BOD":
                c.execute("UPDATE payment_requests SET status = 'Đã duyệt', next_approver = NULL WHERE id = ?", (req_id,))
                conn.commit()
                flash(f"BOD đã DUYỆT HOÀN TẤT đề nghị thanh toán #{req_id}!", "success")
            else:
                if next_person:
                    selected_name = next_person.split(" - ")[0].strip()
                    is_bod_next = any(info["name"] == selected_name and info["role"] == "BOD" for info in USERS.values())
                    c.execute("UPDATE payment_requests SET next_approver = ? WHERE id = ?", (next_person, req_id))
                    conn.commit()
                    if is_bod_next:
                        flash(f"Đã duyệt → Chuyển cho BOD: {selected_name} → Đây sẽ là người duyệt cuối cùng", "success")
                    else:
                        flash(f"Đã duyệt → Chuyển tiếp cho: {selected_name}", "success")
                else:
                    flash("Vui lòng chọn người phê duyệt tiếp theo!", "warning")
                    conn.close()
                    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
                    return render_template("approve_form.html", request=req, approvers=approvers, is_bod=(user["role"] == "BOD"))

        conn.close()
        return redirect(url_for("dashboard"))

    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
    conn.close()
    return render_template("approve_form.html", request=req, approvers=approvers, is_bod=(user["role"] == "BOD"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất thành công!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    print("="*70)
    print("HỆ THỐNG ĐỀ NGHỊ THANH TOÁN ĐÃ CHẠY THÀNH CÔNG!")
    print("→ Truy cập: http://192.168.1.130:5000")
    print("="*70)
    app.run(host="0.0.0.0", port=5000, debug=False)