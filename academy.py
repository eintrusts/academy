# academy.py
import streamlit as st
import sqlite3
import os
import time
from fpdf import FPDF

# -----------------------------
# App config
# -----------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", initial_sidebar_state="collapsed")

LOGO_URL = "https://raw.githubusercontent.com/eintrusts/CAP/main/EinTrust%20%20(2).png"
ADMIN_PASSWORD = "eintrust2025"  # change in production

DB_PATH = "academy.db"

# -----------------------------
# Helper: DB connection
# -----------------------------
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# -----------------------------
# Create tables (if not exists)
# -----------------------------
def init_db():
    c.execute("""CREATE TABLE IF NOT EXISTS students(
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                sex TEXT,
                profession TEXT,
                institution TEXT,
                mobile TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS courses(
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                price REAL
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons(
                lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title TEXT,
                content_type TEXT,
                content_path TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lesson_progress(
                student_id INTEGER,
                lesson_id INTEGER,
                viewed INTEGER DEFAULT 0,
                PRIMARY KEY(student_id,lesson_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS certificates(
                student_id INTEGER,
                course_id INTEGER,
                cert_file TEXT,
                PRIMARY KEY(student_id,course_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments(
                student_id INTEGER,
                course_id INTEGER,
                status TEXT,
                PRIMARY KEY(student_id,course_id)
                )""")
    conn.commit()

init_db()

# -----------------------------
# Theme (dark/light) management
# -----------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # default

def apply_theme_css():
    dark = st.session_state["theme"] == "dark"
    if dark:
        bg = "#0f1720"  # dark background
        card = "#111827"
        card_hover = "#1f2937"
        text = "#e6eef8"
        muted = "#9aa6b2"
        accent = "#ff9900"
    else:
        bg = "#f7f9fb"
        card = "#ffffff"
        card_hover = "#f0f4f8"
        text = "#0b1320"
        muted = "#5b6b77"
        accent = "#ff9900"

    css = f"""
    <style>
    :root {{
      --bg: {bg};
      --card: {card};
      --card-hover: {card_hover};
      --text: {text};
      --muted: {muted};
      --accent: {accent};
    }}
    html, body, [data-testid="stAppViewContainer"] {{ background: var(--bg); color: var(--text); }}
    .topbar {{ background: transparent; }}
    .card-box {{ background: var(--card); padding:16px; border-radius:12px; box-shadow: 0 6px 18px rgba(0,0,0,0.35); transition: transform .12s ease, background .12s ease; }}
    .card-box:hover {{ transform: translateY(-4px); background: var(--card-hover); }}
    .muted {{ color: var(--muted); font-size:0.95rem; }}
    .brand {{ color: var(--accent); font-weight:700; }}
    .btn-primary > button {{ background: var(--accent); color: #000; font-weight:700; border-radius:8px; padding:8px 14px; }}
    .btn-primary > button:hover {{ opacity:0.95; }}
    .small {{ font-size:0.9rem; color:var(--muted); }}
    .course-grid {{ display:grid; grid-template-columns: repeat(auto-fill,minmax(280px,1fr)); gap:18px; }}
    .course-card-title {{ font-size:1.05rem; font-weight:700; }}
    hr {{ border-color: rgba(255,255,255,0.06); }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_theme_css()

# -----------------------------
# Utilities
# -----------------------------
def inr_format(amount):
    try:
        return f"₹{int(amount):,}"
    except Exception:
        return f"₹{amount}"

def save_profile_pic(uploaded_file):
    if not uploaded_file:
        return None
    os.makedirs("profile_pics", exist_ok=True)
    path = os.path.join("profile_pics", f"{int(time.time())}_{uploaded_file.name}")
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def enroll_student_lessons(student_id, course_id):
    rows = c.execute("SELECT lesson_id FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    for (lesson_id,) in rows:
        c.execute("INSERT OR IGNORE INTO lesson_progress(student_id, lesson_id, viewed) VALUES (?,?,0)", (student_id, lesson_id))
    conn.commit()

def mark_lesson_viewed(student_id, lesson_id):
    c.execute("INSERT OR REPLACE INTO lesson_progress(student_id, lesson_id, viewed) VALUES (?,?,1)", (student_id, lesson_id))
    conn.commit()

def generate_certificate(student_name, course_title, student_id, course_id):
    os.makedirs("certificates", exist_ok=True)
    file_name = f"certificates/certificate_{student_id}_{course_id}.pdf"
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(False)
    pdf.set_font("Arial", "B", 28)
    pdf.set_y(40)
    pdf.cell(0, 12, "Certificate of Completion", ln=True, align="C")
    pdf.set_font("Arial", "", 16)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"This certificate is awarded to {student_name} for successfully completing the course \"{course_title}\".", align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Issued by EinTrust Academy — {time.strftime('%d %b %Y')}", ln=True, align="C")
    pdf.output(file_name)
    return file_name

# -----------------------------
# Top bar: theme toggle + logo + auth quick links
# -----------------------------
def top_bar():
    col1, col2, col3 = st.columns([1, 6, 2])
    with col1:
        st.image(LOGO_URL, width=120)
    with col2:
        st.markdown("<div style='text-align:center;'><span class='brand' style='font-size:22px;'>EinTrust Academy</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='small muted' style='text-align:center;'>Professional Learning — Courses, Lessons & Certificates</div>", unsafe_allow_html=True)
    with col3:
        # Theme switch and logout
        theme_choice = st.radio("", ["Dark", "Light"], index=0 if st.session_state["theme"]=="dark" else 1, horizontal=True, key="theme_radio")
        st.session_state["theme"] = "dark" if theme_choice=="Dark" else "light"
        apply_theme_css()
        # Quick Logout buttons
        if 'student' in st.session_state:
            if st.button("Logout", key="logout_student"):
                del st.session_state['student']
                st.experimental_rerun()
        elif 'admin' in st.session_state:
            if st.button("Logout Admin", key="logout_admin"):
                del st.session_state['admin']
                st.experimental_rerun()

top_bar()
st.markdown("<hr>", unsafe_allow_html=True)

# -----------------------------
# Pages: Login / Signup / Forgot password (centered cards)
# -----------------------------
def auth_layout():
    st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
    left, right = st.columns([1,1])
    with left:
        login_card()
    with right:
        signup_card()
    st.markdown("</div>", unsafe_allow_html=True)

def login_card():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:6px;'>Student Login</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small muted'>Enter your email and password</div>", unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Login", key="login_btn", help="Login as student"):
            if not email or not password:
                st.error("Enter both email and password.")
            else:
                row = c.execute("SELECT student_id,name,password FROM students WHERE email=?", (email,)).fetchone()
                if row and row[2] == password:
                    st.success("Login successful.")
                    st.session_state['student'] = {"id": row[0], "name": row[1], "email": email}
                    st.experimental_rerun()
                else:
                    st.error("Incorrect email or password.")
    with col2:
        if st.button("Forgot Password", key="forgot_btn"):
            st.session_state['pw_reset_email'] = email
            st.info("A simulated reset link is shown below (for testing). Use it to set a new password.")
            token = f"RESET-{int(time.time())}"
            st.success(f"Simulated reset link: /reset-password?token={token}&email={email}")
    st.markdown("</div>", unsafe_allow_html=True)

def signup_card():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:6px;'>Create Student Account</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small muted'>Quick registration (profile can be edited later)</div>", unsafe_allow_html=True)
    with st.form("signup_form", clear_on_submit=False):
        name = st.text_input("Full name", key="su_name")
        email = st.text_input("Email", key="su_email")
        password = st.text_input("Set password", type="password", key="su_pass")
        col1, col2 = st.columns([1,1])
        with col1:
            sex = st.selectbox("Sex", ["Prefer not to say", "Male", "Female"], key="su_sex")
            profession = st.selectbox("Profession", ["Student", "Working Professional"], key="su_prof")
        with col2:
            institution = st.text_input("Institution (optional)", key="su_inst")
            mobile = st.text_input("Mobile", key="su_mobile")
        submit = st.form_submit_button("Create Account")
        if submit:
            if not name or not email or not password:
                st.error("Please fill the mandatory fields (name, email, password).")
            else:
                try:
                    c.execute("INSERT INTO students(name,email,password,sex,profession,institution,mobile) VALUES(?,?,?,?,?,?,?)",
                              (name, email, password, sex, profession, institution, mobile))
                    conn.commit()
                    st.success("Account created. Please use the login panel.")
                except Exception as e:
                    st.error("Email is already registered. Try logging in.")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Admin login card (single centered)
# -----------------------------
def admin_auth_card():
    st.markdown("<div style='display:flex; justify-content:center;'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card-box' style='max-width:720px;'>", unsafe_allow_html=True)
        st.markdown("<h3>Admin Login</h3>", unsafe_allow_html=True)
        admin_pass = st.text_input("Admin password", type="password", key="admin_pass")
        if st.button("Enter Admin", key="admin_enter"):
            if admin_pass == ADMIN_PASSWORD:
                st.session_state['admin'] = True
                st.experimental_rerun()
            else:
                st.error("Incorrect admin password.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Student dashboard (sidebar + main)
# -----------------------------
def student_sidebar_and_main():
    # Sidebar navigation (implemented as left column)
    left_col, main_col = st.columns([0.22, 0.78])
    with left_col:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='margin:6px 0;'>Hello, {st.session_state['student']['name']}</h4>", unsafe_allow_html=True)
        st.markdown("<div class='small muted'>Your learning space</div>", unsafe_allow_html=True)
        nav = st.radio("", ["Courses", "My Lessons", "Progress", "Certificates", "Profile"], index=0, key="student_nav")
        st.markdown("</div>", unsafe_allow_html=True)
    with main_col:
        if nav == "Courses":
            student_courses_page()
        elif nav == "My Lessons":
            student_lessons_page()
        elif nav == "Progress":
            student_progress_page()
        elif nav == "Certificates":
            student_certificates_page()
        elif nav == "Profile":
            student_profile_page()

# -----------------------------
# Student pages
# -----------------------------
def student_courses_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Available Courses</h3>", unsafe_allow_html=True)
    rows = c.execute("SELECT course_id, title, description, price FROM courses").fetchall()
    if not rows:
        st.info("No courses published yet. Admin can add courses from the admin dashboard.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Display grid of course cards
    st.markdown("<div class='course-grid'>", unsafe_allow_html=True)
    for course_id, title, desc, price in rows:
        enrolled = c.execute("SELECT * FROM payments WHERE student_id=? AND course_id=? AND status='Success'", (st.session_state['student']['id'], course_id)).fetchone()
        card_html = f"<div class='card-box'><div class='course-card-title'>{title}</div><div class='muted' style='margin:8px 0;'>{desc}</div>"
        card_html += f"<div style='font-weight:700; margin-bottom:8px;'>{inr_format(price)}</div>"
        if enrolled:
            card_html += "<div class='small muted'>Enrolled • Access in My Lessons</div>"
            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)
        else:
            card_html += "<div class='small muted'>Not enrolled</div>"
            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(f"Enroll — {title}", key=f"enroll_{course_id}"):
                # Simulated payment workflow
                st.success("Payment simulated. You are enrolled.")
                c.execute("INSERT OR IGNORE INTO payments(student_id, course_id, status) VALUES(?,?,?)",
                          (st.session_state['student']['id'], course_id, 'Success'))
                conn.commit()
                enroll_student_lessons(st.session_state['student']['id'], course_id)
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def student_lessons_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>My Lessons</h3>", unsafe_allow_html=True)
    lessons = c.execute("""
        SELECT l.lesson_id, l.title, l.content_type, l.content_path, crs.title, crs.course_id
        FROM lessons l
        JOIN courses crs ON crs.course_id=l.course_id
        JOIN payments p ON p.course_id=crs.course_id
        WHERE p.student_id=? AND p.status='Success'
        ORDER BY crs.course_id, l.lesson_id
    """, (st.session_state['student']['id'],)).fetchall()

    if not lessons:
        st.info("You have not enrolled in any course yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for lesson_id, title, ctype, cpath, course_title, course_id in lessons:
        viewed_row = c.execute("SELECT viewed FROM lesson_progress WHERE student_id=? AND lesson_id=?", (st.session_state['student']['id'], lesson_id)).fetchone()
        viewed = viewed_row[0] if viewed_row else 0
        st.markdown(f"<div class='card-box' style='margin-bottom:12px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:700'>{course_title} — {title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='muted'>Type: {ctype.upper()}</div>", unsafe_allow_html=True)
        if ctype == "video":
            try:
                st.video(cpath)
            except:
                st.write("Video URL / path could not be loaded. (Ensure valid public URL or hosted file.)")
        elif ctype == "pdf":
            st.write("PDF / Document content / link:")
            st.write(cpath)
        else:
            st.write(cpath)

        if viewed:
            st.success("Lesson completed")
        else:
            if st.button("Mark as Complete", key=f"mark_{lesson_id}"):
                mark_lesson_viewed(st.session_state['student']['id'], lesson_id)
                st.success("Marked complete. Progress updated.")
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # After listing lessons, check certificate generation
    enrolled_courses = c.execute("SELECT course_id FROM payments WHERE student_id=? AND status='Success'", (st.session_state['student']['id'],)).fetchall()
    for (course_id,) in enrolled_courses:
        total_lessons = c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,)).fetchone()[0]
        if total_lessons == 0:
            continue
        completed = c.execute("""
            SELECT COUNT(*) FROM lesson_progress
            WHERE student_id=? AND lesson_id IN (SELECT lesson_id FROM lessons WHERE course_id=?) AND viewed=1
        """, (st.session_state['student']['id'], course_id)).fetchone()[0]
        if total_lessons == completed:
            exists = c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (st.session_state['student']['id'], course_id)).fetchone()
            if not exists:
                course_title = c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,)).fetchone()[0]
                cert_file = generate_certificate(st.session_state['student']['name'], course_title, st.session_state['student']['id'], course_id)
                c.execute("INSERT INTO certificates(student_id,course_id,cert_file) VALUES(?,?,?)", (st.session_state['student']['id'], course_id, cert_file))
                conn.commit()
                st.balloons()
                st.success(f"Certificate generated for {course_title} — check Certificates tab.")
    st.markdown("</div>", unsafe_allow_html=True)

def student_progress_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>My Progress</h3>", unsafe_allow_html=True)
    rows = c.execute("""
        SELECT crs.course_id, crs.title,
               COUNT(l.lesson_id) as total,
               SUM(COALESCE(lp.viewed,0)) as completed
        FROM courses crs
        LEFT JOIN lessons l ON l.course_id = crs.course_id
        LEFT JOIN lesson_progress lp ON lp.lesson_id = l.lesson_id AND lp.student_id=?
        LEFT JOIN payments p ON p.course_id = crs.course_id AND p.student_id=?
        WHERE p.status='Success'
        GROUP BY crs.course_id
    """, (st.session_state['student']['id'], st.session_state['student']['id'])).fetchall()
    if not rows:
        st.info("No progress yet — enroll and complete lessons.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    for course_id, title, total, completed in rows:
        completed = completed or 0
        pct = int((completed / total) * 100) if total > 0 else 0
        st.markdown(f"<div style='font-weight:700'>{title}</div>", unsafe_allow_html=True)
        st.progress(pct)
        st.markdown(f"<div class='small muted'>{completed}/{total} lessons completed — {pct}%</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def student_certificates_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Certificates</h3>", unsafe_allow_html=True)
    certs = c.execute("SELECT course_id, cert_file FROM certificates WHERE student_id=?", (st.session_state['student']['id'],)).fetchall()
    if not certs:
        st.info("No certificates available. Complete all lessons in a course to generate a certificate.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    for course_id, cert_file in certs:
        course_title = c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,)).fetchone()[0]
        st.markdown(f"<div class='card-box'><div style='font-weight:700'>{course_title}</div>", unsafe_allow_html=True)
        try:
            with open(cert_file, "rb") as f:
                st.download_button("Download Certificate (PDF)", data=f, file_name=os.path.basename(cert_file))
        except FileNotFoundError:
            st.error("Certificate file not found on server.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def student_profile_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>My Profile</h3>", unsafe_allow_html=True)
    row = c.execute("SELECT name,email,sex,profession,institution,mobile FROM students WHERE student_id=?", (st.session_state['student']['id'],)).fetchone()
    if not row:
        st.error("Profile not found.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    name, email, sex, profession, institution, mobile = row
    with st.form("edit_profile"):
        n = st.text_input("Full name", value=name)
        s = st.selectbox("Sex", ["Prefer not to say","Male","Female"], index=["Prefer not to say","Male","Female"].index(sex) if sex in ["Prefer not to say","Male","Female"] else 0)
        prof = st.selectbox("Profession", ["Student","Working Professional"], index=0 if profession!="Working Professional" else 1)
        inst = st.text_input("Institution", value=institution or "")
        mob = st.text_input("Mobile", value=mobile or "")
        submit = st.form_submit_button("Save profile")
        if submit:
            c.execute("UPDATE students SET name=?, sex=?, profession=?, institution=?, mobile=? WHERE student_id=?",
                      (n, s, prof, inst, mob, st.session_state['student']['id']))
            conn.commit()
            st.success("Profile updated.")
            st.session_state['student']['name'] = n
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Admin pages & management (with edit/delete)
# -----------------------------
def admin_sidebar_and_main():
    left, main = st.columns([0.22, 0.78])
    with left:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown("<h4>Admin</h4>", unsafe_allow_html=True)
        page = st.radio("", ["Students","Courses","Lessons","Create Course","Create Lesson"], index=0, key="admin_nav")
        st.markdown("</div>", unsafe_allow_html=True)
    with main:
        if page == "Students":
            admin_students_page()
        elif page == "Courses":
            admin_courses_page()
        elif page == "Lessons":
            admin_lessons_page()
        elif page == "Create Course":
            admin_create_course()
        elif page == "Create Lesson":
            admin_create_lesson()

def admin_students_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Students</h3>", unsafe_allow_html=True)
    rows = c.execute("SELECT student_id, name, email, sex, profession, institution, mobile FROM students").fetchall()
    st.dataframe(rows, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def admin_courses_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Courses</h3>", unsafe_allow_html=True)
    rows = c.execute("SELECT course_id, title, description, price FROM courses").fetchall()
    for course_id, title, desc, price in rows:
        st.markdown(f"<div class='card-box' style='margin-bottom:12px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:700'>{title} — {inr_format(price)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='muted'>{desc}</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            if st.button("Edit", key=f"edit_course_{course_id}"):
                edit_course_modal(course_id)
        with col2:
            if st.button("Delete", key=f"del_course_{course_id}"):
                c.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
                c.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
                conn.commit()
                st.success("Course and its lessons deleted.")
                st.experimental_rerun()
        with col3:
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def admin_lessons_page():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Lessons</h3>", unsafe_allow_html=True)
    rows = c.execute("SELECT l.lesson_id, l.title, l.content_type, crs.title FROM lessons l JOIN courses crs ON crs.course_id=l.course_id").fetchall()
    for lesson_id, title, ctype, course_title in rows:
        st.markdown(f"<div class='card-box' style='margin-bottom:12px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:700'>{course_title} — {title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='muted'>Type: {ctype.upper()}</div>", unsafe_allow_html=True)
        if st.button("Edit", key=f"edit_lesson_{lesson_id}"):
            edit_lesson_modal(lesson_id)
        if st.button("Delete", key=f"del_lesson_{lesson_id}"):
            c.execute("DELETE FROM lessons WHERE lesson_id=?", (lesson_id,))
            conn.commit()
            st.success("Lesson deleted.")
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def admin_create_course():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Create Course</h3>", unsafe_allow_html=True)
    with st.form("create_course_form"):
        title = st.text_input("Course title")
        desc = st.text_area("Short description")
        price = st.number_input("Price (INR)", min_value=0, value=0)
        submit = st.form_submit_button("Create course")
        if submit:
            if not title:
                st.error("Title is required.")
            else:
                c.execute("INSERT INTO courses(title,description,price) VALUES(?,?,?)", (title, desc, price))
                conn.commit()
                st.success("Course created.")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def admin_create_lesson():
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<h3>Create Lesson</h3>", unsafe_allow_html=True)
    courses = c.execute("SELECT course_id, title FROM courses").fetchall()
    if not courses:
        st.info("No courses found. Create a course first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    with st.form("create_lesson_form"):
        course_option = st.selectbox("Select course", [f"{cid} - {t}" for cid, t in courses])
        course_id = int(course_option.split(" - ")[0])
        title = st.text_input("Lesson title")
        ctype = st.selectbox("Content type", ["text", "video", "pdf"])
        path = st.text_input("Content (for text: enter text; for video/pdf: enter URL or path)")
        submit = st.form_submit_button("Create lesson")
        if submit:
            if not title or not path:
                st.error("Title and content are required.")
            else:
                c.execute("INSERT INTO lessons(course_id,title,content_type,content_path) VALUES(?,?,?,?)", (course_id, title, ctype, path))
                conn.commit()
                st.success("Lesson created.")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Admin edit modals (simple inline forms)
# -----------------------------
def edit_course_modal(course_id):
    row = c.execute("SELECT title, description, price FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not row:
        st.error("Course not found.")
        return
    title, desc, price = row
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown(f"<h4>Edit Course: {title}</h4>", unsafe_allow_html=True)
    with st.form(f"edit_course_{course_id}"):
        new_title = st.text_input("Title", value=title)
        new_desc = st.text_area("Description", value=desc)
        new_price = st.number_input("Price (INR)", min_value=0, value=price)
        submitted = st.form_submit_button("Save changes")
        if submitted:
            c.execute("UPDATE courses SET title=?, description=?, price=? WHERE course_id=?", (new_title, new_desc, new_price, course_id))
            conn.commit()
            st.success("Course updated.")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def edit_lesson_modal(lesson_id):
    row = c.execute("SELECT course_id, title, content_type, content_path FROM lessons WHERE lesson_id=?", (lesson_id,)).fetchone()
    if not row:
        st.error("Lesson not found.")
        return
    course_id, title, ctype, path = row
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown(f"<h4>Edit Lesson: {title}</h4>", unsafe_allow_html=True)
    courses = c.execute("SELECT course_id, title FROM courses").fetchall()
    with st.form(f"edit_lesson_{lesson_id}"):
        course_choice = st.selectbox("Course", [f"{cid} - {t}" for cid, t in courses], index=[i for i,(cid,t) in enumerate(courses) if cid==course_id][0] if courses else 0)
        new_course_id = int(course_choice.split(" - ")[0])
        new_title = st.text_input("Title", value=title)
        new_type = st.selectbox("Content type", ["text","video","pdf"], index=["text","video","pdf"].index(ctype))
        new_path = st.text_input("Content", value=path)
        submitted = st.form_submit_button("Save changes")
        if submitted:
            c.execute("UPDATE lessons SET course_id=?, title=?, content_type=?, content_path=? WHERE lesson_id=?",
                      (new_course_id, new_title, new_type, new_path, lesson_id))
            conn.commit()
            st.success("Lesson updated.")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# App main entry
# -----------------------------
def main():
    # If user not authenticated, show auth screens
    if 'student' not in st.session_state and 'admin' not in st.session_state:
        # Present a professional landing + auth
        st.markdown("<div style='max-width:1100px; margin:auto;'>", unsafe_allow_html=True)
        st.markdown("<div style='display:flex; gap:18px; align-items:stretch;'>", unsafe_allow_html=True)
        # Left: welcome narrative
        with st.container():
            st.markdown("<div class='card-box' style='flex:1;'>", unsafe_allow_html=True)
            st.markdown("<h1 style='margin-bottom:6px;'>Welcome to EinTrust Academy</h1>", unsafe_allow_html=True)
            st.markdown("<div class='muted'>Professional online academy for sustainability, ESG & compliance. Create account or login to start learning.</div>", unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<div class='small muted'>If you are Admin, use the Admin Login below.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        # Right: auth cards
        auth_layout()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div style='display:flex; justify-content:center; gap:20px;'>", unsafe_allow_html=True)
        admin_auth_card()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Authenticated
        if 'student' in st.session_state:
            student_sidebar_and_main()
        elif 'admin' in st.session_state:
            admin_sidebar_and_main()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:var(--muted);'>&copy; EinTrust 2025</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
