# =====================================================================
# FLASK BACKEND SYSTEM (IPT-101 TYPHOON DASHBOARD)
# =====================================================================
# WHAT:
# This is the main backend controller of the IPT-101 Typhoon Dashboard system.
#
# PURPOSE:
# - Handles routing (web pages + API)
# - Connects frontend (Jinja2 templates) with backend (Python logic)
# - Manages authentication system (login/logout)
# - Processes dataset using OOP ETL pipeline
# - Generates charts using Matplotlib
#
# SYSTEM ARCHITECTURE FLOW:
#
# CSV DATA → TyphoonDataProcessor (ETL CLASS)
#          → CLEANED DATAFRAME
#          → FLASK ROUTES (filtering, stats, APIs)
#          → JINJA2 TEMPLATES (HTML rendering)
#          → MATPLOTLIB (chart generation)
#          → STATIC FILE OUTPUT (PNG downloads)
# =====================================================================


# =====================================================================
# IMPORT PHASE
# =====================================================================
# WHAT:
# Imports required libraries for web framework, authentication,
# file handling, and data processing integration.
#
# WHY EACH IMPORT IS USED:
#
# - Flask:
#   Core web framework used to create routes and handle HTTP requests.
#
# - render_template:
#   Used to render HTML pages using Jinja2 templating engine.
#
# - request:
#   Reads incoming HTTP data (GET parameters, POST form data).
#
# - jsonify:
#   Converts Python dictionaries/lists into JSON responses for API.
#
# - session:
#   Stores user login state securely using cookies.
#
# - redirect / url_for:
#   Handles navigation between routes safely.
#
# - send_file:
#   Used to return downloadable files (charts/images).
#
# - wraps:
#   Used to preserve function metadata in decorators.
#
# - TyphoonDataProcessor:
#   Custom OOP ETL class responsible for all data cleaning and analysis.
#
# - os:
#   Used for file path operations (chart export system).
# =====================================================================
from flask import (
    Flask, render_template, request,
    jsonify, session, redirect,
    url_for, send_file
)
from functools import wraps
from data_processor import TyphoonDataProcessor
import os


# =====================================================================
# FLASK APPLICATION INITIALIZATION
# =====================================================================
# WHAT:
# Creates the Flask application instance that handles all routing.
#
# WHY secret_key IS IMPORTANT:
# - Encrypts session cookies
# - Protects authentication data
# - Required for login system to function
# =====================================================================
app = Flask(__name__)
app.secret_key = "ipt101-2025"


# =====================================================================
# DATA PROCESSOR INITIALIZATION (OOP ETL ENGINE)
# =====================================================================
# WHAT:
# Creates a global instance of TyphoonDataProcessor.
#
# WHY GLOBAL INSTANCE IS USED:
# - Prevents repeated CSV loading on every request
# - Improves performance significantly
# - Maintains a single consistent dataset in memory
# =====================================================================
processor = TyphoonDataProcessor("typhoon_impacts.csv")
processor.load_and_clean()


# =====================================================================
# ADMIN ACCOUNT (AUTHENTICATION LAYER)
# =====================================================================
# WHAT:
# Defines a simple administrator account for login validation.
#
# WHY THIS EXISTS:
# - Controls access to admin dashboard
# - Demonstrates authentication concept
#
# LIMITATIONS:
# - Not secure (plain text password)
# - No database storage
# - Suitable only for educational use
# =====================================================================
ADMIN = {
    "username": "admin",
    "password": "admin123",
    "name": "Administrator",
    "email": "admin@ipt101.edu"
}


# =====================================================================
# MEMBERS DATA STORE (IN-MEMORY DATABASE)
# =====================================================================
# WHAT:
# Stores editable student/member information.
#
# WHY DICTIONARY IS USED:
# - Fast lookup using ID
# - Easy modification from admin panel
# - Works well with Flask rendering
#
# LIMITATION:
# - No persistence (resets on restart)
# =====================================================================
MEMBERS = {
    1: {"name": "Member 1", "email": "member1@ipt101.edu", "course": "BSIT", "batch": "2025-2026"},
    2: {"name": "Member 2", "email": "member2@ipt101.edu", "course": "BSIT", "batch": "2025-2026"},
    3: {"name": "Member 3", "email": "member3@ipt101.edu", "course": "BSIT", "batch": "2025-2026"},
    4: {"name": "Member 4", "email": "member4@ipt101.edu", "course": "BSIT", "batch": "2025-2026"},
    5: {"name": "Member 5", "email": "member5@ipt101.edu", "course": "BSIT", "batch": "2025-2026"},
}


# =====================================================================
# LOGIN REQUIRED DECORATOR (SECURITY LAYER)
# =====================================================================
# WHAT:
# Protects routes from unauthorized access.
#
# HOW IT WORKS:
# - Checks session["logged_in"]
# - If False → redirect to login page
# - If True → allow access to function
# =====================================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated


# =====================================================================
# DASHBOARD ROUTE (MAIN ANALYTICS PAGE)
# =====================================================================
@app.route("/")
@login_required
def dashboard():

    # WHAT:
    # This route renders the main dashboard with analytics and tables.

    try:
        processor.load_and_clean()

        # WHAT:
        # Retrieves year filter from URL query parameter
        year = request.args.get("year", "all")

        # WHAT:
        # Filters dataset using OOP method
        df = processor.filter_by_year(year)

        # WHAT:
        # Sends processed analytics to frontend UI
        return render_template(
            "dashboard.html",
            stats=processor.get_stats(df),
            years=processor.get_years(),
            selected_year=year,
            all_data=processor.to_records(processor.df),
            table_data=processor.to_records(df),
        )

    except Exception as e:
        return render_template("error.html", message=str(e)), 500


# =====================================================================
# EXPORT CHART ROUTE (MATPLOTLIB DOWNLOAD SYSTEM)
# =====================================================================
@app.route("/export/chart")
@login_required
def export_chart():

    # WHAT:
    # Allows user to download generated charts as PNG files.

    try:
        processor.load_and_clean()

        year = request.args.get("year", "all")
        chart_type = request.args.get("type", "bar")

        # WHAT:
        # Filters dataset for chart generation
        df = processor.filter_by_year(year)

        # WHAT:
        # Calls Matplotlib chart generator
        charts = processor.generate_charts(df)

        chart_map = {
            "bar": "bar",
            "line": "line",
            "doughnut": "pie"
        }

        chart_key = chart_map.get(chart_type, "bar")
        filename = charts[chart_key]

        # WHAT:
        # Builds full file path for download
        file_path = os.path.join(
            app.root_path, "static", "charts", filename
        )

        download_name = f"matplotlib_{chart_key}_{year}.png"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        return render_template("error.html", message=str(e)), 500


# =====================================================================
# MEMBER PAGE ROUTE (REFLECTION SYSTEM)
# =====================================================================
@app.route("/member/<int:mid>")
@login_required
def member_page(mid):

    # WHAT:
    # Displays individual student reflection page.

    # VALIDATION:
    # Prevent invalid member access outside range
    if mid < 1 or mid > 5:
        return render_template("404.html"), 404

    # WHAT:
    # Each member contains UI + reflection data
    # (skills, tags, learning experience)

    data = {
        1: {...},
        2: {...},
        3: {...},
        4: {...},
        5: {...},
    }

    return render_template("member.html", member=data[mid], mid=mid)


# =====================================================================
# LOGIN ROUTE (AUTHENTICATION SYSTEM)
# =====================================================================
@app.route("/login", methods=["GET", "POST"])
def login():

    # WHAT:
    # Handles user login authentication.

    if session.get("logged_in"):
        return redirect(url_for("admin_panel"))

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # WHAT:
        # Validates credentials against admin account
        if username == ADMIN["username"] and password == ADMIN["password"]:

            session["logged_in"] = True
            session["name"] = ADMIN["name"]

            return redirect(url_for("admin_panel"))

        error = "Invalid username or password."

    return render_template("login.html", error=error)


# =====================================================================
# LOGOUT ROUTE (SESSION CLEARING)
# =====================================================================
@app.route("/logout")
def logout():

    # WHAT:
    # Clears session data and logs user out.
    session.clear()
    return redirect(url_for("login"))


# =====================================================================
# ADMIN PANEL ROUTE (CONTROL CENTER)
# =====================================================================
@app.route("/admin")
@login_required
def admin_panel():

    # WHAT:
    # Central admin dashboard showing analytics + member management.

    flash_msg = session.pop("flash", None)

    return render_template(
        "admin.html",
        stats=processor.get_stats(processor.df),
        all_data=processor.to_records(processor.df),
        yearly=processor.get_yearly_totals(),
        members=MEMBERS,
        flash_msg=flash_msg
    )


# =====================================================================
# EDIT MEMBER ROUTE (UPDATE OPERATION - CRUD)
# =====================================================================
@app.route("/admin/members/edit/<int:mid>", methods=["GET", "POST"])
@login_required
def edit_member(mid):

    # WHAT:
    # Allows admin to modify member data.

    if mid not in MEMBERS:
        return render_template("404.html"), 404

    error = success = None

    if request.method == "POST":

        MEMBERS[mid]["name"] = request.form.get("name", MEMBERS[mid]["name"])
        MEMBERS[mid]["email"] = request.form.get("email", MEMBERS[mid]["email"])
        MEMBERS[mid]["course"] = request.form.get("course", MEMBERS[mid]["course"])
        MEMBERS[mid]["batch"] = request.form.get("batch", MEMBERS[mid]["batch"])

        success = f"Member {mid} updated successfully."

    return render_template(
        "edit_member.html",
        mid=mid,
        member=MEMBERS[mid],
        error=error,
        success=success
    )


# =====================================================================
# PROFILE ROUTE (ADMIN SETTINGS MANAGEMENT)
# =====================================================================
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # WHAT:
    # Handles admin profile updates and password changes.

    error = success = None

    if request.method == "POST":

        ADMIN["name"] = request.form.get("name", ADMIN["name"])
        ADMIN["email"] = request.form.get("email", ADMIN["email"])

        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "").strip()

        if new:
            if current != ADMIN["password"]:
                error = "Current password is incorrect."
            else:
                ADMIN["password"] = new
                success = "Password updated successfully."

        if not error:
            session["name"] = ADMIN["name"]
            session["flash"] = "Profile updated successfully."
            return redirect(url_for("admin_panel"))

    return render_template(
        "profile.html",
        username="admin",
        user=ADMIN,
        error=error,
        success=success
    )


# =====================================================================
# API ROUTES (DATA ENDPOINTS)
# =====================================================================

@app.route("/api/data")
def api_data():

    # WHAT:
    # Returns dataset in JSON format (optionally filtered)

    processor.load_and_clean()

    year = request.args.get("year", "all")
    df = processor.filter_by_year(year)

    return jsonify(processor.to_records(df))


@app.route("/api/stats")
def api_stats():

    # WHAT:
    # Returns computed KPI statistics in JSON format

    return jsonify(processor.get_stats(processor.df))


@app.route("/api/typhoon/<name>")
def api_typhoon(name):

    # WHAT:
    # Searches typhoon record by name (case-insensitive match)

    row = processor.df[
        processor.df["Typhoon"].str.upper() == name.upper()
    ]

    if row.empty:
        return jsonify({"error": "Not found"}), 404

    return jsonify(processor.to_records(row))


# =====================================================================
# ERROR HANDLING SYSTEM
# =====================================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Internal server error."), 500


# =====================================================================
# APPLICATION ENTRY POINT
# =====================================================================
if __name__ == "__main__":

    print("\n IPT-101 Typhoon Dashboard")
    print(" Open: http://127.0.0.1:5000")
    print(" Login: admin / admin123\n")

    app.run(debug=True)
