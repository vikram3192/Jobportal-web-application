from flask import Flask, session, send_from_directory, abort, render_template, redirect, url_for
from flask_cors import CORS
from datetime import timedelta
from blueprints import auth_bp, user_bp, admin_bp
from config import SECRET_KEY, PROFILE_PIC_FOLDER,LOGO_FOLDER

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ---------------- Session & Security ----------------
    app.secret_key = SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False   # set True in production with HTTPS
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit

    # ---------------- CORS ----------------
    CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000"])

    # ---------------- Blueprints ----------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # ---------------- Public Routes ----------------
    @app.route("/")
    def home():
        return redirect(url_for("login_page"))

    @app.route("/login")
    def login_page():
        return render_template("auth/login.html")

    @app.route("/register")
    def register_page():
        return render_template("auth/register.html")

    # ---------------- User Dashboard ----------------
    @app.route("/user_dashboard")
    def user_dashboard():
        if "user" not in session:
            return redirect(url_for("login_page"))
        return render_template("user/user_dashboard.html")


    # ---------------- Admin Dashboard ----------------
    @app.route("/admin_dashboard")
    def admin_dashboard():
        if "user" not in session :
            return redirect(url_for("login_page"))
        return render_template("admin/admin_dashboard.html")

    # ---------------- User Job Detail Page ----------------
    @app.route("/job_detail/<int:job_id>")
    def job_detail_page(job_id):
        if "user" not in session:
            return redirect(url_for("login_page"))
        return render_template("user/job_detail.html", job_id=job_id)

    # ---------------- Admin Applications Page ----------------
    @app.route("/applications")
    def applications_page():
        if "user" not in session :
            return redirect(url_for("login_page"))
        return render_template("admin/applications.html")

    # ---------------- Protected Uploads ----------------
    @app.route("/uploads/profile_pics/<filename>")
    def uploaded_file(filename):
        if "user" not in session :
            abort(403)
        return send_from_directory(PROFILE_PIC_FOLDER, filename)
    
    @app.route("/uploads/logos/<filename>")
    def uploaded_logo(filename):
        if "user" not in session:
            abort(403)
        return send_from_directory(LOGO_FOLDER, filename)
    
    # ---------------- Error Handlers ----------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("auth/login.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
