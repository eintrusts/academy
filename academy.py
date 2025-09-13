import streamlit as st
import sqlite3
import re
from PIL import Image
import io
import base64

# --- Constants and Config ---
PAGE_TITLE = "EinTrust Academy"
ADMIN_PASSWORD = "eintrust2025" # NOTE: For a real app, this should be an encrypted password stored in a secure location.
ACCENT_COLOR = "#00B8D9"
SECONDARY_COLOR = "#667EEA"
BACKGROUND_COLOR = "#0D0F12"
CARD_COLOR = "#1C1C1C"

# --- DB Setup ---
conn = sqlite3.connect("academy.db", check_same_thread=False)
c = conn.cursor()

def setup_database():
    """Initializes the database tables if they don't exist."""
    # Using a single users table for both students and admins is more scalable.
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'student' -- 'student' or 'admin'
    )''')
    
    # Courses table
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        subtitle TEXT,
        description TEXT,
        price REAL
    )''')
    
    # Lessons table with a lesson order column
    c.execute('''CREATE TABLE IF NOT EXISTS lessons (
        lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT,
        description TEXT,
        lesson_type TEXT,
        file BLOB,
        link TEXT,
        lesson_order INTEGER,
        FOREIGN KEY(course_id) REFERENCES courses(course_id)
    )''')
    
    # Enrollments table to track who is enrolled in what course
    c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(course_id) REFERENCES courses(course_id),
        UNIQUE(user_id, course_id)
    )''')
    
    conn.commit()

# --- Utility Functions ---

def is_valid_email(email):
    """Validates email format."""
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email)

def is_valid_password(password):
    """Validates password complexity."""
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

def convert_file_to_bytes(uploaded_file):
    """Converts an uploaded file object to bytes."""
    if uploaded_file is not None:
        return uploaded_file.read()
    return None

def get_courses():
    """Fetches all courses."""
    return c.execute("SELECT * FROM courses ORDER BY title ASC").fetchall()

def get_lessons(course_id):
    """Fetches all lessons for a given course, ordered by lesson_order."""
    return c.execute("SELECT * FROM lessons WHERE course_id=? ORDER BY lesson_order ASC", (course_id,)).fetchall()

def add_user(full_name, email, password, role='student'):
    """Adds a new user to the database."""
    try:
        c.execute("INSERT INTO users (full_name, email, password, role) VALUES (?, ?, ?, ?)",
                  (full_name, email, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(email, password):
    """Authenticates a user based on email and password."""
    user = c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password)).fetchone()
    if user:
        st.session_state['user'] = {
            'id': user[0],
            'full_name': user[1],
            'email': user[2],
            'role': user[4]
        }
        return True
    return False

def is_user_enrolled(user_id, course_id):
    """Checks if a user is already enrolled in a course."""
    existing = c.execute("SELECT * FROM enrollments WHERE user_id=? AND course_id=?", (user_id, course_id)).fetchone()
    return existing is not None

def enroll_user_in_course(user_id, course_id):
    """Enrolls a user in a course."""
    if not is_user_enrolled(user_id, course_id):
        c.execute("INSERT INTO enrollments (user_id, course_id) VALUES (?,?)", (user_id, course_id))
        conn.commit()
        return True
    return False

def get_enrolled_courses(user_id):
    """Fetches all courses a user is enrolled in."""
    return c.execute(
        '''SELECT courses.course_id, courses.title, courses.subtitle, courses.description, courses.price
           FROM courses JOIN enrollments
           ON courses.course_id = enrollments.course_id
           WHERE enrollments.user_id=? ORDER BY courses.title ASC''', (user_id,)).fetchall()

def get_all_users():
    """Fetches all users (students and admins)."""
    return c.execute("SELECT * FROM users ORDER BY full_name ASC").fetchall()

def add_course(title, subtitle, description, price):
    """Adds a new course to the database."""
    c.execute("INSERT INTO courses (title, subtitle, description, price) VALUES (?,?,?,?)", (title, subtitle, description, price))
    conn.commit()
    return c.lastrowid

def add_lesson(course_id, title, description, lesson_type, file, link):
    """Adds a new lesson to a course."""
    current_lessons_count = c.execute("SELECT COUNT(*) FROM lessons WHERE course_id=?", (course_id,)).fetchone()[0]
    c.execute("INSERT INTO lessons (course_id, title, description, lesson_type, file, link, lesson_order) VALUES (?,?,?,?,?,?,?)",
              (course_id, title, description, lesson_type, file, link, current_lessons_count + 1))
    conn.commit()

def delete_course(course_id):
    """Deletes a course and its associated lessons and enrollments."""
    c.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
    c.execute("DELETE FROM enrollments WHERE course_id=?", (course_id,))
    c.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
    conn.commit()

def delete_lesson(lesson_id):
    """Deletes a lesson."""
    c.execute("DELETE FROM lessons WHERE lesson_id=?", (lesson_id,))
    conn.commit()

def delete_user(user_id):
    """Deletes a user and their enrollments."""
    c.execute("DELETE FROM enrollments WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()

# --- UI Components ---
def display_course_card(course, button_label="", on_click=None):
    """Displays a single course as a professional-looking card."""
    with st.container():
        st.markdown(f"""
        <div class="course-card">
            <h3 class="course-title">{course[1]}</h3>
            <p class="course-subtitle">{course[2]}</p>
            <p class="course-desc">{course[3]}</p>
            <p style="font-size: 1.2rem; font-weight: bold; color: {ACCENT_COLOR};">Price: {"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
            {"<div style='height: 10px;'></div>" if not button_label else ""}
        </div>
        """, unsafe_allow_html=True)
        if button_label:
            if st.button(button_label, key=f"course_btn_{course[0]}", use_container_width=True):
                if on_click:
                    on_click(course[0])
                    st.experimental_rerun()

def display_courses_grid(courses, enroll_option=False):
    """Displays a list of courses in a responsive grid."""
    if not courses:
        st.info("No courses available.")
        return
    
    cols = st.columns(2)
    for idx, course in enumerate(courses):
        with cols[idx % 2]:
            user_id = st.session_state.user['id'] if 'user' in st.session_state else None
            is_enrolled = is_user_enrolled(user_id, course[0]) if user_id else False

            if enroll_option and user_id and not is_enrolled:
                display_course_card(course, button_label="Enroll Now", on_click=lambda course_id: enroll_user_in_course(user_id, course_id))
            elif is_enrolled:
                display_course_card(course, button_label="Go to Course", on_click=lambda course_id: st.session_state.update(current_course_id=course_id, page='student_dashboard'))
            else:
                display_course_card(course)

def get_logo_base64():
    """Generates a base64 string for a simple logo from a hardcoded string."""
    svg = """
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
      <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linejoin="round"/>
      <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linejoin="round"/>
    </svg>
    """
    return base64.b64encode(svg.encode('utf-8')).decode('utf-8')

# --- Page Layouts ---

def page_header(user=None):
    """Displays a consistent header with logo, title, and user info/nav buttons."""
    logo_base64 = get_logo_base64()
    logo_url = f"data:image/svg+xml;base64,{logo_base64}"
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(logo_url, width=40)
    with col2:
        st.markdown(f"<h1 style='color: white; font-size: 2rem; margin-top: -5px;'>{PAGE_TITLE}</h1>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 1px solid #2e2e2e;'>", unsafe_allow_html=True)
    
    if user:
        user_info, logout_btn = st.columns([4, 1])
        with user_info:
            st.markdown(f"<h3 style='color: {SECONDARY_COLOR};'>Welcome, {user['full_name']}! 👋</h3>", unsafe_allow_html=True)
        with logout_btn:
            if st.button("Logout", key="logout_btn", use_container_width=True):
                st.session_state.clear()
                st.experimental_rerun()
    st.markdown("<br>", unsafe_allow_html=True)

def page_home_public():
    """The public landing page for non-logged-in users."""
    st.title("Welcome to EinTrust Academy")
    st.markdown("Unlock your potential with our expertly crafted courses. Sign up or log in to get started.", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("Available Courses")
    courses = get_courses()
    display_courses_grid(courses)

def page_login_signup():
    """Handles both login and signup on a single page."""
    st.title("Login or Sign Up")
    
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
    
    with login_tab:
        st.subheader("Student Login")
        with st.form("login_form"):
            email = st.text_input("Email ID", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if authenticate_user(email, password):
                    st.success("Login successful! Redirecting...")
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password.")
    
    with signup_tab:
        st.subheader("Create Your Profile")
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email ID", help="Must be unique.")
            password = st.text_input("Password", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char.")
            
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if not is_valid_email(email):
                    st.error("Please enter a valid email address.")
                elif not is_valid_password(password):
                    st.error("Password must be at least 8 characters and contain at least one uppercase letter, one number, and one special character.")
                else:
                    success = add_user(full_name, email, password)
                    if success:
                        st.success("Profile created successfully! Please log in.")
                    else:
                        st.error("Email is already registered. Please log in.")

def page_student_dashboard():
    """The main dashboard for logged-in students."""
    user = st.session_state.user
    
    my_courses_tab, all_courses_tab = st.tabs(["My Courses", "All Courses"])
    
    with my_courses_tab:
        st.subheader("My Enrolled Courses")
        enrolled_courses = get_enrolled_courses(user['id'])
        
        if not enrolled_courses:
            st.info("You are not enrolled in any courses yet. Explore the 'All Courses' tab to get started!")
        else:
            for course in enrolled_courses:
                course_id, title, subtitle, desc, price = course
                with st.expander(f"📚 {title} - {subtitle}"):
                    st.markdown(f"**Course Description:** {desc}")
                    st.markdown("---")
                    st.subheader("Lessons")
                    lessons = get_lessons(course_id)
                    if not lessons:
                        st.warning("No lessons found for this course.")
                    else:
                        for lesson in lessons:
                            lesson_id, _, lesson_title, lesson_desc, lesson_type, file_data, link, _ = lesson
                            st.markdown(f"**{lesson_title}** ({lesson_type})")
                            st.markdown(f"_{lesson_desc}_")
                            
                            if lesson_type == "Video" and file_data:
                                st.video(io.BytesIO(file_data), format="video/mp4")
                            elif lesson_type == "PDF" and file_data:
                                st.download_button(label=f"Download PDF: {lesson_title}", data=file_data, file_name=f"{lesson_title}.pdf")
                            elif lesson_type == "PPT" and file_data:
                                st.download_button(label=f"Download PPT: {lesson_title}", data=file_data, file_name=f"{lesson_title}.pptx")
                            elif lesson_type == "Link" and link:
                                st.markdown(f"**External Link:** [{link}]({link})")
                            st.markdown("<br>", unsafe_allow_html=True)
    
    with all_courses_tab:
        st.subheader("All Available Courses")
        all_courses = get_courses()
        
        cols = st.columns(2)
        for idx, course in enumerate(all_courses):
            with cols[idx % 2]:
                is_enrolled = is_user_enrolled(user['id'], course[0])
                if not is_enrolled:
                    if st.button(f"Enroll in {course[1]}", key=f"enroll_{course[0]}", use_container_width=True):
                        if enroll_user_in_course(user['id'], course[0]):
                            st.success(f"Successfully enrolled in {course[1]}!")
                            st.experimental_rerun()
                
                with st.container():
                    st.markdown(f"""
                    <div class="course-card">
                        <h3 class="course-title">{course[1]}</h3>
                        <p class="course-subtitle">{course[2]}</p>
                        <p class="course-desc">{course[3][:100]}...</p>
                        <p style="font-size: 1rem; font-weight: bold; color: {ACCENT_COLOR};">{"Free" if course[4]==0 else f"₹{course[4]:,.0f}"}</p>
                        {"<p style='font-size: 1rem; color: #4CAF50;'>✅ Enrolled</p>" if is_enrolled else ""}
                    </div>
                    """, unsafe_allow_html=True)

def page_admin_dashboard():
    """The dashboard for managing the platform, accessible only to admins."""
    
    dashboard_tab, users_tab, courses_tab, lessons_tab = st.tabs(["Dashboard", "Users", "Courses", "Lessons"])
    
    with dashboard_tab:
        st.subheader("Admin Overview")
        total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_courses = c.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        total_lessons = c.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        
        st.metric(label="Total Users", value=total_users)
        st.metric(label="Total Courses", value=total_courses)
        st.metric(label="Total Lessons", value=total_lessons)
    
    with users_tab:
        st.subheader("Manage Users")
        users = get_all_users()
        for user in users:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{user[1]}** ({user[2]}) - *{user[4].capitalize()}*")
            with col2:
                if st.button("Delete", key=f"del_user_{user[0]}"):
                    delete_user(user[0])
                    st.success(f"User {user[1]} deleted.")
                    st.experimental_rerun()
    
    with courses_tab:
        st.subheader("Add New Course")
        with st.form("add_course_form"):
            title = st.text_input("Course Title")
            subtitle = st.text_input("Subtitle")
            desc = st.text_area("Description")
            price = st.number_input("Price", min_value=0.0, step=1.0)
            submitted = st.form_submit_button("Add Course")
            if submitted:
                add_course(title, subtitle, desc, price)
                st.success("Course added successfully!")
                st.experimental_rerun()
        
        st.markdown("---")
        st.subheader("Manage Existing Courses")
        courses = get_courses()
        for course in courses:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{course[1]}** - *₹{course[4]:,.0f}*")
            with col2:
                if st.button("Delete", key=f"del_course_{course[0]}"):
                    delete_course(course[0])
                    st.success("Course deleted.")
                    st.experimental_rerun()
    
    with lessons_tab:
        st.subheader("Add New Lesson")
        courses = get_courses()
        course_titles = [c[1] for c in courses]
        
        with st.form("add_lesson_form"):
            selected_title = st.selectbox("Select Course", course_titles)
            selected_course_id = courses[course_titles.index(selected_title)][0] if selected_title else None
            
            title = st.text_input("Lesson Title")
            desc = st.text_area("Description")
            lesson_type = st.selectbox("Type", ["Video", "PDF", "PPT", "Link"])
            
            uploaded_file = None
            link = None
            if lesson_type in ["Video", "PDF", "PPT"]:
                uploaded_file = st.file_uploader(f"Upload {lesson_type} File", type=["mp4", "pdf", "pptx"])
            elif lesson_type == "Link":
                link = st.text_input("External Link URL")
            
            submitted = st.form_submit_button("Add Lesson")
            
            if submitted and selected_course_id:
                file_bytes = convert_file_to_bytes(uploaded_file)
                add_lesson(selected_course_id, title, desc, lesson_type, file_bytes, link)
                st.success("Lesson added successfully!")
                st.experimental_rerun()
        
        st.markdown("---")
        st.subheader("Manage Existing Lessons")
        lessons = c.execute("SELECT lessons.lesson_id, lessons.title, courses.title FROM lessons JOIN courses ON lessons.course_id = courses.course_id ORDER BY courses.title, lessons.lesson_order").fetchall()
        
        for lesson in lessons:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{lesson[1]}** (Course: {lesson[2]})")
            with col2:
                if st.button("Delete", key=f"del_lesson_{lesson[0]}"):
                    delete_lesson(lesson[0])
                    st.success("Lesson deleted.")
                    st.experimental_rerun()
                    
def page_admin_login():
    """Simple login page for the administrator."""
    st.title("Admin Login")
    password = st.text_input("Enter Admin Password", type="password")
    if st.button("Login as Admin"):
        if password == ADMIN_PASSWORD:
            # Create a mock admin user session
            st.session_state['user'] = {
                'id': 0, # Placeholder ID for admin
                'full_name': 'Admin',
                'email': 'admin@eintrust.com',
                'role': 'admin'
            }
            st.experimental_rerun()
        else:
            st.error("Invalid password.")

# --- Main App Logic ---

def main():
    """Main function to run the Streamlit app."""
    setup_database()

    # --- CSS Styles ---
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, .stApp {{
            font-family: 'Inter', sans-serif;
            background-color: {BACKGROUND_COLOR};
            color: #E0E0E0;
        }}
        
        .course-card {{
            background: {CARD_COLOR};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
            transition: transform 0.2s ease-in-out;
            border-left: 5px solid {ACCENT_COLOR};
        }}
        .course-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.5);
        }}
        .course-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            margin-bottom: 0.5rem;
        }}
        .course-subtitle {{
            font-size: 1rem;
            color: #B0B0B0;
        }}
        .course-desc {{
            font-size: 0.9rem;
            color: #CCCCCC;
            margin-top: 10px;
        }}
        .stButton>button {{
            background-color: {ACCENT_COLOR};
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            padding: 10px 20px;
            transition: background-color 0.2s ease-in-out;
        }}
        .stButton>button:hover {{
            background-color: {SECONDARY_COLOR};
            color: white;
        }}
        .stTextInput>div>div>input,
        .stSelectbox>div>div>select,
        .stTextArea>div>textarea,
        .stNumberInput>div>input {{
            background-color: #1e1e1e; 
            color: #f5f5f5; 
            border: 1px solid #333333; 
            border-radius: 6px;
        }}
        .stExpander {{
            border-radius: 12px;
            background: #1c1c1c;
            border: 1px solid #2e2e2e;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {BACKGROUND_COLOR};
            color: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            border: 1px solid {ACCENT_COLOR};
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {ACCENT_COLOR};
            color: {BACKGROUND_COLOR};
        }}
    </style>
    """, unsafe_allow_html=True)

    # --- Page Routing ---
    # Check if a user is logged in
    user = st.session_state.get('user')
    
    if user:
        page_header(user)
        if user['role'] == 'admin':
            page_admin_dashboard()
        else:
            page_student_dashboard()
    else:
        # Public-facing pages
        st.sidebar.markdown(
            f"""
            <div style="text-align: center;">
                <h2 style='color: white;'>EinTrust Academy</h2>
            </div>
            """, unsafe_allow_html=True
        )
        st.sidebar.markdown("<hr>", unsafe_allow_html=True)
        
        page_choice = st.sidebar.radio("Navigation", ["Home", "Login/Sign Up", "Admin Login"])
        
        if page_choice == "Home":
            page_home_public()
        elif page_choice == "Login/Sign Up":
            page_login_signup()
        elif page_choice == "Admin Login":
            page_admin_login()

if __name__ == "__main__":
    main()
