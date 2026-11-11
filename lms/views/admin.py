"""Admin console: analytics, course & module authoring, quizzes, learners, enrollments, certificates."""
import mimetypes

import pandas as pd
import plotly.express as px
import streamlit as st

from .. import auth, config, db, payments, seed, ui

GREEN = "#4CAF50"


def _require_admin():
    if not ui.is_admin():
        st.warning("Admin access required.")
        st.stop()


def _csv_button(df, filename, label="Download CSV"):
    st.download_button(label, df.to_csv(index=False).encode(), file_name=filename, mime="text/csv")


def _int_dtick(max_value):
    """Whole-number axis ticks for small counts (plotly otherwise shows 0.2, 0.4, ...)."""
    return 1 if max_value <= 10 else None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def page_dashboard():
    _require_admin()
    ui.brand_header("Admin dashboard")
    s = db.stats()
    cols = st.columns(6)
    cols[0].metric("Published courses", f"{s['published']} / {s['courses']}")
    cols[1].metric("Modules", s["modules"])
    cols[2].metric("Learners", s["students"])
    cols[3].metric("Enrollments", s["enrollments"])
    cols[4].metric("Certificates", s["certificates"])
    cols[5].metric("Revenue", ui.price_label(s["revenue"]) if s["revenue"] else "₹0")

    if s["pending_requests"]:
        st.info(f"{s['pending_requests']} enrollment request(s) awaiting approval.")
        if st.button("Review requests"):
            ui.go("admin_enrollments")

    left, right = st.columns(2)
    monthly = pd.DataFrame(db.enrollments_by_month())
    with left:
        st.subheader("Enrollments by month", anchor=False)
        if monthly.empty:
            st.caption("No enrollments yet.")
        else:
            fig = px.bar(monthly, x="month", y="enrollments", color_discrete_sequence=[GREEN])
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None, yaxis_title=None, height=320,
                              xaxis_type="category", bargap=0.4)
            fig.update_yaxes(dtick=_int_dtick(monthly["enrollments"].max()))
            st.plotly_chart(fig, width="stretch")

    perf = pd.DataFrame(db.course_performance())
    with right:
        st.subheader("Enrollments and completions by course", anchor=False)
        if perf.empty or perf["enrollments"].sum() == 0:
            st.caption("No course activity yet.")
        else:
            long = perf.melt(id_vars="title", value_vars=["enrollments", "completions"],
                             var_name="metric", value_name="learners")
            fig = px.bar(long, y="title", x="learners", color="metric", barmode="group", orientation="h",
                         color_discrete_map={"enrollments": GREEN, "completions": "#81C784"})
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), yaxis_title=None, xaxis_title=None,
                              legend_title=None, height=320)
            fig.update_xaxes(dtick=_int_dtick(long["learners"].max()))
            st.plotly_chart(fig, width="stretch")

    if not perf.empty:
        st.subheader("Course performance", anchor=False)
        perf["completion rate"] = (perf["completions"] / perf["enrollments"].where(perf["enrollments"] > 0)).fillna(0)
        st.dataframe(
            perf.drop(columns=["course_id"]), hide_index=True, width="stretch",
            column_config={"completion rate": st.column_config.ProgressColumn(format="percent", min_value=0,
                                                                             max_value=1),
                           "revenue": st.column_config.NumberColumn(format="₹%.0f")},
        )


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------
def page_courses():
    _require_admin()
    st.title("Courses", anchor=False)
    courses = db.list_courses(published_only=False)

    options = {"➕ New course": None}
    for c in courses:
        status = "" if c.get("is_published", 1) else "  (draft)"
        options[f"{c['title']}{status}  · #{c['course_id']}"] = c["course_id"]
    default_idx = 0
    selected_id = st.session_state.get("admin_course_id")
    if selected_id in options.values():
        default_idx = list(options.values()).index(selected_id)
    choice = st.selectbox("Select a course to manage", list(options), index=default_idx)
    course_id = options[choice]
    st.session_state["admin_course_id"] = course_id

    if course_id is None:
        _course_form(None)
        with st.expander("Starter content"):
            st.write("Add a set of draft sustainability courses (ESG basics, GHG accounting, BRSR, net zero) "
                     "with lessons and quizzes, to edit and publish.")
            if st.button("Add starter courses"):
                n = seed.load_starter_courses()
                st.success(f"Added {n} draft courses. Review and publish them when ready.")
                st.rerun()
        return

    course = db.get_course(course_id)
    details, modules_tab, learners_tab = st.tabs(["Details", "Modules & quizzes", "Learners"])
    with details:
        _course_form(course)
        if st.button("Preview course page"):
            ui.go("course", id=course_id)
        with st.expander("Danger zone"):
            st.write("Deleting a course also removes its modules, enrollments, progress and certificates.")
            confirm = st.text_input("Type DELETE to confirm", key=f"del_confirm_{course_id}")
            if st.button("Delete course", type="primary", disabled=confirm != "DELETE"):
                db.delete_course(course_id)
                st.session_state.pop("admin_course_id", None)
                st.rerun()
    with modules_tab:
        _modules_editor(course)
    with learners_tab:
        _course_learners(course)


def _course_form(course):
    new = course is None
    course = course or {}
    with st.form(f"course_form_{course.get('course_id', 'new')}", clear_on_submit=new):
        st.subheader("New course" if new else "Course details", anchor=False)
        title = st.text_input("Title *", course.get("title") or "")
        subtitle = st.text_input("Subtitle", course.get("subtitle") or "")
        description = st.text_area("Description (Markdown supported)", course.get("description") or "", height=150)
        outcomes = st.text_area("Learning outcomes (one per line)", course.get("learning_outcomes") or "")
        c1, c2, c3 = st.columns(3)
        cat = course.get("category") if course.get("category") in config.CATEGORIES else "Other"
        category = c1.selectbox("Category", config.CATEGORIES, index=config.CATEGORIES.index(cat))
        lvl = course.get("level") if course.get("level") in config.LEVELS else "Beginner"
        level = c2.selectbox("Level", config.LEVELS, index=config.LEVELS.index(lvl))
        duration = c3.number_input("Duration (hours)", 0.0, 500.0, float(course.get("duration_hours") or 0), 0.5)
        c4, c5, c6 = st.columns(3)
        price = c4.number_input("Price (₹, 0 = free)", 0.0, 1_000_000.0, float(course.get("price") or 0), 100.0)
        pass_mark = c5.number_input("Quiz pass mark (%)", 0, 100,
                                    int(course.get("pass_mark") or config.DEFAULT_PASS_MARK))
        instructor = c6.text_input("Instructor", course.get("instructor") or "")
        thumbnail = st.text_input("Cover image URL", course.get("thumbnail_url") or "")
        published = st.toggle("Published (visible in catalogue)", bool(course.get("is_published", 0 if new else 1)))
        if st.form_submit_button("Create course" if new else "Save changes", type="primary"):
            if not title.strip():
                st.error("Title is required.")
                return
            fields = dict(title=title.strip(), subtitle=subtitle, description=description, price=price,
                          category=category, level=level, duration_hours=duration, instructor=instructor,
                          thumbnail_url=thumbnail.strip(), learning_outcomes=outcomes,
                          is_published=int(published), pass_mark=int(pass_mark))
            if new:
                st.session_state["admin_course_id"] = db.create_course(**fields)
                st.rerun()
            else:
                db.update_course(course["course_id"], **fields)
                st.success("Saved.")


def _modules_editor(course):
    cid = course["course_id"]
    modules = db.list_modules(cid)
    if not modules:
        st.caption("No modules yet. Add the first one below.")
    for i, m in enumerate(modules):
        with st.expander(f"{i + 1}. {m['title']} · {m['module_type']}"):
            b1, b2, _ = st.columns([1, 1, 14])
            if b1.button("↑", key=f"up_{m['module_id']}", disabled=i == 0, help="Move up"):
                db.move_module(m["module_id"], -1)
                st.rerun()
            if b2.button("↓", key=f"down_{m['module_id']}", disabled=i == len(modules) - 1, help="Move down"):
                db.move_module(m["module_id"], +1)
                st.rerun()
            _module_form(cid, m)
            if m["module_type"] == "Quiz":
                _quiz_editor(m)
            if st.button("Delete module", key=f"delmod_{m['module_id']}"):
                db.delete_module(m["module_id"])
                st.rerun()

    st.divider()
    _module_form(cid, None)


def _module_form(course_id, module):
    new = module is None
    module = module or {}
    key = module.get("module_id", f"new_{course_id}")
    with st.form(f"module_form_{key}", clear_on_submit=new):
        if new:
            st.subheader("Add module", anchor=False)
        title = st.text_input("Module title *", module.get("title") or "")
        mtype_current = module.get("module_type") if module.get("module_type") in config.MODULE_TYPES else "Article"
        mtype = st.selectbox("Type", config.MODULE_TYPES, index=config.MODULE_TYPES.index(mtype_current),
                             help="Article: written lesson · Video: YouTube/Vimeo link or upload · "
                                  "PDF: upload a file · Link: external resource · Quiz: graded questions")
        description = st.text_input("Short description", module.get("description") or "")
        content = st.text_area("Lesson content (Markdown)", module.get("content") or "", height=200)
        link = st.text_input("Video / resource URL", module.get("link") or "")
        upload = st.file_uploader("Attach a file (PDF, slides, worksheet, video)")
        remove_file = False
        if module.get("has_file"):
            remove_file = st.checkbox(f"Remove attached file ({module.get('file_name') or 'file'})")
        if st.form_submit_button("Add module" if new else "Save module", type="primary"):
            if not title.strip():
                st.error("Module title is required.")
                return
            file_bytes = file_name = file_mime = None
            if upload is not None:
                file_bytes = upload.getvalue()
                file_name = upload.name
                file_mime = upload.type or mimetypes.guess_type(upload.name)[0]
            if new:
                db.create_module(course_id, title.strip(), mtype, description, content, link.strip(),
                                 file_bytes, file_name, file_mime)
            else:
                db.update_module(module["module_id"], title.strip(), mtype, description, content, link.strip(),
                                 file_bytes, file_name, file_mime, remove_file=remove_file)
            st.rerun()


def _quiz_editor(module):
    st.markdown("**Quiz questions**")
    questions = db.list_questions(module["module_id"])
    for n, q in enumerate(questions, start=1):
        c1, c2 = st.columns([8, 1])
        answer = q["options"][q["correct_index"]]
        c1.markdown(f"{n}. {q['question']}  \n✔️ {answer}  ·  options: {', '.join(q['options'])}")
        if c2.button("🗑", key=f"delq_{q['question_id']}", help="Delete question"):
            db.delete_question(q["question_id"])
            st.rerun()
    with st.form(f"add_q_{module['module_id']}", clear_on_submit=True):
        question = st.text_input("New question")
        opts = [st.text_input(f"Option {i + 1}", key=f"opt_{module['module_id']}_{i}") for i in range(4)]
        correct = st.selectbox("Correct option", [1, 2, 3, 4])
        explanation = st.text_input("Explanation shown after answering (optional)")
        if st.form_submit_button("Add question"):
            filled = [o for o in opts if o.strip()]
            if not question.strip() or len(filled) < 2:
                st.error("Enter the question and at least two options.")
            elif not opts[correct - 1].strip():
                st.error("The correct option cannot be blank.")
            else:
                # Index of the correct answer among the non-blank options.
                idx = [i for i, o in enumerate(opts) if o.strip()].index(correct - 1)
                db.add_question(module["module_id"], question, filled, idx, explanation)
                st.rerun()


def _course_learners(course):
    learners = db.course_learners(course["course_id"])
    if not learners:
        st.caption("No learners enrolled yet.")
        return
    df = pd.DataFrame(learners)[["full_name", "email", "enrolled_at", "source", "done", "total", "progress"]]
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={"progress": st.column_config.ProgressColumn(format="%d%%", min_value=0,
                                                                            max_value=100)})
    _csv_button(df, f"course-{course['course_id']}-learners.csv")


# ---------------------------------------------------------------------------
# Learners
# ---------------------------------------------------------------------------
def page_learners():
    _require_admin()
    st.title("Learners", anchor=False)
    students = db.list_students()
    if not students:
        st.info("No learners have registered yet.")
        return
    df = pd.DataFrame(students)
    query = st.text_input("Search by name, email or organisation")
    if query:
        q = query.lower()
        mask = df[["full_name", "email", "institution"]].fillna("").apply(
            lambda col: col.str.lower().str.contains(q, regex=False)).any(axis=1)
        df = df[mask]
    st.dataframe(df, hide_index=True, width="stretch")
    _csv_button(df, "learners.csv")

    st.divider()
    st.subheader("Manage a learner", anchor=False)
    labels = {f"{s['full_name']} <{s['email']}>": s["student_id"] for s in students}
    sid = labels[st.selectbox("Learner", list(labels))]
    student = db.get_student(sid)
    enrolled = {e["course_id"]: e for e in db.student_enrollments(sid)}

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Enrollments**")
        for e in enrolled.values():
            a, b = st.columns([4, 1])
            a.write(f"{e['title']} · {e['progress']}%")
            if b.button("Remove", key=f"unenroll_{sid}_{e['course_id']}"):
                db.unenroll(sid, e["course_id"])
                st.rerun()
        others = {c["title"]: c["course_id"] for c in db.list_courses(published_only=False)
                  if c["course_id"] not in enrolled}
        if others:
            pick = st.selectbox("Enroll in course", list(others), key=f"enroll_pick_{sid}")
            if st.button("Enroll learner"):
                db.enroll(sid, others[pick], source="admin")
                st.rerun()
    with c2:
        st.markdown("**Account**")
        with st.form(f"reset_{sid}", clear_on_submit=True):
            new_pw = st.text_input("Set a new password", type="password", help=auth.PASSWORD_RULES)
            if st.form_submit_button("Reset password"):
                if auth.is_valid_password(new_pw):
                    db.set_password(sid, new_pw)
                    st.success("Password reset. Share it with the learner securely.")
                else:
                    st.error(auth.PASSWORD_RULES)
        active = bool(student.get("is_active", 1))
        if st.button("Deactivate account" if active else "Reactivate account"):
            db.set_student_active(sid, not active)
            st.rerun()


# ---------------------------------------------------------------------------
# Enrollments & payments
# ---------------------------------------------------------------------------
def page_enrollments():
    _require_admin()
    st.title("Enrollments & payments", anchor=False)
    if payments.razorpay_enabled():
        st.caption("Razorpay checkout is enabled for paid courses.")
    else:
        st.caption("Razorpay is not configured, so paid courses take enrollment requests that you approve here.")

    requests = db.list_payments(status="requested")
    st.subheader(f"Pending requests ({len(requests)})", anchor=False)
    if not requests:
        st.caption("Nothing to review.")
    for p in requests:
        with st.container(border=True):
            a, b, c = st.columns([5, 1, 1])
            a.write(f"**{p['full_name']}** ({p['email']}) → {p['course_title']} · {ui.price_label(p['amount'])}  \n"
                    f"Requested {p['created_at']}")
            if b.button("Approve", key=f"approve_{p['payment_id']}", type="primary"):
                payments.approve_request(p)
                st.rerun()
            if c.button("Reject", key=f"reject_{p['payment_id']}"):
                payments.reject_request(p)
                st.rerun()

    st.subheader("All transactions", anchor=False)
    allp = db.list_payments()
    if allp:
        df = pd.DataFrame(allp)[["payment_id", "created_at", "full_name", "email", "course_title", "amount",
                                 "provider", "provider_ref", "status"]]
        st.dataframe(df, hide_index=True, width="stretch")
        _csv_button(df, "payments.csv")
    else:
        st.caption("No transactions yet.")


def page_certificates():
    _require_admin()
    st.title("Issued certificates", anchor=False)
    certs = db.list_certificates()
    if not certs:
        st.caption("No certificates issued yet.")
        return
    df = pd.DataFrame(certs)
    st.dataframe(df, hide_index=True, width="stretch")
    _csv_button(df, "certificates.csv")
