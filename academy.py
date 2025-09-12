# academy.py
import streamlit as st
import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

# ---------------------------
# Config & constants
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", initial_sidebar_state="collapsed")
DB_FILE = "academy.db"
UPLOAD_DIR = "uploads"
BANNERS_DIR = os.path.join(UPLOAD_DIR, "banners")
LESSON_DIR = os.path.join(UPLOAD_DIR, "lessons")
PROFILE_DIR = os.path.join(UPLOAD_DIR, "profiles")
CERT_DIR = "certificates"
ADMIN_DEFAULT_PASSWORD = "admin123"  # change in production

for d in (UPLOAD_DIR, BANNERS_DIR, LESSON_DIR, PROFILE_DIR, CERT_DIR):
    os.makedirs(d, exist_ok=True)

# ---------------------------
# Database helpers
# ---------------------------
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    # students
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        profile_pic TEXT,
        sex TEXT,
        profession TEXT,
        institution TEXT,
        mobile TEXT,
        created_on TEXT
    )""")
    # admin table
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        admin_id INTEGER PRIMARY KEY,
        password TEXT NOT NULL
    )""")
    # courses
    c.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subtitle TEXT,
        description TEXT,
        price REAL DEFAULT 0,
        category TEXT,
        banner_path TEXT,
        created_on TEXT
    )""")
    # lessons
    c.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT,
        lesson_type TEXT,
        content_path TEXT,
        duration_seconds INTEGER DEFAULT 0,
        "order" INTEGER DEFAULT 0,
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )""")
    # enrollments
    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        paid INTEGER DEFAULT 0,
        enrolled_on TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )""")
    # progress
    c.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        lesson_id INTEGER,
        completed INTEGER DEFAULT 0,
        completed_on TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id)
    )""")
    # certificates
    c.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
        cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        cert_file TEXT,
        generated_on TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )""")
    # password reset tokens (simulation)
    c.execute("""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        token TEXT PRIMARY KEY,
        student_id INTEGER,
        created_on TEXT,
        used INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )""")
    # ensure admin row exists (store hashed password)
    c.execute("SELECT COUNT(*) FROM admin")
    if c.fetchone()[0] == 0:
        hashed = hashlib.sha256(ADMIN_DEFAULT_PASSWORD.encode()).hexdigest()
        c.execute("INSERT INTO admin (admin_id, password) VALUES (?,?)", (1, hashed))
    conn.commit()
    conn.close()

create_tables()

# ---------------------------
# Utility functions
# ---------------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_pw(pw: str, hashed: str) -> bool:
    return hash_pw(pw) == hashed

def inr(amount):
    try:
        return f"₹{float(amount):,.2f}"
    except:
        return f"₹{amount}"

def save_upload(uploaded, folder):
    if uploaded is None:
        return None
    os.makedirs(folder, exist_ok=True)
    name = f"{secrets.token_hex(8)}_{uploaded.name}"
    path = os.path.join(folder, name)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path

def generate_certificate_text(student_name, course_title, student_id, course_id):
    ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    fname = f"EinTrust_{student_name.replace(' ','_')}_{course_title.replace(' ','_')}_{ts}.txt"
    path = os.path.join(CERT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("EinTrust Academy\n")
        f.write("Certificate of Completion\n\n")
        f.write(f"This certifies that {student_name}\n")
        f.write(f"has successfully completed the course: {course_title}\n")
        f.write(f"Date (UTC): {datetime.utcnow().strftime('%Y-%m-%d')}\n\n")
        f.write("Congratulations!\n")
    # store in DB
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO certificates (student_id, course_id, cert_file, generated_on) VALUES (?,?,?,?)",
                (student_id, course_id, path, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return path

# DB helper wrappers
def db_execute(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

def db_fetchall(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def db_fetchone(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row

# ---------------------------
# Session state defaults
# ---------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None
if "student_name" not in st.session_state:
    st.session_state["student_name"] = None
if "admin_logged" not in st.session_state:
    st.session_state["admin_logged"] = False
if "selected_course" not in st.session_state:
    st.session_state["selected_course"] = None

# ---------------------------
# CSS (dark professional)
# ---------------------------
st.markdown("""
<style>
body, .stApp {background:#0b0c0d; color:#e6eef2; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
.topbar {display:flex; justify-content:space-between; align-items:center; padding:14px 24px; background:#0f1112; border-bottom:1px solid #222;}
.logo {font-weight:700; font-size:20px;}
.search {width:420px; padding:8px; border-radius:8px; background:#111315; color:#fff; border:1px solid #2a2d2f;}
.btn-primary {background:#00bfa5; color:#001; padding:8px 12px; border-radius:8px; border:none; font-weight:600;}
.card {background:#121416; padding:14px; border-radius:12px; border:1px solid #1f2326; margin-bottom:12px;}
.card:hover {box-shadow: 0 6px 18px rgba(0,0,0,0.6); transform: translateY(-3px); transition: all .12s ease-in-out;}
.small {color:#9aa7b2; font-size:13px;}
.footer {text-align:center; padding:12px; color:#7f8b91;}
a {color:#00bfa5;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Top bar (logo, search, login)
# ---------------------------
def topbar():
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.markdown("<div class='logo'>EinTrust Academy</div>", unsafe_allow_html=True)
    with col2:
        q = st.text_input("", placeholder="Search for anything", key="global_search", label_visibility="collapsed")
    with col3:
        if st.session_state["student_id"]:
            st.markdown(f"<div style='text-align:right'>Hi, {st.session_state['student_name']}</div>", unsafe_allow_html=True)
        else:
            if st.button("Student Login / Signup"):
                st.session_state["page"] = "login"
    return

# ---------------------------
# Home page: course list + enroll
# ---------------------------
def page_home():
    topbar()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='display:flex; gap:14px;'>", unsafe_allow_html=True)
    main_col, right_col = st.columns([3,1])
    with main_col:
        # category dropdown from DB
        cats = db_fetchall("SELECT DISTINCT category FROM courses WHERE category IS NOT NULL")
        categories = ["All"] + [c[0] for c in cats if c[0]]
        selected_cat = st.selectbox("Category", categories, index=0, key="home_cat")
        q = st.session_state.get("global_search","").strip().lower()
        # build query
        sql = "SELECT course_id, title, subtitle, description, price, category, banner_path FROM courses"
        params = []
        filters = []
        if selected_cat and selected_cat != "All":
            filters.append("category = ?"); params.append(selected_cat)
        if q:
            filters.append("LOWER(title) LIKE ?"); params.append(f"%{q}%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY course_id DESC"
        courses = db_fetchall(sql, tuple(params))
        if not courses:
            st.info("No courses available yet. Admin can add courses from Admin panel.")
        for course in courses:
            course_id, title, subtitle, desc, price, category, banner = course
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"### {title}")
            st.markdown(f"<div class='small'>{subtitle or ''} • {category or ''}</div>", unsafe_allow_html=True)
            st.write(desc or "")
            st.markdown(f"**{inr(price)}**")
            cols = st.columns([1,1,3])
            # Enroll behavior:
            if cols[2].button("Preview / Enroll", key=f"preview_{course_id}"):
                st.session_state["selected_course"] = course_id
                st.session_state["page"] = "course_preview"
            st.markdown("</div>", unsafe_allow_html=True)
    with right_col:
        st.markdown("<div style='position:sticky; top:20px;'>", unsafe_allow_html=True)
        if st.button("Admin", key="admin_btn"):
            st.session_state["page"] = "admin_login"
        st.markdown("<br><div class='small'>© EinTrust</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Course preview page
# ---------------------------
def page_course_preview():
    cid = st.session_state.get("selected_course")
    if not cid:
        st.info("No course selected.")
        return
    topbar()
    row = db_fetchone("SELECT title, subtitle, description, price, category, banner_path FROM courses WHERE course_id=?", (cid,))
    if not row:
        st.error("Course not found.")
        return
    title, subtitle, description, price, category, banner = row
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.markdown(f"<div class='small'>{subtitle or ''} • {category or ''}</div>", unsafe_allow_html=True)
    st.write(description or "")
    st.markdown(f"**{inr(price)}**")
    st.markdown("</div>", unsafe_allow_html=True)

    # Lessons (show even if not enrolled - preview)
    lessons = db_fetchall("SELECT lesson_id, title, lesson_type, duration_seconds FROM lessons WHERE course_id=? ORDER BY \"order\", lesson_id", (cid,))
    st.markdown("### Lessons")
    for lid, ltitle, ltype, dur in lessons:
        st.markdown(f"- {ltitle} ({ltype})")

    # Enroll button flow:
    student_id = st.session_state.get("student_id")
    enrolled = False
    if student_id:
        enr = db_fetchone("SELECT enrollment_id, paid FROM enrollments WHERE student_id=? AND course_id=?", (student_id, cid))
        enrolled = bool(enr)
    if not student_id:
        if st.button("Enroll → Create profile / Login"):
            st.session_state["page"] = "signup"
            st.session_state["after_signup_course"] = cid
    else:
        # logged in
        if not enrolled:
            if price and price > 0:
                if st.button(f"Pay ₹{price:,.2f}"):
                    # go to simulated payment
                    st.session_state["page"] = "payment"
                    st.session_state["payment_course"] = cid
            else:
                if st.button("Enroll (Free)"):
                    db_execute = db_execute_wrapper
                    db_execute("INSERT INTO enrollments (student_id, course_id, paid, enrolled_on) VALUES (?,?,?,?)",
                               (student_id, cid, 0, datetime.utcnow().isoformat()))
                    st.success("Enrolled! Redirecting to course lessons...")
                    st.session_state["page"] = "course_player"
        else:
            # already enrolled
            if st.button("Go to Course Lessons"):
                st.session_state["page"] = "course_player"

# helper wrapper to avoid repetitive get_conn boilerplate
def db_execute_wrapper(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

# ---------------------------
# Payment (simulated)
# ---------------------------
def page_payment():
    # Simulated simple payment UI
    topbar()
    cid = st.session_state.get("payment_course")
    if not cid:
        st.error("No course selected for payment.")
        return
    row = db_fetchone("SELECT title, price FROM courses WHERE course_id=?", (cid,))
    if not row:
        st.error("Course not found.")
        return
    title, price = row
    st.header(f"Payment for: {title}")
    st.write(f"Amount: {inr(price)} (simulated)")

    st.markdown("**Payment Gateway Placeholder**")
    st.markdown("This is a simulated payment screen. Replace this with Razorpay (or other) integration in production.")
    if st.button("Simulate Successful Payment"):
        # record enrollment as paid
        sid = st.session_state.get("student_id")
        if not sid:
            st.error("You must be logged in to pay.")
            return
        db_execute_wrapper("INSERT INTO enrollments (student_id, course_id, paid, enrolled_on) VALUES (?,?,?,?)",
                           (sid, cid, 1, datetime.utcnow().isoformat()))
        st.success("Payment simulated and enrollment recorded.")
        st.session_state["page"] = "course_player"

# ---------------------------
# Course player / lessons / progress
# ---------------------------
def page_course_player():
    topbar()
    cid = st.session_state.get("selected_course") or st.session_state.get("payment_course")
    if not cid:
        st.info("No course selected.")
        return
    # ensure student logged in
    sid = st.session_state.get("student_id")
    if not sid:
        st.error("You must be logged in to view course lessons.")
        return
    # check enrollment
    enr = db_fetchone("SELECT enrollment_id FROM enrollments WHERE student_id=? AND course_id=?", (sid, cid))
    if not enr:
        st.error("You are not enrolled in this course.")
        return

    course = db_fetchone("SELECT title, description FROM courses WHERE course_id=?", (cid,))
    if not course:
        st.error("Course not found.")
        return
    st.header(course[0])
    st.write(course[1] or "")

    lessons = db_fetchall("SELECT lesson_id, title, lesson_type, content_path, duration_seconds FROM lessons WHERE course_id=? ORDER BY \"order\", lesson_id", (cid,))
    if not lessons:
        st.info("No lessons available.")
        return
    # show progress
    total = len(lessons)
    completed_count = db_fetchone("""
        SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id
        WHERE p.student_id=? AND l.course_id=? AND p.completed=1
    """, (sid, cid))[0]
    pct = int((completed_count / total) * 100) if total else 0
    st.progress(pct/100)
    st.markdown(f"**Progress: {pct}% ({completed_count}/{total})**")

    for lid, ltitle, ltype, cpath, dur in lessons:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### {ltitle}")
        st.markdown(f"<div class='small'>{ltype} • {dur or 0} sec</div>", unsafe_allow_html=True)
        if cpath:
            if ltype == "video":
                # attempt to render video — if cpath is remote or local streamlit supports it
                try:
                    st.video(cpath)
                except:
                    st.write(f"Video file: {cpath}")
            elif ltype in ("pdf", "ppt", "text"):
                st.write(f"Content file: {cpath}")
        # completion status
        comp_row = db_fetchone("SELECT completed FROM progress WHERE student_id=? AND lesson_id=?", (sid, lid))
        completed = bool(comp_row and comp_row[0] == 1)
        if completed:
            st.button("Completed", key=f"done_{lid}", disabled=True)
        else:
            if st.button("Mark as Complete", key=f"mark_{lid}"):
                # save progress
                # use insert or update
                existing = db_fetchone("SELECT progress_id FROM progress WHERE student_id=? AND lesson_id=?", (sid, lid))
                if existing:
                    db_execute_wrapper("UPDATE progress SET completed=1, completed_on=? WHERE progress_id=?", (datetime.utcnow().isoformat(), existing[0]))
                else:
                    db_execute_wrapper("INSERT INTO progress (student_id, lesson_id, completed, completed_on) VALUES (?,?,?,?)",
                                       (sid, lid, 1, datetime.utcnow().isoformat()))
                st.success("Marked complete.")
                # re-run to update progress
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # check for certificate creation
    total_lessons = total
    completed_lessons = db_fetchone("""
        SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id
        WHERE p.student_id=? AND l.course_id=? AND p.completed=1
    """, (sid, cid))[0]
    if total_lessons > 0 and completed_lessons >= total_lessons:
        already = db_fetchone("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (sid, cid))
        if not already:
            # generate
            student_name = db_fetchone("SELECT full_name FROM students WHERE student_id=?", (sid,))[0]
            cert_path = generate_certificate_text(student_name, course[0], sid, cid)
            st.success("Course completed! Certificate generated.")
            st.markdown(f"[Download certificate]({cert_path})")
        else:
            st.markdown(f"[Certificate ready]({already[0]})")

# ---------------------------
# Signup -> create profile -> redirect to login
# ---------------------------
def page_signup():
    topbar()
    st.header("Create Profile")
    with st.form("signup_form"):
        full_name = st.text_input("Full name *")
        email = st.text_input("Email *")
        password = st.text_input("Set password *", type="password")
        st.caption("Password must be min 8 chars, include 1 uppercase, 1 number, 1 special char (@,#,*)")
        sex = st.selectbox("Sex", ["Prefer not to say", "Male", "Female"])
        profession = st.selectbox("Profession *", ["Student", "Working Professional"])
        institution = st.text_input("Institution")
        mobile = st.text_input("Mobile *")
        profile_pic = st.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Create Profile")
        if submitted:
            errors = []
            if not full_name.strip(): errors.append("Full name required")
            if not email.strip(): errors.append("Email required")
            if not password or len(password) < 8: errors.append("Password must be 8+ chars")
            if not any(c.isupper() for c in password): errors.append("Password must have 1 uppercase")
            if not any(c.isdigit() for c in password): errors.append("Password must have 1 number")
            if not any(ch in "@#*" for ch in password): errors.append("Password must have 1 special char among @ # *")
            if not mobile.strip(): errors.append("Mobile required")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                # upload profile pic
                pic_path = None
                if profile_pic:
                    pic_path = save_upload(profile_pic, PROFILE_DIR)
                try:
                    db_execute_wrapper("INSERT INTO students (full_name,email,password,profile_pic,sex,profession,institution,mobile,created_on) VALUES (?,?,?,?,?,?,?,?,?)",
                                       (full_name.strip(), email.strip().lower(), hash_pw(password), pic_path, sex, profession, institution, mobile.strip(), datetime.utcnow().isoformat()))
                    st.success("Profile created. Please login now.")
                    # if user came here after clicking Enroll, remember that
                    after_course = st.session_state.pop("after_signup_course", None)
                    if after_course:
                        # user needs to login next, store that we should redirect to that course after login
                        st.session_state["post_signup_course"] = after_course
                    st.session_state["page"] = "login"
                except Exception as e:
                    st.error("Could not create profile. Email might already exist.")
                    st.exception(e)

# ---------------------------
# Login page
# ---------------------------
def page_login():
    topbar()
    st.header("Student Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not email or not password:
            st.error("Enter email and password")
            return
        row = db_fetchone("SELECT student_id, full_name, password FROM students WHERE email=?", (email.strip().lower(),))
        if not row:
            st.error("No account with that email.")
            return
        sid, full_name, hashed = row
        if verify_pw(password, hashed):
            st.success(f"Welcome {full_name}!")
            st.session_state["student_id"] = sid
            st.session_state["student_name"] = full_name
            # redirect to post_signup_course if present
            post_course = st.session_state.pop("post_signup_course", None)
            if post_course:
                st.session_state["selected_course"] = post_course
                # if course free -> directly enroll & play
                price_row = db_fetchone("SELECT price FROM courses WHERE course_id=?", (post_course,))
                if price_row and price_row[0] and price_row[0] > 0:
                    st.session_state["page"] = "course_preview"
                    st.session_state["selected_course"] = post_course
                else:
                    # enroll free course
                    db_execute_wrapper("INSERT INTO enrollments (student_id, course_id, paid, enrolled_on) VALUES (?,?,?,?)",
                                       (sid, post_course, 0, datetime.utcnow().isoformat()))
                    st.success("Enrolled in free course. Redirecting to lessons...")
                    st.session_state["selected_course"] = post_course
                    st.session_state["page"] = "course_player"
            else:
                st.session_state["page"] = "home"
        else:
            st.error("Incorrect password")
    if st.button("Forgot password?"):
        st.session_state["page"] = "forgot_password"

# ---------------------------
# Forgot & Reset password (simulated)
# ---------------------------
def page_forgot_password():
    topbar()
    st.header("Forgot password (simulated)")
    email = st.text_input("Enter your registered email")
    if st.button("Send reset link (simulated)"):
        if not email:
            st.error("Provide email")
            return
        row = db_fetchone("SELECT student_id FROM students WHERE email=?", (email.strip().lower(),))
        if not row:
            st.error("Email not found")
            return
        token = secrets.token_urlsafe(24)
        db_execute_wrapper("INSERT INTO reset_tokens (token, student_id, created_on, used) VALUES (?,?,?,?)", (token, row[0], datetime.utcnow().isoformat(), 0))
        st.success("Reset token generated (simulated). Copy the token below and go to Reset Password.")
        st.code(token)

def page_reset_password():
    topbar()
    st.header("Reset password (simulated)")
    token = st.text_input("Reset token")
    new_pw = st.text_input("New password", type="password")
    if st.button("Reset Password"):
        if not token or not new_pw:
            st.error("Provide token and new password")
            return
        row = db_fetchone("SELECT student_id, used FROM reset_tokens WHERE token=?", (token,))
        if not row:
            st.error("Invalid token")
            return
        if row[1] == 1:
            st.error("Token already used")
            return
        if len(new_pw) < 8:
            st.error("Password too short")
            return
        student_id = row[0]
        db_execute_wrapper("UPDATE students SET password=? WHERE student_id=?", (hash_pw(new_pw), student_id))
        db_execute_wrapper("UPDATE reset_tokens SET used=1 WHERE token=?", (token,))
        st.success("Password reset successful. Please login.")
        st.session_state["page"] = "login"

# ---------------------------
# Student dashboard
# ---------------------------
def page_dashboard():
    topbar()
    sid = st.session_state.get("student_id")
    if not sid:
        st.error("You must be logged in to access dashboard.")
        return
    st.header("My Dashboard")
    # enrolled courses
    enrolls = db_fetchall("SELECT e.enrollment_id, e.course_id, c.title, c.price FROM enrollments e JOIN courses c ON e.course_id=c.course_id WHERE e.student_id=?", (sid,))
    st.subheader("Enrolled Courses")
    if not enrolls:
        st.info("You have not enrolled in any courses yet.")
    else:
        for enr in enrolls:
            _, cid, title, price = enr
            # progress
            total = db_fetchone("SELECT COUNT(*) FROM lessons WHERE course_id=?", (cid,))[0]
            completed = db_fetchone("""
                SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id
                WHERE p.student_id=? AND l.course_id=? AND p.completed=1
            """, (sid, cid))[0]
            pct = int((completed/total)*100) if total else 0
            st.markdown(f"**{title}** — {inr(price)} — Progress: {pct}%")
            if pct == 100:
                cert = db_fetchone("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (sid, cid))
                if cert and cert[0]:
                    st.markdown(f"[Download certificate]({cert[0]})")
    # students certificates table
    st.subheader("Certificates")
    certs = db_fetchall("SELECT c.course_id, co.title, c.cert_file, c.generated_on FROM certificates c JOIN courses co ON c.course_id = co.course_id WHERE c.student_id=?", (sid,))
    if not certs:
        st.info("No certificates yet.")
    else:
        for cert in certs:
            course_id, title, path, gen_on = cert
            st.markdown(f"- {title} — generated on {gen_on} — [Download]({path})")

# ---------------------------
# Admin login & dashboard
# ---------------------------
def page_admin_login():
    topbar()
    st.header("Admin Login")
    pwd = st.text_input("Enter admin password", type="password")
    if st.button("Enter"):
        row = db_fetchone("SELECT password FROM admin WHERE admin_id=1")
        if row and verify_pw(pwd, row[0]):
            st.session_state["admin_logged"] = True
            st.success("Admin logged in")
            st.session_state["page"] = "admin"
            st.experimental_rerun()
        else:
            st.error("Incorrect admin password")

def page_admin():
    topbar()
    if not st.session_state.get("admin_logged"):
        st.warning("Admin access required")
        return
    st.header("Admin Dashboard")
    st.subheader("Create Course")
    with st.form("create_course"):
        title = st.text_input("Title")
        subtitle = st.text_input("Subtitle")
        description = st.text_area("Description")
        price = st.number_input("Price (INR)", min_value=0.0, format="%.2f")
        category = st.text_input("Category")
        banner = st.file_uploader("Banner (optional)", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Create Course")
        if submitted:
            banner_path = save_upload(banner, BANNERS_DIR) if banner else None
            db_execute_wrapper("INSERT INTO courses (title,subtitle,description,price,category,banner_path,created_on) VALUES (?,?,?,?,?,?,?)",
                               (title, subtitle, description, price, category, banner_path, datetime.utcnow().isoformat()))
            st.success("Course created")

    st.subheader("Courses / Manage")
    courses = db_fetchall("SELECT course_id, title, category FROM courses ORDER BY course_id DESC")
    for cid, t, cat in courses:
        cols = st.columns([3,1,1,1])
        cols[0].markdown(f"**{t}** — {cat or ''}")
        if cols[1].button("Add Lesson", key=f"add_lesson_{cid}"):
            st.session_state["admin_add_for"] = cid
            st.session_state["admin_mode"] = "add_lesson"
        if cols[2].button("View Lessons", key=f"view_lesson_{cid}"):
            lessons = db_fetchall("SELECT lesson_id, title, lesson_type FROM lessons WHERE course_id=?", (cid,))
            if not lessons:
                st.info("No lessons")
            else:
                for lid, ltitle, ltype in lessons:
                    st.markdown(f"- {ltitle} ({ltype})")
                    if st.button("Delete Lesson", key=f"del_{lid}"):
                        db_execute_wrapper("DELETE FROM progress WHERE lesson_id=?", (lid,))
                        db_execute_wrapper("DELETE FROM lessons WHERE lesson_id=?", (lid,))
                        st.experimental_rerun()
        if cols[3].button("Delete Course", key=f"del_course_{cid}"):
            db_execute_wrapper("DELETE FROM lessons WHERE course_id=?", (cid,))
            db_execute_wrapper("DELETE FROM enrollments WHERE course_id=?", (cid,))
            db_execute_wrapper("DELETE FROM certificates WHERE course_id=?", (cid,))
            db_execute_wrapper("DELETE FROM courses WHERE course_id=?", (cid,))
            st.experimental_rerun()

    # Add lesson form (if triggered)
    if st.session_state.get("admin_mode") == "add_lesson":
        cid = st.session_state.get("admin_add_for")
        st.subheader(f"Add lesson to course id {cid}")
        with st.form("create_lesson"):
            ltitle = st.text_input("Lesson title")
            ltype = st.selectbox("Lesson type", ["video","pdf","ppt","text"])
            uploaded = st.file_uploader("Upload file (optional)", type=["mp4","pdf","pptx","txt","png","jpg","jpeg"])
            duration = st.number_input("Duration seconds (for simulation)", min_value=0, step=10)
            submitted = st.form_submit_button("Create Lesson")
            if submitted:
                path = save_upload(uploaded, LESSON_DIR) if uploaded else None
                db_execute_wrapper("INSERT INTO lessons (course_id,title,lesson_type,content_path,duration_seconds) VALUES (?,?,?,?,?)",
                                   (cid, ltitle, ltype, path, int(duration)))
                st.success("Lesson created")
                st.session_state["admin_mode"] = None
                st.experimental_rerun()

    st.subheader("All Students")
    students = db_fetchall("SELECT student_id, full_name, email, mobile, profession, institution, sex, created_on FROM students ORDER BY student_id DESC")
    if students:
        st.table(students)
    else:
        st.info("No registered students yet.")

# ---------------------------
# Router
# ---------------------------
def router():
    page = st.session_state.get("page", "home")
    # map pages
    if page == "home":
        page_home()
    elif page == "course_preview":
        page_course_preview()
    elif page == "payment":
        page_payment()
    elif page == "course_player":
        page_course_player()
    elif page == "signup":
        page_signup()
    elif page == "login":
        page_login()
    elif page == "forgot_password":
        page_forgot_password()
    elif page == "reset_password":
        page_reset_password()
    elif page == "dashboard":
        page_dashboard()
    elif page == "admin_login":
        page_admin_login()
    elif page == "admin":
        page_admin()
    elif page == "course_preview":
        page_course_preview()
    else:
        page_home()

# ---------------------------
# Run app
# ---------------------------
def main():
    st.sidebar.title("Navigation")
    # small nav controls
    nav = st.sidebar.radio("Go to", ["Home","My Dashboard","Signup","Login","Admin"])
    # map selection to pages
    if nav == "Home":
        st.session_state["page"] = "home"
    elif nav == "My Dashboard":
        st.session_state["page"] = "dashboard"
    elif nav == "Signup":
        st.session_state["page"] = "signup"
    elif nav == "Login":
        st.session_state["page"] = "login"
    elif nav == "Admin":
        st.session_state["page"] = "admin_login"

    router()
    st.markdown("<div class='footer'>© EinTrust</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
