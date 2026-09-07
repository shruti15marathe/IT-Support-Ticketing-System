from flask import Blueprint,request,jsonify,current_app,send_from_directory
from datetime import datetime
from database import query,get_connection
from auth import login_required,roles
from utils import add_history,notify,notify_role,save_upload
bp=Blueprint('tickets',__name__,url_prefix='/api/tickets')

BASE_SELECT="""SELECT t.*,c.company_name customer_name,u.full_name creator_name,tech.full_name technician_name,cat.name category_name
FROM tickets t JOIN customers c ON c.id=t.customer_id JOIN users u ON u.id=t.created_by JOIN categories cat ON cat.id=t.category_id
LEFT JOIN users tech ON tech.id=t.assigned_technician_id"""

def visible_clause(user):
    if user['role']=='admin': return '',()
    if user['role']=='technician': return ' AND t.assigned_technician_id=%s',(user['id'],)
    return ' AND t.customer_id=(SELECT id FROM customers WHERE user_id=%s)',(user['id'],)

@bp.get('')
@login_required
def list_tickets(user):
    p=max(int(request.args.get('page',1)),1); limit=min(max(int(request.args.get('limit',10)),1),100); offset=(p-1)*limit
    where=' WHERE 1=1'; vals=[]
    for col,arg in [('t.status','status'),('t.priority','priority'),('t.category_id','category'),('t.assigned_technician_id','technician'),('t.customer_id','customer')]:
        if request.args.get(arg): where+=f' AND {col}=%s'; vals.append(request.args[arg])
    if request.args.get('search'):
        s='%'+request.args['search']+'%'; where+=' AND (t.ticket_number LIKE %s OR t.subject LIKE %s OR c.company_name LIKE %s OR tech.full_name LIKE %s)'; vals += [s,s,s,s]
    if request.args.get('from'): where+=' AND DATE(t.created_at)>=%s'; vals.append(request.args['from'])
    if request.args.get('to'): where+=' AND DATE(t.created_at)<=%s'; vals.append(request.args['to'])
    extra,ev=visible_clause(user); where+=extra; vals+=list(ev)
    allowed_sort={'created_at':'t.created_at','priority':'t.priority','status':'t.status','subject':'t.subject','ticket_number':'t.ticket_number'}; sort=allowed_sort.get(request.args.get('sort'),'t.created_at'); direction='ASC' if request.args.get('dir')=='asc' else 'DESC'
    rows=query(BASE_SELECT+where+f' ORDER BY {sort} {direction} LIMIT %s OFFSET %s',tuple(vals+[limit,offset]),fetch=True)
    total=query('SELECT COUNT(*) n FROM tickets t JOIN customers c ON c.id=t.customer_id LEFT JOIN users tech ON tech.id=t.assigned_technician_id'+where,tuple(vals),fetch=True)[0]['n']
    return jsonify({'items':rows,'page':p,'limit':limit,'total':total,'pages':(total+limit-1)//limit})

@bp.post('')
@login_required
def create_ticket(user):
    d=request.form if request.form else (request.get_json() or {})
    if user['role']=='customer':
        cs=query('SELECT id FROM customers WHERE user_id=%s AND status="active"',(user['id'],),fetch=True); customer_id=cs[0]['id'] if cs else None
    else: customer_id=d.get('customer_id')
    required=[customer_id,d.get('subject'),d.get('description'),d.get('category_id'),d.get('priority') or 'Medium']
    if any(x in (None,'') for x in required): return jsonify({'error':'Customer, subject, description, category and priority are required'}),400
    conn=get_connection(); cur=conn.cursor(); cur.execute("INSERT INTO tickets(ticket_number,customer_id,created_by,subject,description,category_id,priority,status) VALUES('PENDING',%s,%s,%s,%s,%s,%s,'Open')",(customer_id,user['id'],d['subject'],d['description'],d['category_id'],d.get('priority','Medium'))); tid=cur.lastrowid; num=f'TKT-{tid:06d}'; cur.execute('UPDATE tickets SET ticket_number=%s WHERE id=%s',(num,tid)); conn.commit(); cur.close(); conn.close()
    add_history(tid,user['id'],'Ticket created',details=f'Ticket {num} created')
    notify_role('admin',tid,'New ticket created',f'{num} - {d["subject"]}',exclude_id=user['id'])
    if request.files.get('attachment'):
        save_attachment(tid,user,request.files['attachment'])
    return jsonify({'id':tid,'ticket_number':num}),201

def save_attachment(tid,user,file):
    meta=save_upload(file)
    if not meta:return
    query('INSERT INTO ticket_attachments(ticket_id,uploaded_by,original_name,stored_name,file_path,mime_type,file_size) VALUES(%s,%s,%s,%s,%s,%s,%s)',(tid,user['id'],meta['original_name'],meta['stored_name'],meta['file_path'],meta['mime_type'],meta['file_size']),commit=True)
    add_history(tid,user['id'],'Attachment uploaded',details=meta['original_name'])

@bp.get('/<int:tid>')
@login_required
def detail(user,tid):
    extra,ev=visible_clause(user); rows=query(BASE_SELECT+' WHERE t.id=%s'+extra,(tid,*ev),fetch=True)
    if not rows:return jsonify({'error':'Ticket not found'}),404
    t=rows[0]; comments=query("SELECT tc.*,u.full_name,u.role FROM ticket_comments tc JOIN users u ON u.id=tc.user_id WHERE ticket_id=%s AND (is_internal=0 OR %s IN ('admin','technician')) ORDER BY tc.created_at",(tid,user['role']),fetch=True)
    at=query("SELECT a.*,u.full_name uploader FROM ticket_attachments a JOIN users u ON u.id=a.uploaded_by WHERE ticket_id=%s ORDER BY a.created_at",(tid,),fetch=True)
    hist=query("SELECT h.*,u.full_name FROM ticket_history h JOIN users u ON u.id=h.user_id WHERE ticket_id=%s ORDER BY h.created_at DESC",(tid,),fetch=True)
    return jsonify({'ticket':t,'comments':comments,'attachments':at,'history':hist})

@bp.put('/<int:tid>')
@roles('admin')
def edit_ticket(user,tid):
    d=request.get_json() or {}; old=query('SELECT * FROM tickets WHERE id=%s',(tid,),fetch=True)
    if not old:return jsonify({'error':'Not found'}),404
    old=old[0]; fields=[]; vals=[]
    for k in ['subject','description','category_id','priority']:
        if k in d:fields.append(k+'=%s');vals.append(d[k])
    if not fields:return jsonify({'error':'Nothing to update'}),400
    vals.append(tid);query('UPDATE tickets SET '+','.join(fields)+' WHERE id=%s',tuple(vals),commit=True)
    for k in ['subject','category_id','priority']:
        if k in d and str(old[k])!=str(d[k]): add_history(tid,user['id'],f'{k.replace("_"," ").title()} changed',str(old[k]),str(d[k]))
    return jsonify({'message':'Updated'})

@bp.patch('/<int:tid>/assign')
@roles('admin')
def assign(user,tid):
    d=request.get_json() or {}; tech=d.get('technician_id'); old=query('SELECT assigned_technician_id,status,ticket_number FROM tickets WHERE id=%s',(tid,),fetch=True)
    if not old:return jsonify({'error':'Not found'}),404
    old=old[0]; status='Assigned' if tech else 'Open'; query('UPDATE tickets SET assigned_technician_id=%s,status=%s WHERE id=%s',(tech,status,tid),commit=True)
    add_history(tid,user['id'],'Ticket assigned',str(old['assigned_technician_id']),str(tech))
    if tech: notify(int(tech),tid,'Ticket assigned',f'{old["ticket_number"]} has been assigned to you')
    return jsonify({'message':'Assignment updated'})

@bp.patch('/<int:tid>/status')
@login_required
def status(user,tid):
    d=request.get_json() or {}; new=d.get('status'); valid=['Open','Assigned','In Progress','Waiting for Customer','Resolved','Closed','Reopened']
    if new not in valid:return jsonify({'error':'Invalid status'}),400
    t=query('SELECT * FROM tickets WHERE id=%s',(tid,),fetch=True)
    if not t:return jsonify({'error':'Not found'}),404
    t=t[0]
    if user['role']=='technician' and t['assigned_technician_id']!=user['id']:return jsonify({'error':'Not your ticket'}),403
    if user['role']=='customer' and new not in ('Closed','Reopened'):return jsonify({'error':'Customers may confirm closure or reopen'}),403
    if new=='Closed': query('UPDATE tickets SET status=%s,closed_at=NOW() WHERE id=%s',(new,tid),commit=True)
    elif new=='Resolved': query('UPDATE tickets SET status=%s,resolved_at=NOW() WHERE id=%s',(new,tid),commit=True)
    else: query('UPDATE tickets SET status=%s WHERE id=%s',(new,tid),commit=True)
    add_history(tid,user['id'],'Status changed',t['status'],new)
    notify_role('admin',tid,'Status changed',f'{t["ticket_number"]}: {t["status"]} → {new}',exclude_id=user['id'])
    if t['assigned_technician_id'] and t['assigned_technician_id']!=user['id']: notify(t['assigned_technician_id'],tid,'Ticket status changed',f'{t["ticket_number"]} is now {new}')
    if t['customer_id']:
        cu=query('SELECT user_id FROM customers WHERE id=%s',(t['customer_id'],),fetch=True)
        if cu and cu[0]['user_id'] and cu[0]['user_id']!=user['id']: notify(cu[0]['user_id'],tid,'Ticket status changed',f'{t["ticket_number"]} is now {new}')
    return jsonify({'message':'Status updated'})

@bp.post('/<int:tid>/comments')
@login_required
def comment(user,tid):
    d=request.form if request.form else (request.get_json() or {}); text=(d.get('comment') or '').strip(); internal=str(d.get('is_internal','false')).lower() in ('1','true','yes')
    t=query('SELECT * FROM tickets WHERE id=%s',(tid,),fetch=True)
    if not t:return jsonify({'error':'Not found'}),404
    t=t[0]
    if user['role']=='customer': internal=False
    if user['role']=='technician' and t['assigned_technician_id']!=user['id']:return jsonify({'error':'Not your ticket'}),403
    if not text:return jsonify({'error':'Comment is required'}),400
    cid=query('INSERT INTO ticket_comments(ticket_id,user_id,comment,is_internal) VALUES(%s,%s,%s,%s)',(tid,user['id'],text,internal),commit=True)
    add_history(tid,user['id'],'Internal note added' if internal else 'Comment added',details=text[:200])
    if not internal:
        if user['role']=='customer' and t['assigned_technician_id']:notify(t['assigned_technician_id'],tid,'Customer replied',f'{t["ticket_number"]} has a new reply')
        elif user['role']=='technician':notify_role('admin',tid,'Technician commented',f'{t["ticket_number"]} has a new technician comment',exclude_id=user['id'])
    return jsonify({'id':cid}),201

@bp.post('/<int:tid>/attachments')
@login_required
def attachment(user,tid):
    t=query('SELECT * FROM tickets WHERE id=%s',(tid,),fetch=True)
    if not t:return jsonify({'error':'Not found'}),404
    if user['role']=='technician' and t[0]['assigned_technician_id']!=user['id']:return jsonify({'error':'Not your ticket'}),403
    try: save_attachment(tid,user,request.files.get('file')); return jsonify({'message':'Uploaded'}),201
    except ValueError as e:return jsonify({'error':str(e)}),400

@bp.get('/attachments/<path:filename>')
@login_required
def download(user,filename): return send_from_directory(current_app.config['UPLOAD_FOLDER'],filename,as_attachment=True)
