from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "vidyasathi-secret-key-2026"


# ---------------------------------------------------------
# MYSQL CONNECTION
# ---------------------------------------------------------

import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", ""),
        database=os.environ.get("MYSQLDATABASE", "vidyasathi_db")
    )

# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scholarships")
    scholarship_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM government_schemes")
    scheme_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM updates")
    update_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        "home.html",
        scholarship_count=scholarship_count,
        scheme_count=scheme_count,
        update_count=update_count
    )


# ---------------------------------------------------------
# ABOUT
# ---------------------------------------------------------

@app.route("/about")
def about():
    return render_template("about.html")


# ---------------------------------------------------------
# SCHOLARSHIPS - PUBLIC
# ---------------------------------------------------------

@app.route("/scholarships")
def scholarships():
    query = request.args.get("q", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if query:
        search = "%" + query + "%"

        cursor.execute(
            """
            SELECT *
            FROM scholarships
            WHERE name LIKE %s
               OR category LIKE %s
               OR description LIKE %s
               OR eligibility LIKE %s
            ORDER BY id DESC
            """,
            (search, search, search, search)
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM scholarships
            ORDER BY id DESC
            """
        )

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in items:
        item["title"] = item.get("name", "")
        item["amount"] = "See official details"
        item["description"] = item.get("description", "")
        item["eligibility"] = item.get("eligibility", "")
        item["category"] = item.get("category", "")
        item["deadline"] = item.get("deadline", "")
        item["official_link"] = item.get("official_link", "")
        item["documents"] = "Check official scholarship guidelines"

    return render_template(
        "list.html",
        page_title="Scholarships",
        page_subtitle="Explore scholarship opportunities, benefits, eligibility and important deadlines.",
        items=items,
        kind="scholarship",
        query=query
    )


# ---------------------------------------------------------
# GOVERNMENT SCHEMES - PUBLIC
# ---------------------------------------------------------

@app.route("/schemes")
@app.route("/government-schemes")
def schemes():
    query = request.args.get("q", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if query:
        search = "%" + query + "%"

        cursor.execute(
            """
            SELECT *
            FROM government_schemes
            WHERE name LIKE %s
               OR category LIKE %s
               OR description LIKE %s
               OR eligibility LIKE %s
            ORDER BY id DESC
            """,
            (search, search, search, search)
        )
    else:
        cursor.execute(
            """
            SELECT *
            FROM government_schemes
            ORDER BY id DESC
            """
        )

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in items:
        item["title"] = item.get("name", "")
        item["description"] = item.get("description", "")
        item["eligibility"] = item.get("eligibility", "")
        item["category"] = item.get("category", "")
        item["deadline"] = item.get("deadline", "")
        item["amount"] = "See official details"
        item["benefits"] = "See official scheme guidelines"
        item["official_link"] = item.get("official_link", "")
        item["documents"] = "Check official scheme guidelines"

    return render_template(
        "list.html",
        page_title="Government Schemes",
        page_subtitle="Explore government schemes, benefits, eligibility and important information.",
        items=items,
        kind="scheme",
        query=query
    )


# ---------------------------------------------------------
# DETAILS
# ---------------------------------------------------------

@app.route("/details/<int:item_id>")
def details(item_id):
    kind = request.args.get("kind", "scholarship")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if kind == "scheme":
        cursor.execute(
            """
            SELECT *
            FROM government_schemes
            WHERE id = %s
            """,
            (item_id,)
        )

        item = cursor.fetchone()

        if item:
            item["title"] = item.get("name", "")
            item["amount"] = "See official details"
            item["benefits"] = "See official scheme guidelines"
            item["documents"] = "Check official scheme guidelines"

    else:
        cursor.execute(
            """
            SELECT *
            FROM scholarships
            WHERE id = %s
            """,
            (item_id,)
        )

        item = cursor.fetchone()

        if item:
            item["title"] = item.get("name", "")
            item["amount"] = "See official details"
            item["documents"] = "Check official scholarship guidelines"

    cursor.close()
    conn.close()

    if not item:
        return render_template("404.html"), 404

    return render_template(
        "details.html",
        item=item,
        kind=kind
    )


# ---------------------------------------------------------
# LATEST UPDATES - PUBLIC
# ---------------------------------------------------------

@app.route("/updates")
def updates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM updates
        ORDER BY update_date DESC, id DESC
        """
    )

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    for item in items:
        item["date"] = item.get("update_date", "")

    return render_template(
        "updates.html",
        items=items,
        updates=items
    )


# ---------------------------------------------------------
# ELIGIBILITY CHECKER
# ---------------------------------------------------------

@app.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    results = []
    message = ""
    student_class = ""
    gender = ""
    category = ""
    annual_income = ""

    if request.method == "POST":
        student_class = request.form.get("class", "")
        gender = request.form.get("gender", "")
        category = request.form.get("category", "")
        annual_income = request.form.get("annual_income", "")

        try:
            income = float(annual_income)
        except (ValueError, TypeError):
            income = 0

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM scholarships
            WHERE (category = %s OR category = 'General')
              AND (
                    annual_income_limit IS NULL
                    OR annual_income_limit = 0
                    OR annual_income_limit >= %s
              )
            ORDER BY id DESC
            """,
            (category, income)
        )

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if results:
            message = (
                "Great! We found scholarship opportunities "
                "that may match your information."
            )
        else:
            message = (
                "No matching scholarships were found "
                "for the information entered."
            )

    return render_template(
        "eligibility.html",
        results=results,
        message=message,
        student_class=student_class,
        gender=gender,
        category=category,
        annual_income=annual_income
    )


# ---------------------------------------------------------
# ADMIN LOGIN
# ---------------------------------------------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM admin WHERE username = %s",
            (username,)
        )

        admin_user = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin_user and check_password_hash(
            admin_user["password"],
            password
        ):
            session["admin_logged_in"] = True
            session["admin_username"] = username

            return redirect(url_for("admin_dashboard"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password."
        )

    return render_template("admin_login.html")


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scholarships")
    scholarship_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM government_schemes")
    scheme_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM updates")
    update_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        scholarship_count=scholarship_count,
        scheme_count=scheme_count,
        update_count=update_count
    )


# ---------------------------------------------------------
# ADMIN - MANAGE SCHOLARSHIPS
# ---------------------------------------------------------

@app.route("/admin/scholarships", methods=["GET", "POST"])
def manage_scholarships():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        eligibility_text = request.form.get("eligibility", "").strip()
        category = request.form.get("category", "").strip()
        annual_income_limit = request.form.get("annual_income_limit") or None
        deadline = request.form.get("deadline") or None
        official_link = request.form.get("official_link", "").strip()

        cursor.execute(
            """
            INSERT INTO scholarships
            (name, description, eligibility, category,
             annual_income_limit, deadline, official_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                name,
                description,
                eligibility_text,
                category,
                annual_income_limit,
                deadline,
                official_link
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("manage_scholarships"))

    cursor.execute(
        "SELECT * FROM scholarships ORDER BY id DESC"
    )

    scholarship_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "manage_scholarships.html",
        scholarships=scholarship_list
    )


# ---------------------------------------------------------
# ADMIN - DELETE SCHOLARSHIP
# ---------------------------------------------------------

@app.route("/admin/scholarships/delete/<int:scholarship_id>")
def delete_scholarship(scholarship_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM scholarships WHERE id = %s",
        (scholarship_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("manage_scholarships"))


# ---------------------------------------------------------
# ADMIN - MANAGE GOVERNMENT SCHEMES
# ---------------------------------------------------------

@app.route("/admin/schemes", methods=["GET", "POST"])
def manage_schemes():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        eligibility_text = request.form.get("eligibility", "").strip()
        category = request.form.get("category", "").strip()
        annual_income_limit = request.form.get("annual_income_limit") or None
        deadline = request.form.get("deadline") or None
        official_link = request.form.get("official_link", "").strip()

        cursor.execute(
            """
            INSERT INTO government_schemes
            (name, description, eligibility, category,
             annual_income_limit, deadline, official_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                name,
                description,
                eligibility_text,
                category,
                annual_income_limit,
                deadline,
                official_link
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("manage_schemes"))

    cursor.execute(
        "SELECT * FROM government_schemes ORDER BY id DESC"
    )

    schemes_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "manage_schemes.html",
        schemes=schemes_list
    )


# ---------------------------------------------------------
# ADMIN - DELETE GOVERNMENT SCHEME
# ---------------------------------------------------------

@app.route("/admin/schemes/delete/<int:scheme_id>")
def delete_scheme(scheme_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM government_schemes WHERE id = %s",
        (scheme_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("manage_schemes"))


# ---------------------------------------------------------
# ADMIN - MANAGE UPDATES
# ---------------------------------------------------------

@app.route("/admin/updates", methods=["GET", "POST"])
def manage_updates():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        update_date = request.form.get("update_date") or None
        link = request.form.get("link", "").strip()

        cursor.execute(
            """
            INSERT INTO updates
            (title, description, update_date, link)
            VALUES (%s, %s, %s, %s)
            """,
            (title, description, update_date, link)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("manage_updates"))

    cursor.execute(
        """
        SELECT *
        FROM updates
        ORDER BY update_date DESC, id DESC
        """
    )

    updates_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "manage_updates.html",
        updates=updates_list
    )


# ---------------------------------------------------------
# ADMIN - DELETE UPDATE
# ---------------------------------------------------------

@app.route("/admin/updates/delete/<int:update_id>")
def delete_update(update_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM updates WHERE id = %s",
        (update_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("manage_updates"))


# ---------------------------------------------------------
# ADMIN LOGOUT
# ---------------------------------------------------------

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)

    return redirect(url_for("admin"))


# ---------------------------------------------------------
# 404 ERROR PAGE
# ---------------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


# ---------------------------------------------------------
# START FLASK APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
