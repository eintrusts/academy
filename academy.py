import streamlit as st
import sqlite3
import hashlib
import os

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="EinTrust Academy", page_icon="🎓", layout="wide")

# Custom dark theme CSS
st.markdown("""
    <style>
    body { background-color: #121212; color: #f5f5f5; }
    .stApp { background-color: #121212; }
    .course-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
    }
    .course-card {
        border-radius: 12px;
        padding: 20px;
        background-color: #1e1e1e;
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        transition: transform 0.2s ease;
    }
    .course-card:hover {
        transform: translateY(-5px);
    }
    .course-title {
        font-size: 20px;
        font-weight: bold;
        color: #f5f5f5;
        margin-bottom: 5px;
    }
    .course-subtitle {
        font-size: 14px;
        color: #bbb;
        margin-bottom: 10px;
    }
    .course-desc {
        font-size: 13px;
        color: #ddd;
        margin-bottom: 15px;
    }
    .top-buttons {
        position: absolute;
        top: 15px;
        right: 20px;
    }
    .admin-btn {
        position: absolute;
        bottom: 10px;
        right: 20px;
        font-size: 11px;
        color: #888;
    }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "academy.db"

# ---------------------------
# DB INIT
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('student','admin')) NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subtitle TEXT,
            description TEXT,
            price REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT,
            content TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id INTEGER,
            progress REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(course_id) REFERENCES courses(course_id)
        )
    """)

    conn.commit()
    conn.close()

def seed_demo_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM courses")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO courses (title, subtitle, description, price) VALUES (?, ?, ?, ?)", 
                  ("Sustainability 101", "Basics of Sustainability", 
                   "Learn the fundamentals of sustainability, ESG, and climate action.", 
                   499))
        course_id = c.lastrowid

        lessons = [
            (course_id, "Introduction to Sustainability", "This lesson covers the basics of sustainability."),
            (course_id, "Climate Change Basics", "Understanding climate science and impacts."),
            (course_id, "Sustainability in Business", "How companies adopt ESG practices.")
        ]
        c.executemany("INSERT INTO lessons (course_id, title, content) VALUES (?, ?, ?)", lessons)

    conn.commit()
    conn.close()

# ---------------------------
# HELPERS
# ---------------------------
def make_hash(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def check_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, make_hash(password)))
    data = c.fetchone()
    conn.close()
    return data

def add_user(name, email, password, role="student"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
              (name, email, make_hash(password), role))
    conn.commit()
    conn.close()

# ---------------------------
# HOME (Courses Page)
# ---------------------------
def home_page():
    st.markdown('<div class="top-buttons"><a href="?page=login">🔑 Login</a></div>', unsafe_allow_html=True)
    st.markdown('<div class="admin-btn"><a href="?page=admin">Admin</a></div>', unsafe_allow_html=True)

    st.title("🎓 EinTrust Academy")
    st.subheader("Discover Courses and Start Learning")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    courses = c.execute("SELECT * FROM courses").fetchall()
    conn.close()

    st.markdown('<div class="course-grid">', unsafe_allow_html=True)
    for course in courses:
        st.markdown(f"""
        <div class="course-card">
            <div class="course-title">{course[1]}</div>
            <div class="course-subtitle">{course[2]}</div>
            <div class="course-desc">{course[3][:100]}...</div>
            <a href="?page=preview&course_id={course[0]}">👉 View Details</a>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# PREVIEW COURSE
# ---------------------------
def preview_page(course_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM courses WHERE course_id=?", (course_id,))
    course = c.fetchone()
    lessons = c.execute("SELECT title FROM lessons WHERE course_id=?", (course_id,)).fetchall()
    conn.close()

    if course:
        st.title(course[1])
        st.subheader(course[2])
        st.write(course[3])
        st.write(f"💰 Price: ₹{course[4]}")

        st.markdown("### Lessons")
        for l in lessons:
            st.write(f"- {l[0]}")

        if "user" not in st.session_state:
            if st.button("Enroll Now"):
                st.session_state["redirect"] = "signup"
                st.experimental_rerun()
        else:
            st.success("You are logged in. Click Enroll in student dashboard.")

# ---------------------------
# LOGIN / SIGNUP
# ---------------------------
def login_page():
    st.title("🔑 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_user(email, password)
        if user:
            st.session_state["user"] = {"id": user[0], "name": user[1], "role": user[4]}
            st.success("Login successful")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")

def signup_page():
    st.title("📝 Signup")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        try:
            add_user(name, email, password)
            st.success("Account created. Please login.")
            st.session_state["redirect"] = "login"
            st.experimental_rerun()
        except:
            st.error("Email already registered.")

# ---------------------------
# ADMIN
# ---------------------------
def admin_page():
    st.title("⚙️ Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if password == "admin123":  # Demo password
            st.session_state["user"] = {"id": 0, "name": "Admin", "role": "admin"}
            st.experimental_rerun()
        else:
            st.error("Invalid password")

# ---------------------------
# ROUTER
# ---------------------------
def main():
    init_db()
    seed_demo_data()

    query_params = st.experimental_get_query_params()
    page = query_params.get("page", ["home"])[0]

    if "redirect" in st.session_state:
        page = st.session_state.pop("redirect")

    if page == "home":
        home_page()
    elif page == "preview":
        course_id = int(query_params.get("course_id", [0])[0])
        preview_page(course_id)
    elif page == "login":
        login_page()
    elif page == "signup":
        signup_page()
    elif page == "admin":
        admin_page()

if __name__ == "__main__":
    main()
