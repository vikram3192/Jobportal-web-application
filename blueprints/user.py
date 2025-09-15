from flask import Blueprint, request, session, jsonify
from config import db_cursor, PROFILE_PIC_FOLDER, allowed_image_file, allowed_resume_file, LOGO_FOLDER
from resume_upload import save_resume
from functools import wraps
from werkzeug.utils import secure_filename
import os, time

user_bp = Blueprint("user", __name__, url_prefix="/api")

# -------------------- HELPERS --------------------
def api_response(success, message, **kwargs):
    """Standard JSON response"""
    data = {"success": success, "message": message}
    if kwargs:
        data.update(kwargs)
    return jsonify(data)

def login_required(role="User"):
    """Decorator for role-based session check"""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if "user" not in session or session["user"]["role"] != role:
                return api_response(False, "Unauthorized"), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# ---------- JOB HELPERS ----------------
def get_jobs(page, per_page, q=""):
    """Fetch jobs with logo and whether current user applied"""
    offset = (page - 1) * per_page
    user_id = session["user"]["id"]
    with db_cursor(dictionary=True) as cursor:
        base_sql = """
            SELECT j.id, j.company, j.title, j.location, j.job_type, j.logo_filename,
                   EXISTS(SELECT 1 FROM applications a WHERE a.job_id = j.id AND a.user_id = %s) AS applied
            FROM jobs j
        """
        params = [user_id]

        if q:
            base_sql += " WHERE (j.title LIKE %s OR j.company LIKE %s OR j.location LIKE %s) "
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

        base_sql += " ORDER BY j.created_at DESC LIMIT %s OFFSET %s"
        params.extend([per_page + 1, offset])

        cursor.execute(base_sql, tuple(params))
        jobs = cursor.fetchall()

    for job in jobs:
        job["logo_url"] = f"/uploads/logos/{job['logo_filename']}" if job.get("logo_filename") else "/static/images/default-logo.png"
        job["applied"] = bool(job.get("applied"))
    return jobs


def get_job(job_id):
    """Fetch job detail with applied status"""
    user_id = session["user"]["id"]
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """SELECT j.*,
                      EXISTS(
                        SELECT 1 FROM applications a
                        WHERE a.job_id = j.id AND a.user_id = %s
                      ) AS applied
               FROM jobs j
               WHERE j.id=%s""",
            (user_id, job_id),
        )
        job = cursor.fetchone()
        if job:
            if job.get("deadline"):
                job["deadline"] = job["deadline"].strftime("%Y-%m-%d")
            job["logo_url"] = f"/uploads/logos/{job['logo_filename']}" if job.get("logo_filename") else "/static/images/default-logo.png"
            job["applied"] = bool(job.get("applied"))
        return job



# -------------------- JOB LIST --------------------
@user_bp.route("/jobs", methods=["GET"])
@login_required(role="User")
def api_jobs():
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    page = max(1, page)
    per_page = 6
    q = request.args.get("q", "").strip()

    jobs = get_jobs(page, per_page, q)
    has_next = len(jobs) > per_page
    jobs = jobs[:per_page]

    return api_response(True, "Jobs fetched", jobs=jobs, page=page, has_next=has_next)


# -------------------- JOB DETAIL --------------------
@user_bp.route("/job/<int:job_id>", methods=["GET"])
@login_required(role="User")
def api_job_detail(job_id):
    job = get_job(job_id)
    if not job:
        return api_response(False, "Job not found"), 404
    return api_response(True, "Job found", job=job)


# -------------------- APPLY JOB --------------------
@user_bp.route("/apply/<int:job_id>", methods=["POST"])
@login_required(role="User")
def api_apply_job(job_id):
    user_id = session["user"]["id"]
    
    # confirm job exists
    job = get_job(job_id)
    if not job:
        return api_response(False, "Job not found"), 404
    
    # check duplicate application
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT id FROM applications WHERE user_id=%s AND job_id=%s",
            (user_id, job_id),
        )
        if cursor.fetchone():
            return api_response(False, "Already applied"), 400

    file = request.files.get("resume")
    if not file or file.filename == "":
        return api_response(False, "Resume required"), 400
    
    if not allowed_resume_file(file.filename):
        return api_response(False, "Unsupported resume file type"), 400
    
    filename, error = save_resume(file, user_id, job_id)
    if error:
        return api_response(False, error), 400

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO applications (user_id, job_id, resume_path) VALUES (%s, %s, %s)",
            (user_id, job_id, filename),
        )

    return api_response(True, "Application submitted")


# -------------------- UPLOAD PROFILE PICTURE --------------------
@user_bp.route("/upload-profile", methods=["POST"])
@login_required(role="User")
def api_upload_profile():
    file = request.files.get("profile_pic")
    if not file or file.filename == "":
        return api_response(False, "No file selected"), 400
    
    filename_in = secure_filename(file.filename)
    if not filename_in or not allowed_image_file(filename_in):
        return api_response(False, "Invalid file type"), 400
    
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"user{session['user']['id']}_{int(time.time())}.{ext}"
    filepath = os.path.join(PROFILE_PIC_FOLDER, filename)

    try:
        os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)
        file.save(filepath)
    except Exception as e:
        print(f"Error saving profile pic: {e}")
        return api_response(False, "Error saving file"), 500
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "UPDATE users SET profile_pic=%s WHERE id=%s",
                (filename, session["user"]["id"]),
            )
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"[DB ERROR] {e}")
        return api_response(False, "Internal server error"), 500
    
    session["user"]["profile_pic"] = filename
    return api_response(True, "Profile updated", filename=filename)


# -------------------- REMOVE PROFILE PICTURE --------------------
@user_bp.route("/remove-profile", methods=["POST"])
@login_required(role="User")
def api_remove_profile():
    old_pic = session["user"].get("profile_pic")
    if old_pic:
        filepath = os.path.join(PROFILE_PIC_FOLDER, old_pic)
        try:
            if (
                os.path.exists(filepath)
                and os.path.commonpath([os.path.abspath(filepath), os.path.abspath(PROFILE_PIC_FOLDER)])
                == os.path.abspath(PROFILE_PIC_FOLDER)
            ):
                os.remove(filepath)
        except Exception as e:
            print(f"Could not delete old profile pic: {e}")

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET profile_pic=NULL WHERE id=%s",
            (session["user"]["id"],),
        )

    session["user"].pop("profile_pic", None)
    return api_response(True, "Profile picture removed")
