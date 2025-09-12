# academy.py
import streamlit as st
import sqlite3
import os
import time
import re
import hashlib
from fpdf import FPDF
from io import BytesIO

# -----------------------
# Config
# -----------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", initial_sidebar_state="collapsed")
DB = "academy.db"
LOGO = "https://raw.githubusercontent.com/eintrusts/CAP/main/EinTrust%20%20(2).png"
ADMIN_PASSWORD = "EinTrustAdmin123"  # change in production

# -----------------------
# Styling (dark theme)
# -----------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    :root{
      --bg:#0d1117; --card:#0f1720; --muted:#9aa6b2; --text:#e6eef8; --accent:#ff9900;
    }
    html, body, [data-testid="stAppViewContainer"] { background: linear-gradient(180deg,#07101a 0%, #0d1117 100%); color:var(--text); font-family: 'Inter', sans-serif;}
    .topbar {background:transparent}
    .header {display:flex; justify-content:space-between; align-items:center; padding:14px 8px;}
    .brand {display:flex; gap:12px; align-items:center;}
    .brand h1{margin:0; font-size:20px; color:var(--accent)}
    .nav-right {display:flex; gap:8px; align-items:center;}
    .btn {background:var(--accent); color:#000; padding:8px 14px; border-radius:10px; font-weight:700; border:none;}
    .btn:hover {opacity:0.95; transform:translateY(-2px);}
    .small {color:var(--muted); font-size:0.95rem;}
    .course-grid {display:grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap:20px; padding:16px;}
    .course-card {background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:14px; border-radius:12px; transition: transform .12s ease; box-shadow:0 6px 24px rgba(0,0,0,0.6);}
    .course-card:hover {transform: translateY(-6px);}
    .course-banner {width:100%; height:150px; object-fit:cover; border-radius:8px;}
    .muted {color:var(--muted);}
    .auth-card {background:var(--card); padding:18px; border-radius:12px; width:420px;}
    .admin-floating {position:fixed; bottom:18px; right:18px; background:transparent; color:var(--muted); font-size:12px; border-radius:6px; padding:8px;}
    .course-lesson {background:rgba(255,255,255,0.02); padding:10px; border-radius:8px; margin-bottom:8px;}
    hr {border-color: rgba(255,255,255,0.06);}
    .progress-bar {height:10px; background:rgba(255,255,255,0.06); border-radius:6px; overflow:hidden;}
    .progress-fill {height:100%; background:var(--accent);}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# DB helpers
# -----------------------
def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                sex TEXT,
                profession TEXT,
                institution TEXT,
                mobile TEXT,
                pic TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                subtitle TEXT,
                description TEXT,
                price REAL,
                banner TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
                lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title TEXT,
                content_type TEXT,
                content_path TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments (
                student_id INTEGER,
                course_id INTEGER,
                status TEXT,
                PRIMARY KEY(student_id,course_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lesson_progress (
                student_id INTEGER,
                lesson_id INTEGER,
                viewed INTEGER DEFAULT 0,
                PRIMARY KEY(student_id,lesson_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS certificates (
                student_id INTEGER,
                course_id INTEGER,
                cert_file TEXT,
                PRIMARY KEY(student_id,course_id)
    )""")
    conn.commit()
    conn.close()

def seed_demo():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM courses")
    if c.fetchone()[0] == 0:
        # Course 1
        c.execute("INSERT INTO courses (title,subtitle,description,price) VALUES (?,?,?,?)",
                  ("Sustainability Basics","Intro to sustainability & ESG","A practical introduction to sustainability, ESG and corporate responsibility.",0))
        cid1 = c.lastrowid
        c.executemany("INSERT INTO lessons (course_id,title,content_type,content_path) VALUES (?,?,?,?)", [
            (cid1, "Welcome & Course Overview", "text", "Welcome to Sustainability Basics — in this lesson we'll see course flow."),
            (cid1, "Why Sustainability Matters", "text", "Overview of why sustainability is critical for businesses and communities."),
            (cid1, "Short Intro Video", "video", "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"),
        ])
        # Course 2
        c.execute("INSERT INTO courses (title,subtitle,description,price) VALUES (?,?,?,?)",
                  ("Climate Change Essentials","Science and impacts","Understand the core science behind climate change and its implications.",499))
        cid2 = c.lastrowid
        c.executemany("INSERT INTO lessons (course_id,title,content_type,content_path) VALUES (?,?,?,?)", [
            (cid2, "Greenhouse Gases 101", "text", "What are greenhouse gases and how do they warm the planet?"),
            (cid2, "Climate Impacts", "text", "Observed and projected impacts across regions and sectors."),
            (cid2, "Case Study Video", "video", "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"),
        ])
        # Course 3
        c.execute("INSERT INTO courses (title,subtitle,description,price) VALUES (?,?,?,?)",
                  ("ESG for Professionals","Apply ESG in business","Practical frameworks to build ESG programs for organizations.",1500))
        cid3 = c.lastrowid
        c.executemany("INSERT INTO lessons (course_id,title,content_type,content_path) VALUES (?,?,?,?)", [
            (cid3, "ESG Frameworks Overview", "text", "Learn commonly used ESG frameworks and standards."),
            (cid3, "Materiality Assessment", "pdf", "https://www.wri.org/"),
            (cid3, "Implementing ESG Programs", "text", "Steps to integrate ESG into business strategy."),
        ])
    conn.commit()
    conn.close()

# -----------------------
# Security / password
# -----------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def pw_valid(pw: str) -> (bool, str):
    # rules: min 8, at least 1 number, at least 1 uppercase, at least one special @ # *
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"\d", pw):
        return False, "Password must contain at least one number."
    if not re.search(r"[A-Z]", pw):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[@#*]", pw):
        return False, "Password must contain at least one special character (@, # or *)."
    return True, ""

# -----------------------
# Utility functions
# -----------------------
def enroll_student(student_id:int, course_id:int):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO payments(student_id,course_id,status) VALUES(?,?,?)",(student_id,course_id,"Success"))
    # create lesson progress rows
    lessons = c.execute("SELECT lesson_id FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    for (lid,) in lessons:
        c.execute("INSERT OR IGNORE INTO lesson_progress(student_id, lesson_id, viewed) VALUES (?,?,?)",(student_id,lid,0))
    conn.commit(); conn.close()

def mark_lesson_complete(student_id:int, lesson_id:int):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO lesson_progress(student_id, lesson_id, viewed) VALUES (?,?,1)", (student_id, lesson_id))
    conn.commit(); conn.close()

def generate_certificate(student_name, course_title, student_id, course_id):
    os.makedirs("certs", exist_ok=True)
    fname = f"certs/certificate_{student_id}_{course_id}.pdf"
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial","B",26)
    pdf.cell(0, 16, "Certificate of Completion", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial","",16)
    pdf.multi_cell(0, 10, f"This certifies that {student_name} has completed the course '{course_title}'.", align="C")
    pdf.ln(6)
    pdf.set_font("Arial","",12)
    pdf.cell(0,8,f"Issued by EinTrust Academy on {time.strftime('%d %b %Y')}", ln=True, align="C")
    pdf.output(fname)
    return fname

# -----------------------
# UI: Header / nav
# -----------------------
def header():
    st.markdown(
        f"""
        <div class="header">
          <div class="brand">
            <img src="{LOGO}" width="48" style="border-radius:8px;"/>
            <div>
              <h1>EinTrust Academy</h1>
              <div class="small muted">Professional LMS — sustainability, ESG & more</div>
            </div>
          </div>
          <div class="nav-right">
            <a href="?page=login"><button class="btn">Login</button></a>
          </div>
        </div>
        <hr>
        """, unsafe_allow_html=True)

# -----------------------
# Pages
# -----------------------
def home_page():
    header()
    conn = get_conn(); c = conn.cursor()
    rows = c.execute("SELECT course_id,title,subtitle,description,price,banner FROM courses ORDER BY course_id DESC").fetchall()
    conn.close()
    st.markdown('<div class="course-grid">', unsafe_allow_html=True)
    for course_id,title,subtitle,description,price,banner in rows:
        banner_html = f"<img src='{banner}' class='course-banner'/>" if banner else ""
        card = f"""
          <div class="course-card">
            {banner_html}
            <div style='margin-top:10px; font-weight:700'>{title}</div>
            <div class='muted'>{subtitle or description[:110]}</div>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px;'>
              <div style='font-weight:700'>{'Free' if not price else f'₹{int(price):,}'}</div>
              <div><a href='?page=preview&course_id={course_id}'><button class='btn'>View Course</button></a></div>
            </div>
          </div>
        """
        st.markdown(card, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # admin floating small button bottom-right
    st.markdown(f"""<a class="admin-floating" href="?page=admin">Admin</a>""", unsafe_allow_html=True)

def preview_course(course_id:int):
    header()
    conn = get_conn(); c = conn.cursor()
    course = c.execute("SELECT course_id,title,subtitle,description,price,banner FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not course:
        st.error("Course not found.")
        conn.close(); return
    cid,title,subtitle,description,price,banner = course
    if banner:
        st.image(banner, use_column_width=True)
    st.markdown(f"<h2 style='margin-top:8px'>{title}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='muted'>{subtitle or ''}</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown(f"<div>{description}</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4>Lessons</h4>", unsafe_allow_html=True)
        lessons = c.execute("SELECT lesson_id,title,content_type FROM lessons WHERE course_id=? ORDER BY lesson_id", (cid,)).fetchall()
        # show lessons (visible to all) but lock open unless enrolled
        is_enrolled = False
        if 'student' in st.session_state:
            sid = st.session_state['student']['id']
            p = c.execute("SELECT status FROM payments WHERE student_id=? AND course_id=?", (sid, cid)).fetchone()
            is_enrolled = bool(p and p[0] == "Success")
        for lid, ltitle, ltype in lessons:
            lock_note = "" if is_enrolled else "<span class='muted'> (locked — enroll to access)</span>"
            st.markdown(f"<div class='course-lesson'><b>{ltitle}</b> <span class='muted'>• {ltype.upper()}</span> {lock_note}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card' style='padding:14px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:700; font-size:18px'>{'Free' if not price else f'₹{int(price):,}'}</div>", unsafe_allow_html=True)
        st.markdown("<div class='small muted' style='margin-top:8px;'>Access to lessons and certificate on completion</div>", unsafe_allow_html=True)
        if 'student' in st.session_state:
            if is_enrolled:
                st.success("You are enrolled")
                if st.button("Go to My Course"):
                    st.session_state['page'] = "dashboard"
                    st.session_state['view_course'] = cid
                    st.experimental_rerun()
            else:
                if st.button("Enroll Now (simulate)"):
                    enroll_student(st.session_state['student']['id'], cid)
                    st.success("Enrolled — simulated payment")
                    st.experimental_rerun()
        else:
            # redirect to signup; remember next action
            if st.button("Enroll Now"):
                st.session_state['next_enroll'] = cid
                st.session_state['page'] = "signup"
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    conn.close()

def signup_page():
    header()
    st.markdown("<div style='display:flex; justify-content:center; padding:24px;'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Create account</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small muted'>Signup with email — you will complete profile after login if you wish.</div>", unsafe_allow_html=True)
    email = st.text_input("Email (required)", key="su_email")
    password = st.text_input("Password (required)", type="password", key="su_password")
    st.markdown("<div class='small muted' style='margin-top:6px;'>Password rules: min 8 chars • at least 1 number • 1 uppercase • 1 special (@, # or *)</div>", unsafe_allow_html=True)
    if st.button("Create account"):
        valid, msg = pw_valid(password)
        if not email:
            st.error("Email is required.")
        elif not valid:
            st.error(msg)
        else:
            conn = get_conn(); c = conn.cursor()
            try:
                c.execute("INSERT INTO students (email, password) VALUES (?, ?)", (email, hash_pw(password:=password)))
                conn.commit()
                conn.close()
                st.success("Account created. Please login.")
                st.session_state['page'] = "login"
                st.experimental_rerun()
            except Exception:
                st.error("Email already registered.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def login_page():
    header()
    st.markdown("<div style='display:flex; justify-content:center; padding:24px;'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Login</h3>", unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        if not email or not password:
            st.error("Provide email and password")
        else:
            conn = get_conn(); c = conn.cursor()
            row = c.execute("SELECT student_id,email,password,name FROM students WHERE email=?", (email,)).fetchone()
            conn.close()
            if row and row[2] == hash_pw(password):
                st.success("Login successful")
                st.session_state['student'] = {"id": row[0], "email": row[1], "name": row[3] or ""}
                # If there is a pending enroll action, perform enroll after login
                if st.session_state.get('next_enroll'):
                    enroll_student(st.session_state['student']['id'], st.session_state['next_enroll'])
                    st.success("You have been enrolled (simulated).")
                    st.session_state.pop('next_enroll', None)
                    st.session_state['page'] = "dashboard"
                else:
                    st.session_state['page'] = "dashboard"
                st.experimental_rerun()
            else:
                st.error("Incorrect email/password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def dashboard_page():
    # student dashboard: tabs for My Courses, Browse, Profile
    header()
    st.markdown("<div style='padding:12px;'>", unsafe_allow_html=True)
    st.markdown(f"<div class='small muted'>Welcome, {st.session_state['student'].get('email')}</div>", unsafe_allow_html=True)
    tabs = st.tabs(["My Courses", "Browse Courses", "Profile"])
    # My Courses
    with tabs[0]:
        st.markdown("<h3>My Courses</h3>", unsafe_allow_html=True)
        conn = get_conn(); c = conn.cursor()
        rows = c.execute("""SELECT cr.course_id, cr.title, cr.subtitle, cr.price
                            FROM courses cr
                            JOIN payments p ON p.course_id=cr.course_id
                            WHERE p.student_id=? AND p.status='Success'""", (st.session_state['student']['id'],)).fetchall()
        if not rows:
            st.info("You have not enrolled in any course yet.")
        for cid,title,subtitle,price in rows:
            st.markdown("<div class='course-card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex; justify-content:space-between;'><div><div style='font-weight:700'>{title}</div><div class='muted'>{subtitle or ''}</div></div><div style='font-weight:700'>{'Free' if not price else f'₹{int(price):,}'}</div></div>", unsafe_allow_html=True)
            # compute progress
            total = c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (cid,)).fetchone()[0]
            completed = c.execute("""SELECT COUNT(*) FROM lesson_progress lp
                                     JOIN lessons l ON l.lesson_id=lp.lesson_id
                                     WHERE lp.student_id=? AND l.course_id=? AND lp.viewed=1""", (st.session_state['student']['id'], cid)).fetchone()[0]
            pct = int((completed/total)*100) if total>0 else 0
            st.markdown(f"<div class='small muted'>{completed}/{total} lessons completed • {pct}%</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='progress-bar' style='margin-top:8px;'><div class='progress-fill' style='width:{pct}%;'></div></div>", unsafe_allow_html=True)
            if st.button(f"Open Course {cid}", key=f"open_{cid}"):
                st.session_state['view_course'] = cid
                st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        conn.close()
    # Browse
    with tabs[1]:
        home_page()  # reuse browse grid (shows header again)
    # Profile
    with tabs[2]:
        conn = get_conn(); c = conn.cursor()
        st.markdown("<h3>Profile</h3>", unsafe_allow_html=True)
        row = c.execute("SELECT email,name,sex,profession,institution,mobile,pic FROM students WHERE student_id=?", (st.session_state['student']['id'],)).fetchone()
        if row:
            email,name,sex,profession,institution,mobile,pic = row
            st.image(pic or LOGO, width=120)
            with st.form("edit_profile"):
                n = st.text_input("Name (optional)", value=name or "")
                s = st.selectbox("Sex", ["Prefer not to say","Male","Female"], index=0 if not sex else (0 if sex=="Prefer not to say" else (1 if sex=="Male" else 2)))
                prof = st.selectbox("Profession", ["Student","Working Professional"], index=0 if (profession!="Working Professional") else 1)
                inst = st.text_input("Institution (optional)", value=institution or "")
                mob = st.text_input("Mobile (optional)", value=mobile or "")
                if st.form_submit_button("Save"):
                    c.execute("UPDATE students SET name=?,sex=?,profession=?,institution=?,mobile=? WHERE student_id=?",
                              (n,s,prof,inst,mob,st.session_state['student']['id']))
                    conn.commit()
                    st.success("Profile updated.")
        conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

def course_view_from_dashboard():
    # show course preview for enrolled course
    cid = st.session_state.get('view_course')
    if cid:
        preview_course(cid)
        if st.button("Back to Dashboard"):
            st.session_state.pop('view_course', None)
            st.experimental_rerun()

# -----------------------
# Admin
# -----------------------
def admin_login_page():
    st.markdown("<div style='display:flex; justify-content:center; padding:24px;'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Admin Login</h3>", unsafe_allow_html=True)
    pwd = st.text_input("Admin password", type="password")
    if st.button("Enter Admin"):
        if pwd == ADMIN_PASSWORD:
            st.session_state['admin'] = True
            st.session_state['page'] = 'admin'
            st.experimental_rerun()
        else:
            st.error("Incorrect admin password")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def admin_dashboard():
    header()
    st.markdown("<h3>Admin — Manage Platform</h3>", unsafe_allow_html=True)
    tabs = st.tabs(["Courses", "Lessons", "Students"])
    # Courses
    with tabs[0]:
        st.markdown("<h4>Create Course</h4>", unsafe_allow_html=True)
        with st.form("create_course"):
            t = st.text_input("Title")
            sub = st.text_input("Subtitle")
            desc = st.text_area("Description")
            price = st.number_input("Price (INR)", min_value=0, step=100)
            banner = st.file_uploader("Banner image (optional)", type=["png","jpg","jpeg"])
            if st.form_submit_button("Create"):
                bpath = None
                if banner:
                    os.makedirs("banners", exist_ok=True)
                    bpath = os.path.join("banners", f"{int(time.time())}_{banner.name}")
                    with open(bpath, "wb") as f: f.write(banner.getbuffer())
                conn = get_conn(); c = conn.cursor()
                c.execute("INSERT INTO courses(title,subtitle,description,price,banner) VALUES(?,?,?,?,?)",(t,sub,desc,price,bpath))
                conn.commit(); conn.close()
                st.success("Course created")
        st.markdown("<hr>", unsafe_allow_html=True)
        conn = get_conn(); c = conn.cursor()
        rows = c.execute("SELECT course_id,title,subtitle,price FROM courses").fetchall()
        for cid,title,subtitle,price in rows:
            st.markdown("<div class='course-card'>", unsafe_allow_html=True)
            st.markdown(f"<div style='display:flex; justify-content:space-between;'><div><b>{title}</b><div class='muted'>{subtitle}</div></div><div>{'Free' if not price else f'₹{int(price):,}'}</div></div>", unsafe_allow_html=True)
            col1,col2 = st.columns([1,1])
            with col1:
                if st.button("Edit", key=f"edit_c_{cid}"):
                    st.session_state['admin_edit_course'] = cid
                    st.experimental_rerun()
            with col2:
                if st.button("Delete", key=f"del_c_{cid}"):
                    c.execute("DELETE FROM lessons WHERE course_id=?", (cid,))
                    c.execute("DELETE FROM courses WHERE course_id=?", (cid,))
                    conn.commit()
                    st.success("Deleted")
                    st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        conn.close()
    # Lessons
    with tabs[1]:
        st.markdown("<h4>Add Lesson</h4>", unsafe_allow_html=True)
        conn = get_conn(); c = conn.cursor()
        courses = c.execute("SELECT course_id,title FROM courses").fetchall()
        conn.close()
        if not courses:
            st.info("Create a course first.")
        else:
            with st.form("add_lesson"):
                opt = st.selectbox("Course",[f"{cid} - {t}" for cid,t in courses])
                cid = int(opt.split(" - ")[0])
                lt = st.text_input("Lesson title")
                ctype = st.selectbox("Type", ["text","video","pdf"])
                path = st.text_input("Content (text or URL)")
                if st.form_submit_button("Add Lesson"):
                    conn = get_conn(); c = conn.cursor()
                    c.execute("INSERT INTO lessons(course_id,title,content_type,content_path) VALUES(?,?,?,?)",(cid,lt,ctype,path))
                    conn.commit(); conn.close()
                    st.success("Lesson added")
        st.markdown("<hr>", unsafe_allow_html=True)
        conn = get_conn(); c = conn.cursor()
        rows = c.execute("SELECT l.lesson_id, l.title, l.content_type, cr.title FROM lessons l JOIN courses cr ON cr.course_id = l.course_id ORDER BY cr.course_id").fetchall()
        for lid,lt,ctype,ctitle in rows:
            st.markdown("<div class='course-lesson'>", unsafe_allow_html=True)
            st.markdown(f"<b>{ctitle} • {lt}</b> <div class='muted'>{ctype.upper()}</div>", unsafe_allow_html=True)
            col1,col2 = st.columns([1,1])
            with col1:
                if st.button("Edit", key=f"edit_l_{lid}"):
                    st.session_state['admin_edit_lesson'] = lid
                    st.experimental_rerun()
            with col2:
                if st.button("Delete", key=f"del_l_{lid}"):
                    c.execute("DELETE FROM lessons WHERE lesson_id=?", (lid,))
                    conn.commit(); st.success("Deleted"); st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        conn.close()
    # Students
    with tabs[2]:
        st.markdown("<h4>Students</h4>", unsafe_allow_html=True)
        conn = get_conn(); c = conn.cursor()
        rows = c.execute("SELECT student_id,email,name,sex,profession,institution,mobile FROM students").fetchall()
        conn.close()
        st.dataframe(rows)

# -----------------------
# Router
# -----------------------
def main():
    init_db(); seed_demo()
    # determine page via query param or session_state
    params = st.experimental_get_query_params()
    page = st.session_state.get('page') or params.get('page',['home'])[0]
    # Allow direct preview param
    if params.get('course_id'):
        st.session_state['view_course_param'] = int(params.get('course_id')[0])
    # top header and login link always handled inside page renderers

    # Page router
    if page == "home":
        home_page()
    elif page == "preview" or st.session_state.get('view_course_param'):
        cid = st.session_state.pop('view_course_param', None) or int(params.get('course_id',[0])[0])
        preview_course(cid)
    elif page == "signup":
        signup_page()
    elif page == "login":
        login_page()
    elif page == "dashboard" or ('student' in st.session_state and page == "dashboard"):
        if st.session_state.get('view_course'):
            course_view_from_dashboard()
        else:
            dashboard_page()
    elif page == "admin" or 'admin' in st.session_state:
        if 'admin' not in st.session_state:
            admin_login_page()
        else:
            admin_dashboard()
    else:
        home_page()

if __name__ == "__main__":
    main()
