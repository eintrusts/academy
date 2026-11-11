"""Learner pages: course player, quizzes, my learning, certificates and profile."""
import streamlit as st

from .. import auth, certificates, config, db, payments, ui


def _require_student():
    student = ui.current_student()
    if not student:
        st.warning("Please sign in to continue.")
        if st.button("Sign in"):
            ui.go("auth")
        st.stop()
    return student


# ---------------------------------------------------------------------------
# Course player
# ---------------------------------------------------------------------------
def course_player(student, course):
    sid, cid = student["student_id"], course["course_id"]
    modules = db.list_modules(cid)
    done_ids = db.completed_module_ids(sid, cid)
    done, total, pct = db.course_progress(sid, cid)

    st.title(course["title"], anchor=False)
    st.progress(pct / 100, text=f"{done} of {total} modules complete ({pct}%)")

    if total and done == total:
        _certificate_banner(student, course)

    if not modules:
        st.info("Content for this course is being prepared. You'll be able to start soon.")
        return

    state_key = f"current_module_{cid}"
    ids = [m["module_id"] for m in modules]
    if st.session_state.get(state_key) not in ids:
        first_open = next((m for m in ids if m not in done_ids), ids[0])
        st.session_state[state_key] = first_open

    nav, content = st.columns([1, 3])
    with nav:
        st.markdown("**Modules**")
        for i, m in enumerate(modules, start=1):
            icon = "✅" if m["module_id"] in done_ids else ("▶️" if m["module_id"] == st.session_state[state_key] else "⬜")
            if st.button(f"{icon} {i}. {m['title']}", key=f"nav_{m['module_id']}", width="stretch",
                         type="secondary"):
                st.session_state[state_key] = m["module_id"]
                st.rerun()

    with content:
        module = next(m for m in modules if m["module_id"] == st.session_state[state_key])
        viewed = st.session_state.setdefault("viewed_modules", set())
        if module["module_id"] not in viewed:
            viewed.add(module["module_id"])
            db.increment_module_views(module["module_id"])
        idx = ids.index(module["module_id"])
        next_id = ids[idx + 1] if idx < len(ids) - 1 else None
        if _render_module(student, course, module, module["module_id"] in done_ids):
            if next_id:
                st.session_state[state_key] = next_id
            st.rerun()

        prev_col, _, next_col = st.columns([1, 2, 1])
        if idx > 0 and prev_col.button("← Previous", width="stretch"):
            st.session_state[state_key] = ids[idx - 1]
            st.rerun()
        if idx < len(ids) - 1 and next_col.button("Next →", width="stretch"):
            st.session_state[state_key] = ids[idx + 1]
            st.rerun()


def _render_module(student, course, module, is_done):
    """Render one module. Returns True when the learner has just completed it."""
    with st.container(border=True):
        st.subheader(module["title"], anchor=False)
        st.caption(module["module_type"])
        if module.get("description"):
            st.write(module["description"])

        mtype = module["module_type"]
        if mtype == "Quiz":
            _render_quiz(student, course, module, is_done)
            return False

        if module.get("content"):
            st.markdown(module["content"])
        if mtype == "Video":
            if module.get("link"):
                st.video(module["link"])
            elif module.get("has_file"):
                st.video(db.get_module_file(module["module_id"])["file"])
        elif mtype == "Link" and module.get("link"):
            st.link_button("Open resource ↗", module["link"])
        elif module.get("link"):
            st.markdown(f"[Open resource ↗]({module['link']})")

        # Uploaded videos without a link already play inline; every other file is offered as a download.
        if module.get("has_file") and not (mtype == "Video" and not module.get("link")):
            f = db.get_module_file(module["module_id"])
            if f and f["file"]:
                st.download_button(
                    f"Download {f['file_name'] or 'file'}", data=f["file"],
                    file_name=f["file_name"] or f"module-{module['module_id']}",
                    mime=f["file_mime"] or "application/octet-stream",
                    key=f"dl_{module['module_id']}",
                )

        st.divider()
        if is_done:
            st.success("You've completed this module.")
        elif st.button("Mark as complete", type="primary", key=f"done_{module['module_id']}"):
            db.mark_module_complete(student["student_id"], module["module_id"])
            return True
    return False


def _render_quiz(student, course, module, is_done):
    questions = db.list_questions(module["module_id"])
    pass_mark = course.get("pass_mark") or config.DEFAULT_PASS_MARK
    if not questions:
        st.info("This quiz has no questions yet.")
        return
    best = db.best_quiz_score(student["student_id"], module["module_id"])
    st.write(f"{len(questions)} questions · pass mark {pass_mark}%"
             + (f" · your best score {best:g}%" if best is not None else ""))
    if is_done:
        st.success("You've passed this quiz. You can retake it to practise.")

    result_key = f"quiz_result_{module['module_id']}"
    with st.form(f"quiz_{module['module_id']}"):
        answers = {}
        for n, q in enumerate(questions, start=1):
            choice = st.radio(f"**{n}. {q['question']}**", range(len(q["options"])),
                              format_func=lambda i, q=q: q["options"][i], index=None,
                              key=f"q_{q['question_id']}")
            answers[q["question_id"]] = choice
        if st.form_submit_button("Submit answers", type="primary"):
            if any(a is None for a in answers.values()):
                st.warning("Please answer every question.")
            else:
                st.session_state[result_key] = db.grade_quiz(
                    student["student_id"], module["module_id"], answers, pass_mark)

    if result_key in st.session_state:
        score, passed, results = st.session_state[result_key]
        (st.success if passed else st.error)(
            f"You scored {score:g}%. " + ("Passed!" if passed else f"You need {pass_mark}% to pass. Try again."))
        with st.expander("Review answers", expanded=not passed):
            for n, r in enumerate(results, start=1):
                q = r["question"]
                mark = "✅" if r["correct"] else "❌"
                st.markdown(f"{mark} **{n}. {q['question']}**  \nCorrect answer: {q['options'][q['correct_index']]}")
                if q.get("explanation"):
                    st.caption(q["explanation"])
        if passed and not is_done:
            st.session_state.pop(result_key)
            st.rerun()


def _certificate_banner(student, course):
    cert_id = db.issue_certificate(student["student_id"], course["course_id"])
    if not cert_id:
        return
    cert = db.get_certificate(cert_id)
    with st.container(border=True):
        st.markdown("### 🎓 Course complete!")
        st.write(f"Congratulations, {student['full_name']}. Your certificate ID is `{cert_id}`.")
        _certificate_download(cert, key=f"cert_course_{cert_id}")


def _certificate_download(cert, key):
    pdf = certificates.build_certificate(cert["full_name"], cert["course_title"], cert["cert_id"],
                                         cert["issued_at"], cert.get("duration_hours"))
    st.download_button("Download certificate (PDF)", data=pdf, file_name=f"{cert['cert_id']}.pdf",
                       mime="application/pdf", key=key, type="primary")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_my_learning():
    student = _require_student()
    _refresh_pending_payments(student)
    ui.brand_header(f"Welcome back, {student['full_name'].split(' ')[0] if student['full_name'] else 'learner'}")

    enrollments = db.student_enrollments(student["student_id"])
    certs = db.student_certificates(student["student_id"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Enrolled courses", len(enrollments))
    m2.metric("In progress", sum(1 for e in enrollments if 0 < e["progress"] < 100))
    m3.metric("Certificates", len(certs))

    if not enrollments:
        st.info("You haven't enrolled in any courses yet.")
        if st.button("Browse courses", type="primary"):
            ui.go("catalog")
        return

    for e in enrollments:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(e["title"], anchor=False)
            left.progress(e["progress"] / 100, text=f"{e['done']}/{e['total']} modules · {e['progress']}%")
            label = "Review" if e["total"] and e["progress"] == 100 else ("Start" if e["done"] == 0 else "Continue")
            if right.button(label, key=f"go_{e['course_id']}", type="primary", width="stretch"):
                ui.go("course", id=e["course_id"])

    pending = [p for p in db.list_payments() if p["student_id"] == student["student_id"]
               and p["status"] in ("requested", "created")]
    if pending:
        st.subheader("Awaiting confirmation", anchor=False)
        for p in pending:
            st.write(f"- {p['course_title']} · {ui.price_label(p['amount'])} · "
                     + ("payment pending" if p["status"] == "created" else "request sent to EinTrust"))
    ui.footer()


def _refresh_pending_payments(student):
    if st.session_state.get("payments_refreshed") or not payments.razorpay_enabled():
        return
    st.session_state["payments_refreshed"] = True
    for p in db.list_payments(status="created"):
        if p["student_id"] == student["student_id"]:
            try:
                payments.refresh_payment(p)
            except Exception:
                pass  # gateway unreachable; the learner can retry from the course page


def page_certificates():
    student = _require_student()
    st.title("My certificates", anchor=False)
    certs = db.student_certificates(student["student_id"])
    if not certs:
        st.info("Complete every module of a course to earn its certificate.")
        return
    for c in certs:
        cert = db.get_certificate(c["cert_id"])
        with st.container(border=True):
            st.subheader(c["course_title"], anchor=False)
            st.caption(f"Issued {c['issued_at'][:10]} · ID {c['cert_id']}")
            _certificate_download(cert, key=f"cert_{c['cert_id']}")
    if config.app_url():
        st.caption(f"Anyone can verify a certificate at {config.app_url()}/verify")


def page_profile():
    student = _require_student()
    st.title("My profile", anchor=False)
    with st.form("profile"):
        full_name = st.text_input("Full name (as printed on certificates)", student["full_name"] or "")
        st.text_input("Email", student["email"], disabled=True)
        c1, c2 = st.columns(2)
        profession = c1.text_input("Job title / profession", student.get("profession") or "")
        institution = c2.text_input("Organisation / institution", student.get("institution") or "")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone", student.get("phone") or "")
        genders = ["Prefer not to say", "Female", "Male", "Other"]
        gender = c4.selectbox("Gender", genders,
                              index=genders.index(student["gender"]) if student.get("gender") in genders else 0)
        if st.form_submit_button("Save profile", type="primary"):
            if not full_name.strip():
                st.error("Name cannot be empty.")
            else:
                db.update_student_profile(student["student_id"], full_name, gender, profession, institution, phone)
                st.success("Profile saved.")

    with st.form("change_password", clear_on_submit=True):
        st.subheader("Change password", anchor=False)
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password", help=auth.PASSWORD_RULES)
        confirm = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Update password"):
            if not auth.verify_password(current, student["password"]):
                st.error("Current password is incorrect.")
            elif not auth.is_valid_password(new):
                st.error(auth.PASSWORD_RULES)
            elif new != confirm:
                st.error("New passwords do not match.")
            else:
                db.set_password(student["student_id"], new)
                st.success("Password updated.")
