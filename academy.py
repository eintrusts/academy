import streamlit as st
import sqlite3

# -----------------------------
# CONFIG & THEME
# -----------------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

st.markdown("""
    <style>
    body {background-color: #121212; color: #ffffff;}
    .stTabs [role="tablist"] button {background-color: #1E1E1E; color: #ccc; border-radius: 10px; font-weight:500;}
    .stTabs [role="tablist"] button[aria-selected="true"] {background-color: #2E2E2E; color: #fff;}
    .stButton>button {background-color:#3a3a3a; color:#fff; border-radius:6px; padding:8px 20px;}
    </style>
""", unsafe_allow_html=True)

# Logo
st.image("https://github.com/eintrusts/CAP/raw/main/EinTrust%20%20(2).png", width=160)

# -----------------------------
# DATABASE SETUP
# -----------------------------
def init_db():
    conn = sqlite3.connect("academy.db")
    c = conn.cursor()

    # Courses
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        subtitle TEXT,
        description TEXT,
        price REAL,
        is_paid INTEGER
    )""")

    # Users
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )""")

    # Enrollments
    c.execute("""CREATE TABLE IF NOT EXISTS enrollments (
        enroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        progress INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )""")

    conn.commit()
    return conn, c

conn, c = init_db()

# -----------------------------
# PAGES
# -----------------------------

def page_home():
    st.subheader("Available Courses")

    courses = c.execute("SELECT * FROM courses ORDER BY course_id DESC").fetchall()
    if not courses:
        st.info("No courses available yet.")
    else:
        for course in courses:
            course_id, title, subtitle, description, price, is_paid = course
            with st.container():
                st.write(f"### {title}")
                st.write(subtitle)
                st.write(description)
                if is_paid:
                    st.write(f"Paid Course – ₹{price:,.2f}")
                else:
                    st.write("Free Course")

                if st.button(f"Enroll in {title}", key=f"enroll_home_{course_id}"):
                    st.session_state["selected_course"] = course_id
                    if "user" not in st.session_state:
                        st.session_state["page"] = "signup"
                    else:
                        if is_paid:
                            st.session_state["page"] = "payment"
                        else:
                            st.session_state["page"] = "lesson"

def page_signup():
    st.subheader("Create Profile")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            try:
                c.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)", (name, email, password))
                conn.commit()
                st.success("Profile created! Please log in.")
                st.session_state["page"] = "login"
            except sqlite3.IntegrityError:
                st.error("Email already exists. Please use another.")

def page_login():
    st.subheader("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
            if user:
                st.session_state["user"] = user
                st.success("Login successful!")
                st.session_state["page"] = "home"
            else:
                st.error("Invalid credentials.")

def page_lesson():
    st.subheader("Course Lessons")
    course_id = st.session_state.get("selected_course")
    if not course_id:
        st.warning("No course selected.")
        return

    course = c.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not course:
        st.error("Course not found.")
        return

    st.write(f"### {course[1]}")
    st.write(course[3])
    st.info("Lessons will be displayed here (Demo).")

    if st.button("Mark Course Complete", key=f"complete_{course_id}"):
        user_id = st.session_state["user"][0]
        c.execute("UPDATE enrollments SET progress=100 WHERE user_id=? AND course_id=?", (user_id, course_id))
        conn.commit()
        st.success("Course Completed! Certificate will be generated automatically.")

def page_payment():
    st.subheader("Payment Gateway (Demo)")
    st.warning("Payment integration is in demo mode.")
    if st.button("Simulate Payment Success", key="pay_success"):
        user_id = st.session_state["user"][0]
        course_id = st.session_state["selected_course"]
        c.execute("INSERT INTO enrollments (user_id,course_id,progress) VALUES (?,?,0)", (user_id, course_id))
        conn.commit()
        st.success("Payment successful! Redirecting to lessons...")
        st.session_state["page"] = "lesson"

def page_admin():
    st.subheader("Admin Dashboard")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == "admin123":  # Demo password
            st.session_state["is_admin"] = True
        else:
            st.error("Invalid password")

    if st.session_state.get("is_admin"):
        st.success("Welcome, Admin")

        st.write("### Manage Courses")
        with st.form("add_course_form"):
            title = st.text_input("Course Title")
            subtitle = st.text_input("Subtitle")
            desc = st.text_area("Description")
            price = st.number_input("Price (₹)", min_value=0.0)
            is_paid = st.checkbox("Paid Course?")
            submitted = st.form_submit_button("Add Course")
            if submitted:
                c.execute("INSERT INTO courses (title,subtitle,description,price,is_paid) VALUES (?,?,?,?,?)",
                          (title, subtitle, desc, price, 1 if is_paid else 0))
                conn.commit()
                st.success("Course added successfully!")

        st.write("### All Students")
        students = c.execute("SELECT name,email FROM users").fetchall()
        for s in students:
            st.write(f"{s[0]} - {s[1]}")

# -----------------------------
# NAVIGATION
# -----------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

menu = st.tabs(["Home", "Signup", "Login", "Admin"])

with menu[0]:
    if st.session_state["page"] == "home":
        page_home()

with menu[1]:
    if st.session_state["page"] == "signup":
        page_signup()

with menu[2]:
    if st.session_state["page"] == "login":
        page_login()

with menu[3]:
    page_admin()

# Dynamic navigation
if st.session_state["page"] == "lesson":
    page_lesson()
elif st.session_state["page"] == "payment":
    page_payment()
