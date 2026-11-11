"""Pages anyone can open: catalogue, course page, sign-in and certificate verification."""
import streamlit as st

from .. import auth, config, db, payments, ui
from . import student as student_views


def page_catalog():
    ui.brand_header()
    courses = db.list_courses(published_only=True)

    search_col, cat_col, level_col, price_col = st.columns([3, 2, 2, 2])
    query = search_col.text_input("Search courses", placeholder="e.g. carbon, BRSR, net zero",
                                  label_visibility="collapsed")
    categories = sorted({c.get("category") or "Other" for c in courses})
    category = cat_col.selectbox("Category", ["All categories"] + categories, label_visibility="collapsed")
    level = level_col.selectbox("Level", ["All levels"] + config.LEVELS, label_visibility="collapsed")
    price = price_col.selectbox("Price", ["Free & paid", "Free", "Paid"], label_visibility="collapsed")

    def keep(c):
        text = " ".join(str(c.get(k) or "") for k in ("title", "subtitle", "description", "category")).lower()
        if query and query.lower() not in text:
            return False
        if category != "All categories" and (c.get("category") or "Other") != category:
            return False
        if level != "All levels" and c.get("level") != level:
            return False
        if price == "Free" and float(c.get("price") or 0) > 0:
            return False
        if price == "Paid" and float(c.get("price") or 0) == 0:
            return False
        return True

    shown = [c for c in courses if keep(c)]
    if not courses:
        st.info("New courses are on the way. Check back soon.")
    elif not shown:
        st.info("No courses match those filters.")
    cols = st.columns(3)
    for i, course in enumerate(shown):
        with cols[i % 3]:
            ui.course_card(course, "cat")
    ui.footer()


def page_course():
    course_id = st.query_params.get("id")
    course = db.get_course(int(course_id)) if course_id and str(course_id).isdigit() else None
    if not course or (not course.get("is_published", 1) and not ui.is_admin()):
        st.warning("That course could not be found.")
        if st.button("Browse courses"):
            ui.go("catalog")
        return

    viewed = st.session_state.setdefault("viewed_courses", set())
    if course["course_id"] not in viewed:
        viewed.add(course["course_id"])
        db.increment_course_views(course["course_id"])

    student = ui.current_student()
    if student and db.is_enrolled(student["student_id"], course["course_id"]):
        student_views.course_player(student, course)
        return

    if not course.get("is_published", 1):
        st.info("Preview: this course is unpublished and hidden from learners.")
    st.title(course["title"], anchor=False)
    if course.get("subtitle"):
        st.write(f"**{course['subtitle']}**")
    ui.course_tags(course)

    main, side = st.columns([2, 1])
    with main:
        if course.get("thumbnail_url"):
            st.image(course["thumbnail_url"], width="stretch")
        if course.get("description"):
            st.markdown(course["description"])
        if course.get("learning_outcomes"):
            st.subheader("What you'll learn", anchor=False)
            for line in course["learning_outcomes"].splitlines():
                if line.strip():
                    st.markdown(f"- {line.strip().lstrip('-• ').strip()}")
        modules = db.list_modules(course["course_id"])
        st.subheader("Curriculum", anchor=False)
        if modules:
            for i, m in enumerate(modules, start=1):
                st.markdown(f"{i}. **{m['title']}** · {m['module_type']}")
        else:
            st.caption("Curriculum coming soon.")

    with side:
        with st.container(border=True):
            st.markdown(f"### {ui.price_label(course['price'])}")
            if course.get("instructor"):
                st.caption(f"Instructor: {course['instructor']}")
            st.caption(f"Certificate on completion · pass mark {course.get('pass_mark') or config.DEFAULT_PASS_MARK}%")
            _enroll_box(student, course)
    ui.footer()


def _enroll_box(student, course):
    if ui.is_admin() and not student:
        st.caption("You are signed in as admin. Learners enroll from here.")
        return
    if not student:
        st.write("Sign in or create a free account to enroll.")
        if st.button("Sign in to enroll", type="primary", width="stretch"):
            st.session_state["after_login"] = course["course_id"]
            ui.go("auth")
        return

    if float(course.get("price") or 0) == 0:
        if st.button("Enroll for free", type="primary", width="stretch"):
            db.enroll(student["student_id"], course["course_id"])
            st.rerun()
        return

    pending = db.open_payment(student["student_id"], course["course_id"])
    if pending and pending["provider"] == "manual":
        st.info("Your enrollment request has been sent. The EinTrust team will confirm it shortly.")
        return

    if payments.razorpay_enabled():
        if pending:
            # Check the gateway once automatically (e.g. after Razorpay redirects back), then on demand.
            auto_key = f"auto_checked_{pending['payment_id']}"
            first_check = auto_key not in st.session_state
            st.session_state[auto_key] = True
            st.link_button("Complete payment", pending["payment_url"], type="primary", width="stretch")
            clicked = st.button("I've completed payment", width="stretch")
            if first_check or clicked:
                try:
                    status = payments.refresh_payment(pending)
                except Exception as exc:
                    st.error(f"Could not reach the payment gateway: {exc}")
                    status = "created"
                if status == "paid":
                    st.rerun()
                if status == "created":
                    if clicked:
                        st.warning("We haven't received the payment yet. It can take a minute to confirm.")
                    st.caption("After paying, return here and press “I've completed payment”.")
                    return
            else:
                st.caption("After paying, return here and press “I've completed payment”.")
                return
        if st.button(f"Buy now · {ui.price_label(course['price'])}", type="primary", width="stretch"):
            try:
                payments.start_checkout(student, course)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not start checkout: {exc}")
    else:
        st.write("Enroll via invoice, bank transfer or corporate batch. We'll confirm by email.")
        if st.button("Request enrollment", type="primary", width="stretch"):
            payments.request_enrollment(student, course)
            st.rerun()


def page_auth():
    ui.brand_header("Sign in to continue learning")
    signin_tab, register_tab, admin_tab = st.tabs(["Sign in", "Create account", "Admin"])

    with signin_tab:
        with st.form("signin"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
                student = db.authenticate(email, password)
                if student:
                    st.session_state["student_id"] = student["student_id"]
                    st.session_state.pop("is_admin", None)
                    _after_login()
                else:
                    st.error("Incorrect email or password.")
        st.caption("Forgot your password? Contact the EinTrust team and we'll reset it for you.")

    with register_tab:
        with st.form("register"):
            full_name = st.text_input("Full name *")
            email = st.text_input("Email *")
            password = st.text_input("Password *", type="password", help=auth.PASSWORD_RULES)
            confirm = st.text_input("Confirm password *", type="password")
            c1, c2 = st.columns(2)
            profession = c1.text_input("Job title / profession")
            institution = c2.text_input("Organisation / institution")
            c3, c4 = st.columns(2)
            phone = c3.text_input("Phone")
            gender = c4.selectbox("Gender", ["Prefer not to say", "Female", "Male", "Other"])
            if st.form_submit_button("Create account", type="primary"):
                if not full_name.strip():
                    st.error("Please enter your name.")
                elif not auth.is_valid_email(email):
                    st.error("Please enter a valid email address.")
                elif not auth.is_valid_password(password):
                    st.error(auth.PASSWORD_RULES)
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    sid = db.create_student(full_name, email, password, gender, profession, institution, phone)
                    if sid:
                        st.session_state["student_id"] = sid
                        st.session_state.pop("is_admin", None)
                        _after_login()
                    else:
                        st.error("That email is already registered. Please sign in.")

    with admin_tab:
        if not auth.admin_configured():
            st.warning("Admin access is disabled until ADMIN_PASSWORD is set in the app secrets. "
                       "See README.md.")
        with st.form("admin_signin"):
            password = st.text_input("Admin password", type="password")
            if st.form_submit_button("Sign in as admin"):
                if auth.check_admin_password(password):
                    st.session_state["is_admin"] = True
                    st.session_state.pop("student_id", None)
                    st.session_state["landing_page"] = "admin_dashboard"
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")
    ui.footer()


def _after_login():
    course_id = st.session_state.pop("after_login", None)
    if course_id:
        st.session_state["landing_page"] = "course"
        st.session_state["landing_params"] = {"id": course_id}
    else:
        st.session_state["landing_page"] = "my_learning"
    st.rerun()


def page_verify():
    ui.brand_header("Certificate verification")
    cert_id = st.text_input("Certificate ID", value=st.query_params.get("id", ""), placeholder="EINT-XXXXXXXX")
    if cert_id:
        cert = db.get_certificate(cert_id)
        if cert:
            st.success("This certificate is valid.")
            with st.container(border=True):
                st.markdown(f"**Awarded to:** {cert['full_name']}")
                st.markdown(f"**Course:** {cert['course_title']}")
                st.markdown(f"**Issued:** {cert['issued_at'][:10]}")
                st.markdown(f"**Certificate ID:** `{cert['cert_id']}`")
        else:
            st.error("No certificate found with that ID.")
    ui.footer()
