# academy.py
import streamlit as st
import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

# ----------------------- Config -----------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")
LOGO_URL = "https://github.com/eintrusts/CAP/blob/main/EinTrust%20%20(2).png?raw=true"

DB_FILE = "academy.db"
UPLOAD_DIR = "uploads"
BANNERS_DIR = os.path.join(UPLOAD_DIR, "banners")
LESSONS_DIR = os.path.join(UPLOAD_DIR, "lessons")
PROFILE_DIR = os.path.join(UPLOAD_DIR, "profiles")
CERT_DIR = "certificates"
for d in (UPLOAD_DIR, BANNERS_DIR, LESSONS_DIR, PROFILE_DIR, CERT_DIR):
    os.makedirs(d, exist_ok=True)

ADMIN_DEFAULT_PASSWORD = "admin123"  # change before production

# ----------------------- DB helpers -----------------------
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS students (
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
    c.execute("""CREATE TABLE IF NOT EXISTS admin (
                    admin_id INTEGER PRIMARY KEY,
                    password TEXT NOT NULL
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    subtitle TEXT,
                    description TEXT,
                    price REAL DEFAULT 0,
                    category TEXT,
                    banner_path TEXT,
                    created_on TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    title TEXT,
                    lesson_type TEXT,
                    content_path TEXT,
                    duration_seconds INTEGER DEFAULT 0,
                    "order" INTEGER DEFAULT 0,
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS enrollments (
                    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id INTEGER,
                    paid INTEGER DEFAULT 0,
                    enrolled_on TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS progress (
                    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    lesson_id INTEGER,
                    completed INTEGER DEFAULT 0,
                    completed_on TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(lesson_id) REFERENCES lessons(lesson_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS certificates (
                    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id INTEGER,
                    cert_file TEXT,
                    generated_on TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reset_tokens (
                    token TEXT PRIMARY KEY,
                    student_id INTEGER,
                    created_on TEXT,
                    used INTEGER DEFAULT 0,
                    FOREIGN KEY(student_id) REFERENCES students(student_id)
                )""")
    # ensure admin exists with hashed default pw
    c.execute("SELECT COUNT(*) FROM admin")
    if c.fetchone()[0] == 0:
        hashed = hashlib.sha256(ADMIN_DEFAULT_PASSWORD.encode()).hexdigest()
        c.execute("INSERT INTO admin (admin_id, password) VALUES (?,?)", (1, hashed))
    conn.commit()
    conn.close()

create_tables()

# ----------------------- Utilities -----------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_pw(pw: str, hashed: str) -> bool:
    return hash_pw(pw) == hashed

def inr(x):
    try:
        return f"₹{float(x):,.2f}"
    except:
        return f"₹{x}"

def save_upload(uploaded, folder):
    if uploaded is None:
        return None
    os.makedirs(folder, exist_ok=True)
    name = f"{secrets.token_hex(8)}_{uploaded.name}"
    path = os.path.join(folder, name)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path

def generate_certificate(student_name, course_title, student_id, course_id):
    ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    fname = f"EinTrust_{student_name.replace(' ','_')}_{course_title.replace(' ','_')}_{ts}.txt"
    path = os.path.join(CERT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write("EinTrust Academy\n")
        f.write("Certificate of Completion\n\n")
        f.write(f"This certifies that {student_name}\n")
        f.write(f"has successfully completed the course: {course_title}\n")
        f.write(f"Date (UTC): {datetime.utcnow().strftime('%Y-%m-%d')}\n\n")
        f.write("EinTrust Academy\n")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO certificates (student_id, course_id, cert_file, generated_on) VALUES (?,?,?,?)",
                (student_id, course_id, path, datetime.utcnow().isoformat()))
    conn.commit(); conn.close()
    return path

# DB convenience wrappers
def db_exec(query, params=()):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(query, params); conn.commit(); conn.close()

def db_fetchall(query, params=()):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(query, params); rows = cur.fetchall(); conn.close(); return rows

def db_fetchone(query, params=()):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(query, params); row = cur.fetchone(); conn.close(); return row

# ----------------------- Session defaults -----------------------
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

# ----------------------- CSS & Header -----------------------
st.markdown("""
<style>
body {background:#0b0c0d; color:#e6eef2;}
.topbar {display:flex; align-items:center; justify-content:space-between; padding:14px 20px; background:#0f1112; border-bottom:1px solid #222;}
.logo {display:flex; align-items:center; gap:12px;}
.logo img {height:44px;}
.logo h1 {margin:0; font-size:20px; color:#00d4ff;}
.search {width:420px; padding:8px; border-radius:8px; background:#111315; color:#fff; border:1px solid #333;}
.card {background:#121416; padding:14px; border-radius:10px; margin-bottom:12px; border:1px solid #1f2326;}
.card:hover {box-shadow: 0 6px 18px rgba(0,0,0,0.6); transform: translateY(-2px);}
.small {color:#9aa7b2; font-size:13px;}
.admin-fab {position:fixed; right:18px; bottom:18px; background:#ff4757; color:white; padding:10px 12px; border-radius:8px; font-weight:700;}
.footer {text-align:center; padding:12px; color:#7f8b91;}
</style>
""", unsafe_allow_html=True)

# Header with logo (URL). If not reachable, shows text name.
try:
    st.markdown(f"""
    <div class="topbar">
        <div class="logo">
            <img src="{LOGO_URL}" alt="logo" />
            <h1>EinTrust Academy</h1>
        </div>
        <div style="flex:1; text-align:center;">
            <input class="search" placeholder="Search for anything..." id="searchbox" />
        </div>
        <div style="text-align:right;">
            <!-- Login / name shown in page content area to avoid duplicate input IDs -->
        </div>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    st.markdown('<div class="topbar"><div class="logo"><h1>EinTrust Academy</h1></div></div>', unsafe_allow_html=True)

# ----------------------- Pages Implementation -----------------------

# ---- HOME / COURSES ----
def page_home():
    st.session_state["page"]="home"
    st.write("")  # spacing
    st.markdown("## Browse Courses")
    # dynamic categories
    cats = [r[0] for r in db_fetchall("SELECT DISTINCT category FROM courses WHERE category IS NOT NULL AND category<>''")]
    categories = ["All"] + cats
    selected_cat = st.selectbox("Category", categories, key="home_cat")
    search_q = st.text_input("Search", key="home_search_input")
    # build query
    sql = "SELECT course_id,title,subtitle,description,price,category,banner_path FROM courses"
    params=[]
    filters=[]
    if selected_cat and selected_cat != "All":
        filters.append("category=?"); params.append(selected_cat)
    if search_q:
        filters.append("LOWER(title) LIKE ?"); params.append(f"%{search_q.lower()}%")
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY course_id DESC"
    try:
        courses = db_fetchall(sql, tuple(params))
    except Exception as e:
        st.error("Error loading courses."); st.exception(e); courses=[]
    if not courses:
        st.info("No courses available. Admin can add courses from Admin panel.")
        return
    cols = st.columns(2)
    i=0
    for course in courses:
        cid, title, subtitle, desc, price, cat, banner = course
        with cols[i%2]:
            st.markdown(f"<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"### {title}")
            st.markdown(f"<div class='small'>{subtitle or ''} • {cat or ''}</div>", unsafe_allow_html=True)
            st.write(desc or "")
            st.markdown(f"**{inr(price)}**")
            # Enroll as a tab-style selection (use button but unique key)
            if st.button("Preview / Enroll", key=f"preview_{cid}"):
                st.session_state["selected_course"]=cid
                st.session_state["page"]="course_preview"
            st.markdown("</div>", unsafe_allow_html=True)
        i+=1

# ---- COURSE PREVIEW ----
def page_course_preview():
    cid = st.session_state.get("selected_course")
    if not cid:
        st.info("No course selected.")
        return
    row = db_fetchone("SELECT title,subtitle,description,price,category,banner_path FROM courses WHERE course_id=?", (cid,))
    if not row:
        st.error("Course not found.")
        return
    title, subtitle, description, price, category, banner = row
    st.markdown(f"<div class='card'><h2>{title}</h2><div class='small'>{subtitle or ''} • {category or ''}</div><p>{description or ''}</p><b>{inr(price)}</b></div>", unsafe_allow_html=True)
    lessons = db_fetchall("SELECT lesson_id,title,lesson_type,duration_seconds FROM lessons WHERE course_id=? ORDER BY \"order\", lesson_id", (cid,))
    st.markdown("### Lessons")
    for lid, ltitle, ltype, dur in lessons:
        st.markdown(f"- {ltitle} ({ltype}) — <span class='small'>{dur or 0} sec</span>", unsafe_allow_html=True)
    # Enroll flow
    sid = st.session_state.get("student_id")
    enrolled = False
    if sid:
        enrolled = bool(db_fetchone("SELECT enrollment_id FROM enrollments WHERE student_id=? AND course_id=?", (sid, cid)))
    if not sid:
        if st.button("Enroll (Create profile / Login)", key=f"enroll_req_{cid}"):
            st.session_state["after_enroll_course"]=cid
            st.session_state["page"]="signup"
    else:
        if not enrolled:
            if price and price>0:
                if st.button("Pay & Enroll (Simulated)", key=f"pay_{cid}"):
                    st.session_state["payment_course"]=cid
                    st.session_state["page"]="payment"
            else:
                if st.button("Enroll (Free)", key=f"enroll_free_{cid}"):
                    db_exec("INSERT INTO enrollments (student_id,course_id,paid,enrolled_on) VALUES (?,?,?,?)", (sid, cid, 0, datetime.utcnow().isoformat()))
                    st.success("Enrolled. Opening course lessons...")
                    st.session_state["page"]="course_player"
        else:
            if st.button("Open course lessons", key=f"open_{cid}"):
                st.session_state["page"]="course_player"

# ---- PAYMENT (simulated) ----
def page_payment():
    cid = st.session_state.get("payment_course")
    if not cid:
        st.error("No course selected for payment.")
        return
    row = db_fetchone("SELECT title,price FROM courses WHERE course_id=?", (cid,))
    if not row:
        st.error("Course not found.")
        return
    title, price = row
    st.header(f"Payment for: {title}")
    st.write(f"Amount: {inr(price)} (simulated)")
    st.info("Payment gateway placeholder. Click simulate to complete transaction.")
    if st.button("Simulate Successful Payment", key=f"simulate_pay_{cid}"):
        sid = st.session_state.get("student_id")
        if not sid:
            st.error("You must be logged in to pay.")
            return
        db_exec("INSERT INTO enrollments (student_id,course_id,paid,enrolled_on) VALUES (?,?,?,?)", (sid, cid, 1, datetime.utcnow().isoformat()))
        st.success("Payment simulated and enrollment recorded.")
        st.session_state["page"]="course_player"

# ---- COURSE PLAYER ----
def page_course_player():
    cid = st.session_state.get("selected_course") or st.session_state.get("payment_course")
    sid = st.session_state.get("student_id")
    if not cid:
        st.info("No course selected.")
        return
    if not sid:
        st.error("Login required to view course lessons.")
        return
    # ensure enrolled
    if not db_fetchone("SELECT enrollment_id FROM enrollments WHERE student_id=? AND course_id=?", (sid, cid)):
        st.error("You are not enrolled in this course.")
        return
    course = db_fetchone("SELECT title, description FROM courses WHERE course_id=?", (cid,))
    st.header(course[0])
    st.write(course[1] or "")
    lessons = db_fetchall("SELECT lesson_id, title, lesson_type, content_path, duration_seconds FROM lessons WHERE course_id=? ORDER BY \"order\", lesson_id", (cid,))
    if not lessons:
        st.info("No lessons uploaded for this course.")
        return
    total = len(lessons)
    completed = db_fetchone("SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id WHERE p.student_id=? AND l.course_id=? AND p.completed=1", (sid, cid))[0]
    pct = int((completed/total)*100) if total else 0
    st.progress(pct/100)
    st.markdown(f"**Progress: {pct}% ({completed}/{total})**")
    for lid, ltitle, ltype, cpath, dur in lessons:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"### {ltitle}")
        st.markdown(f"<div class='small'>{ltype} — {dur or 0} sec</div>", unsafe_allow_html=True)
        if cpath:
            if ltype == "video":
                try:
                    st.video(cpath)
                except:
                    st.write(f"Video file: {cpath}")
            else:
                st.write(f"Resource: {cpath}")
        # completion
        row = db_fetchone("SELECT completed FROM progress WHERE student_id=? AND lesson_id=?", (sid, lid))
        done = bool(row and row[0]==1)
        if done:
            st.button("Completed", key=f"completed_{lid}", disabled=True)
        else:
            if st.button("Mark as Complete", key=f"mark_{lid}"):
                ex = db_fetchone("SELECT progress_id FROM progress WHERE student_id=? AND lesson_id=?", (sid, lid))
                if ex:
                    db_exec("UPDATE progress SET completed=1, completed_on=? WHERE progress_id=?", (datetime.utcnow().isoformat(), ex[0]))
                else:
                    db_exec("INSERT INTO progress (student_id, lesson_id, completed, completed_on) VALUES (?,?,?,?)", (sid, lid, 1, datetime.utcnow().isoformat()))
                st.success("Marked complete.")
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    # certificate creation
    completed_lessons = db_fetchone("SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id WHERE p.student_id=? AND l.course_id=? AND p.completed=1", (sid, cid))[0]
    if total>0 and completed_lessons >= total:
        already = db_fetchone("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (sid, cid))
        if not already:
            sname = db_fetchone("SELECT full_name FROM students WHERE student_id=?", (sid,))[0]
            cert_path = generate_certificate(sname, course[0], sid, cid)
            st.success("Course completed — certificate generated.")
            st.markdown(f"[Download certificate]({cert_path})")
        else:
            st.markdown(f"[Certificate ready]({already[0]})")

# ---- SIGNUP / LOGIN / FORGOT ----
def page_signup():
    st.header("Create Profile")
    with st.form("signup_form", clear_on_submit=False):
        full_name = st.text_input("Full name *", key="signup_fullname")
        email = st.text_input("Email *", key="signup_email")
        password = st.text_input("Set password *", type="password", key="signup_password")
        st.caption("Min 8 chars, 1 uppercase, 1 number, 1 special char (@,#,*)")
        sex = st.selectbox("Sex", ["Prefer not to say","Male","Female"], key="signup_sex")
        profession = st.selectbox("Profession *", ["Student","Working Professional"], key="signup_prof")
        institution = st.text_input("Institution", key="signup_inst")
        mobile = st.text_input("Mobile *", key="signup_mobile")
        profile_pic = st.file_uploader("Profile picture (optional)", key="signup_pic", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Create profile", key="signup_submit")
        if submitted:
            errs=[]
            if not full_name.strip(): errs.append("Full name required")
            if not email.strip(): errs.append("Email required")
            if not password or len(password)<8: errs.append("Password must be 8+ chars")
            if not any(ch.isupper() for ch in password): errs.append("1 uppercase required")
            if not any(ch.isdigit() for ch in password): errs.append("1 number required")
            if not any(ch in "@#*" for ch in password): errs.append("1 special char (@,#,*) required")
            if not mobile.strip(): errs.append("Mobile required")
            if errs:
                for e in errs: st.error(e)
            else:
                pic_path = save_upload(profile_pic, PROFILE_DIR) if profile_pic else None
                try:
                    db_exec("INSERT INTO students (full_name,email,password,profile_pic,sex,profession,institution,mobile,created_on) VALUES (?,?,?,?,?,?,?,?,?)",
                            (full_name.strip(), email.strip().lower(), hash_pw(password), pic_path, sex, profession, institution, mobile.strip(), datetime.utcnow().isoformat()))
                    st.success("Profile created. Please login.")
                    # if user clicked enroll before signup, remember
                    aft = st.session_state.pop("after_enroll_course", None)
                    if aft:
                        st.session_state["post_signup_course"]=aft
                    st.session_state["page"]="login"
                except Exception as e:
                    st.error("Email already registered or DB error.")
                    st.exception(e)

def page_login():
    st.header("Student Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", key="login_submit"):
        if not email or not password:
            st.error("Provide email and password")
            return
        row = db_fetchone("SELECT student_id, full_name, password FROM students WHERE email=?", (email.strip().lower(),))
        if not row:
            st.error("No account found")
            return
        sid, name, hashed = row
        if verify_pw(password, hashed):
            st.success(f"Welcome, {name}!")
            st.session_state["student_id"]=sid
            st.session_state["student_name"]=name
            # handle post-signup/enroll redirect
            post = st.session_state.pop("post_signup_course", None)
            if post:
                pr = db_fetchone("SELECT price FROM courses WHERE course_id=?", (post,))
                if pr and pr[0] and pr[0]>0:
                    st.session_state["payment_course"]=post
                    st.session_state["page"]="payment"
                else:
                    db_exec("INSERT INTO enrollments (student_id,course_id,paid,enrolled_on) VALUES (?,?,?,?)", (sid, post, 0, datetime.utcnow().isoformat()))
                    st.success("Enrolled in free course. Opening lessons...")
                    st.session_state["selected_course"]=post
                    st.session_state["page"]="course_player"
            else:
                st.session_state["page"]="home"
        else:
            st.error("Incorrect password")
    if st.button("Forgot password?", key="login_forgot"):
        st.session_state["page"]="forgot_password"

def page_forgot_password():
    st.header("Forgot Password (simulated)")
    email = st.text_input("Registered email", key="forgot_email")
    if st.button("Generate reset token (simulated)", key="forgot_gen"):
        if not email: st.error("Provide email"); return
        row = db_fetchone("SELECT student_id FROM students WHERE email=?", (email.strip().lower(),))
        if not row:
            st.error("Email not found"); return
        token = secrets.token_urlsafe(24)
        db_exec("INSERT INTO reset_tokens (token, student_id, created_on, used) VALUES (?,?,?,0)", (token, row[0], datetime.utcnow().isoformat()))
        st.success("Reset token generated (simulated). Copy token and go to Reset Password page.")
        st.code(token)

def page_reset_password():
    st.header("Reset Password (simulated)")
    token = st.text_input("Reset token", key="reset_token")
    newpw = st.text_input("New password", type="password", key="reset_newpw")
    if st.button("Reset Password", key="reset_do"):
        if not token or not newpw:
            st.error("Provide token and new password"); return
        row = db_fetchone("SELECT student_id, used FROM reset_tokens WHERE token=?", (token,))
        if not row: st.error("Invalid token"); return
        if row[1]==1: st.error("Token used"); return
        sid = row[0]
        db_exec("UPDATE students SET password=? WHERE student_id=?", (hash_pw(newpw), sid))
        db_exec("UPDATE reset_tokens SET used=1 WHERE token=?", (token,))
        st.success("Password reset. Please login.")
        st.session_state["page"]="login"

# ---- STUDENT DASHBOARD ----
def page_dashboard():
    sid = st.session_state.get("student_id")
    if not sid:
        st.error("Login required.")
        return
    st.header("My Dashboard")
    enrolls = db_fetchall("SELECT e.enrollment_id, e.course_id, c.title, c.price FROM enrollments e JOIN courses c ON e.course_id=c.course_id WHERE e.student_id=?", (sid,))
    st.subheader("Enrolled Courses")
    if not enrolls:
        st.info("No enrollments yet.")
    else:
        for enr in enrolls:
            _, cid, title, price = enr
            total = db_fetchone("SELECT COUNT(*) FROM lessons WHERE course_id=?", (cid,))[0]
            completed = db_fetchone("""
                SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id
                WHERE p.student_id=? AND l.course_id=? AND p.completed=1
            """, (sid, cid))[0]
            pct = int((completed/total)*100) if total else 0
            st.markdown(f"**{title}** — {inr(price)} — Progress: {pct}%")
            if pct==100:
                cert = db_fetchone("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (sid, cid))
                if cert and cert[0]:
                    st.markdown(f"[Download certificate]({cert[0]})")

# ---- ADMIN LOGIN & DASHBOARD ----
def page_admin_login():
    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.header("Admin Login")
    pwd = st.text_input("Admin password", type="password", key="admin_pwd")
    if st.button("Login as Admin", key="admin_login_btn"):
        row = db_fetchone("SELECT password FROM admin WHERE admin_id=1")
        if row and verify_pw(pwd, row[0]):
            st.session_state["admin_logged"]=True
            st.success("Admin logged in")
            st.session_state["page"]="admin"
        else:
            st.error("Incorrect password")

def page_admin():
    if not st.session_state.get("admin_logged"):
        st.warning("Admin required.")
        return
    st.header("Admin Dashboard")
    # Add course
    with st.expander("Add Course", expanded=True):
        title = st.text_input("Title", key="admin_course_title")
        subtitle = st.text_input("Subtitle", key="admin_course_sub")
        desc = st.text_area("Description", key="admin_course_desc")
        price = st.number_input("Price (INR)", min_value=0.0, format="%.2f", key="admin_course_price")
        cat = st.text_input("Category", key="admin_course_cat")
        banner = st.file_uploader("Banner image (optional)", key="admin_course_banner", type=["png","jpg","jpeg"])
        if st.button("Create Course", key="admin_create_course"):
            banner_path = save_upload(banner, BANNERS_DIR) if banner else None
            db_exec("INSERT INTO courses (title,subtitle,description,price,category,banner_path,created_on) VALUES (?,?,?,?,?,?,?)",
                    (title, subtitle, desc, float(price), cat, banner_path, datetime.utcnow().isoformat()))
            st.success("Course created")
    # Manage courses
    st.subheader("Courses")
    courses = db_fetchall("SELECT course_id,title,category,price FROM courses ORDER BY course_id DESC")
    for cid, t, cat, pr in courses:
        cols = st.columns([3,1,1,1])
        cols[0].markdown(f"**{t}** — {cat or ''} — {inr(pr)}")
        if cols[1].button("Add Lesson", key=f"admin_add_lesson_{cid}"):
            st.session_state["admin_add_for"]=cid; st.session_state["admin_mode"]="add_lesson"
        if cols[2].button("View Lessons", key=f"admin_view_lessons_{cid}"):
            lessons = db_fetchall("SELECT lesson_id,title,lesson_type FROM lessons WHERE course_id=?", (cid,))
            if not lessons: st.info("No lessons")
            else:
                for lid, lt, lty in lessons:
                    st.markdown(f"- {lt} ({lty})")
                    if st.button("Delete Lesson", key=f"admin_del_lesson_{lid}"):
                        db_exec("DELETE FROM progress WHERE lesson_id=?", (lid,))
                        db_exec("DELETE FROM lessons WHERE lesson_id=?", (lid,))
                        st.experimental_rerun()
        if cols[3].button("Delete Course", key=f"admin_del_course_{cid}"):
            db_exec("DELETE FROM lessons WHERE course_id=?", (cid,))
            db_exec("DELETE FROM enrollments WHERE course_id=?", (cid,))
            db_exec("DELETE FROM certificates WHERE course_id=?", (cid,))
            db_exec("DELETE FROM courses WHERE course_id=?", (cid,))
            st.experimental_rerun()
    # Add lesson if requested
    if st.session_state.get("admin_mode")=="add_lesson":
        cid = st.session_state.get("admin_add_for")
        st.markdown(f"### Add lesson to course id {cid}")
        ltitle = st.text_input("Lesson title", key="admin_les_title")
        ltype = st.selectbox("Lesson type", ["video","pdf","ppt","text"], key="admin_les_type")
        uploaded = st.file_uploader("Upload file (optional)", key="admin_les_file")
        duration = st.number_input("Duration seconds (for simulation)", min_value=0, step=10, key="admin_les_dur")
        if st.button("Create Lesson", key="admin_create_lesson"):
            path = save_upload(uploaded, LESSONS_DIR) if uploaded else None
            db_exec("INSERT INTO lessons (course_id,title,lesson_type,content_path,duration_seconds) VALUES (?,?,?,?,?)", (cid, ltitle, ltype, path, int(duration)))
            st.success("Lesson created"); st.session_state["admin_mode"]=None; st.experimental_rerun()
    # Students table
    st.subheader("Students")
    studs = db_fetchall("SELECT student_id, full_name, email, mobile, profession, institution, sex, created_on FROM students ORDER BY student_id DESC")
    if studs:
        st.table(studs)
    else:
        st.info("No registered students yet.")

# ----------------------- Router -----------------------
def router():
    p = st.session_state.get("page","home")
    if p=="home":
        page_home()
    elif p=="course_preview":
        page_course_preview()
    elif p=="payment":
        page_payment()
    elif p=="course_player":
        page_course_player()
    elif p=="signup":
        page_signup()
    elif p=="login":
        page_login()
    elif p=="forgot_password":
        page_forgot_password()
    elif p=="reset_password":
        page_reset_password()
    elif p=="dashboard":
        page_dashboard()
    elif p=="admin_login":
        page_admin_login()
    elif p=="admin":
        page_admin()
    else:
        page_home()

# ----------------------- Navigation (tabs style) -----------------------
tabs = st.tabs(["Home","Courses","Signup","Login","Dashboard","Admin"])
with tabs[0]:
    st.session_state["page"]="home"; page_home()
with tabs[1]:
    st.session_state["page"]="home"; page_home()
with tabs[2]:
    st.session_state["page"]="signup"; page_signup()
with tabs[3]:
    st.session_state["page"]="login"; page_login()
with tabs[4]:
    st.session_state["page"]="dashboard"; page_dashboard()
with tabs[5]:
    # Admin tab shows login or dashboard depending on session
    if not st.session_state.get("admin_logged"):
        page_admin_login()
    else:
        page_admin()

# Floating admin small button bottom-right
if st.button("Admin", key="fab_admin"):
    st.session_state["page"]="admin_login"
    st.experimental_rerun()

st.markdown("<div class='footer'>© EinTrust</div>", unsafe_allow_html=True)
