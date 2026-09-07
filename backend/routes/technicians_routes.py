from flask import Blueprint, render_template

technician_bp = Blueprint("technician", __name__)
@technician_bp.route("/technicians")
def technician_page():
    return render_template("technicians.html")
from flask import Blueprint,request,jsonify
from database import query
from auth import roles,hash_password
bp=Blueprint('technicians',__name__,url_prefix='/api/technicians')
@bp.get('')
@roles('admin')
def technicians(user):
    return jsonify(query("SELECT u.id,u.username,u.email,u.full_name,u.phone,u.department,u.skills,u.status,u.joining_date,COUNT(t.id) assigned_count FROM users u LEFT JOIN tickets t ON t.assigned_technician_id=u.id WHERE u.role='technician' GROUP BY u.id ORDER BY u.full_name",fetch=True))
@bp.post('')
@roles('admin')
def add(user):
    d=request.get_json() or {}
    req=['username','email','password','full_name']
    if any(not d.get(x) for x in req): return jsonify({'error':'Required fields missing'}),400
    uid=query("INSERT INTO users(username,email,password_hash,role,full_name,phone,department,skills,status,joining_date) VALUES(%s,%s,%s,'technician',%s,%s,%s,%s,'active',%s)",(d['username'],d['email'],hash_password(d['password']),d['full_name'],d.get('phone'),d.get('department'),d.get('skills'),d.get('joining_date')),commit=True); return jsonify({'id':uid}),201
@bp.put('/<int:uid>')
@roles('admin')
def edit(user,uid):
    d=request.get_json() or {}; fields=[]; vals=[]
    for k in ['full_name','email','phone','department','skills','status','joining_date']:
        if k in d: fields.append(k+'=%s'); vals.append(d[k])
    if d.get('password'): fields.append('password_hash=%s'); vals.append(hash_password(d['password']))
    vals.append(uid); query("UPDATE users SET "+','.join(fields)+" WHERE id=%s AND role='technician'",tuple(vals),commit=True); return jsonify({'message':'Updated'})
