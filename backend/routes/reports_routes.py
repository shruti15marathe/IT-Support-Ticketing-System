from flask import Blueprint,request,jsonify
from database import query
from auth import roles
bp=Blueprint('reports',__name__,url_prefix='/api/reports')
def filters():
    w=' WHERE 1=1';v=[]
    for col,key in [('t.assigned_technician_id','technician'),('t.customer_id','customer'),('t.priority','priority'),('t.category_id','category'),('t.status','status')]:
        if request.args.get(key):w+=f' AND {col}=%s';v.append(request.args[key])
    if request.args.get('from'):w+=' AND DATE(t.created_at)>=%s';v.append(request.args['from'])
    if request.args.get('to'):w+=' AND DATE(t.created_at)<=%s';v.append(request.args['to'])
    return w,v
@bp.get('')
@roles('admin')
def report(user):
    w,v=filters();
    summary=query('SELECT COUNT(*) total,SUM(status="Open") open_count,SUM(status="Closed") closed_count,SUM(status="Resolved") resolved_count FROM tickets t'+w,tuple(v),fetch=True)[0]
    by_priority=query('SELECT priority label,COUNT(*) value FROM tickets t'+w+' GROUP BY priority',tuple(v),fetch=True)
    by_category=query('SELECT c.name label,COUNT(t.id) value FROM tickets t JOIN categories c ON c.id=t.category_id'+w+' GROUP BY c.id',tuple(v),fetch=True)
    by_tech=query('SELECT COALESCE(u.full_name,"Unassigned") label,COUNT(t.id) value FROM tickets t LEFT JOIN users u ON u.id=t.assigned_technician_id'+w+' GROUP BY t.assigned_technician_id',tuple(v),fetch=True)
    by_status=query('SELECT status label,COUNT(*) value FROM tickets t'+w+' GROUP BY status',tuple(v),fetch=True)
    table=query('SELECT t.ticket_number,t.subject,c.company_name customer_name,COALESCE(u.full_name,"Unassigned") technician_name,t.priority,t.status,t.created_at FROM tickets t JOIN customers c ON c.id=t.customer_id LEFT JOIN users u ON u.id=t.assigned_technician_id'+w+' ORDER BY t.created_at DESC',tuple(v),fetch=True)
    return jsonify({'summary':summary,'charts':{'priority':by_priority,'category':by_category,'technician':by_tech,'status':by_status},'table':table})
