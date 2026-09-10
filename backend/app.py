from flask import Flask, jsonify, request, render_template, session, redirect
from flask_cors import CORS
from datetime import datetime, timedelta,timezone
from functools import wraps
from routes.technicians_routes import technician_bp
import mysql.connector
import os
from config import Config

app = Flask(__name__)
app.register_blueprint(technician_bp)
app.secret_key = "change-this-to-a-random-secret-key"
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
    return render_template("login.html")

# ---------- Dashboard Page ----------


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
            t.response_due_at,
            t.resolution_due_at,
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
            t.priority,
            t.response_due_at,
            t.resolution_due_at,
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
    cursor = db.cursor(dictionary=True)

    technician_id = data.get("technician_id")
    ticket_number = data.get("ticket_number")

    if not ticket_number:
        cursor.close()
        db.close()
        return jsonify({"success": False, "message": "Ticket number is required"}), 400

    cursor.execute(
        "SELECT assigned_to, customer_id FROM tickets WHERE ticket_number = %s",
        (ticket_number,)
    )
    ticket = cursor.fetchone()

    if not ticket:
        cursor.close()
        db.close()
        return jsonify({"success": False, "message": "Ticket not found"}), 404

    old_tech = ticket["assigned_to"]
    customer = ticket["customer_id"]

    if technician_id:
        cursor.execute(
            """UPDATE tickets
               SET assigned_to = %s, status = 'Assigned'
               WHERE ticket_number = %s""",
            (technician_id, ticket_number)
        )
    else:
        cursor.execute(
            """UPDATE tickets
               SET assigned_to = NULL, status = 'Open'
               WHERE ticket_number = %s""",
            (ticket_number,)
        )

    db.commit()
    cursor.close()
    db.close()

    if technician_id:
        create_notification(
            technician_id, "New Ticket Assigned",
            f"{ticket_number} has been assigned to you.", "assignment"
        )

        if old_tech and str(old_tech) != str(technician_id):
            create_notification(
                old_tech, "Ticket Reassigned",
                f"{ticket_number} has been reassigned to another technician.",
                "reassignment"
            )

        if customer:
            create_notification(
                customer, "Technician Assigned",
                f"A technician has been assigned to {ticket_number}.",
                "assignment"
            )

    elif old_tech:
        create_notification(
            old_tech, "Ticket Unassigned",
            f"{ticket_number} is no longer assigned to you.",
            "unassignment"
        )

        if customer:
            create_notification(
                customer, "Technician Unassigned",
                f"{ticket_number} is currently unassigned.",
                "unassignment"
            )

    return jsonify({"success": True})

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if session.get("role") != "admin":
            return "Access Denied", 403
        return view(*args, **kwargs)
    return wrapped_view


def customer_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if session.get("role") != "customer":
            return "Access Denied", 403
        return view(*args, **kwargs)
    return wrapped_view


def technician_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        if session.get("role") != "technician":
            return "Access Denied", 403
        return view(*args, **kwargs)
    return wrapped_view
# ---------- Technician Page ----------

@app.route("/technicians")
@technician_required
def technicians_page():
    return render_template("technicians.html")

# ---------- Users API ----------

@app.route("/users")
@admin_required
def users():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            full_name,
            email,
            role,
            account_status
        FROM users
        ORDER BY role, full_name
    """)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(data)

# ---------- Add User ----------

@app.route("/users/add", methods=["POST"])
@admin_required
def add_user():

    data = request.get_json()

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check duplicate email
    cursor.execute(
        "SELECT id FROM users WHERE email=%s",
        (email,)
    )

    if cursor.fetchone():
        cursor.close()
        db.close()

        return jsonify({
            "success": False,
            "message": "Email already exists"
        }), 400

    # Insert user
    cursor.execute("""
        INSERT INTO users
        (
            full_name,
            email,
            password_hash,
            role,
            account_status
        )
        VALUES (%s, %s, %s, %s, 'active')
    """, (
        full_name,
        email,
        password,
        role
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True,
        "message": "User created successfully"
    })

# ---------- Update User ----------

@app.route("/users/update/<int:user_id>",methods=["PUT"])
@admin_required
def update_user(user_id):
    data=request.get_json()

    db=get_db()
    cursor=db.cursor(dictionary=True)

    cursor.execute(
        "SELECT id FROM users WHERE email=%s AND id!=%s",
        (data.get("email"),user_id)
    )

    if cursor.fetchone():
        cursor.close()
        db.close()
        return jsonify({"success":False,"message":"Email already exists"}),400

    if data.get("password"):
        cursor.execute("""
            UPDATE users
            SET full_name=%s,email=%s,password_hash=%s,role=%s,account_status=%s
            WHERE id=%s
        """,(
            data.get("full_name"),
            data.get("email"),
            data.get("password"),
            data.get("role"),
            data.get("account_status","active"),
            user_id
        ))
    else:
        cursor.execute("""
            UPDATE users
            SET full_name=%s,email=%s,role=%s,account_status=%s
            WHERE id=%s
        """,(
            data.get("full_name"),
            data.get("email"),
            data.get("role"),
            data.get("account_status","active"),
            user_id
        ))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success":True})

@app.route("/users/status/<int:user_id>",methods=["PUT"])
@admin_required
def update_user_status(user_id):
    data=request.get_json()

    db=get_db()
    cursor=db.cursor()

    cursor.execute("""
        UPDATE users
        SET account_status=%s
        WHERE id=%s
    """,(data["account_status"],user_id))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success":True})

# ---------- Login Page ----------

@app.route("/login")
def login_page():
    return render_template("login.html")
# ---------- Login ----------
@app.route("/login",methods=["POST"])
def login():
    data=request.get_json()

    db=get_db()
    cursor=db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s",(data["email"],))
    user=cursor.fetchone()

    cursor.close()
    db.close()

    if not user or user["password_hash"]!=data["password"]:
        return jsonify({"success":False,"message":"Invalid email or password"}),401

    if user["account_status"]=="inactive":
        return jsonify({"success":False,"message":"Account is inactive"}),403

    session.clear()
    session["user_id"]=user["id"]
    session["role"]=user["role"]
    session["full_name"]=user["full_name"]

    return jsonify({"success":True,"user":user})
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
        (ticket_number, -_id, created_by,
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

@app.route("/ticket/details/<ticket_number>")
def ticket_details(ticket_number):
    db=get_db()
    cursor=db.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.*,
               u.full_name AS technician_name
        FROM tickets t
       LEFT JOIN users u
ON t.assigned_to=u.id
        WHERE t.ticket_number=%s
    """,(ticket_number,))

    ticket=cursor.fetchone()

    cursor.close()
    db.close()

    if not ticket:
        return jsonify({"success":False,"message":"Ticket not found"}),404

    return jsonify(ticket)

from datetime import timedelta

from datetime import timedelta

@app.route("/ticket/comments/<ticket_number>")
def get_comments(ticket_number):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT tc.comment,
               tc.created_at,
               u.full_name,
               u.role
        FROM ticket_comments tc
        JOIN users u ON tc.user_id = u.id
        WHERE tc.ticket_number = %s
        ORDER BY tc.created_at ASC
    """, (ticket_number,))

    comments = cursor.fetchall()

    for c in comments:
        if c["created_at"]:
            c["created_at"] = c["created_at"].strftime("%d %b %Y %I:%M %p")

    cursor.close()
    db.close()

    return jsonify(comments)

@app.route("/ticket/comments", methods=["POST"])
def add_comment():
    data = request.get_json()

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO ticket_comments
        (ticket_number, user_id, comment)
        VALUES (%s, %s, %s)
    """, (
        data["ticket_number"],
        data["user_id"],
        data["comment"]
    ))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({"success": True})

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


@app.route("/technician/status",methods=["PUT"])
@technician_required
def technician_update_status():
    data=request.get_json()

    db=get_db()
    cursor=db.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status=%s
        WHERE ticket_number=%s
    """,(data["status"],data["ticket_number"]))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success":True})

# ---------- Update Ticket Status ----------
@app.route("/ticket/<ticket_number>", methods=["PUT"])
def update_ticket(ticket_number):
    data = request.get_json()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT status, customer_id
        FROM tickets
        WHERE ticket_number = %s
    """, (ticket_number,))

    ticket = cursor.fetchone()

    if not ticket:
        cursor.close()
        db.close()
        return jsonify({
            "success": False,
            "message": "Ticket not found"
        }), 404

    old_status = ticket["status"]
    customer_id = ticket["customer_id"]
    new_status = data["status"]
    resolution_notes = data.get("resolution_notes", "")

    cursor.execute("""
        UPDATE tickets
        SET status = %s,
            resolution_notes = %s
        WHERE ticket_number = %s
    """, (
        new_status,
        resolution_notes,
        ticket_number
    ))

    db.commit()

    cursor.close()
    db.close()

    # Only notify when the status actually changes
    if old_status != new_status:

        if new_status == "Resolved":
            title = "Ticket Resolved"
            message = f"{ticket_number} has been resolved."
        else:
            title = "Ticket Updated"
            message = f"{ticket_number} is now {new_status}."

        # Notify customer
        if customer_id:
            create_notification(
                customer_id,
                title,
                message,
                "status"
            )

        # Notify all admins
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM users
            WHERE role = 'admin'
        """)

        admins = cursor.fetchall()

        cursor.close()
        db.close()

        for admin in admins:
            create_notification(
                admin["id"],
                title,
                message,
                "status"
            )

    return jsonify({
        "success": True
    })

# ---------- Admin Dashboard ----------
@app.route("/admin")
@admin_required
def admin_page():
    return render_template("admin.html")

@app.route("/admin/reports-page")
@admin_required
def admin_reports_page():
    return render_template("admin_reports.html")

@app.route("/admin/reports")
@admin_required
def admin_reports():
    db=get_db()
    cursor=db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) total FROM tickets")
    total=cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) open FROM tickets WHERE status='Open'")
    open_t=cursor.fetchone()["open"]

    cursor.execute("SELECT COUNT(*) progress FROM tickets WHERE status='In Progress'")
    progress=cursor.fetchone()["progress"]

    cursor.execute("SELECT COUNT(*) resolved FROM tickets WHERE status='Resolved'")
    resolved=cursor.fetchone()["resolved"]

    cursor.execute("""
        SELECT priority,COUNT(*) count
        FROM tickets
        GROUP BY priority
    """)
    priority=cursor.fetchall()

    cursor.execute("""
        SELECT u.full_name,COUNT(t.id) tickets
        FROM users u
        LEFT JOIN tickets t
        ON u.id=t.assigned_to
        WHERE u.role='technician'
        GROUP BY u.id,u.full_name
    """)
    technicians=cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
        "total":total,
        "open":open_t,
        "progress":progress,
        "resolved":resolved,
        "priority":priority,
        "technicians":technicians
    })

# ---------- Customer Portal ----------

@app.route("/customer")
@customer_required
def customer_page():
    return render_template("customer.html")

from datetime import datetime, timedelta

@app.route("/customer/create-ticket", methods=["POST"])
def customer_create_ticket():
    data = request.get_json()
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM tickets")
    total = cursor.fetchone()["total"] + 1
    ticket_number = f"TKT-{1000 + total}"

    sla = {
        "Low": (timedelta(hours=4), timedelta(hours=48)),
        "Medium": (timedelta(hours=2), timedelta(hours=24)),
        "High": (timedelta(minutes=30), timedelta(hours=4)),
        "Critical": (timedelta(minutes=15), timedelta(hours=2))
    }

    priority = data.get("priority", "Medium")
    now = datetime.now()
    response_due = now + sla[priority][0]
    resolution_due = now + sla[priority][1]

    cursor.execute("""
        INSERT INTO tickets
        (
            ticket_number,
            customer_id,
            created_by,
            subject,
            description,
            priority,
            status,
            response_due_at,
            resolution_due_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, 'Open', %s, %s)
    """, (
        ticket_number,
        data["customer_id"],
        data["customer_id"],
        data["subject"],
        data["description"],
        priority,
        response_due,
        resolution_due
    ))

    db.commit()
    cursor.close()
    db.close()

    # Notify all admins
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id
        FROM users
        WHERE role = 'admin'
    """)

    admins = cursor.fetchall()

    cursor.close()
    db.close()

    for admin in admins:
        create_notification(
            admin["id"],
            "New Ticket Created",
            f"{ticket_number} has been created by a customer.",
            "ticket"
        )

    return jsonify({
        "success": True,
        "ticket_number": ticket_number,
        "response_due_at": response_due.strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_due_at": resolution_due.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/ticket/view/<ticket_number>")
def ticket_view_page(ticket_number):
    return render_template("ticket_details.html")

#notification#
def create_notification(user_id, title, message, notification_type="info"):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO notifications
        (user_id, title, message, type)
        VALUES (%s, %s, %s, %s)
    """, (
        user_id,
        title,
        message,
        notification_type
    ))

    db.commit()

    cursor.close()
    db.close()


#user notification#
@app.route("/notifications/<int:user_id>", methods=["GET"])
def get_notifications(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            title,
            message,
            type,
            is_read,
            created_at
        FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """, (user_id,))

    notifications = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify(notifications)


@app.route("/notifications/<int:notification_id>/read", methods=["PUT"])
def mark_notification_read(notification_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read = TRUE
        WHERE id = %s
    """, (notification_id,))

    db.commit()

    cursor.close()
    db.close()

    return jsonify({
        "success": True
    })
def check_sla_notifications():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT ticket_number, customer_id, assigned_to,
               response_due_at, resolution_due_at
        FROM tickets
        WHERE status NOT IN ('Resolved', 'Closed')
    """)
    tickets = cursor.fetchall()

    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    admins = [a["id"] for a in cursor.fetchall()]

    for ticket in tickets:
        recipients = set(admins)

        if ticket["customer_id"]:
            recipients.add(ticket["customer_id"])

        if ticket["assigned_to"]:
            recipients.add(ticket["assigned_to"])

        for user_id in recipients:

            for sla_type, due_at in [
                ("response", ticket["response_due_at"]),
                ("resolution", ticket["resolution_due_at"])
            ]:
                if not due_at:
                    continue

                minutes_left = (
                    due_at - datetime.now(timezone.utc).replace(tzinfo=None)
                ).total_seconds() / 60

                if minutes_left <= 0:
                    event_key = f"{ticket['ticket_number']}-{sla_type}-overdue"
                    title = f"{sla_type.title()} SLA Overdue"
                    message = (
                        f"{ticket['ticket_number']} has exceeded "
                        f"its {sla_type} SLA."
                    )

                elif minutes_left <= 30:
                    event_key = f"{ticket['ticket_number']}-{sla_type}-warning"
                    title = f"{sla_type.title()} SLA Approaching"
                    message = (
                        f"{ticket['ticket_number']} {sla_type} deadline "
                        f"is approaching."
                    )

                else:
                    continue

                cursor.execute("""
                    SELECT id
                    FROM notifications
                    WHERE user_id = %s AND event_key = %s
                    LIMIT 1
                """, (user_id, event_key))

                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO notifications
                        (user_id, title, message, type, event_key)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        title,
                        message,
                        "sla",
                        event_key
                    ))

    db.commit()
    cursor.close()
    db.close()

@app.route("/admin/users")
@admin_required
def admin_users_page():
    return render_template("admin_users.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- Run Server ----------
if __name__ == "__main__":
    print(app.url_map)
    app.run(debug=True, port=5050)