import streamlit as st
import sqlite3
import hashlib

# ------------------- DATABASE -------------------
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

# ------------------- CREATE TABLES -------------------
def create_tables():
    c.execute("""CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    subtitle TEXT,
                    description TEXT,
                    price REAL,
                    banner_path TEXT
                )""")
    
    conn.commit()

create_tables()

# ------------------- STREAMLIT CONFIG -------------------
st.set_page_config(page_title="EinTrust Academy", layout="wide")

# ------------------- UTILITIES -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- HOME PAGE -------------------
def home_page():
    st.title("EinTrust Academy")
    st.subheader("Available Courses")
    
    try:
        courses = c.execute("SELECT course_id,title,subtitle,description,price,banner_path FROM courses ORDER BY course_id DESC").fetchall()
        if not courses:
            st.info("No courses available yet.")
        for course in courses:
            st.write(f"**{course[1]}** — {course[2]} | ₹{course[4]}")
            st.write(course[3])
    except sqlite3.OperationalError as e:
        st.error("Database not ready. Courses table may not exist yet.")
        st.error(str(e))

# ------------------- MAIN -------------------
home_page()
