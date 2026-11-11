"""Paid-course checkout via Razorpay Payment Links.

When ``RAZORPAY_KEY_ID`` and ``RAZORPAY_KEY_SECRET`` are configured, learners get
a hosted Razorpay payment page and the course unlocks once the link reports
``paid``. Without keys, paid courses fall back to an enrollment request that an
admin approves (for invoices, bank transfers or corporate batches).
"""
from . import config, db


def razorpay_enabled():
    return bool(config.get_secret("RAZORPAY_KEY_ID") and config.get_secret("RAZORPAY_KEY_SECRET"))


def _client():
    import razorpay

    return razorpay.Client(auth=(config.get_secret("RAZORPAY_KEY_ID"), config.get_secret("RAZORPAY_KEY_SECRET")))


def start_checkout(student, course):
    """Create a Razorpay payment link and record it. Returns the payment row id and URL."""
    payload = {
        "amount": int(round(float(course["price"]) * 100)),  # paise
        "currency": "INR",
        "description": f"{config.BRAND_NAME}: {course['title']}"[:2048],
        "customer": {"name": student["full_name"], "email": student["email"]},
        "notify": {"email": True},
        "reminder_enable": True,
        "notes": {"student_id": str(student["student_id"]), "course_id": str(course["course_id"])},
    }
    if config.app_url():
        payload["callback_url"] = config.app_url()
        payload["callback_method"] = "get"
    link = _client().payment_link.create(payload)
    payment_id = db.create_payment(student["student_id"], course["course_id"], course["price"], "razorpay",
                                   "created", provider_ref=link["id"], payment_url=link["short_url"])
    return payment_id, link["short_url"]


def refresh_payment(payment):
    """Check a Razorpay payment link; enroll the learner if it has been paid. Returns the new status."""
    if payment["provider"] != "razorpay" or payment["status"] != "created":
        return payment["status"]
    link = _client().payment_link.fetch(payment["provider_ref"])
    status = link.get("status")
    if status == "paid":
        db.set_payment_status(payment["payment_id"], "paid")
        db.enroll(payment["student_id"], payment["course_id"], source="razorpay")
        return "paid"
    if status in ("cancelled", "expired"):
        db.set_payment_status(payment["payment_id"], status)
        return status
    return "created"


def request_enrollment(student, course):
    return db.create_payment(student["student_id"], course["course_id"], course["price"], "manual", "requested")


def approve_request(payment):
    db.set_payment_status(payment["payment_id"], "paid")
    db.enroll(payment["student_id"], payment["course_id"], source="admin")


def reject_request(payment):
    db.set_payment_status(payment["payment_id"], "rejected")
