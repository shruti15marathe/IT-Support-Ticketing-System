from flask import Blueprint,request,jsonify
from database import query
from auth import roles
bp=Blueprint('customers',__name__,url_prefix='/api/customers')
@bp.get('')
@roles('admin')
def list_customers(user):
    s=request.args.get('search','%'); s=f'%{s}%' if s!='%' else s
    return jsonify(query("SELECT c.*,u.username FROM customers c LEFT JOIN users u ON u.id=c.user_id WHERE c.company_name LIKE %s OR c.contact_person LIKE %s OR c.email LIKE %s ORDER BY c.id DESC",(s,s,s),fetch=True))
@bp.post('')
@roles('admin')
def create_customer(user):
    d=request.get_json() or {}; req=['company_name','contact_person','email']
    if any(not d.get(x) for x in req): return jsonify({'error':'Required fields missing'}),400
    cid=query("INSERT INTO customers(company_name,contact_person,email,phone,address,status) VALUES(%s,%s,%s,%s,%s,%s)",(d['company_name'],d['contact_person'],d['email'],d.get('phone'),d.get('address'),'active'),commit=True); return jsonify({'id':cid}),201
@bp.put('/<int:cid>')
@roles('admin')
def update_customer(user,cid):
    d=request.get_json() or {}; fields=[]; vals=[]
    for k in ['company_name','contact_person','email','phone','address','status']:
        if k in d: fields.append(k+'=%s'); vals.append(d[k])
    if not fields:return jsonify({'error':'Nothing to update'}),400
    vals.append(cid); query('UPDATE customers SET '+','.join(fields)+' WHERE id=%s',tuple(vals),commit=True); return jsonify({'message':'Updated'})
@bp.get('/<int:cid>')
@roles('admin')
def get_customer(user,cid):
    c=query('SELECT * FROM customers WHERE id=%s',(cid,),fetch=True)
    if not c:return jsonify({'error':'Not found'}),404
    c=c[0]; c['tickets']=query('SELECT ticket_number,subject,status,priority,created_at FROM tickets WHERE customer_id=%s ORDER BY id DESC',(cid,),fetch=True); return jsonify(c)
