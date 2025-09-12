# academy.py
import streamlit as st
import sqlite3
import os
import time
import csv
from fpdf import FPDF
from io import BytesIO

st.set_page_config("EinTrust Academy", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------
# Constants
# ---------------------------
LOGO = "https://raw.githubusercontent.com/eintrusts/CAP/main/EinTrust%20%20(2).png"
ADMIN_PASSWORD = "EinTrustAdmin123"
DB = "academy.db"

# ---------------------------
# DB init
# ---------------------------
conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute("""CREATE TABLE IF NOT EXISTS students(
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                sex TEXT,
                profession TEXT,
                institution TEXT,
                mobile TEXT,
                pic TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS courses(
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                subtitle TEXT,
                description TEXT,
                price REAL,
                banner_path TEXT
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

# ---------------------------
# Styling (dark theme only)
# ---------------------------
def set_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    :root{
      --bg:#0f1720;
      --card:#111827;
      --card-2:#131922;
      --muted:#9aa6b2;
      --text:#e6eef8;
      --accent:#ff9900;
      --glass: rgba(255,255,255,0.03);
    }
    html, body, [data-testid="stAppViewContainer"] { background: linear-gradient(180deg,#0b1220 0%, #0f1720 100%); color:var(--text); font-family: 'Inter', sans-serif;}
    .topbar {background:transparent}
    .card { background:var(--card); padding:16px; border-radius:12px; box-shadow: 0 6px 18px rgba(0,0,0,0.6);}
    .card-ghost { background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:16px; border-radius:12px;}
    .muted { color:var(--muted); font-size:0.95rem; }
    .brand { color:var(--accent); font-weight:700; }
    .btn { background:var(--accent); color:#000; padding:8px 14px; border-radius:10px; font-weight:700; border:none;}
    .btn:hover { opacity:0.95; transform: translateY(-2px); }
    .course-grid { display:grid; grid-template-columns: repeat(auto-fill,minmax(300px,1fr)); gap:18px; }
    .course-card { background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02)); border-radius:12px; padding:14px; transition: transform .12s ease, box-shadow .12s ease; }
    .course-card:hover { transform: translateY(-6px); box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
    .small { font-size:0.9rem; color:var(--muted); }
    .padded { padding:12px; }
    .sidebar { background: transparent; padding-top:10px; }
    hr { border-color: rgba(255,255,255,0.06); margin:12px 0 18px 0; }
    .center { display:flex; justify-content:center; align-items:center; }
    .auth-card { width:420px; background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); padding:22px; border-radius:12px; }
    .course-banner { width:100%; height:180px; border-radius:10px; object-fit:cover; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_css()

# ---------------------------
# Utilities
# ---------------------------
def inr(v):
    try:
        v = int(v)
        s = f"₹{v:,}"
    except:
        s = f"₹{v}"
    return s

def save_uploaded_file(uploaded, folder):
    if uploaded is None:
        return None
    os.makedirs(folder, exist_ok=True)
    fname = f"{int(time.time())}_{uploaded.name}"
    path = os.path.join(folder, fname)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path

def enroll_lessons(student_id, course_id):
    rows = c.execute("SELECT lesson_id FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    for (lid,) in rows:
        c.execute("INSERT OR IGNORE INTO lesson_progress(student_id, lesson_id, viewed) VALUES(?,?,0)", (student_id, lid))
    conn.commit()

def mark_viewed(student_id, lesson_id):
    c.execute("INSERT OR REPLACE INTO lesson_progress(student_id, lesson_id, viewed) VALUES(?,?,1)", (student_id, lesson_id))
    conn.commit()

def generate_certificate(student_name, course_title, student_id, course_id):
    os.makedirs("certificates", exist_ok=True)
    fname = f"cert_{student_id}_{course_id}.pdf"
    path = os.path.join("certificates", fname)
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 28)
    pdf.set_y(40)
    pdf.cell(0, 12, "Certificate of Completion", ln=True, align="C")
    pdf.set_font("Arial", "", 16)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"This certifies that {student_name} has successfully completed the course \"{course_title}\".", align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Issued by EinTrust Academy • {time.strftime('%d %b %Y')}", ln=True, align="C")
    pdf.output(path)
    return path

# ---------------------------
# Auth components
# ---------------------------
def signup_panel():
    st.markdown("<div class='auth-card card'>", unsafe_allow_html=True)
    st.markdown("<h3>Create an account</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small muted'>Enter details to register</div>", unsafe_allow_html=True)
    with st.form("signup"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Set password", type="password")
        sex = st.selectbox("Sex", ["Prefer not to say", "Male", "Female"])
        profession = st.selectbox("Profession", ["Student", "Working Professional"])
        institution = st.text_input("Institution (optional)")
        mobile = st.text_input("Mobile")
        pic = st.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Create account")
        if submitted:
            if not name or not email or not password:
                st.error("Please fill required fields.")
            else:
                pic_path = save_uploaded_file(pic, "profile_pics") if pic else None
                try:
                    c.execute("INSERT INTO students(name,email,password,sex,profession,institution,mobile,pic) VALUES(?,?,?,?,?,?,?,?)",
                              (name, email, password, sex, profession, institution, mobile, pic_path))
                    conn.commit()
                    st.success("Account created. Please log in.")
                except Exception:
                    st.error("Email already registered.")
    st.markdown("</div>", unsafe_allow_html=True)

def login_panel():
    st.markdown("<div class='auth-card card'>", unsafe_allow_html=True)
    st.markdown("<h3>Welcome back</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small muted'>Login to continue</div>", unsafe_allow_html=True)
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="btn_login"):
        if not email or not password:
            st.error("Enter both fields.")
        else:
            row = c.execute("SELECT student_id, name, password FROM students WHERE email=?", (email,)).fetchone()
            if row and row[2] == password:
                st.session_state['student'] = {"id": row[0], "name": row[1], "email": email}
                st.experimental_rerun()
            else:
                st.error("Incorrect email/password.")
    if st.button("Forgot password?"):
        st.info("Simulated reset link: (for testing) shown below")
        token = f"RESET-{int(time.time())}"
        st.success(f"/reset-password?token={token}&email={email}")
    st.markdown("</div>", unsafe_allow_html=True)

def admin_login_panel():
    st.markdown("<div class='auth-card card'>", unsafe_allow_html=True)
    st.markdown("<h3>Admin sign-in</h3>", unsafe_allow_html=True)
    pwd = st.text_input("Admin password", type="password")
    if st.button("Enter as Admin"):
        if pwd == ADMIN_PASSWORD:
            st.session_state['admin'] = True
            st.experimental_rerun()
        else:
            st.error("Incorrect admin password")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Main layout for logged-out view
# ---------------------------
def landing_auth():
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<img src='{LOGO}' width='160'/>", unsafe_allow_html=True)
        st.markdown("<h1 style='margin-top:6px;'>EinTrust Academy</h1>", unsafe_allow_html=True)
        st.markdown("<div class='muted'>Professional courses on Sustainability, ESG and Compliance — learn at your own pace.</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='small muted'>Already have an account? Login on the right. Admins sign in below.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        login_panel()
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        signup_panel()
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        admin_login_panel()

# ---------------------------
# Sidebar & navigation for student
# ---------------------------
def student_sidebar():
    st.sidebar.markdown("<div style='padding:12px; border-radius:8px;' class='card-ghost'>", unsafe_allow_html=True)
    st.sidebar.image(LOGO, width=120)
    st.sidebar.markdown(f"<div style='margin-top:8px; font-weight:700;'>{st.session_state['student']['name']}</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='small muted'>Student</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    nav = st.sidebar.radio("", ["Browse Courses", "My Courses", "Progress & Certificates", "Profile"], index=0)
    if st.sidebar.button("Logout"):
        del st.session_state['student']
        st.experimental_rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    return nav

# ---------------------------
# Student pages
# ---------------------------
def page_browse_courses():
    st.markdown("<div class='card'><h2>Browse Courses</h2><div class='small muted'>Explore all published courses</div></div>", unsafe_allow_html=True)
    courses = c.execute("SELECT course_id, title, subtitle, description, price, banner_path FROM courses ORDER BY course_id DESC").fetchall()
    if not courses:
        st.info("No courses published yet.")
        return
    st.markdown("<div class='course-grid'>", unsafe_allow_html=True)
    for course_id, title, subtitle, desc, price, banner in courses:
        banner_html = f"<img src='{banner}' class='course-banner'/>" if banner else ""
        card = f"""
        <div class='course-card'>
          {banner_html}
          <div style='margin-top:10px; font-weight:700; font-size:1.05rem;'>{title}</div>
          <div class='small muted' style='margin:6px 0;'>{subtitle or desc[:100]}</div>
          <div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px;'>
            <div style='font-weight:700;'>{inr(price or 0)}</div>
            <div><form></form></div>
          </div>
        </div>
        """
        st.markdown(card, unsafe_allow_html=True)
        # Course preview button
        if st.button(f"View Course — {title}", key=f"view_{course_id}"):
            st.session_state['view_course'] = course_id
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def page_my_courses():
    st.markdown("<div class='card'><h2>My Courses</h2><div class='small muted'>Courses you are enrolled in</div></div>", unsafe_allow_html=True)
    rows = c.execute("""SELECT crs.course_id, crs.title, crs.subtitle, crs.description, crs.price
                        FROM courses crs
                        JOIN payments p ON p.course_id = crs.course_id
                        WHERE p.student_id=? AND p.status='Success'""", (st.session_state['student']['id'],)).fetchall()
    if not rows:
        st.info("You haven't enrolled in any courses yet.")
        return
    for course_id, title, subtitle, description, price in rows:
        st.markdown("<div class='card' style='margin-bottom:10px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center;'><div><div style='font-weight:700'>{title}</div><div class='small muted'>{subtitle or description[:120]}</div></div><div>{inr(price)}</div></div>", unsafe_allow_html=True)
        if st.button(f"Continue — {course_id}", key=f"cont_{course_id}"):
            st.session_state['view_course'] = course_id
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def page_progress_certificates():
    st.markdown("<div class='card'><h2>Progress & Certificates</h2><div class='small muted'>Overview of your learning progress</div></div>", unsafe_allow_html=True)
    enrolled = c.execute("SELECT course_id FROM payments WHERE student_id=? AND status='Success'", (st.session_state['student']['id'],)).fetchall()
    if not enrolled:
        st.info("You have no enrolled courses.")
        return
    for (course_id,) in enrolled:
        title = c.execute("SELECT title FROM courses WHERE course_id=?", (course_id,)).fetchone()[0]
        total = c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,)).fetchone()[0]
        completed = c.execute("""SELECT COUNT(*) FROM lesson_progress WHERE student_id=? AND lesson_id IN
                                 (SELECT lesson_id FROM lessons WHERE course_id=?) AND viewed=1""", (st.session_state['student']['id'], course_id)).fetchone()[0]
        pct = int((completed / total) * 100) if total>0 else 0
        st.markdown("<div class='card' style='margin-bottom:12px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:700'>{title}</div>", unsafe_allow_html=True)
        st.progress(pct)
        st.markdown(f"<div class='small muted'>{completed}/{total} lessons completed • {pct}%</div>", unsafe_allow_html=True)
        # certificate
        cert = c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (st.session_state['student']['id'], course_id)).fetchone()
        if cert and cert[0] and os.path.exists(cert[0]):
            with open(cert[0],"rb") as f:
                st.download_button("Download Certificate", data=f, file_name=os.path.basename(cert[0]), key=f"dl_{course_id}")
        st.markdown("</div>", unsafe_allow_html=True)

def page_profile():
    st.markdown("<div class='card'><h2>Profile</h2></div>", unsafe_allow_html=True)
    row = c.execute("SELECT name,email,sex,profession,institution,mobile,pic FROM students WHERE student_id=?", (st.session_state['student']['id'],)).fetchone()
    if not row:
        st.error("Profile not found.")
        return
    name, email, sex, profession, institution, mobile, pic = row
    st.image(pic if pic else LOGO, width=120)
    with st.form("edit_profile"):
        n = st.text_input("Full name", value=name)
        s = st.selectbox("Sex", ["Prefer not to say","Male","Female"], index=["Prefer not to say","Male","Female"].index(sex) if sex in ["Prefer not to say","Male","Female"] else 0)
        prof = st.selectbox("Profession", ["Student","Working Professional"], index=0 if profession!="Working Professional" else 1)
        inst = st.text_input("Institution", value=institution or "")
        mob = st.text_input("Mobile", value=mobile or "")
        pic_up = st.file_uploader("Change profile picture", type=["png","jpg","jpeg"])
        submit = st.form_submit_button("Save profile")
        if submit:
            pic_path = save_uploaded_file(pic_up, "profile_pics") if pic_up else pic
            c.execute("UPDATE students SET name=?, sex=?, profession=?, institution=?, mobile=?, pic=? WHERE student_id=?",
                      (n, s, prof, inst, mob, pic_path, st.session_state['student']['id']))
            conn.commit()
            st.success("Profile updated.")
            st.session_state['student']['name'] = n
            st.experimental_rerun()

# ---------------------------
# Course preview page
# ---------------------------
def course_preview(course_id):
    row = c.execute("SELECT course_id, title, subtitle, description, price, banner_path FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not row:
        st.error("Course not found.")
        return
    cid, title, subtitle, description, price, banner = row
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if banner and os.path.exists(banner):
        st.image(banner, use_column_width=True, caption=None)
    st.markdown(f"<h2 style='margin-top:8px'>{title}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='small muted'>{subtitle or ''}</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; gap:18px;'>", unsafe_allow_html=True)
    st.markdown(f"<div style='flex:1;'>{description}</div>", unsafe_allow_html=True)
    enrolled = None
    if 'student' in st.session_state:
        enrolled = c.execute("SELECT status FROM payments WHERE student_id=? AND course_id=?", (st.session_state['student']['id'], cid)).fetchone()
    right_html = f"<div style='min-width:220px; padding:12px; background:var(--card); border-radius:10px;'>"
    right_html += f"<div style='font-weight:700; font-size:1.1rem'>{inr(price)}</div>"
    right_html += f"<div class='small muted' style='margin-top:6px;'>What you'll get: access to lessons, certificate on completion.</div>"
    right_html += "</div>"
    st.markdown(right_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Lessons listing
    st.markdown("<hr>", unsafe_allow_html=True)
    lessons = c.execute("SELECT lesson_id, title, content_type FROM lessons WHERE course_id=? ORDER BY lesson_id", (cid,)).fetchall()
    for lid, ltitle, ltype in lessons:
        locked = (enrolled is None)
        status = ""
        if enrolled:
            viewed = c.execute("SELECT viewed FROM lesson_progress WHERE student_id=? AND lesson_id=?", (st.session_state['student']['id'], lid)).fetchone()
            status = " • Completed" if viewed and viewed[0]==1 else ""
        st.markdown(f"<div class='course-card' style='padding:12px; margin-bottom:8px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between;'><div style='font-weight:600'>{ltitle}</div><div class='small muted'>{ltype.upper()}{status}</div></div>", unsafe_allow_html=True)
        if locked:
            st.markdown("<div class='small muted'>Enroll to access this lesson</div>", unsafe_allow_html=True)
        else:
            if st.button(f"Open Lesson {lid}", key=f"open_{lid}"):
                st.session_state['open_lesson'] = lid
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Enroll / Continue area
    if 'student' in st.session_state:
        if enrolled:
            st.success("You are enrolled in this course.")
            if st.button("Continue course"):
                st.session_state['open_course'] = cid
                st.experimental_rerun()
        else:
            if st.button("Enroll (Simulate Payment)"):
                c.execute("INSERT OR IGNORE INTO payments(student_id, course_id, status) VALUES(?,?,?)", (st.session_state['student']['id'], cid, 'Success'))
                conn.commit()
                enroll_lessons(st.session_state['student']['id'], cid)
                st.success("Enrolled — payments simulated.")
                st.experimental_rerun()
    else:
        st.info("Login to enroll in this course.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Lesson viewer
# ---------------------------
def open_lesson(lesson_id):
    row = c.execute("SELECT lesson_id, course_id, title, content_type, content_path FROM lessons WHERE lesson_id=?", (lesson_id,)).fetchone()
    if not row:
        st.error("Lesson not found.")
        return
    lid, cid, title, ctype, cpath = row
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    # course title
    course_title = c.execute("SELECT title FROM courses WHERE course_id=?", (cid,)).fetchone()[0]
    st.markdown(f"<div style='font-weight:700'>{course_title} • {title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='small muted'>Type: {ctype.upper()}</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    if ctype == "video":
        try:
            st.video(cpath)
        except:
            st.write("Video URL could not be loaded.")
    elif ctype == "pdf":
        st.write("PDF / Doc link:", cpath)
    else:
        st.write(cpath)
    # Mark complete
    if 'student' in st.session_state:
        viewed = c.execute("SELECT viewed FROM lesson_progress WHERE student_id=? AND lesson_id=?", (st.session_state['student']['id'], lid)).fetchone()
        if viewed and viewed[0]==1:
            st.success("Lesson completed")
        else:
            if st.button("Mark as complete"):
                mark_viewed(st.session_state['student']['id'], lid)
                st.success("Marked complete — progress updated.")
                st.experimental_rerun()
    else:
        st.info("Login to track progress.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Admin pages
# ---------------------------
def admin_sidebar():
    st.sidebar.markdown("<div class='card-ghost' style='padding:12px; border-radius:10px;'>", unsafe_allow_html=True)
    st.sidebar.markdown("<div style='font-weight:700;'>Admin</div>", unsafe_allow_html=True)
    choice = st.sidebar.radio("", ["Manage Courses", "Manage Lessons", "Manage Students"], index=0)
    if st.sidebar.button("Logout Admin"):
        del st.session_state['admin']
        st.experimental_rerun()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    return choice

def admin_manage_courses():
    st.markdown("<div class='card'><h3>Courses</h3></div>", unsafe_allow_html=True)
    rows = c.execute("SELECT course_id, title, subtitle, price FROM courses").fetchall()
    if not rows:
        st.info("No courses — create one below.")
    for course_id, title, subtitle, price in rows:
        st.markdown("<div class='card' style='margin-bottom:10px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center;'><div><div style='font-weight:700'>{title}</div><div class='small muted'>{subtitle or ''}</div></div><div style='text-align:right'>{inr(price)}</div></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            if st.button("Edit", key=f"edit_c_{course_id}"):
                edit_course(course_id)
        with col2:
            if st.button("Delete", key=f"del_c_{course_id}"):
                c.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
                c.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
                conn.commit()
                st.success("Course deleted")
                st.experimental_rerun()
        with col3:
            if st.button("View Lessons", key=f"view_l_{course_id}"):
                st.session_state['admin_view_course'] = course_id
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h4>Create new course</h4>", unsafe_allow_html=True)
    with st.form("create_course"):
        t = st.text_input("Title")
        stl = st.text_input("Subtitle")
        desc = st.text_area("Description")
        price = st.number_input("Price (INR)", min_value=0)
        banner = st.file_uploader("Banner image (optional)", type=["png","jpg","jpeg"])
        if st.form_submit_button("Create course"):
            banner_path = save_uploaded_file(banner, "banners") if banner else None
            c.execute("INSERT INTO courses(title, subtitle, description, price, banner_path) VALUES(?,?,?,?,?)",
                      (t, stl, desc, price, banner_path))
            conn.commit()
            st.success("Course created")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def edit_course(course_id):
    row = c.execute("SELECT title, subtitle, description, price, banner_path FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not row:
        st.error("Course not found")
        return
    title, subtitle, desc, price, banner = row
    st.markdown("<div class='card'><h4>Edit course</h4>", unsafe_allow_html=True)
    with st.form(f"edit_course_{course_id}"):
        t = st.text_input("Title", value=title)
        stl = st.text_input("Subtitle", value=subtitle)
        d = st.text_area("Description", value=desc)
        p = st.number_input("Price (INR)", min_value=0, value=int(price or 0))
        banner_up = st.file_uploader("Replace banner (optional)", type=["png","jpg","jpeg"])
        if st.form_submit_button("Save changes"):
            banner_path = save_uploaded_file(banner_up, "banners") if banner_up else banner
            c.execute("UPDATE courses SET title=?, subtitle=?, description=?, price=?, banner_path=? WHERE course_id=?",
                      (t, stl, d, p, banner_path, course_id))
            conn.commit()
            st.success("Updated")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def admin_manage_lessons():
    st.markdown("<div class='card'><h3>Lessons</h3></div>", unsafe_allow_html=True)
    rows = c.execute("""SELECT l.lesson_id, l.title, l.content_type, crs.title, crs.course_id
                        FROM lessons l JOIN courses crs ON crs.course_id=l.course_id
                        ORDER BY crs.course_id, l.lesson_id""").fetchall()
    if not rows:
        st.info("No lessons yet.")
    current_course = None
    for lid, ltitle, ltype, ctitle, cid in rows:
        # group by course
        if current_course != cid:
            st.markdown(f"<div class='card' style='background:transparent; box-shadow:none; margin-top:8px;'><div style='font-weight:700'>{ctitle}</div></div>", unsafe_allow_html=True)
            current_course = cid
        st.markdown("<div class='card' style='margin-bottom:8px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center;'><div>{ltitle}</div><div class='small muted'>{ltype.upper()}</div></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Edit", key=f"edit_l_{lid}"):
                edit_lesson(lid)
        with col2:
            if st.button("Delete", key=f"del_l_{lid}"):
                c.execute("DELETE FROM lessons WHERE lesson_id=?", (lid,))
                conn.commit()
                st.success("Lesson removed")
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h4>Add Lesson</h4>", unsafe_allow_html=True)
    courses = c.execute("SELECT course_id, title FROM courses").fetchall()
    if not courses:
        st.info("Create a course first.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    with st.form("add_lesson"):
        sel = st.selectbox("Course", [f"{cid} - {t}" for cid,t in courses])
        cid = int(sel.split(" - ")[0])
        t = st.text_input("Lesson title")
        ltype = st.selectbox("Type", ["text","video","pdf"])
        path = st.text_input("Content (text or URL)")
        if st.form_submit_button("Add"):
            if not t or not path:
                st.error("Title and content required.")
            else:
                c.execute("INSERT INTO lessons(course_id, title, content_type, content_path) VALUES(?,?,?,?)", (cid, t, ltype, path))
                conn.commit()
                st.success("Lesson added")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def edit_lesson(lesson_id):
    row = c.execute("SELECT course_id, title, content_type, content_path FROM lessons WHERE lesson_id=?", (lesson_id,)).fetchone()
    if not row:
        st.error("Lesson not found")
        return
    course_id, title, ctype, path = row
    st.markdown("<div class='card'><h4>Edit lesson</h4>", unsafe_allow_html=True)
    courses = c.execute("SELECT course_id, title FROM courses").fetchall()
    with st.form(f"edit_l_{lesson_id}"):
        sel = st.selectbox("Course", [f"{cid} - {t}" for cid,t in courses], index=[i for i,(cid,t) in enumerate(courses) if cid==course_id][0] if courses else 0)
        new_cid = int(sel.split(" - ")[0])
        nt = st.text_input("Title", value=title)
        ntype = st.selectbox("Type", ["text","video","pdf"], index=["text","video","pdf"].index(ctype))
        npath = st.text_input("Content", value=path)
        if st.form_submit_button("Save"):
            c.execute("UPDATE lessons SET course_id=?, title=?, content_type=?, content_path=? WHERE lesson_id=?",
                      (new_cid, nt, ntype, npath, lesson_id))
            conn.commit()
            st.success("Lesson updated")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def admin_manage_students():
    st.markdown("<div class='card'><h3>Students</h3></div>", unsafe_allow_html=True)
    rows = c.execute("SELECT student_id, name, email, sex, profession, institution, mobile FROM students").fetchall()
    if not rows:
        st.info("No students registered yet.")
        return
    st.dataframe(rows, use_container_width=True)
    if st.button("Export CSV"):
        buf = BytesIO()
        w = csv.writer(buf)
        w.writerow(["student_id","name","email","sex","profession","institution","mobile"])
        for r in rows:
            w.writerow(r)
        st.download_button("Download CSV", data=buf.getvalue(), file_name="students.csv")
    st.markdown("<div class='small muted'>Passwords are not shown for security.</div>", unsafe_allow_html=True)

# ---------------------------
# Helper: save uploaded
# ---------------------------
def save_uploaded_file(uploaded, folder):
    if uploaded is None: return None
    os.makedirs(folder, exist_ok=True)
    fname = f"{int(time.time())}_{uploaded.name}"
    path = os.path.join(folder, fname)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path

# ---------------------------
# App: main
# ---------------------------
def main():
    st.markdown("<div style='max-width:1200px; margin:auto;'>", unsafe_allow_html=True)

    # LOGOUT handling: ensure view_course / open_lesson state is reset when not applicable
    if 'view_course' not in st.session_state:
        st.session_state['view_course'] = None
    if 'open_lesson' not in st.session_state:
        st.session_state['open_lesson'] = None
    if 'open_course' not in st.session_state:
        st.session_state['open_course'] = None
    if 'admin_view_course' not in st.session_state:
        st.session_state['admin_view_course'] = None

    # Not authenticated
    if 'student' not in st.session_state and 'admin' not in st.session_state:
        landing_auth()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Admin area
    if 'admin' in st.session_state:
        choice = admin_sidebar()
        if choice == "Manage Courses":
            admin_manage_courses()
            # show lessons inline for selected course
            if st.session_state.get('admin_view_course'):
                cid = st.session_state['admin_view_course']
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(f"<div class='card'><h4>Lessons for selected course</h4></div>", unsafe_allow_html=True)
                rows = c.execute("SELECT lesson_id,title,content_type,content_path FROM lessons WHERE course_id=? ORDER BY lesson_id", (cid,)).fetchall()
                if not rows:
                    st.info("No lessons in this course.")
                for lid, t, ct, cp in rows:
                    st.markdown("<div class='card' style='margin-bottom:8px;'>", unsafe_allow_html=True)
                    st.markdown(f"<div style='display:flex; justify-content:space-between;'><div style='font-weight:700'>{t}</div><div class='small muted'>{ct.upper()}</div></div>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1,1])
                    with col1:
                        if st.button("Edit", key=f"admin_edit_l_{lid}"):
                            edit_lesson(lid)
                    with col2:
                        if st.button("Delete", key=f"admin_del_l_{lid}"):
                            c.execute("DELETE FROM lessons WHERE lesson_id=?", (lid,))
                            conn.commit()
                            st.success("Deleted")
                            st.experimental_rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        elif choice == "Manage Lessons":
            admin_manage_lessons()
        elif choice == "Manage Students":
            admin_manage_students()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Student area
    nav = student_sidebar()
    # If a course preview is selected
    if st.session_state.get('view_course'):
        course_preview(st.session_state['view_course'])
        # allow going back
        if st.button("Back to Browse"):
            st.session_state['view_course'] = None
            st.experimental_rerun()
        return

    # If open lesson selected
    if st.session_state.get('open_lesson'):
        open_lesson(st.session_state['open_lesson'])
        if st.button("Back to course"):
            st.session_state['open_lesson'] = None
            st.experimental_rerun()
        return

    # If open_course selected (continue)
    if st.session_state.get('open_course'):
        course_preview(st.session_state['open_course'])
        if st.button("Back to My Courses"):
            st.session_state['open_course'] = None
            st.experimental_rerun()
        return

    # Normal navigation
    if nav == "Browse Courses":
        page_browse_courses()
    elif nav == "My Courses":
        page_my_courses()
    elif nav == "Progress & Certificates":
        page_progress_certificates()
    elif nav == "Profile":
        page_profile()

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
