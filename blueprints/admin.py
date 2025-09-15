from flask import Blueprint, request, session, jsonify, send_from_directory
from config import (
    db_cursor,
    PROFILE_PIC_FOLDER,
    RESUME_FOLDER,
    allowed_image_file,
    MAX_FILE_SIZE,
    LOGO_FOLDER,
)
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# -------------------- HELPERS --------------------
def api_response(success, message, **kwargs):
    data = {"success": success, "message": message}
    if kwargs:
        data.update(kwargs)
    return jsonify(data)

def admin_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if not user or user.get("role") != "Employer":
            return api_response(False, "Unauthorized"), 403
        return fn(*args, **kwargs)
    return decorated

def _add_job(title, experience, salary, location, description, job_type, deadline):
    """Insert a job, reusing employer's saved logo."""
    with db_cursor(commit=True, dictionary=True) as cursor:
        cursor.execute(
            "SELECT organization_name, logo_filename FROM employers WHERE id=%s",
            (session["user"]["id"],),
        )
        employer = cursor.fetchone()
        company_name = employer["organization_name"] if employer else "Unknown Company"
        logo_filename = employer.get("logo_filename") if employer else None

        cursor.execute(
            """INSERT INTO jobs 
               (title, company, experience, salary, location, description, job_type, deadline, posted_by, logo_filename) 
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                title,
                company_name,
                experience,
                salary,
                location,
                description,
                job_type,
                deadline,
                session["user"]["id"],
                logo_filename,
            ),
        )

def _list_jobs(q="", page=1, per_page=6):
    offset = (page - 1) * per_page
    with db_cursor(dictionary=True) as cursor:
        if q:
            cursor.execute(
                """SELECT j.*, 
                          (SELECT COUNT(*) FROM applications a WHERE a.job_id=j.id) AS applications_count 
                   FROM jobs j 
                   WHERE j.posted_by=%s AND (j.title LIKE %s OR j.company LIKE %s OR j.location LIKE %s) 
                   ORDER BY j.created_at DESC
                   LIMIT %s OFFSET %s""",
                (
                    session["user"]["id"],
                    f"%{q}%",
                    f"%{q}%",
                    f"%{q}%",
                    per_page + 1,
                    offset,
                ),
            )
        else:
            cursor.execute(
                """SELECT j.*, 
                          (SELECT COUNT(*) FROM applications a WHERE a.job_id=j.id) AS applications_count 
                   FROM jobs j 
                   WHERE j.posted_by=%s 
                   ORDER BY j.created_at DESC
                   LIMIT %s OFFSET %s""",
                (session["user"]["id"], per_page + 1, offset),
            )
        jobs = cursor.fetchall()
        has_next = len(jobs) > per_page
        jobs = jobs[:per_page]

        for job in jobs:
            if job.get("logo_filename"):
                job["logo_url"] = f"/uploads/logos/{job['logo_filename']}"
            else:
                job["logo_url"] = "/static/images/default-logo.png"
        return jobs, has_next

def _get_applications(job_id, page=1, per_page=10):
    offset = (page - 1) * per_page
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """SELECT j.*, 
                      e.employer_name,
                      e.organization_name, 
                      e.organization_email, 
                      e.mobile AS organization_mobile, 
                      e.logo_filename
               FROM jobs j
               JOIN employers e ON j.posted_by = e.id
               WHERE j.id=%s AND j.posted_by=%s""",
            (job_id, session["user"]["id"]),
        )
        job = cursor.fetchone()
        if not job:
            return None, None, None

        cursor.execute(
            """SELECT a.id AS application_id,
                      u.id AS user_id,
                      u.name,
                      u.email,
                      u.mobile,
                      a.applied_at,
                      a.resume_path
               FROM applications a
               JOIN users u ON a.user_id = u.id
               WHERE a.job_id=%s
               ORDER BY a.applied_at DESC
               LIMIT %s OFFSET %s""",
            (job_id, per_page + 1, offset),
        )
        applicants = cursor.fetchall()
        has_next = len(applicants) > per_page
        applicants = applicants[:per_page]

        for app in applicants:
            app["resume_filename"] = (
                os.path.basename(app["resume_path"])
                if app.get("resume_path")
                else ""
            )
        return job, applicants, has_next



# -------------------- API ROUTES --------------------

# Post job
@admin_bp.route("/jobs", methods=["POST"])
@admin_required
def api_post_job():
    data = request.form
    title = (data.get("title") or "").strip()
    experience = (data.get("experience") or "").strip()
    salary = (data.get("salary") or "").strip()
    location = (data.get("location") or "").strip()
    description = (data.get("description") or "").strip()
    job_type = (data.get("job_type") or "Full-Time").strip()
    deadline = data.get("deadline")

    if not all([title, experience, salary, location, job_type]):
        return api_response(False, "Missing required fields"), 400

    try:
        float(salary)
    except ValueError:
        return api_response(False, "Salary must be a number"), 400

    if deadline:
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            return api_response(False, "Deadline must be YYYY-MM-DD"), 400

    try:
        _add_job(title, experience, salary, location, description, job_type, deadline)
        return api_response(True, "Job posted successfully")
    except Exception as e:
        print("[ERROR posting job]", e)
        return api_response(False, f"Internal error: {e}"), 500

# List jobs
@admin_bp.route("/jobs", methods=["GET"])
@admin_required
def api_list_jobs():
    q = request.args.get("q", "").strip()
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    page = max(1, page)
    per_page = 6
    jobs, has_next = _list_jobs(q, page, per_page)
    return api_response(True, "Jobs fetched", jobs=jobs, page=page, has_next=has_next)

# Delete job
@admin_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
@admin_required
def api_delete_job(job_id):
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM jobs WHERE id=%s AND posted_by=%s",
                (job_id, session["user"]["id"]),
            )
            deleted = cursor.rowcount
    except Exception as e:
        return api_response(
            False, f"Cannot delete job (may have applications): {e}"
        ), 400

    if deleted:
        return api_response(True, "Job deleted successfully")
    return api_response(False, "Job not found or not allowed"), 404

# Get applications
@admin_bp.route("/applications/<int:job_id>", methods=["GET"])
@admin_required
def api_applications(job_id):
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    page = max(1, page)
    per_page = 10

    job, applicants, has_next = _get_applications(job_id, page, per_page)
    if not job:
        return api_response(False, "Job not found or not allowed"), 404
    return api_response(
        True,
        "Applications fetched",
        job=job,
        applicants=applicants,
        page=page,
        has_next=has_next,
    )

# Download resume
@admin_bp.route("/resumes/<filename>", methods=["GET"])
@admin_required
def api_download_resume(filename):
    safe_name = secure_filename(filename)
    file_path = os.path.join(RESUME_FOLDER, safe_name)
    if not os.path.exists(file_path):
        return api_response(False, "File not found"), 404
    return send_from_directory(RESUME_FOLDER, safe_name, as_attachment=True)

# Upload profile picture
@admin_bp.route("/profile/upload", methods=["POST"])
@admin_required
def api_upload_profile():
    file = request.files.get("profile_pic")
    if not file or file.filename == "":
        return api_response(False, "No file selected"), 400
    if not allowed_image_file(file.filename):
        return api_response(False, "Only PNG, JPG, JPEG allowed"), 400

    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_FILE_SIZE:
        return api_response(False, "File too large (max 2MB)"), 400
    file.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = secure_filename(f"admin{session['user']['id']}_{timestamp}.{ext}")
    filepath = os.path.join(PROFILE_PIC_FOLDER, filename)
    file.save(filepath)

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET profile_pic=%s WHERE id=%s",
            (filename, session["user"]["id"]),
        )

    session["user"]["profile_pic"] = filename
    return api_response(True, "Profile updated", filename=filename)

# Remove profile picture
@admin_bp.route("/profile/remove", methods=["POST"])
@admin_required
def api_remove_profile():
    old_pic = session["user"].get("profile_pic")
    if old_pic:
        filepath = os.path.join(PROFILE_PIC_FOLDER, old_pic)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Could not delete old admin profile pic: {e}")

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET profile_pic=NULL WHERE id=%s",
            (session["user"]["id"],),
        )

    session["user"].pop("profile_pic", None)
    return api_response(True, "Profile removed")

# Upload employer logo (only once)
@admin_bp.route("/upload-logo", methods=["POST"])
@admin_required
def upload_logo():
    file = request.files.get("logo")
    if not file or file.filename == "":
        return api_response(False, "No logo uploaded"), 400

    if not allowed_image_file(file.filename):
        return api_response(False, "Invalid file type"), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"employer{session['user']['id']}.{ext}"
    filepath = os.path.join(LOGO_FOLDER, filename)
    os.makedirs(LOGO_FOLDER, exist_ok=True)
    file.save(filepath)

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE employers SET logo_filename=%s WHERE id=%s",
            (filename, session["user"]["id"]),
        )
    session["user"]["logo_filename"] = filename
    
    return api_response(True, "Logo uploaded", logo_url=f"/uploads/logos/{filename}")
