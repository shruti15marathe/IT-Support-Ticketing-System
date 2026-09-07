from flask import Blueprint,jsonify,render_template
from database import query
from auth import login_required
bp=Blueprint('dashboard',__name__,url_prefix='/api/dashboard')
page_bp = Blueprint("dashboard_page", __name__)

@page_bp.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")
@login_required
def dashboard(user):
    extra,vals=(' AND assigned_technician_id=%s',(user['id'],)) if user['role']=='technician' else (' AND customer_id=(SELECT id FROM customers WHERE user_id=%s)',(user['id'],)) if user['role']=='customer' else ('',())
    base='SELECT COUNT(*) n FROM tickets WHERE 1=1'+extra
    statuses={s:query(base+' AND status=%s',vals+(s,),fetch=True)[0]['n'] for s in ['Open','Assigned','In Progress','Waiting for Customer','Resolved','Closed','Reopened']}
    total=query(base,vals,fetch=True)[0]['n']; critical=query(base+' AND priority="Critical"',vals,fetch=True)[0]['n']
    by_status=query('SELECT status label,COUNT(*) value FROM tickets WHERE 1=1'+extra+' GROUP BY status',vals,fetch=True)
    by_priority=query('SELECT priority label,COUNT(*) value FROM tickets WHERE 1=1'+extra+' GROUP BY priority',vals,fetch=True)
    by_category=query('SELECT c.name label,COUNT(t.id) value FROM categories c JOIN tickets t ON t.category_id=c.id WHERE 1=1'+extra+' GROUP BY c.id',vals,fetch=True)
    by_tech=query('SELECT COALESCE(u.full_name,"Unassigned") label,COUNT(t.id) value FROM tickets t LEFT JOIN users u ON u.id=t.assigned_technician_id WHERE 1=1'+extra+' GROUP BY t.assigned_technician_id',vals,fetch=True)
    monthly=query("SELECT DATE_FORMAT(created_at,'%Y-%m') label,COUNT(*) value FROM tickets WHERE created_at>=DATE_SUB(CURDATE(),INTERVAL 11 MONTH)"+extra+' GROUP BY label ORDER BY label',vals,fetch=True)
    recent=query("SELECT t.id,t.ticket_number,t.subject,t.priority,t.status,t.created_at,c.company_name customer_name,u.full_name technician_name FROM tickets t JOIN customers c ON c.id=t.customer_id LEFT JOIN users u ON u.id=t.assigned_technician_id WHERE 1=1"+extra+' ORDER BY t.id DESC LIMIT 8',vals,fetch=True)
    return jsonify({'cards':{'total':total,**statuses,'Critical':critical},'charts':{'status':by_status,'priority':by_priority,'category':by_category,'technician':by_tech,'monthly':monthly},'recent':recent})
