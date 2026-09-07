from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime
from routes.technicians_routes import technician_bp
import mysql.connector
import os
from config import Config

app = Flask(__name__)
app.register_blueprint(technician_bp)
CORS(app)

# ---------- Database ----------
def get_db():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

# ---------- Home ----------
@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "IT Support Ticketing Backend Running"
    })

# ---------- Dashboard Page ----------

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")
# ---------- Users ----------
@app.route("/users")
def users():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, full_name, email, role
        FROM users
    """)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(data)

# ---------- Admin Tickets ----------

@app.route("/admin/tickets")
def admin_tickets():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.ticket_number,
            t.subject,
            t.priority,
            t.status,
            u.full_name AS technician
        FROM tickets t
        LEFT JOIN users u
            ON t.assigned_to = u.id
        ORDER BY t.id DESC
    """)

    tickets = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(tickets)

# ---------- Customer Tickets ----------

@app.route("/customer/tickets/<int:user_id>")
def customer_tickets(user_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.ticket_number,
            t.subject,
            t.status,
            u.full_name AS technician,
            t.resolution_notes
        FROM tickets t
        LEFT JOIN users u
            ON t.assigned_to = u.id
        WHERE t.customer_id = %s
        ORDER BY t.id DESC
    """, (user_id,))

    tickets = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(tickets)

# ---------- Assign Technician ----------

@app.route("/admin/assign", methods=["PUT"])
def assign_technician():

    data = request.get_json()

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE tickets
        SET assigned_to=%s,
            status='Assigned'
        WHERE ticket_number=%s
    """, (
        data["technician_id"],
        data["ticket_number"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({"success": True})

# ---------- Technician Page ----------

@app.route("/technicians")
def technicians_page():
    return render_template("technicians.html")

# ---------- Login Page ----------

@app.route("/login")
def login_page():
    return render_template("login.html")
# ---------- Login ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, full_name, email, role
        FROM users
        WHERE email=%s
        AND password_hash=%s
        AND account_status='active'
    """, (email, password))

    user = cursor.fetchone()

    cursor.close()
    db.close()

    if user:
        return jsonify({
            "success": True,
            "user": user
        })

    return jsonify({
        "success": False,
        "message": "Invalid email or password"
    }), 401

from datetime import datetime

@app.route("/tickets", methods=["POST"])
def create_ticket():

    data = request.get_json()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Generate ticket number
    cursor.execute("SELECT COUNT(*) AS total FROM tickets")
    total = cursor.fetchone()["total"] + 1

    ticket_number = f"TKT-{1000 + total}"

    cursor.execute("""
        INSERT INTO tickets
        (ticket_number, customer_id, created_by,
         subject, description, category_id, priority)

        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        ticket_number,
        data["customer_id"],
        data["customer_id"],
        data["subject"],
        data["description"],
        data["category_id"],
        data["priority"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "ticket_number": ticket_number
    })
# ---------- Single Ticket Details ----------

@app.route("/ticket/<ticket_number>")
def get_ticket(ticket_number):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT ticket_number,
               subject,
               description,
               priority,
               status
        FROM tickets
        WHERE ticket_number = %s
    """, (ticket_number,))

    ticket = cursor.fetchone()

    cursor.close()
    db.close()

    return jsonify(ticket)
    # ---------- Technician Assigned Tickets ----------

@app.route("/mytickets/<int:user_id>")
def my_tickets(user_id):
    ...

# ---------- Technician Assigned Tickets ----------
@app.route("/technician/tickets/<int:tech_id>")
def technician_tickets(tech_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT ticket_number, subject, priority, status
        FROM tickets
      WHERE assigned_to = %s
    """, (tech_id,))

    tickets = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(tickets)

# ---------- Update Ticket Status ----------

@app.route("/ticket/<ticket_number>", methods=["PUT"])
def update_ticket(ticket_number):

    data = request.get_json()

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status=%s,
            resolution_notes=%s
        WHERE ticket_number=%s
    """, (
        data["status"],
        data["resolution_notes"],
        ticket_number
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({"success": True})

print(app.url_map)

# ---------- Admin Dashboard ----------

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

# ---------- Customer Portal ----------

@app.route("/customer")
def customer_page():
    return render_template("customer.html")

@app.route("/customer/create-ticket", methods=["POST"])
def customer_create_ticket():

    data = request.get_json()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Generate Ticket Number
    cursor.execute("SELECT COUNT(*) AS total FROM tickets")
    total = cursor.fetchone()["total"] + 1
    ticket_number = f"TKT-{1000 + total}"

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO tickets
        (ticket_number, customer_id, created_by,
         subject, description, priority, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Open')
    """, (
        ticket_number,
        data["customer_id"],
        data["customer_id"],
        data["subject"],
        data["description"],
        data["priority"]
    ))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "ticket_number": ticket_number
    })

# ---------- Run Server ----------
if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True, port=5050)