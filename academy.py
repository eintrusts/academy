# academy.py
import streamlit as st
import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

# ---------------------------
# CONFIG & DB SETUP
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide", page_icon=None, initial_sidebar_state="collapsed")

DB_FILE = "academy.db"
CERT_DIR = "certificates"
os.makedirs(CERT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

def create_tables():
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
    )
    """)
    # admin
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        admin_id INTEGER PRIMARY KEY,
        password TEXT NOT NULL
    )
    """)
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
    )
    """)
    # lessons
    c.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT,
        lesson_type TEXT,
        content_path TEXT,
        duration_seconds INTEGER DEFAULT 0,
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    """)
    # enrollments
    c.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        enrolled_on TEXT,
        FOREIGN KEY(student_id) REFERENCES students(student_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )
    """)
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
    )
    """)
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
    )
    """)
    # password reset tokens (simulation)
    c.execute("""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        token TEXT PRIMARY KEY,
        student_id INTEGER,
        created_on TEXT,
        used INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)
    # ensure admin exists (default password 'admin123' hashed)
    c.execute("SELECT COUNT(*) FROM admin")
    if c.fetchone()[0] == 0:
        default_admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO admin (admin_id, password) VALUES (?,?)", (1, default_admin_pw))
    conn.commit()

create_tables()

# ---------------------------
# UTILS
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

def save_uploaded_file(uploaded_file, folder="uploads"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{secrets.token_hex(8)}_{uploaded_file.name}")
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def generate_certificate_txt(student_name, course_title, student_id, course_id):
    now = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    filename = f"EinTrust_cert_{student_name.replace(' ','_')}_{course_title.replace(' ','_')}_{now}.txt"
    path = os.path.join(CERT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("EinTrust Academy\n")
        f.write("Certificate of Completion\n")
        f.write("\n")
        f.write(f"This certifies that {student_name}\n")
        f.write(f"has successfully completed the course: {course_title}\n")
        f.write(f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}\n")
        f.write("\n")
        f.write("EinTrust Academy\n")
    # save record
    c.execute("INSERT INTO certificates (student_id,course_id,cert_file,generated_on) VALUES (?,?,?,?)",
              (student_id, course_id, path, datetime.utcnow().isoformat()))
    conn.commit()
    return path

# ---------------------------
# CSS (dark theme, hover)
# ---------------------------
st.markdown("""
<style>
body, .stApp {background:#0e0f11; color:#e6eef2; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;}
.topbar {display:flex; justify-content:space-between; align-items:center; padding:14px 24px; background:#121314; border-bottom:1px solid #222;}
.logo {font-weight:700; font-size:20px;}
.search {width: 420px; padding:6px; border-radius:6px; background:#1b1c1e; color:#fff; border:1px solid #333;}
.btn {background:#00bfa5; color:#001; padding:8px 12px; border-radius:8px; border:none; cursor:pointer;}
.card {background:#141516; padding:14px; border-radius:10px; border:1px solid #222; margin-bottom:12px;}
.card:hover {box-shadow: 0 6px 18px rgba(0,0,0,0.6); transform: translateY(-2px); transition: all .15s ease-in-out;}
.small {font-size:13px; color:#9aa7b2;}
.footer {text-align:center; padding:12px; color:#7f8b91;}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Session state defaults
# ---------------------------
if "student_id" not in st.session_state:
    st.session_state["student_id"] = None
if "student_name" not in st.session_state:
    st.session_state["student_name"] = None
if "admin_logged" not in st.session_state:
    st.session_state["admin_logged"] = False
if "current_course" not in st.session_state:
    st.session_state["current_course"] = None

# ---------------------------
# Top Navigation (no icons)
# ---------------------------
def render_topbar():
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        st.markdown('<div class="topbar"><div class="logo">EinTrust Academy</div></div>', unsafe_allow_html=True)
    with col2:
        # search & category
        query = st.text_input("", placeholder="Search for anything", key="search_input", label_visibility="collapsed")
    with col3:
        if st.session_state["student_id"]:
            st.markdown(f"<div style='text-align:right'>Hi, {st.session_state['student_name']}</div>", unsafe_allow_html=True)
        else:
            if st.button("Login / Signup"):
                st.session_state["page"] = "login"
    return

# ---------------------------
# Pages
# ---------------------------

# HOME / BROWSE
def page_home():
    render_topbar()
    st.write("")  # spacing
    st.markdown("<div style='display:flex; gap:18px;'>", unsafe_allow_html=True)

    # Left: course list
    col1, col2 = st.columns([3,1])
    with col1:
        # category dropdown (dynamic)
        try:
            categories = [r[0] for r in c.execute("SELECT DISTINCT category FROM courses WHERE category IS NOT NULL").fetchall()]
        except Exception:
            categories = []
        categories = ["All"] + categories
        selected_cat = st.selectbox("Category", options=categories, index=0, key="cat")
        q = st.session_state.get("search_input", "").strip().lower()
        # build query safely
        sql = "SELECT course_id,title,subtitle,description,price,category,banner_path FROM courses"
        params = []
        filters = []
        if selected_cat and selected_cat != "All":
            filters.append("category = ?")
            params.append(selected_cat)
        if q:
            filters.append("LOWER(title) LIKE ?")
            params.append(f"%{q}%")
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY course_id DESC"

        try:
            courses = c.execute(sql, tuple(params)).fetchall()
        except Exception as e:
            st.error("Error loading courses. Database schema may not match expected columns.")
            st.exception(e)
            courses = []

        if not courses:
            st.info("No courses available yet. Admin can add courses from Admin Panel.")
        else:
            for course in courses:
                course_id, title, subtitle, desc, price, category, banner = course
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"### {title}")
                st.markdown(f"<div class='small'>{subtitle or ''} • {category or ''}</div>", unsafe_allow_html=True)
                st.write(desc or "")
                st.markdown(f"**{inr(price)}**")
                cols = st.columns([1,1,3])
                with cols[2]:
                    if st.button("Preview / Enroll", key=f"preview_{course_id}"):
                        st.session_state["current_course"] = course_id
                        st.session_state["page"] = "course_preview"
                st.markdown("</div>", unsafe_allow_html=True)

    # Right: small admin button & copyright
    with col2:
        st.markdown("<div style='position:sticky; top:20px;'>", unsafe_allow_html=True)
        if st.button("Admin", key="admin_small"):
            st.session_state["page"] = "admin_login"
        st.markdown("<br><div class='small'>© EinTrust</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# COURSE PREVIEW
def page_course_preview():
    course_id = st.session_state.get("current_course")
    if not course_id:
        st.info("No course selected.")
        return
    # load course
    course = c.execute("SELECT title,subtitle,description,price,category,banner_path FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not course:
        st.error("Course not found.")
        return
    title, subtitle, description, price, category, banner = course
    render_topbar()
    st.markdown(f"<div class='card'><h2>{title}</h2><div class='small'>{subtitle or ''} • {category or ''}</div><p>{description}</p><b>{inr(price)}</b></div>", unsafe_allow_html=True)

    # lessons list
    lessons = c.execute("SELECT lesson_id,title,lesson_type,duration_seconds FROM lessons WHERE course_id=? ORDER BY lesson_id ASC", (course_id,)).fetchall()
    if not lessons:
        st.info("No lessons uploaded for this course yet.")
    else:
        st.markdown("### Lessons")
        student_id = st.session_state.get("student_id")
        for lesson in lessons:
            lesson_id, ltitle, ltype, dur = lesson
            # check completion
            completed = 0
            if student_id:
                row = c.execute("SELECT completed FROM progress WHERE student_id=? AND lesson_id=?", (student_id, lesson_id)).fetchone()
                if row and row[0] == 1:
                    completed = 1
            status = "Complete" if completed else "Not Complete"
            st.markdown(f"- **{ltitle}** ({ltype}) — <span class='small'>{status}</span>", unsafe_allow_html=True)
            # show Mark Complete only if enrolled
            enrolled = False
            if student_id:
                enr = c.execute("SELECT enrollment_id FROM enrollments WHERE student_id=? AND course_id=?", (student_id, course_id)).fetchone()
                enrolled = bool(enr)
            if student_id:
                if not enrolled:
                    if st.button("Enroll to access lessons", key=f"enrollbtn_{lesson_id}"):
                        c.execute("INSERT INTO enrollments (student_id,course_id,enrolled_on) VALUES (?,?,?)", (student_id, course_id, datetime.utcnow().isoformat()))
                        conn.commit()
                        st.success("Enrolled — you can now mark lessons complete.")
                else:
                    if completed:
                        st.button("Completed", key=f"done_{lesson_id}", disabled=True)
                    else:
                        if st.button("Mark as Complete", key=f"mark_{lesson_id}"):
                            # mark progress
                            c.execute("INSERT OR REPLACE INTO progress (student_id,lesson_id,completed,completed_on) VALUES (?,?,?,?)",
                                      (student_id, lesson_id, 1, datetime.utcnow().isoformat()))
                            conn.commit()
                            st.success("Marked as complete.")
                            # check if all lesson completed -> generate certificate
                            total_lessons = c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,)).fetchone()[0]
                            completed_lessons = c.execute("""
                                SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id
                                WHERE p.student_id=? AND l.course_id=? AND p.completed=1
                            """, (student_id, course_id)).fetchone()[0]
                            if total_lessons > 0 and completed_lessons >= total_lessons:
                                # generate certificate (text file) if not already generated
                                existing_cert = c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (student_id, course_id)).fetchone()
                                if not existing_cert:
                                    student_name = c.execute("SELECT full_name FROM students WHERE student_id=?", (student_id,)).fetchone()[0]
                                    cert_path = generate_certificate_txt(student_name, title, student_id, course_id)
                                    st.success("Course completed! Certificate generated.")
            else:
                if st.button("Login / Signup to Enroll", key=f"loginreq_{lesson_id}"):
                    st.session_state["page"] = "login"

# STUDENT SIGNUP + LOGIN + PROFILE
def page_signup():
    render_topbar()
    st.header("Create your student profile")
    with st.form("signup", clear_on_submit=False):
        full_name = st.text_input("Full name *")
        email = st.text_input("Email *")
        password = st.text_input("Set password * (min 8 chars, 1 uppercase, 1 number, 1 special char)", type="password")
        sex = st.selectbox("Sex", ["Prefer not to say", "Male", "Female"])
        profession = st.selectbox("Profession *", ["Student", "Working Professional"])
        institution = st.text_input("Institution")
        mobile = st.text_input("Mobile *")
        profile_pic = st.file_uploader("Profile picture (optional)", type=["png","jpg","jpeg"])
        submitted = st.form_submit_button("Create profile")
        if submitted:
            # basic validation
            errors = []
            if not full_name.strip(): errors.append("Full name required")
            if not email.strip(): errors.append("Email required")
            if not password or len(password) < 8: errors.append("Password must be 8+ chars")
            # password rule checks
            if not any(ch.isupper() for ch in password): errors.append("Password needs 1 uppercase")
            if not any(ch.isdigit() for ch in password): errors.append("Password needs 1 number")
            if not any(ch in "@#*" for ch in password): errors.append("Password needs 1 special char (@,#,*)")
            if not mobile.strip(): errors.append("Mobile required")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                # store profile
                try:
                    pic_path = None
                    if profile_pic:
                        pic_path = save_uploaded_file(profile_pic, folder="profile_pics")
                    c.execute("""
                        INSERT INTO students (full_name,email,password,profile_pic,sex,profession,institution,mobile,created_on)
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (full_name.strip(), email.strip().lower(), hash_pw(password), pic_path, sex, profession, institution, mobile.strip(), datetime.utcnow().isoformat()))
                    conn.commit()
                    st.success("Profile created — please login.")
                    st.session_state["page"] = "login"
                except sqlite3.IntegrityError:
                    st.error("Email already registered. Try logging in.")

def page_login():
    render_topbar()
    st.header("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if not email or not password:
            st.error("Enter email and password")
        else:
            user = c.execute("SELECT student_id, full_name, password FROM students WHERE email=?", (email.strip().lower(),)).fetchone()
            if user and verify_pw(password, user[2]):
                st.session_state["student_id"] = user[0]
                st.session_state["student_name"] = user[1]
                st.success(f"Welcome back, {user[1]}!")
                st.session_state["page"] = "home"
            else:
                st.error("Incorrect email or password")
    if st.button("Forgot password?"):
        st.session_state["page"] = "forgot_password"

def page_forgot_password():
    render_topbar()
    st.header("Forgot Password (simulation)")
    email = st.text_input("Enter your registered email")
    if st.button("Send reset link (simulated)"):
        if not email:
            st.error("Provide email")
        else:
            user = c.execute("SELECT student_id FROM students WHERE email=?", (email.strip().lower(),)).fetchone()
            if not user:
                st.error("Email not found")
            else:
                token = secrets.token_urlsafe(24)
                created = datetime.utcnow().isoformat()
                c.execute("INSERT INTO reset_tokens (token, student_id, created_on, used) VALUES (?,?,?,0)", (token, user[0], created))
                conn.commit()
                # Simulate by showing the reset link in-app (since SMTP isn't configured)
                reset_link = f"RESET-LINK (simulated): use this token on Reset page -> {token}"
                st.success("Reset link generated (simulated). Copy the token below to reset your password.")
                st.code(reset_link)

def page_reset_password():
    render_topbar()
    st.header("Reset Password (simulation)")
    token = st.text_input("Paste reset token")
    new_pw = st.text_input("Enter new password", type="password")
    if st.button("Reset Password"):
        row = c.execute("SELECT student_id, used FROM reset_tokens WHERE token=?", (token,)).fetchone()
        if not row:
            st.error("Invalid token")
        elif row[1] == 1:
            st.error("Token already used")
        else:
            student_id = row[0]
            if not new_pw or len(new_pw) < 8:
                st.error("Password too short")
            else:
                c.execute("UPDATE students SET password=? WHERE student_id=?", (hash_pw(new_pw), student_id))
                c.execute("UPDATE reset_tokens SET used=1 WHERE token=?", (token,))
                conn.commit()
                st.success("Password reset successful! Please login.")
                st.session_state["page"] = "login"

# STUDENT DASHBOARD (progress & certificates)
def page_student_dashboard():
    render_topbar()
    sid = st.session_state.get("student_id")
    if not sid:
        st.error("You must be logged in to view the dashboard.")
        return
    st.header("My Dashboard")
    # Enrolled courses
    enrolls = c.execute("SELECT e.enrollment_id, e.course_id, c.title, c.price FROM enrollments e JOIN courses c ON e.course_id = c.course_id WHERE e.student_id=?", (sid,)).fetchall()
    st.subheader("Enrolled Courses")
    if not enrolls:
        st.info("You have not enrolled in any course yet.")
    else:
        for en in enrolls:
            _, course_id, title, price = en
            # progress percent = completed lessons / total lessons
            total = c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,)).fetchone()[0]
            completed = c.execute("""
                SELECT COUNT(*) FROM progress p JOIN lessons l ON p.lesson_id = l.lesson_id
                WHERE p.student_id=? AND l.course_id=? AND p.completed=1
            """, (sid, course_id)).fetchone()[0]
            pct = int((completed/total)*100) if total>0 else 0
            st.markdown(f"**{title}** — {inr(price)} — Progress: {pct}%")
            if pct == 100:
                # show certificate link if exists
                cert = c.execute("SELECT cert_file FROM certificates WHERE student_id=? AND course_id=?", (sid, course_id)).fetchone()
                if cert and cert[0]:
                    st.markdown(f"[Download Certificate]({cert[0]})")
    # Certificates table
    st.subheader("Certificates")
    certs = c.execute("SELECT course_id, cert_file, generated_on FROM certificates WHERE student_id=?", (sid,)).fetchall()
    if certs:
        for cert in certs:
            st.write(f"Course ID: {cert[0]} — Generated on: {cert[2]}")
            st.markdown(f"[Download]({cert[1]})")
    else:
        st.info("No certificates yet.")

# ADMIN: add/edit/delete courses and lessons
def page_admin_panel():
    render_topbar()
    # simple auth check
    if not st.session_state.get("admin_logged"):
        st.warning("Admin required — provide password.")
        pw = st.text_input("Admin password", type="password")
        if st.button("Login as Admin"):
            db_pw_row = c.execute("SELECT password FROM admin WHERE admin_id=1").fetchone()
            if db_pw_row and verify_pw(pw, db_pw_row[0]):
                st.session_state["admin_logged"] = True
                st.success("Admin logged in")
            else:
                st.error("Incorrect password")
        return
    st.header("Admin Panel — Manage Courses & Lessons")

    # Add course form
    with st.expander("Add New Course", expanded=True):
        ct = st.text_input("Course title")
        csub = st.text_input("Subtitle")
        cdesc = st.text_area("Description")
        cprice = st.number_input("Price (INR)", min_value=0.0, format="%.2f")
        ccat = st.text_input("Category")
        banner = st.file_uploader("Banner image (optional)", type=["png","jpg","jpeg"])
        if st.button("Create Course"):
            if not ct.strip():
                st.error("Title required")
            else:
                banner_path = None
                if banner:
                    banner_path = save_uploaded_file(banner, folder="banners")
                c.execute("INSERT INTO courses (title,subtitle,description,price,category,banner_path,created_on) VALUES (?,?,?,?,?,?,?)",
                          (ct.strip(), csub.strip(), cdesc.strip(), float(cprice), ccat.strip() or None, banner_path, datetime.utcnow().isoformat()))
                conn.commit()
                st.success("Course created")

    # List courses & manage
    st.markdown("### Existing Courses")
    courses = c.execute("SELECT course_id,title,category FROM courses ORDER BY course_id DESC").fetchall()
    for course in courses:
        cid, title, cat = course
        cols = st.columns([3,1,1,1])
        cols[0].markdown(f"**{title}** — {cat or ''}")
        if cols[1].button("Add Lesson", key=f"addles_{cid}"):
            st.session_state["admin_add_lesson_for"] = cid
            st.session_state["show_add_lesson"] = True
        if cols[2].button("Delete", key=f"delcourse_{cid}"):
            c.execute("DELETE FROM lessons WHERE course_id=?", (cid,))
            c.execute("DELETE FROM enrollments WHERE course_id=?", (cid,))
            c.execute("DELETE FROM certificates WHERE course_id=?", (cid,))
            c.execute("DELETE FROM courses WHERE course_id=?", (cid,))
            conn.commit()
            st.experimental_rerun()
        if cols[3].button("View Lessons", key=f"viewles_{cid}"):
            lessons = c.execute("SELECT lesson_id,title,lesson_type FROM lessons WHERE course_id=?", (cid,)).fetchall()
            if not lessons:
                st.info("No lessons for this course")
            else:
                for les in lessons:
                    lid, ltitle, ltype = les
                    st.markdown(f"- {ltitle} ({ltype})")
                    if st.button("Delete Lesson", key=f"del_l_{lid}"):
                        c.execute("DELETE FROM progress WHERE lesson_id=?", (lid,))
                        c.execute("DELETE FROM lessons WHERE lesson_id=?", (lid,))
                        conn.commit()
                        st.experimental_rerun()
    # Add lesson modal-like
    if st.session_state.get("show_add_lesson"):
        cid = st.session_state.get("admin_add_lesson_for")
        st.markdown(f"### Add Lesson to Course ID: {cid}")
        ltitle = st.text_input("Lesson title", key="les_title")
        ltype = st.selectbox("Lesson type", ["video","pdf","ppt","text"], key="les_type")
        uploaded = st.file_uploader("Upload file for lesson (optional)", key="les_file")
        duration = st.number_input("Duration in seconds (for simulation)", min_value=0, step=10, key="les_dur")
        if st.button("Create Lesson"):
            content_path = None
            if uploaded:
                content_path = save_uploaded_file(uploaded, folder="lesson_files")
            c.execute("INSERT INTO lessons (course_id,title,lesson_type,content_path,duration_seconds) VALUES (?,?,?,?,?)",
                      (cid, ltitle, ltype, content_path, int(duration)))
            conn.commit()
            st.success("Lesson created")
            st.session_state["show_add_lesson"] = False
            st.experimental_rerun()

# ---------------------------
# Router
# ---------------------------
def router():
    page = st.sidebar.selectbox("Menu", ["Home", "Course Preview", "Signup", "Login", "Forgot Password", "Reset Password", "My Dashboard", "Admin"])
    # map to pages — but also allow direct navigation via session state
    if st.session_state.get("page"):
        # page set by buttons (e.g., preview) takes precedence
        p = st.session_state["page"]
    else:
        p = page

    # allow explicit pages
    if p == "Home" or p == "home":
        st.title("")
        page_home()
    elif p == "Course Preview" or p == "course_preview":
        page_course_preview()
    elif p == "Signup":
        page_signup()
    elif p == "Login":
        page_login()
    elif p == "Forgot Password":
        page_forgot_password()
    elif p == "Reset Password":
        page_reset_password()
    elif p == "My Dashboard":
        page_student_dashboard()
    elif p == "Admin":
        page_admin_panel()
    else:
        # fallback
        page_home()

# ---------------------------
# Run
# ---------------------------
def main():
    # clear transient page setting (so menu controls work naturally)
    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    router()
    st.markdown("<div class='footer'>© EinTrust</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
